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
from sdlc_lens.services.github_source import (
    MAX_REPOS,
    AuthenticationError,
    GitHubSourceError,
    get_authenticated_login,
    list_repositories_detailed,
)
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


async def browse_all_connection_repos(
    session: AsyncSession,
) -> tuple[list[dict], list[dict]]:
    """Aggregate the repos visible to EVERY stored connection (CR-01KXB377).

    No credential is supplied by the caller: the operator registered them once,
    so adding a project is a pick from a list rather than another paste of a PAT.

    Each repo entry carries the ``connection_id`` / ``connection_label`` of the
    connection that surfaced it - the credential a project created from it will
    be bound to. Repos are de-duplicated by ``full_name``, first connection wins
    (connections are walked oldest first), and the aggregate is capped at
    ``MAX_REPOS`` exactly as a single-connection browse is.

    The cap is AGGREGATE, not per-connection: it bounds the one thing that has
    to stay bounded - the size of this response and the number of rows the
    picker can then fan out per-repo Contents checks over. A per-connection cap
    would multiply by the number of registered connections instead.

    But a cap that bites must SAY so. A connection whose repos did not fit (the
    limit filled up before it was reached, or partway through it) contributes
    fewer repos than it can see, so it is reported in ``degraded`` exactly like a
    connection that failed - never truncated in silence, which would show the
    operator a complete-looking list that quietly omits their repo (BG-01KXBBTB).

    A connection that cannot be used at all - an expired token, a rate-limited
    or undecryptable credential - contributes no repos and is reported in the
    second return value; it never fails the whole browse. So does a connection
    that only partially degrades (see :func:`list_repositories_detailed`), which
    still contributes the repos it COULD see.

    Returns:
        ``(repos, degraded)`` where each degraded entry is
        ``{connection_id, label, reason}``.
    """
    connections = await list_connections(session)
    repos: dict[str, dict] = {}
    degraded: list[dict] = []

    for connection in connections:
        if len(repos) >= MAX_REPOS:
            # The cap filled before this connection was even reached: browsing it
            # would cost a rate-limited call for repos we could not admit anyway.
            degraded.append(_degradation(connection, _CAP_UNREACHED_REASON))
            continue

        try:
            # Both the decrypt and the GitHub calls raise GitHubSourceError
            # subclasses; either way this connection degrades rather than
            # failing the browse.
            token = await resolve_connection_token(session, connection.id)
            listing = await list_repositories_detailed(token)
        except GitHubSourceError as exc:
            logger.info(
                "Connection %r contributed no repositories: %s", connection.label, exc.message
            )
            degraded.append(_degradation(connection, exc.message))
            continue

        degraded.extend(_degradation(connection, reason) for reason in listing.degraded)

        for item in listing.repos:
            if len(repos) >= MAX_REPOS:
                logger.info(
                    "The %d-repository limit truncated connection %r",
                    MAX_REPOS,
                    connection.label,
                )
                degraded.append(_degradation(connection, _CAP_TRUNCATED_REASON))
                break
            if item["full_name"] in repos:
                continue
            repos[item["full_name"]] = {
                **item,
                "connection_id": connection.id,
                "connection_label": connection.label,
            }

    ordered = sorted(repos.values(), key=lambda r: r["full_name"].lower())
    return ordered, degraded


_CAP_TRUNCATED_REASON = (
    f"Not all repositories could be listed: the {MAX_REPOS}-repository limit was "
    "reached while listing this connection"
)

_CAP_UNREACHED_REASON = (
    f"Not all repositories could be listed: the {MAX_REPOS}-repository limit was "
    "reached before this connection was reached"
)


def _degradation(connection: GitHubConnection, reason: str) -> dict:
    """Build a degradation entry naming the connection and why it degraded."""
    return {
        "connection_id": connection.id,
        "label": connection.label,
        "reason": reason,
    }


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
