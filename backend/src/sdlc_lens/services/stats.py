"""Statistics service - aggregate document counts and completion metrics."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project
from sdlc_lens.utils.sdlc_status import is_terminal

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
        # A story counts as "done" when it is in a terminal/resolved state.
        # is_terminal canonicalises (strips prose/bold/parentheses) first, so
        # "Complete (81/88 ...)" and "Done — shipped" both count.
        if is_terminal("story", status_val):
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

    # Bounded number of grouped queries across ALL projects (independent of
    # project count), aggregated in Python afterwards. This replaces the old
    # per-project loop that issued ~3 queries per project.

    # Documents grouped by (project, type): drives total_documents, by_type
    # and per-project totals.
    type_rows = await session.execute(
        select(Document.project_id, Document.doc_type, func.count()).group_by(
            Document.project_id, Document.doc_type
        )
    )
    total_documents = 0
    by_type: dict[str, int] = {}
    project_totals: dict[int, int] = {}
    for project_id, doc_type, count in type_rows:
        total_documents += count
        by_type[doc_type] = by_type.get(doc_type, 0) + count
        project_totals[project_id] = project_totals.get(project_id, 0) + count

    # Documents grouped by (project, status): drives by_status.
    status_rows = await session.execute(
        select(Document.project_id, Document.status, func.count()).group_by(
            Document.project_id, Document.status
        )
    )
    by_status: dict[str, int] = {}
    for _project_id, status_val, count in status_rows:
        key = status_val if status_val is not None else "null"
        by_status[key] = by_status.get(key, 0) + count

    # Story documents grouped by (project, status): drives per-project and
    # aggregate completion from TRUE integer counts, never reconstructed from
    # a rounded percentage.
    story_rows = await session.execute(
        select(Document.project_id, Document.status, func.count())
        .where(Document.doc_type == "story")
        .group_by(Document.project_id, Document.status)
    )
    project_total_stories: dict[int, int] = {}
    project_done_stories: dict[int, int] = {}
    total_stories = 0
    total_done_stories = 0
    for project_id, status_val, count in story_rows:
        project_total_stories[project_id] = project_total_stories.get(project_id, 0) + count
        total_stories += count
        # A story counts as "done" when it is in a terminal/resolved state,
        # canonicalised via sdlc_status so prose/bold/parentheses are stripped.
        if is_terminal("story", status_val):
            project_done_stories[project_id] = project_done_stories.get(project_id, 0) + count
            total_done_stories += count

    project_summaries = []
    for proj in projects:
        p_total_stories = project_total_stories.get(proj.id, 0)
        p_done_stories = project_done_stories.get(proj.id, 0)
        p_completion = (
            round(p_done_stories / p_total_stories * 100, 1) if p_total_stories > 0 else 0.0
        )
        project_summaries.append(
            {
                "slug": proj.slug,
                "name": proj.name,
                "total_documents": project_totals.get(proj.id, 0),
                "completion_percentage": p_completion,
                "last_synced_at": proj.last_synced_at,
            }
        )

    completion = round(total_done_stories / total_stories * 100, 1) if total_stories > 0 else 0.0

    return {
        "total_projects": len(projects),
        "total_documents": total_documents,
        "by_type": by_type,
        "by_status": by_status,
        "completion_percentage": completion,
        "projects": project_summaries,
    }
