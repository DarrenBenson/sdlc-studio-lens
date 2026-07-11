"""Sync service - trigger sync and manage state machine."""

import logging

from sqlalchemy import select, update
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

    # Atomic transition: only flip to "syncing" if the project is not already
    # syncing. A conditional UPDATE avoids the check-then-set race where two
    # concurrent triggers both read a non-syncing status and both proceed.
    outcome = await session.execute(
        update(Project)
        .where(Project.slug == slug, Project.sync_status != "syncing")
        .values(sync_status="syncing", sync_error=None)
    )
    await session.commit()

    if outcome.rowcount == 0:
        # No row transitioned: either the project does not exist, or it was
        # already syncing. Distinguish the two so callers map them correctly.
        existing = await session.execute(select(Project).where(Project.slug == slug))
        if existing.scalar_one_or_none() is None:
            raise ProjectNotFoundError
        raise SyncInProgressError

    result = await session.execute(select(Project).where(Project.slug == slug))
    project = result.scalar_one()
    await session.refresh(project)
    return project


async def run_sync_task(slug: str, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Background task that performs the sync.

    Creates its own session since the request session is closed after 202 response.
    Delegates to sync_project for actual document processing.

    Any failure is recorded as sync_status="error" in a fresh session so the
    project is never left stuck in "syncing" (which would 409 every future
    sync). The error is always logged, never silently swallowed.
    """
    try:
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
    except Exception as exc:
        logger.exception("Sync task failed for project '%s'", slug)
        # Recover in a fresh session: the original may be in a bad state
        # (mid-transaction, rolled back, or closed). Never leave "syncing".
        try:
            async with session_factory() as recovery:
                result = await recovery.execute(select(Project).where(Project.slug == slug))
                project = result.scalar_one_or_none()
                if project is not None:
                    project.sync_status = "error"
                    project.sync_error = str(exc)
                    await recovery.commit()
        except Exception:
            logger.exception("Failed to record sync error for project '%s'", slug)
