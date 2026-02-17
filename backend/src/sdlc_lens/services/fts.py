"""FTS5 full-text search index management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# DDL for creating the FTS5 virtual table (external content mode).
FTS5_CREATE_SQL = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5("
    "title, content, "
    "content=documents, content_rowid=id, "
    "tokenize=\"unicode61 tokenchars '_'\")"
)


async def fts_insert(
    session: AsyncSession,
    rowid: int,
    title: str,
    content: str,
) -> None:
    """Insert a document into the FTS5 index."""
    await session.execute(
        text(
            "INSERT INTO documents_fts(rowid, title, content) "
            "VALUES (:rowid, :title, :content)"
        ),
        {"rowid": rowid, "title": title, "content": content},
    )


async def fts_update(
    session: AsyncSession,
    rowid: int,
    *,
    old_title: str,
    old_content: str,
    new_title: str,
    new_content: str,
) -> None:
    """Update a document in the FTS5 index (delete old + insert new)."""
    await fts_delete(session, rowid, old_title, old_content)
    await fts_insert(session, rowid, new_title, new_content)


async def fts_delete(
    session: AsyncSession,
    rowid: int,
    title: str,
    content: str,
) -> None:
    """Delete a document from the FTS5 index."""
    await session.execute(
        text(
            "INSERT INTO documents_fts(documents_fts, rowid, title, content) "
            "VALUES('delete', :rowid, :title, :content)"
        ),
        {"rowid": rowid, "title": title, "content": content},
    )


async def fts_rebuild(session: AsyncSession) -> None:
    """Rebuild the FTS5 index from the documents table."""
    await session.execute(
        text(
            "INSERT INTO documents_fts(documents_fts) VALUES('rebuild')"
        )
    )
