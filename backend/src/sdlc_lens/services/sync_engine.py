"""Sync engine - collects files from sources, parses documents, manages DB records."""

from __future__ import annotations

import datetime
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy import text as sql_text

from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.parser import parse_document
from sdlc_lens.utils.hashing import compute_hash
from sdlc_lens.utils.inference import infer_type_and_id

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Directories to skip during filesystem walk
_EXCLUDED_DIRS = frozenset({
    ".venv", ".git", ".hg", ".svn", "__pycache__",
    "node_modules", ".tox", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", "dist", "build", ".eggs",
})


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
    {"status", "owner", "priority", "story_points", "epic", "story"}
)

# Matches the document ID at the start of a markdown link text.
# e.g. "[EP0007: Git Repository Sync](../epics/...)" captures "EP0007"
# e.g. "[US0028](../stories/...)" captures "US0028"
_MD_LINK_ID_RE = re.compile(r"^\[([A-Z]{2}\d{4})")

# Matches a clean document ID prefix in plain text.
# e.g. "EP0007" or "US0163: Container Service Status" captures the ID prefix.
_PLAIN_ID_RE = re.compile(r"^([A-Z]{2}\d{4})\b")


def extract_doc_id(value: str | None) -> str | None:
    """Extract a clean document ID from a markdown link or plain text.

    Handles values like:
      - ``[EP0007: Git Repository Sync](../epics/EP0007-...md)`` → ``EP0007``
      - ``[US0028](../stories/US0028-...md)`` → ``US0028``
      - ``US0163: Container Service Status`` → ``US0163``
      - ``EP0007`` → ``EP0007`` (returned unchanged)
      - ``None`` or ``""`` → ``None``
    """
    if not value or not value.strip():
        return None
    stripped = value.strip()
    match = _MD_LINK_ID_RE.match(stripped)
    if match:
        return match.group(1)
    match = _PLAIN_ID_RE.match(stripped)
    if match:
        return match.group(1)
    return stripped


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


def collect_local_files(sdlc_path: str) -> tuple[dict[str, tuple[str, bytes]], int]:
    """Collect .md files from the local filesystem.

    Walks the directory tree, computes SHA-256 hashes, and returns
    a dict of {relative_path: (hash, raw_bytes)} plus an error count.

    Args:
        sdlc_path: Absolute path to the sdlc-studio directory.

    Returns:
        Tuple of (files_dict, error_count).
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


async def collect_github_files(project: Project) -> dict[str, tuple[str, bytes]]:
    """Collect .md files from a GitHub repository.

    Delegates to the github_source module which uses the GitHub REST API
    (Trees + Blobs) to fetch files.

    Args:
        project: Project with source_type="github" and repo fields set.

    Returns:
        Dict mapping relative file paths to (hash, content) tuples.
    """
    from sdlc_lens.services.github_source import fetch_github_files

    return await fetch_github_files(
        repo_url=project.repo_url,
        branch=project.repo_branch,
        repo_path=project.repo_path,
        access_token=project.access_token,
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
) -> dict:
    """Build a dict of Document column values from parsed data."""
    # Separate standard fields from extra metadata
    extra = {
        k: v
        for k, v in parsed_meta.items()
        if k not in _STANDARD_FIELDS
    }

    return {
        "project_id": project_id,
        "doc_type": doc_type,
        "doc_id": doc_id,
        "title": parsed_title or doc_id,
        "status": parsed_meta.get("status"),
        "owner": parsed_meta.get("owner"),
        "priority": parsed_meta.get("priority"),
        "story_points": parsed_meta.get("story_points"),
        "epic": extract_doc_id(parsed_meta.get("epic")),
        "story": extract_doc_id(parsed_meta.get("story")),
        "metadata_json": json.dumps(extra) if extra else None,
        "content": parsed_body,
        "file_path": file_path,
        "file_hash": file_hash,
        "synced_at": datetime.datetime.now(datetime.UTC),
    }


async def _rebuild_fts_if_exists(session: AsyncSession) -> None:
    """Rebuild FTS5 index if the virtual table exists."""
    try:
        row = await session.execute(
            sql_text(
                "SELECT name FROM sqlite_master "
                "WHERE name='documents_fts' AND type='table'"
            )
        )
        if row.scalar_one_or_none() is not None:
            from sdlc_lens.services.fts import fts_rebuild

            await fts_rebuild(session)
            await session.commit()
    except Exception:
        logger.debug("FTS5 rebuild skipped (table may not exist)")


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
    elif project.source_type == "github":
        if not project.repo_url:
            project.sync_status = "error"
            project.sync_error = "No repo_url configured for GitHub project"
            await session.commit()
            return result

    # Set project to syncing
    project.sync_status = "syncing"
    await session.flush()

    try:
        # Step 1: Collect files from configured source
        if project.source_type == "local":
            fs_files, collect_errors = collect_local_files(project.sdlc_path)
            result.errors += collect_errors
        elif project.source_type == "github":
            fs_files = await collect_github_files(project)
        else:
            project.sync_status = "error"
            project.sync_error = f"Unknown source_type: {project.source_type}"
            await session.commit()
            return result

        # Step 2: Load existing documents from DB
        db_result = await session.execute(
            select(Document).where(
                Document.project_id == project_id
            )
        )
        existing_docs = {
            doc.file_path: doc for doc in db_result.scalars().all()
        }

        # Step 3: Process collected files
        for rel_path, (file_hash, raw) in fs_files.items():
            doc = existing_docs.get(rel_path)

            if doc is not None and doc.file_hash == file_hash:
                # Skip - unchanged
                result.skipped += 1
                continue

            # Parse the file content
            try:
                text = raw.decode("utf-8-sig")  # strips BOM
            except UnicodeDecodeError:
                logger.warning(
                    "Cannot decode %s as UTF-8, skipping", rel_path
                )
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
        logger.exception(
            "Sync failed for project %d: %s", project_id, exc
        )

    return result
