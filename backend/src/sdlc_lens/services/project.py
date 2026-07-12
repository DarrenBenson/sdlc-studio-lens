"""Project service - business logic for project registration."""

import logging
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.config import settings
from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project
from sdlc_lens.utils.crypto import encrypt_token
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


def _resolve_local_path(sdlc_path: str) -> Path:
    """Resolve and validate a local sdlc_path.

    Ensures the path is an existing directory and, when an allowlist base is
    configured, that it resolves within that base.

    Raises:
        PathNotFoundError: If the path is not a directory, or is outside the
            configured allowed base.
    """
    resolved = Path(sdlc_path).resolve()
    if not resolved.is_dir():
        raise PathNotFoundError

    _enforce_allowlist_membership(resolved)
    return resolved


def _enforce_allowlist_membership(sdlc_path: str | Path) -> None:
    """Raise if sdlc_path is outside the configured allowlist base.

    Membership check only - it does NOT require the directory to exist, so an
    unrelated metadata edit on a local project never fails merely because the
    directory is temporarily missing (existence is enforced at sync time).
    """
    if settings.allowed_project_base is None:
        return
    base = Path(settings.allowed_project_base).resolve()
    if not Path(sdlc_path).resolve().is_relative_to(base):
        raise PathNotFoundError(message="sdlc_path must be within the allowed base")


async def _assert_connection_exists(session: AsyncSession, connection_id: int | None) -> None:
    """Raise if connection_id is supplied but names no stored connection.

    Imported lazily: ``services.github_connection`` pulls in the GitHub source
    module, which this service does not otherwise need.
    """
    if connection_id is None:
        return
    from sdlc_lens.services.github_connection import get_connection

    await get_connection(session, connection_id)


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
    connection_id: int | None = None,
) -> Project:
    """Register a new project.

    For local projects, validates the filesystem path.
    For GitHub projects, skips path validation.

    Raises:
        PathNotFoundError: If source_type is local and sdlc_path does not exist.
        SlugConflictError: If a project with the same slug already exists.
        EmptySlugError: If the generated slug is empty.
        ConnectionNotFoundError: If connection_id names no stored connection.
    """
    slug = generate_slug(name)
    if not slug:
        raise EmptySlugError

    await _assert_connection_exists(session, connection_id)

    # Validate local path only for local source type
    resolved_path: str | None = None
    if source_type == "local":
        if not sdlc_path:
            raise PathNotFoundError(message="sdlc_path is required for local projects")
        resolved_path = str(_resolve_local_path(sdlc_path))

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
        access_token=encrypt_token(access_token),
        connection_id=connection_id,
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
    """Count documents belonging to a project.

    A database error is allowed to propagate: the documents table is part of the
    baseline schema, so a failure here is a genuine fault, not the missing-table
    condition the old broad ``except`` masked by returning 0.
    """
    result = await session.execute(
        select(func.count()).select_from(Document).where(Document.project_id == project_id)
    )
    return result.scalar_one()


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
    connection_id: int | None = None,
    clear_connection: bool = False,
) -> Project:
    """Update a project's fields.

    ``connection_id`` attaches a stored GitHub connection; ``clear_connection``
    detaches whatever is attached (the caller distinguishes an omitted field from
    an explicit null), after which the project falls back to its own access_token.

    Raises:
        ProjectNotFoundError: If no project with the given slug exists.
        PathNotFoundError: If the new sdlc_path does not exist or is not a directory.
        ConnectionNotFoundError: If connection_id names no stored connection.
    """
    project = await get_project_by_slug(session, slug)
    await _assert_connection_exists(session, connection_id)

    # Determine effective (post-update) source type for validation.
    effective_source = source_type if source_type is not None else project.source_type

    if sdlc_path is not None:
        # Store the supplied value; the effective-invariant check below validates
        # (and normalises) it when the resulting project is local.
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
        project.access_token = encrypt_token(access_token)

    if connection_id is not None:
        project.connection_id = connection_id
    elif clear_connection:
        project.connection_id = None

    # Validate the effective post-update invariant: whenever the RESULTING
    # project is local, its RESULTING sdlc_path must satisfy the allowlist - even
    # when sdlc_path was not supplied this call. This closes the two-step bypass
    # where an out-of-base path is stashed on a non-local project (stored
    # unvalidated) and then made live by a later transition to source_type
    # 'local' that supplies no sdlc_path. Re-resolving is idempotent for a value
    # already validated above.
    if effective_source == "local" and project.sdlc_path is not None:
        if sdlc_path is not None:
            # A path was supplied this call: it must exist AND satisfy the allowlist.
            project.sdlc_path = str(_resolve_local_path(project.sdlc_path))
        else:
            # No path supplied (metadata edit, or a transition to local): re-validate
            # allowlist membership only - do not require the directory to exist, so an
            # unrelated edit does not fail if the dir is temporarily gone. This still
            # closes the two-step bypass (an out-of-base stored path is refused here).
            _enforce_allowlist_membership(project.sdlc_path)

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
