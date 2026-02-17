"""Full-text search service using SQLite FTS5."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def _escape_fts_query(query: str) -> str:
    """Escape a user query for safe use in FTS5 MATCH.

    Wraps the query in double quotes so that FTS5 special characters
    (such as *, OR, AND, NOT, NEAR) are treated as literal text.
    Internal double quotes are escaped by doubling them.
    """
    escaped = query.replace('"', '""')
    return f'"{escaped}"'


async def search_documents(
    session: AsyncSession,
    *,
    query: str,
    project_slug: str | None = None,
    doc_type: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> dict[str, Any]:
    """Search documents using FTS5 full-text index.

    Parameters
    ----------
    session : AsyncSession
        Database session.
    query : str
        Search query string.
    project_slug : str | None
        Filter results to a specific project.
    doc_type : str | None
        Filter results to a specific document type.
    page : int
        Page number (1-indexed).
    per_page : int
        Number of results per page.

    Returns
    -------
    dict
        Dictionary with items, total, query, page, and per_page.
    """
    fts_query = _escape_fts_query(query)
    offset = (page - 1) * per_page

    # Build WHERE clause fragments
    where_clauses = ["documents_fts MATCH :query"]
    params: dict[str, Any] = {"query": fts_query}

    if project_slug is not None:
        where_clauses.append("p.slug = :project_slug")
        params["project_slug"] = project_slug

    if doc_type is not None:
        where_clauses.append("d.doc_type = :doc_type")
        params["doc_type"] = doc_type

    where_sql = " AND ".join(where_clauses)

    # Count total matches
    count_sql = text(
        "SELECT COUNT(*) "
        "FROM documents_fts "
        "JOIN documents d ON documents_fts.rowid = d.id "
        "JOIN projects p ON d.project_id = p.id "
        f"WHERE {where_sql}"
    )
    count_result = await session.execute(count_sql, params)
    total = count_result.scalar_one()

    if total == 0:
        return {
            "items": [],
            "total": 0,
            "query": query,
            "page": page,
            "per_page": per_page,
        }

    # Fetch paginated results with BM25 ranking and snippets
    # Note: bm25() returns negative values; more negative = more relevant.
    # ORDER BY rank ASC puts the most relevant first.
    # We negate the value in the SELECT so the API returns positive scores
    # (higher = more relevant).
    search_sql = text(
        "SELECT "
        "  d.doc_id, "
        "  d.doc_type, "
        "  d.title, "
        "  p.slug AS project_slug, "
        "  p.name AS project_name, "
        "  d.status, "
        "  snippet(documents_fts, 1, '<mark>', '</mark>', '...', 32) AS snippet, "
        "  -bm25(documents_fts) AS score "
        "FROM documents_fts "
        "JOIN documents d ON documents_fts.rowid = d.id "
        "JOIN projects p ON d.project_id = p.id "
        f"WHERE {where_sql} "
        "ORDER BY bm25(documents_fts) "
        "LIMIT :limit OFFSET :offset"
    )

    params["limit"] = per_page
    params["offset"] = offset

    result = await session.execute(search_sql, params)
    rows = result.mappings().all()

    items = [
        {
            "doc_id": row["doc_id"],
            "type": row["doc_type"],
            "title": row["title"],
            "project_slug": row["project_slug"],
            "project_name": row["project_name"],
            "status": row["status"],
            "snippet": row["snippet"],
            "score": round(float(row["score"]), 4),
        }
        for row in rows
    ]

    return {
        "items": items,
        "total": total,
        "query": query,
        "page": page,
        "per_page": per_page,
    }
