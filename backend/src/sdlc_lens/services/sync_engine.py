"""Sync engine - collects files from sources, parses documents, manages DB records."""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from sqlalchemy import select
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import async_object_session

from sdlc_lens.config import settings
from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.parser import parse_document
from sdlc_lens.services.project_config import (
    ProjectConfig,
    parse_project_config,
    read_local_project_config,
)
from sdlc_lens.utils.hashing import compute_blob_sha, compute_hash
from sdlc_lens.utils.inference import infer_type_and_id
from sdlc_lens.utils.sdlc_ids import extract_ref_id, id_head, norm_id
from sdlc_lens.utils.sdlc_status import canonical_status

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Parser/schema epoch. Bump this whenever the parsing, inference or
# canonicalisation logic that feeds a document's derived columns (doc_type,
# status, epic/story, ref_id, depends_on, aliases) changes. A stored row below
# the current epoch is re-parsed on the next sync even when its content hash is
# unchanged, so a byte-identical document heals its derived fields after an app
# upgrade instead of keeping the values an older build computed. Existing rows
# default to 0 (pre-epoch) and re-parse once to reach the current epoch.
PARSER_EPOCH = 1

# Directories to skip during filesystem walk
_EXCLUDED_DIRS = frozenset(
    {
        ".venv",
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        "node_modules",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".eggs",
    }
)


@dataclass
class SyncResult:
    """Counts for each sync operation."""

    added: int = 0
    updated: int = 0
    skipped: int = 0
    deleted: int = 0
    errors: int = 0


# Standard metadata fields stored as dedicated columns
_STANDARD_FIELDS = frozenset(
    {"status", "owner", "priority", "story_points", "epic", "story", "depends_on", "aliases"}
)

# Reference extraction now lives in utils.sdlc_ids and handles sequential, hyphenated
# and v3 ULID ids plus wiki-links. Kept under the historical name for callers/tests.
extract_doc_id = extract_ref_id


def _norm_ref(value: str | None) -> str | None:
    """The normalised id of a single reference value (link/plain/bare), or None."""
    return norm_id(extract_ref_id(value))


def _norm_ref_list(value: str | None) -> str | None:
    """Normalise a comma/space-separated list of references to a comma-joined string.

    Used for ``Depends on`` and ``Aliases`` (which may name several ids). Returns None
    when no ids are found.
    """
    if not value:
        return None
    ids: list[str] = []
    for chunk in re.split(r"[,\s]+", value):
        normed = _norm_ref(chunk)
        if normed and normed not in ids:
            ids.append(normed)
    return ",".join(ids) if ids else None


class FileEntry(NamedTuple):
    """One path in a sync manifest.

    The manifest is **complete**: it holds an entry for **every** live path in the
    source, always. Only ``raw`` is optional.

    That distinction is load-bearing, and it is the whole reason this type exists.
    ``sync_project`` decides two things from the manifest:

    * whether the source is empty ("source returned no documents - refusing to delete
      existing documents") - the guard that fixes **BG-01KX8BFP**, a High-severity
      silent-data-loss bug; and
    * which documents no longer exist upstream and should be deleted.

    An incremental sync fetches only the blobs that changed, so the obvious design -
    passing just the changed files - would hand those two checks an *empty or partial*
    dict on a perfectly healthy no-op sync. The guard would fire spuriously, and the
    deletion loop would consider every document absent. That regresses a High-severity
    data-loss bug on the commonest path in the system.

    So the manifest keeps every path and unchanged files simply carry ``raw=None``. The
    guard and the deletion loop are then correct *by construction* and need no special
    case - the failure is not defended against, it is unrepresentable.

    ``raw is None`` means "this file is byte-identical to what is stored; do not fetch
    it, do not re-parse it". Anything that *does* need re-parsing (a stale parser epoch,
    a NULL blob_sha) must arrive with real bytes - the path selector is responsible for
    that (RFC-01KXARHK, D7), and ``sync_project`` fails loud rather than silently
    skipping if it is ever handed a contentless entry it must parse.
    """

    file_hash: str
    """sha256 of the raw bytes - ours, used to detect a byte change.

    For a contentless entry (``raw is None``) this must be the hash the source believes
    the file currently has - i.e. byte-exact with the stored ``doc.file_hash`` when the
    file really is unchanged. That is what makes the skip fire. A fetcher that echoes a
    wrong hash here sends the entry into the fail-loud branch rather than silently
    corrupting the row.

    Empty string when ``unreadable``: there are no bytes, so there is no hash.
    """

    raw: bytes | None
    """The file's bytes, or None when the file is known-unchanged and was not fetched."""

    blob_sha: str
    """git blob SHA-1 of the raw bytes - what GitHub's Trees API reports per path."""

    unreadable: bool = False
    """The path EXISTS in the source but its bytes could not be obtained this sync.

    A permission error, an EIO, an NFS blip, a file locked by an editor mid-walk. This
    is emphatically **not** the same as "deleted upstream", and conflating the two is
    silent data loss: the deletion loop treats a path's ABSENCE from the manifest as
    "gone", so a file that merely failed to read must still appear here, or its document
    is destroyed while it sits perfectly intact on disk.

    That is BG-01KX8BFP's failure class, and it was live on the local walker: a single
    `chmod 000` on one file deleted its document and still reported `sync_status=synced`.
    Keeping the path in the manifest fixes it *by construction* - the invariant that
    every live path is a key becomes true, rather than merely asserted.
    """


