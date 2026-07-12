"""Pydantic schemas for the stored GitHub connection endpoints (CR-01KXAZX9).

The raw token is accepted on creation and never returned: every response carries
only ``masked_token`` (``****`` plus the real last 4, via
:func:`sdlc_lens.api.schemas.projects.mask_token`).
"""

import datetime

from pydantic import BaseModel, Field

from sdlc_lens.api.schemas.github import GitHubRepoItem


class ConnectionCreate(BaseModel):
    """Body for registering a connection. The token is validated, then encrypted."""

    label: str = Field(..., min_length=1, max_length=100)
    access_token: str = Field(..., min_length=1)


class ConnectionUpdate(BaseModel):
    """Body for rotating a connection's token. The new token is validated first."""

    access_token: str = Field(..., min_length=1)


class ConnectionResponse(BaseModel):
    """A stored connection as exposed by the API. Never carries the raw token."""

    id: int
    label: str
    login: str
    masked_token: str | None = None
    created_at: datetime.datetime
    last_validated_at: datetime.datetime | None = None


class ConnectionRepoItem(GitHubRepoItem):
    """A repo from the aggregate browse, tagged with the connection that saw it.

    That connection is the credential a project created from this row will be
    bound to, so the id travels with the repo rather than being re-chosen later.
    """

    connection_id: int
    connection_label: str


class ConnectionDegradation(BaseModel):
    """A connection that could not be fully browsed, and why.

    Reported alongside the repos rather than raised: one dead credential must not
    hide the repos every other connection can see.
    """

    connection_id: int
    label: str
    reason: str


class ConnectionReposResponse(BaseModel):
    """The aggregate browse: every connection's repos, plus what degraded."""

    repos: list[ConnectionRepoItem] = Field(default_factory=list)
    degraded: list[ConnectionDegradation] = Field(default_factory=list)
