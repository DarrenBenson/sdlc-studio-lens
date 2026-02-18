"""Project service - business logic for project registration."""

import logging
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project
from sdlc_lens.utils.slug import generate_slug

logger = logging.getLogger(__name__)


class PathNotFoundError(Exception):
    """Raised when the sdlc_path does not exist or is not a directory."""

    def __init__(self, message: str = "Project sdlc-studio path does not exist on filesystem"):
        self.message = message
        super().__init__(self.message)


class SlugConflictError(Exception):
    """Raised when a project with the same slug already exists."""

    def __init__(self, message: str = "Project slug already exists"):
        self.message = message
        super().__init__(self.message)


class EmptySlugError(Exception):
    """Raised when the generated slug is empty after sanitisation."""

    def __init__(self, message: str = "Project name produces an empty slug after sanitisation"):
        self.message = message
        super().__init__(self.message)


class ProjectNotFoundError(Exception):
    """Raised when a project with the given slug does not exist."""

    def __init__(self, message: str = "Project not found"):
        self.message = message
        super().__init__(self.message)


async def create_project(
    session: AsyncSession,
    name: str,
    sdlc_path: str | None = None,
    *,
    source_type: str = "local",
    repo_url: str | None = None,
    repo_branch: str = "main",
    repo_path: str = "sdlc-studio",
    access_token: str | None = None,
) -> Project:
    """Register a new project.

    For local projects, validates the filesystem path.
    For GitHub projects, skips path validation.

    Raises:
        PathNotFoundError: If source_type is local and sdlc_path does not exist.
        SlugConflictError: If a project with the same slug already exists.
        EmptySlugError: If the generated slug is empty.
    """
    slug = generate_slug(name)
    if not slug:
        raise EmptySlugError

    # Validate local path only for local source type
    resolved_path: str | None = None
    if source_type == "local":
        if not sdlc_path:
            raise PathNotFoundError(message="sdlc_path is required for local projects")
        resolved = Path(sdlc_path).resolve()
        if not resolved.is_dir():
            raise PathNotFoundError
        resolved_path = str(resolved)

    # Check for existing slug
    existing = await session.execute(select(Project).where(Project.slug == slug))
    if existing.scalar_one_or_none() is not None:
        raise SlugConflictError

    project = Project(
        slug=slug,
        name=name,
        sdlc_path=resolved_path,
        source_type=source_type,
        repo_url=repo_url,
        repo_branch=repo_branch,
        repo_path=repo_path,
        access_token=access_token,
    )
    session.add(project)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise SlugConflictError from exc

    await session.refresh(project)
    return project


async def list_projects(session: AsyncSession) -> list[Project]:
    """List all registered projects ordered by created_at."""
    result = await session.execute(select(Project).order_by(Project.created_at))
    return list(result.scalars().all())


async def get_project_by_slug(session: AsyncSession, slug: str) -> Project:
    """Get a project by its slug.

    Raises:
        ProjectNotFoundError: If no project with the given slug exists.
    """
    result = await session.execute(select(Project).where(Project.slug == slug))
    project = result.scalar_one_or_none()
    if project is None:
        raise ProjectNotFoundError
    return project


async def get_document_count(session: AsyncSession, project_id: int) -> int:
    """Count documents belonging to a project."""
    try:
        result = await session.execute(
            select(func.count()).select_from(Document).where(Document.project_id == project_id)
        )
        return result.scalar_one()
    except OperationalError:
        # Documents table may not exist yet (created in EP0002)
        return 0


async def update_project(
    session: AsyncSession,
    slug: str,
    name: str | None = None,
    sdlc_path: str | None = None,
    *,
    source_type: str | None = None,
    repo_url: str | None = None,
    repo_branch: str | None = None,
    repo_path: str | None = None,
    access_token: str | None = None,
) -> Project:
    """Update a project's fields.

    Raises:
        ProjectNotFoundError: If no project with the given slug exists.
        PathNotFoundError: If the new sdlc_path does not exist or is not a directory.
    """
    project = await get_project_by_slug(session, slug)

    # Determine effective source type for validation
    effective_source = source_type if source_type is not None else project.source_type

    if sdlc_path is not None:
        if effective_source == "local":
            resolved = Path(sdlc_path).resolve()
            if not resolved.is_dir():
                raise PathNotFoundError
            project.sdlc_path = str(resolved)
        else:
            # For non-local, store as-is (no validation)
            project.sdlc_path = sdlc_path

    if name is not None:
        project.name = name

    if source_type is not None:
        project.source_type = source_type

    if repo_url is not None:
        project.repo_url = repo_url

    if repo_branch is not None:
        project.repo_branch = repo_branch

    if repo_path is not None:
        project.repo_path = repo_path

    if access_token is not None:
        project.access_token = access_token

    await session.commit()
    await session.refresh(project)
    return project


async def delete_project(session: AsyncSession, slug: str) -> None:
    """Delete a project and cascade to its documents.

    Raises:
        ProjectNotFoundError: If no project with the given slug exists.
    """
    project = await get_project_by_slug(session, slug)
    await session.delete(project)
    await session.commit()