def _walk_md_files(root: Path) -> list[Path]:
    """Walk directory tree for *.md files, skipping excluded directories."""
    results: list[Path] = []
    for child in sorted(root.iterdir()):
        if child.is_dir():
            if child.name in _EXCLUDED_DIRS or child.name.startswith("."):
                continue
            results.extend(_walk_md_files(child))
        elif child.is_file() and child.suffix == ".md":
            results.append(child)
    return results


def _walk_local_files(sdlc_path: str) -> tuple[dict[str, FileEntry], int]:
    """Synchronous filesystem walk + read for local .md files.

    Walks the directory tree and returns a complete manifest of
    {relative_path: FileEntry} plus an error count. A local walk always has the bytes
    in hand, so every entry carries ``raw`` - a local source is never incremental.
    This is blocking CPU/IO work, so it is invoked from a worker thread (see
    ``collect_local_files``) rather than inline on the event loop.
    """
    root = Path(sdlc_path)
    fs_files: dict[str, FileEntry] = {}
    errors = 0

    for md_file in sorted(_walk_md_files(root)):
        rel_path = str(md_file.relative_to(root))
        filename = md_file.name

        # Skip _index.md files
        inference = infer_type_and_id(filename, rel_path)
        if inference is None:
            continue

        try:
            raw = md_file.read_bytes()
        except (PermissionError, OSError) as exc:
            # The file EXISTS - the walk just found it - we simply cannot read it right
            # now. It must still enter the manifest, or the deletion loop will read its
            # absence as "deleted upstream" and destroy a document that is sitting intact
            # on disk. (Confirmed: a `chmod 000` on one file used to delete its document
            # and still report sync_status=synced.)
            logger.warning("Cannot read %s: %s", md_file, exc)
            errors += 1
            fs_files[rel_path] = FileEntry(
                file_hash="",
                raw=None,
                blob_sha="",
                unreadable=True,
            )
            continue

        fs_files[rel_path] = FileEntry(
            file_hash=compute_hash(raw),
            raw=raw,
            blob_sha=compute_blob_sha(raw),
        )

    return fs_files, errors


async def collect_local_files(sdlc_path: str) -> tuple[dict[str, FileEntry], int]:
    """Collect .md files from the local filesystem.

    Offloads the blocking directory walk and per-file read to a worker thread
    so the event loop stays responsive during a sync. Returns a complete manifest
    of {relative_path: FileEntry} plus an error count.

    Args:
        sdlc_path: Absolute path to the sdlc-studio directory.

    Returns:
        Tuple of (manifest, error_count).
    """
    return await asyncio.to_thread(_walk_local_files, sdlc_path)


