"""Statistics service - aggregate document counts and completion metrics."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_project_stats(
    session: AsyncSession,
    project: Project,
) -> dict:
    """Compute statistics for a single project.

    Returns a dict with: total_documents, by_type, by_status,
    completion_percentage, slug, name, last_synced_at.
    """
    project_id = project.id

    # Count by type
    type_rows = await session.execute(
        select(Document.doc_type, func.count())
        .where(Document.project_id == project_id)
        .group_by(Document.doc_type)
    )
    by_type: dict[str, int] = {}
    total = 0
    for doc_type, count in type_rows:
        by_type[doc_type] = count
        total += count

    # Count by status
    status_rows = await session.execute(
        select(Document.status, func.count())
        .where(Document.project_id == project_id)
        .group_by(Document.status)
    )
    by_status: dict[str, int] = {}
    for status_val, count in status_rows:
        key = status_val if status_val is not None else "null"
        by_status[key] = count

    # Completion: Done stories / Total stories
    story_rows = await session.execute(
        select(Document.status, func.count())
        .where(
            Document.project_id == project_id,
            Document.doc_type == "story",
        )
        .group_by(Document.status)
    )
    total_stories = 0
    done_stories = 0
    for status_val, count in story_rows:
        total_stories += count
        if status_val == "Done":
            done_stories += count

    completion = round(done_stories / total_stories * 100, 1) if total_stories > 0 else 0.0

    return {
        "slug": project.slug,
        "name": project.name,
        "total_documents": total,
        "by_type": by_type,
        "by_status": by_status,
        "completion_percentage": completion,
        "last_synced_at": project.last_synced_at,
    }


async def get_aggregate_stats(session: AsyncSession) -> dict:
    """Compute aggregate statistics across all projects.

    Returns a dict with: total_projects, total_documents, by_type,
    by_status, completion_percentage, projects array.
    """
    # Get all projects
    result = await session.execute(select(Project))
    projects = list(result.scalars().all())

    if not projects:
        return {
            "total_projects": 0,
            "total_documents": 0,
            "by_type": {},
            "by_status": {},
            "completion_percentage": 0.0,
            "projects": [],
        }

    total_documents = 0
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    total_done_stories = 0
    total_stories = 0
    project_summaries = []

    for proj in projects:
        stats = await get_project_stats(session, proj)
        total_documents += stats["total_documents"]

        for t, c in stats["by_type"].items():
            by_type[t] = by_type.get(t, 0) + c
        for s, c in stats["by_status"].items():
            by_status[s] = by_status.get(s, 0) + c

        # Track story counts for weighted completion
        story_count = stats["by_type"].get("story", 0)
        done_count = 0
        if story_count > 0:
            done_count = int(round(stats["completion_percentage"] / 100 * story_count))
        total_stories += story_count
        total_done_stories += done_count

        project_summaries.append({
            "slug": stats["slug"],
            "name": stats["name"],
            "total_documents": stats["total_documents"],
            "completion_percentage": stats["completion_percentage"],
            "last_synced_at": stats["last_synced_at"],
        })

    completion = round(total_done_stories / total_stories * 100, 1) if total_stories > 0 else 0.0

    return {
        "total_projects": len(projects),
        "total_documents": total_documents,
        "by_type": by_type,
        "by_status": by_status,
        "completion_percentage": completion,
        "projects": project_summaries,
    }
