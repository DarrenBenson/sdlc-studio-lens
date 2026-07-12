"""Stored GitHub connection routes (CR-01KXAZX9).

A connection is registered once with a label and a PAT; the PAT is validated
against GitHub, encrypted at rest and never returned. Projects and the repo
browser then refer to it by id.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.api.deps import get_db
from sdlc_lens.api.schemas.connections import ConnectionCreate, ConnectionResponse
from sdlc_lens.api.schemas.projects import mask_token
from sdlc_lens.db.models.github_connection import GitHubConnection
from sdlc_lens.services.github_connection import (
    ConnectionInUseError,
    ConnectionNotFoundError,
    LabelExistsError,
    create_connection,
    delete_connection,
    list_connections,
    validate_connection,
)
from sdlc_lens.services.github_source import (
    AuthenticationError,
    GitHubSourceError,
    RateLimitError,
)

router = APIRouter(prefix="/connections", tags=["connections"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _connection_response(connection: GitHubConnection) -> ConnectionResponse:
    """Serialise a connection, masking the stored token."""
    return ConnectionResponse(
        id=connection.id,
        label=connection.label,
        login=connection.login,
        masked_token=mask_token(connection.access_token),
        created_at=connection.created_at,
        last_validated_at=connection.last_validated_at,
    )


def _github_error_response(exc: GitHubSourceError) -> JSONResponse:
    """Map a GitHub error raised while validating a token to the canonical shape.

    An authentication failure here always means the supplied/stored PAT is not
    usable, so it surfaces as INVALID_TOKEN rather than the browse endpoints'
    generic AUTH_FAILED.
    """
    if isinstance(exc, RateLimitError):
        return JSONResponse(
            status_code=429,
            content={"error": {"code": "RATE_LIMITED", "message": exc.message}},
        )
    if isinstance(exc, AuthenticationError):
        return JSONResponse(
            status_code=401,
            content={"error": {"code": "INVALID_TOKEN", "message": exc.message}},
        )
    return JSONResponse(
        status_code=502,
        content={"error": {"code": "GITHUB_ERROR", "message": exc.message}},
    )


def _not_found(exc: ConnectionNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": {"code": "NOT_FOUND", "message": exc.message}},
    )


@router.get("", response_model=list[ConnectionResponse])
async def list_all_connections(db: DbDep) -> list[ConnectionResponse]:
    """List the stored GitHub connections. Tokens are masked."""
    connections = await list_connections(db)
    return [_connection_response(c) for c in connections]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ConnectionResponse)
async def register_connection(
    body: ConnectionCreate, db: DbDep
) -> ConnectionResponse | JSONResponse:
    """Register a connection: validate the token, resolve its login, store it.

    An invalid or expired token is rejected and nothing is persisted.
    """
    try:
        connection = await create_connection(db, body.label, body.access_token)
    except LabelExistsError as exc:
        return JSONResponse(
            status_code=409,
            content={"error": {"code": "LABEL_EXISTS", "message": exc.message}},
        )
    except GitHubSourceError as exc:
        return _github_error_response(exc)

    return _connection_response(connection)


@router.post("/{connection_id}/validate", response_model=ConnectionResponse)
async def revalidate_connection(
    connection_id: int, db: DbDep
) -> ConnectionResponse | JSONResponse:
    """Re-check a stored token against GitHub and refresh last_validated_at."""
    try:
        connection = await validate_connection(db, connection_id)
    except ConnectionNotFoundError as exc:
        return _not_found(exc)
    except GitHubSourceError as exc:
        return _github_error_response(exc)

    return _connection_response(connection)


@router.delete(
    "/{connection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def remove_connection(connection_id: int, db: DbDep) -> Response | JSONResponse:
    """Delete a connection. Refused while a project still references it."""
    try:
        await delete_connection(db, connection_id)
    except ConnectionNotFoundError as exc:
        return _not_found(exc)
    except ConnectionInUseError as exc:
        return JSONResponse(
            status_code=409,
            content={"error": {"code": "CONNECTION_IN_USE", "message": exc.message}},
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