async def resolve_sync_token(project: Project) -> str | None:
    """The token a GitHub sync should authenticate with, decrypted.

    Precedence (CR-01KXAZX9): a stored connection's token when the project has a
    ``connection_id``, otherwise the project's own ``access_token``. Existing
    projects therefore keep working untouched - no stored secret is migrated.

    A ``connection_id`` that cannot be resolved is a hard failure, never a
    fallback. In production the column carries no foreign key (migration 011 adds
    a plain nullable column, since SQLite cannot ALTER-add an FK), so an orphaned
    reference is genuinely possible - and falling back would sync a private repo
    unauthenticated and report the misleading "Repository not found".

    Raises:
        ConnectionNotFoundError: If ``connection_id`` names no stored connection.
        AuthenticationError: If the connection's token cannot be decrypted.
    """
    from sdlc_lens.services.github_connection import (
        ConnectionNotFoundError,
        resolve_connection_token,
    )
    from sdlc_lens.utils.crypto import decrypt_token

    if project.connection_id is None:
        return decrypt_token(project.access_token)

    session = async_object_session(project)
    if session is None:
        raise ConnectionNotFoundError(
            f"Project {project.slug} uses GitHub connection {project.connection_id}, "
            "which could not be loaded (the project is detached from its session)"
        )

    try:
        return await resolve_connection_token(session, project.connection_id)
    except ConnectionNotFoundError as exc:
        raise ConnectionNotFoundError(
            f"Project {project.slug} uses GitHub connection {project.connection_id}, "
            "which no longer exists. Re-point the project at a stored connection, "
            "or detach it and give the project its own token."
        ) from exc


async def collect_github_files(
    project: Project,
) -> tuple[dict[str, FileEntry], ProjectConfig]:
    """Collect .md files and project config from a GitHub repository.

    Delegates to the github_source module which downloads the repository
    tarball once and extracts both the .md tree and the ``.config.yaml`` /
    ``.version`` metadata sitting at the repo_path root.

    The tarball path always has every file's bytes, so every entry here carries
    ``raw``. The incremental Trees+Blobs path (US-01KXCCTV) is what will start
    returning contentless entries for unchanged files.

    Args:
        project: Project with source_type="github" and repo fields set.

    Returns:
        Tuple of (manifest, parsed ProjectConfig). The config is parsed
        best-effort; a missing or malformed one yields an empty
        :class:`ProjectConfig`.
    """
    from sdlc_lens.services.github_source import fetch_github_files_and_config

    raw_files, config_files = await fetch_github_files_and_config(
        repo_url=project.repo_url,
        branch=project.repo_branch,
        repo_path=project.repo_path,
        # The real PAT for the API call: the connection's token when one is
        # attached, else the project's own - decrypted either way.
        access_token=await resolve_sync_token(project),
    )
    manifest = {
        rel_path: FileEntry(
            file_hash=file_hash,
            raw=raw,
            blob_sha=compute_blob_sha(raw),
        )
        for rel_path, (file_hash, raw) in raw_files.items()
    }
    return manifest, _parse_github_config(config_files)


def _decode_config_bytes(raw: bytes | None) -> str | None:
    """Decode raw config bytes to text, tolerating a BOM; None if undecodable."""
    if raw is None:
        return None
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None


def _parse_github_config(config_files: dict[str, bytes]) -> ProjectConfig:
    """Parse ``.config.yaml`` / ``.version`` bytes into a :class:`ProjectConfig`.

    Best-effort: missing or unparseable config yields an empty config so a
    github sync is never failed by bad metadata.
    """
    return parse_project_config(
        _decode_config_bytes(config_files.get(".config.yaml")),
        _decode_config_bytes(config_files.get(".version")),
    )


def _build_doc_attrs(
    parsed_meta: dict,
    parsed_title: str | None,
    parsed_body: str,
    doc_type: str,
    doc_id: str,
    file_path: str,
    file_hash: str,
    project_id: int,
    status_vocab: dict[str, list[str]] | None = None,
    blob_sha: str | None = None,
) -> dict:
    """Build a dict of Document column values from parsed data.

    ``status_vocab`` is the project's parsed custom vocabulary; the tokens for
    this ``doc_type`` are fed to :func:`canonical_status` so project-defined
    statuses canonicalise to themselves.
    """
    # Separate standard fields from extra metadata
    extra = {k: v for k, v in parsed_meta.items() if k not in _STANDARD_FIELDS}
    extra_vocab = status_vocab.get(doc_type) if status_vocab else None

    return {
        "project_id": project_id,
        "doc_type": doc_type,
        "doc_id": doc_id,
        "title": parsed_title or doc_id,
        "status": canonical_status(parsed_meta.get("status"), doc_type, extra_vocab=extra_vocab),
        "owner": parsed_meta.get("owner"),
        "priority": parsed_meta.get("priority"),
        "story_points": parsed_meta.get("story_points"),
        "epic": _norm_ref(parsed_meta.get("epic")),
        "story": _norm_ref(parsed_meta.get("story")),
        "ref_id": norm_id(id_head(doc_id)),
        "depends_on": _norm_ref_list(parsed_meta.get("depends_on")),
        "aliases": _norm_ref_list(parsed_meta.get("aliases")),
        "metadata_json": json.dumps(extra) if extra else None,
        "content": parsed_body,
        "file_path": file_path,
        "file_hash": file_hash,
        "blob_sha": blob_sha,
        "parser_epoch": PARSER_EPOCH,
        "synced_at": datetime.datetime.now(datetime.UTC),
    }


