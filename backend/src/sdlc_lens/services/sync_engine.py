"""Sync engine - walks filesystem, parses documents, manages DB records."""

from __future__ import annotations

import datetime
import json
import logging
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
    {"status", "owner", "priority", "story_points", "epic"}
)


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
        "epic": parsed_meta.get("epic"),
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
    project_id: int,
    sdlc_path: str,
    session: AsyncSession,
) -> SyncResult:
    """Sync documents from a project's sdlc-studio directory.

    Walks the filesystem, hashes files, parses new/changed documents,
    and manages database records (add/update/skip/delete).

    Args:
        project_id: The project's database ID.
        sdlc_path: Absolute path to the sdlc-studio directory.
        session: Async database session.

    Returns:
        SyncResult with counts for each operation.
    """
    result = SyncResult()
    root = Path(sdlc_path)

    # Validate path exists
    if not root.is_dir():
        # Set project to error state
        proj = await session.get(Project, project_id)
        if proj:
            proj.sync_status = "error"
            proj.sync_error = f"Path not found: {sdlc_path}"
            await session.commit()
        return result

    # Set project to syncing
    proj = await session.get(Project, project_id)
    if proj:
        proj.sync_status = "syncing"
        await session.flush()

    try:
        # Step 1: Walk filesystem, build {rel_path: (hash, raw_bytes)}
        fs_files: dict[str, tuple[str, bytes]] = {}
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
                result.errors += 1
                continue

            file_hash = compute_hash(raw)
            fs_files[rel_path] = (file_hash, raw)

        # Step 2: Load existing documents from DB
        db_result = await session.execute(
            select(Document).where(
                Document.project_id == project_id
            )
        )
        existing_docs = {
            doc.file_path: doc for doc in db_result.scalars().all()
        }

        # Step 3: Process filesystem files
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

        # Step 4: Delete documents no longer on filesystem
        for rel_path, doc in existing_docs.items():
            if rel_path not in fs_files:
                await session.delete(doc)
                result.deleted += 1

        # Step 5: Update project status
        if proj:
            proj.sync_status = "synced"
            proj.last_synced_at = datetime.datetime.now(datetime.UTC)
            proj.sync_error = None

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
