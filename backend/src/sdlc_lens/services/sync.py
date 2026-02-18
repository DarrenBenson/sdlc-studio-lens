"""Sync service - trigger sync and manage state machine."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from sdlc_lens.db.models.project import Project
from sdlc_lens.services.sync_engine import sync_project

logger = logging.getLogger(__name__)


class SyncInProgressError(Exception):
    """Raised when a sync is already running for the project."""

    def __init__(self, message: str = "Sync already running for this project"):
        self.message = message
        super().__init__(self.message)


async def trigger_sync(session: AsyncSession, slug: str) -> Project:
    """Set project status to syncing and prepare for background task.

    Raises:
        ProjectNotFoundError: If no project with the given slug exists.
        SyncInProgressError: If the project is already syncing.
    """
    from sdlc_lens.services.project import ProjectNotFoundError

    result = await session.execute(select(Project).where(Project.slug == slug))
    project = result.scalar_one_or_none()
    if project is None:
        raise ProjectNotFoundError

    if project.sync_status == "syncing":
        raise SyncInProgressError

    project.sync_status = "syncing"
    project.sync_error = None
    await session.commit()
    await session.refresh(project)
    return project


async def run_sync_task(slug: str, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Background task that performs the sync.

    Creates its own session since the request session is closed after 202 response.
    Delegates to sync_project for actual document processing.
    """
    async with session_factory() as session:
        result = await session.execute(select(Project).where(Project.slug == slug))
        project = result.scalar_one_or_none()
        if project is None:
            logger.warning("Project '%s' deleted during sync", slug)
            return

        sync_result = await sync_project(project, session)
        logger.info(
            "Sync completed for '%s': added=%d updated=%d skipped=%d deleted=%d errors=%d",
            slug,
            sync_result.added,
            sync_result.updated,
            sync_result.skipped,
            sync_result.deleted,
            sync_result.errors,
        )