async def _rebuild_fts_if_exists(session: AsyncSession) -> None:
    """Rebuild FTS5 index if the virtual table exists."""
    row = await session.execute(
        sql_text("SELECT name FROM sqlite_master WHERE name='documents_fts' AND type='table'")
    )
    if row.scalar_one_or_none() is None:
        # The FTS virtual table is absent - nothing to rebuild. This is the only
        # condition the guard covers; a real rebuild failure below is not swallowed.
        return

    from sdlc_lens.services.fts import fts_rebuild

    try:
        await fts_rebuild(session)
        await session.commit()
    except Exception:
        logger.warning("FTS5 rebuild failed after sync; search index may be stale", exc_info=True)


async def sync_project(
    project: Project,
    session: AsyncSession,
) -> SyncResult:
    """Sync documents from a project's configured source.

    Dispatches to the appropriate file collector based on source_type,
    then processes the collected files: compare hashes, parse new/changed
    documents, delete removed documents, and rebuild the FTS index.

    Args:
        project: The Project ORM instance.
        session: Async database session.

    Returns:
        SyncResult with counts for each operation.
    """
    result = SyncResult()
    project_id = project.id

    # Validate source configuration
    if project.source_type == "local":
        if not project.sdlc_path:
            project.sync_status = "error"
            project.sync_error = "No sdlc_path configured for local project"
            await session.commit()
            return result

        root = Path(project.sdlc_path)
        if not root.is_dir():
            project.sync_status = "error"
            project.sync_error = f"Path not found: {project.sdlc_path}"
            await session.commit()
            return result

        # Defence in depth: refuse to walk a stored sdlc_path outside the
        # configured allowlist base, so a path that slipped past registration
        # cannot be harvested. When allowed_project_base is unset (None), no
        # restriction applies (backward compatible).
        if settings.allowed_project_base is not None:
            base = Path(settings.allowed_project_base).resolve()
            if not root.resolve().is_relative_to(base):
                project.sync_status = "error"
                project.sync_error = "sdlc_path is outside the allowed base"
                await session.commit()
                return result
    elif project.source_type == "github":
        if not project.repo_url:
            project.sync_status = "error"
            project.sync_error = "No repo_url configured for GitHub project"
            await session.commit()
            return result

    # Set project to syncing
    project.sync_status = "syncing"
    await session.flush()

    config = ProjectConfig()

    try:
        # Step 1: Collect files from configured source
        if project.source_type == "local":
            fs_files, collect_errors = await collect_local_files(project.sdlc_path)
            result.errors += collect_errors
            # Best-effort: read .config.yaml / .version alongside the collected tree.
            # A missing or malformed config must not fail the sync.
            config = await asyncio.to_thread(read_local_project_config, project.sdlc_path)
            project.schema_version = config.schema_version
            project.profile = config.profile
            project.status_vocab = json.dumps(config.status_vocab) if config.status_vocab else None
        elif project.source_type == "github":
            # collect_github_files reads .config.yaml / .version from the tarball
            # alongside the .md tree. Best-effort, exactly like the local branch:
            # a missing or malformed config yields an empty ProjectConfig.
            fs_files, config = await collect_github_files(project)
            project.schema_version = config.schema_version
            project.profile = config.profile
            project.status_vocab = json.dumps(config.status_vocab) if config.status_vocab else None
        else:
            project.sync_status = "error"
            project.sync_error = f"Unknown source_type: {project.source_type}"
            await session.commit()
            return result

        # Step 2: Load existing documents from DB
        db_result = await session.execute(
            select(Document).where(Document.project_id == project_id)
        )
        existing_docs = {doc.file_path: doc for doc in db_result.scalars().all()}

        # Guard: refuse to wipe existing documents when the source yields nothing.
        # An empty result usually means a misconfigured repo_path/branch, an
        # emptied local directory, or a partial fetch - not a genuine deletion of
        # every document. Deleting all records here would be silent data loss, so
        # treat it as a sync failure and preserve the existing documents.
        if not fs_files and existing_docs:
            project.sync_status = "error"
            project.sync_error = (
                "source returned no documents - refusing to delete existing documents"
            )
            await session.commit()
            return result

        # Step 3: Process collected files
        #
        # NOTE the guard above and the deletion loop below both key off `fs_files`, and
        # `fs_files` is the COMPLETE manifest - every live path, whether or not its bytes
        # were fetched. Neither needs to know that content is optional, and neither must
        # ever be re-keyed to "the files we fetched": on a no-op incremental sync that set
        # is empty, which would read as an empty source (BG-01KX8BFP) or delete every
        # document. See FileEntry's docstring.
        for rel_path, entry in fs_files.items():
            file_hash = entry.file_hash
            raw = entry.raw
            doc = existing_docs.get(rel_path)

            # The path exists but we could not read its bytes this run. Leave the stored
            # document exactly as it is: an unreadable file is NOT a deleted file, and
            # the row we hold is still the best copy we have. It stays in fs_files, so
            # the deletion loop below leaves it alone.
            #
            # Not counted here: the collector already counted it (`collect_errors`), and
            # that count is folded into `result.errors` above. Counting again would
            # double-report and mislead.
            if entry.unreadable:
                continue

            # A stored row whose parser_epoch is below the current PARSER_EPOCH was
            # derived by an older parser/inference/canonicalisation build; reparse it
            # on a matching hash so doc_type, status, ref_id, epic/story, depends_on
            # and aliases recompute after an app upgrade rather than staying stale.
            # This generalises the ref_id-null self-heal: legacy rows (epoch 0) are
            # reparsed regardless of ref_id, while a singleton with ref_id=NULL still
            # settles once its epoch is current instead of re-parsing every sync.
            stale_epoch = doc is not None and (doc.parser_epoch or 0) < PARSER_EPOCH
            # Belt-and-braces: also reparse a legacy row from before migration 007's
            # backfill that carries ref_id=NULL even though its id resolves to one.
            # Singletons (prd, trd, ...) have no artefact id head and legitimately
            # keep ref_id=NULL, so they are not treated as needing a backfill.
            needs_ref_backfill = (
                doc is not None and doc.ref_id is None and norm_id(id_head(doc.doc_id)) is not None
            )
            # Same self-heal, for blob_sha. Every row in a database migrated from before
            # 012 carries blob_sha=NULL. Without this clause a byte-unchanged file is
            # skipped, so those rows stay NULL FOREVER - the project is permanently
            # "unknown", permanently takes the tarball path, and incremental sync never
            # engages for a single existing install. The tarball only "backfills" because
            # this makes the row eligible to be rewritten; fetching the bytes is not
            # enough on its own.
            needs_blob_sha_backfill = doc is not None and doc.blob_sha is None
            if (
                doc is not None
                and doc.file_hash == file_hash
                and not stale_epoch
                and not needs_ref_backfill
                and not needs_blob_sha_backfill
            ):
                # Skip - unchanged content and derived state already current
                result.skipped += 1
                continue

            # Past the skip, so this document MUST be re-parsed - and re-parsing needs
            # real bytes. Reaching here with raw=None is a contradiction: the path
            # selector is required to fetch (or fall back to a tarball for) anything
            # that needs a reparse - a changed blob, a stale parser epoch, a NULL
            # blob_sha (RFC-01KXARHK, D7).
            #
            # We do NOT paper over it by skipping. A silent skip would leave the document
            # on stale derived fields for ever while the sync reported success - which is
            # BG-01KXARHJ all over again, and a tool must fail loud rather than report a
            # success it did not achieve (LL0008). And we cannot re-parse from the stored
            # `content` column: that column holds body-only text with the frontmatter
            # blockquote stripped (parser.py:183), so status/epic/story/depends_on/aliases
            # simply are not in it.
            if raw is None:
                logger.error(
                    "Sync bug: %s needs a reparse but arrived with no content "
                    "(changed=%s stale_epoch=%s ref_backfill=%s blob_sha_backfill=%s). "
                    "The fetch path must supply bytes for anything needing a reparse.",
                    rel_path,
                    doc is None or doc.file_hash != file_hash,
                    stale_epoch,
                    needs_ref_backfill,
                    needs_blob_sha_backfill,
                )
                result.errors += 1
                continue

            # We have the bytes, so the manifest's blob_sha is checkable - CHECK IT.
            # We store `entry.blob_sha` (the source's word) rather than recomputing, so a
            # source that lies about a path's SHA would poison the row permanently: the
            # skip condition never revisits a non-NULL blob_sha, so every future
            # incremental diff for that path would be wrong for ever - either "changed"
            # on every sync (defeating the feature) or "unchanged" for ever (the document
            # never updates again). Trusting one side silently is no better than
            # recomputing and diverging silently; the only honest option is to detect it.
            actual_blob_sha = compute_blob_sha(raw)
            if entry.blob_sha != actual_blob_sha:
                logger.error(
                    "Sync bug: %s manifest blob_sha %r does not match its bytes (%r). "
                    "Refusing to store a blob SHA the content contradicts.",
                    rel_path,
                    entry.blob_sha,
                    actual_blob_sha,
                )
                result.errors += 1
                continue

            # Parse the file content
            try:
                text = raw.decode("utf-8-sig")  # strips BOM
            except UnicodeDecodeError:
                logger.warning("Cannot decode %s as UTF-8, skipping", rel_path)
                result.errors += 1
                continue

            parsed = parse_document(text)
            filename = Path(rel_path).name
            inference = infer_type_and_id(filename, rel_path)
            if inference is None:
                continue

            attrs = _build_doc_attrs(
                parsed_meta=parsed.metadata,
                parsed_title=parsed.title,
                parsed_body=parsed.body,
                doc_type=inference.doc_type,
                doc_id=inference.doc_id,
                file_path=rel_path,
                file_hash=file_hash,
                project_id=project_id,
                status_vocab=config.status_vocab,
                # Taken from the manifest, not recomputed. Under an incremental sync the
                # Trees response is the authority on a path's blob SHA, and re-deriving
                # it here from the bytes would silently diverge if the two ever disagreed
                # - precisely the mismatch we would least want to paper over.
                blob_sha=entry.blob_sha,
            )

            if doc is not None:
                # Update - changed hash
                for key, value in attrs.items():
                    if key != "project_id":
                        setattr(doc, key, value)
                result.updated += 1
            else:
                # Add - new file
                new_doc = Document(**attrs)
                session.add(new_doc)
                result.added += 1

        # Step 4: Delete documents no longer in source.
        #
        # Keyed on the MANIFEST, never on "what we fetched". A path is absent here only
        # when the source genuinely no longer has it: an unchanged file is present with
        # raw=None, and an unreadable file is present with unreadable=True. Both survive.
        for rel_path, doc in existing_docs.items():
            if rel_path not in fs_files:
                await session.delete(doc)
                result.deleted += 1

        # Step 5: Update project status.
        #
        # A sync that could not process some of its files did NOT fully succeed, and must
        # not claim it did. Reporting "synced" with a fresh timestamp while N documents
        # were skipped unreadable - or left rotting on stale derived fields - is exactly
        # the silent-success failure LL0008 forbids: a tool must never report a success it
        # did not achieve. The counts are surfaced in sync_error so the operator can see
        # WHAT was missed, not merely that something was.
        project.last_synced_at = datetime.datetime.now(datetime.UTC)
        if result.errors:
            project.sync_status = "error"
            project.sync_error = (
                f"{result.errors} file(s) could not be synced and were left unchanged; "
                f"{result.added} added, {result.updated} updated, {result.deleted} deleted. "
                "Their stored documents are preserved - see the server log for each path."
            )
        else:
            project.sync_status = "synced"
            project.sync_error = None

        await session.commit()

        # Step 6: Rebuild FTS5 index if table exists
        await _rebuild_fts_if_exists(session)

    except Exception as exc:
        await session.rollback()
        # Re-fetch project after rollback
        proj = await session.get(Project, project_id)
        if proj:
            proj.sync_status = "error"
            proj.sync_error = str(exc)
            await session.commit()
        logger.exception("Sync failed for project %d: %s", project_id, exc)

    return result
