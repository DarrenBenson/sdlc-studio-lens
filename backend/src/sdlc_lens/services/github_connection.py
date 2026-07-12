"""GitHub connection service - stored, reusable, validated credentials (CR-01KXAZX9).

A connection is a labelled GitHub PAT, validated against ``GET /user`` before it
is stored and encrypted at rest. Projects point at one via
``projects.connection_id`` instead of each carrying its own copy of the secret.

The raw token never leaves this layer: callers get the ORM row (whose
``access_token`` is ciphertext) or, for an outbound GitHub call, the decrypted
token from :func:`resolve_connection_token`.
"""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from sdlc_lens.db.models.github_connection import GitHubConnection
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.github_source import AuthenticationError, get_authenticated_login
from sdlc_lens.utils.crypto import decrypt_token, encrypt_token

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ConnectionNotFoundError(Exception):
    """Raised when no connection exists with the given id."""

    def __init__(self, message: str = "Connection not found"):
        self.message = message
        super().__init__(self.message)


class LabelExistsError(Exception):
    """Raised when a connection with the same label already exists."""

    def __init__(self, message: str = "A connection with this label already exists"):
        self.message = message
        super().__init__(self.message)


class ConnectionInUseError(Exception):
    """Raised when a connection cannot be deleted because projects reference it."""

    def __init__(self, message: str = "Connection is in use"):
        self.message = message
        super().__init__(self.message)


async def list_connections(session: AsyncSession) -> list[GitHubConnection]:
    """List all stored connections, oldest first."""
    result = await session.execute(select(GitHubConnection).order_by(GitHubConnection.created_at))
    return list(result.scalars().all())


async def get_connection(session: AsyncSession, connection_id: int) -> GitHubConnection:
    """Fetch a connection by id.

    Raises:
        ConnectionNotFoundError: If no connection has that id.
    """
    connection = await session.get(GitHubConnection, connection_id)
    if connection is None:
        raise ConnectionNotFoundError
    return connection


async def resolve_connection_token(session: AsyncSession, connection_id: int) -> str:
    """Return the DECRYPTED token for a stored connection, for an outbound call.

    Raises:
        ConnectionNotFoundError: If no connection has that id.
        AuthenticationError: If the stored token cannot be decrypted (the
            encryption key is missing, was rotated, or the ciphertext is
            corrupt). The message names THAT cause: the credential is never
            sent to GitHub as ciphertext, so a lost key can never be
            misreported as the operator's PAT being rejected.
    """
    connection = await get_connection(session, connection_id)
    token = decrypt_token(connection.access_token)
    if not token:
        raise AuthenticationError(
            f"The stored credential for connection {connection_id} "
            f"({connection.label!r}) could not be decrypted: the encryption key is "
            "missing or has changed. Restore SDLC_LENS_TOKEN_ENCRYPTION_KEY, or "
            "rotate this connection with a fresh token."
        )
    return token


async def create_connection(
    session: AsyncSession,
    label: str,
    access_token: str,
) -> GitHubConnection:
    """Validate a token against GitHub, then store it as a labelled connection.

    The token is validated BEFORE anything is persisted, so an invalid or expired
    credential leaves no row behind. The resolved GitHub login is stored with it.

    Raises:
        LabelExistsError: If a connection with the same label already exists.
        AuthenticationError: If GitHub rejects the token.
        RateLimitError / GitHubSourceError: On other GitHub API failures.
    """
    label = label.strip()

    existing = await session.execute(
        select(GitHubConnection).where(GitHubConnection.label == label)
    )
    if existing.scalar_one_or_none() is not None:
        raise LabelExistsError

    # Validate first: nothing is written unless GitHub accepts the token.
    login = await get_authenticated_login(access_token)

    connection = GitHubConnection(
        label=label,
        login=login,
        access_token=encrypt_token(access_token),
        last_validated_at=datetime.datetime.now(datetime.UTC),
    )
    session.add(connection)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise LabelExistsError from exc

    await session.refresh(connection)
    logger.info("Registered GitHub connection %r for login %s", label, login)
    return connection


async def validate_connection(session: AsyncSession, connection_id: int) -> GitHubConnection:
    """Re-check a stored token against GitHub and refresh ``last_validated_at``.

    The resolved login is refreshed too (an account can be renamed).

    Raises:
        ConnectionNotFoundError: If no connection has that id.
        AuthenticationError: If the token is no longer valid.
        RateLimitError / GitHubSourceError: On other GitHub API failures.
    """
    connection = await get_connection(session, connection_id)
    token = await resolve_connection_token(session, connection_id)

    login = await get_authenticated_login(token)

    connection.login = login
    connection.last_validated_at = datetime.datetime.now(datetime.UTC)
    await session.commit()
    await session.refresh(connection)
    return connection


async def rotate_connection(
    session: AsyncSession,
    connection_id: int,
    access_token: str,
) -> GitHubConnection:
    """Replace a stored connection's token with a new, validated one.

    Rotation is the whole point of storing a credential once: an expired PAT is
    a one-field edit here, not a detach-delete-re-add-reattach dance across every
    project that uses it. The new token is validated BEFORE anything is written,
    so a bad token leaves the old (still working) one intact.

    Raises:
        ConnectionNotFoundError: If no connection has that id.
        AuthenticationError: If GitHub rejects the new token.
        RateLimitError / GitHubSourceError: On other GitHub API failures.
    """
    connection = await get_connection(session, connection_id)

    # Validate first: nothing is written unless GitHub accepts the new token.
    login = await get_authenticated_login(access_token)

    connection.access_token = encrypt_token(access_token)
    connection.login = login
    connection.last_validated_at = datetime.datetime.now(datetime.UTC)
    await session.commit()
    await session.refresh(connection)
    logger.info("Rotated the token for GitHub connection %r (login %s)", connection.label, login)
    return connection


async def delete_connection(session: AsyncSession, connection_id: int) -> None:
    """Delete a connection, refusing while any project still references it.

    Raises:
        ConnectionNotFoundError: If no connection has that id.
        ConnectionInUseError: If one or more projects reference the connection.
            The message names them, so the operator knows what to re-point first.
    """
    connection = await get_connection(session, connection_id)

    result = await session.execute(
        select(Project.slug).where(Project.connection_id == connection_id).order_by(Project.slug)
    )
    slugs = list(result.scalars().all())
    if slugs:
        raise ConnectionInUseError(
            "Connection is in use by "
            f"{'project' if len(slugs) == 1 else 'projects'}: {', '.join(slugs)}. "
            "Re-point or delete them first."
        )

    await session.delete(connection)
    await session.commit()
