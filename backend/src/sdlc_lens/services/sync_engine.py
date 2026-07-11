"""Sync engine - collects files from sources, parses documents, manages DB records."""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy import text as sql_text

from sdlc_lens.config import settings
from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.parser import parse_document
from sdlc_lens.services.project_config import (
    ProjectConfig,
    parse_project_config,
    read_local_project_config,
)
from sdlc_lens.utils.hashing import compute_hash
from sdlc_lens.utils.inference import infer_type_and_id
from sdlc_lens.utils.sdlc_ids import extract_ref_id, id_head, norm_id
from sdlc_lens.utils.sdlc_status import canonical_status

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

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


def _walk_local_files(sdlc_path: str) -> tuple[dict[str, tuple[str, bytes]], int]:
    """Synchronous filesystem walk + read for local .md files.

    Walks the directory tree, computes SHA-256 hashes, and returns a dict of
    {relative_path: (hash, raw_bytes)} plus an error count. This is blocking
    CPU/IO work, so it is invoked from a worker thread (see
    ``collect_local_files``) rather than inline on the event loop.
    """
    root = Path(sdlc_path)
    fs_files: dict[str, tuple[str, bytes]] = {}
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
            logger.warning("Cannot read %s: %s", md_file, exc)
            errors += 1
            continue

        file_hash = compute_hash(raw)
        fs_files[rel_path] = (file_hash, raw)

    return fs_files, errors


async def collect_local_files(sdlc_path: str) -> tuple[dict[str, tuple[str, bytes]], int]:
    """Collect .md files from the local filesystem.

    Offloads the blocking directory walk and per-file read to a worker thread
    so the event loop stays responsive during a sync. Returns a dict of
    {relative_path: (hash, raw_bytes)} plus an error count.

    Args:
        sdlc_path: Absolute path to the sdlc-studio directory.

    Returns:
        Tuple of (files_dict, error_count).
    """
    return await asyncio.to_thread(_walk_local_files, sdlc_path)


async def collect_github_files(
    project: Project,
) -> tuple[dict[str, tuple[str, bytes]], ProjectConfig]:
    """Collect .md files and project config from a GitHub repository.

    Delegates to the github_source module which downloads the repository
    tarball once and extracts both the .md tree and the ``.config.yaml`` /
    ``.version`` metadata sitting at the repo_path root.

    Args:
        project: Project with source_type="github" and repo fields set.

    Returns:
        Tuple of ({relative_path: (hash, content)}, parsed ProjectConfig). The
        config is parsed best-effort; a missing or malformed one yields an
        empty :class:`ProjectConfig`.
    """
    from sdlc_lens.services.github_source import fetch_github_files_and_config
    from sdlc_lens.utils.crypto import decrypt_token

    fs_files, config_files = await fetch_github_files_and_config(
        repo_url=project.repo_url,
        branch=project.repo_branch,
        repo_path=project.repo_path,
        # Decrypt the at-rest token back to the real PAT for the API call.
        access_token=decrypt_token(project.access_token),
    )
    return fs_files, _parse_github_config(config_files)


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
        for rel_path, (file_hash, raw) in fs_files.items():
            doc = existing_docs.get(rel_path)

            # A legacy row from before migration 007's backfill has ref_id=NULL
            # even though its id resolves to one; reparse it on a matching hash so
            # the reference-resolution columns populate. Singletons (prd, trd, ...)
            # have no artefact id head and legitimately keep ref_id=NULL, so they
            # are not treated as needing a backfill.
            needs_ref_backfill = (
                doc is not None and doc.ref_id is None and norm_id(id_head(doc.doc_id)) is not None
            )
            if doc is not None and doc.file_hash == file_hash and not needs_ref_backfill:
                # Skip - unchanged
                result.skipped += 1
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

        # Step 4: Delete documents no longer in source
        for rel_path, doc in existing_docs.items():
            if rel_path not in fs_files:
                await session.delete(doc)
                result.deleted += 1

        # Step 5: Update project status
        project.sync_status = "synced"
        project.last_synced_at = datetime.datetime.now(datetime.UTC)
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
