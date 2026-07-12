"""Pydantic schemas for the stored GitHub connection endpoints (CR-01KXAZX9).

The raw token is accepted on creation and never returned: every response carries
only ``masked_token`` (``****`` plus the real last 4, via
:func:`sdlc_lens.api.schemas.projects.mask_token`).
"""

import datetime

from pydantic import BaseModel, Field


class ConnectionCreate(BaseModel):
    """Body for registering a connection. The token is validated, then encrypted."""

    label: str = Field(..., min_length=1, max_length=100)
    access_token: str = Field(..., min_length=1)


class ConnectionResponse(BaseModel):
    """A stored connection as exposed by the API. Never carries the raw token."""

    id: int
    label: str
    login: str
    masked_token: str | None = None
    created_at: datetime.datetime
    last_validated_at: datetime.datetime | None = None
