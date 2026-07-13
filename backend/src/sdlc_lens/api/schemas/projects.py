"""Pydantic schemas for project endpoints."""

import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from sdlc_lens.utils.crypto import decrypt_token


def mask_token(token: str | None) -> str | None:
    """Mask a stored access token, showing only the last 4 characters.

    The stored value may be Fernet ciphertext, so decrypt first to expose the
    real last-4 to the user. The masked result never leaks ciphertext or the
    full plaintext.
    """
    token = decrypt_token(token)
    if not token:
        return None
    if len(token) <= 4:
        return "****"
    return f"****{token[-4:]}"


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    source_type: Literal["local", "github"] = "local"
    sdlc_path: str | None = Field(None, min_length=1)
    repo_url: str | None = Field(None, min_length=1)
    repo_branch: str = "main"
    repo_path: str = "sdlc-studio"
    access_token: str | None = None
    # Optional stored GitHub connection (CR-01KXAZX9). When set, its token is
    # used for the sync in preference to any per-project access_token.
    connection_id: int | None = None

    @model_validator(mode="after")
    def validate_source_fields(self) -> "ProjectCreate":
        if self.source_type == "local":
            if not self.sdlc_path:
                msg = "'sdlc_path' is required for local source type"
                raise ValueError(msg)
        elif self.source_type == "github" and not self.repo_url:
            msg = "'repo_url' is required for github source type"
            raise ValueError(msg)
        return self


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    sdlc_path: str | None = Field(None, min_length=1)
    source_type: Literal["local", "github"] | None = None
    repo_url: str | None = None
    repo_branch: str | None = None
    repo_path: str | None = None
    access_token: str | None = None
    connection_id: int | None = None
    # Per-project opt-in to background freshness polling (CR-01KXCAZJ). Default off; an
    # existing project keeps behaving exactly as it does today until this is set.
    auto_sync: bool | None = None

    def clears_connection(self) -> bool:
        """True when the body explicitly sends ``connection_id: null``.

        An omitted field leaves the current connection alone; an explicit null
        detaches it.
        """
        return "connection_id" in self.model_fields_set and self.connection_id is None

    def clears_access_token(self) -> bool:
        """True when the body explicitly sends ``access_token: null``.

        An omitted field leaves the stored token alone; an explicit null purges
        it, so a project's credential can actually be removed.
        """
        return "access_token" in self.model_fields_set and self.access_token is None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "ProjectUpdate":
        fields = [
            self.name,
            self.sdlc_path,
            self.source_type,
            self.repo_url,
            self.repo_branch,
            self.repo_path,
            self.access_token,
            self.connection_id,
            # Toggling auto-sync IS an edit. Omitting it here would 422 the one request
            # the UI's toggle actually makes - a new field must be added to this list or
            # it is silently unsettable on its own.
            self.auto_sync,
        ]
        # An explicit null for connection_id (detach) or access_token (purge) is
        # a real edit, even though its value is None.
        explicit_null = self.clears_connection() or self.clears_access_token()
        if all(f is None for f in fields) and not explicit_null:
            msg = "At least one field must be provided"
            raise ValueError(msg)
        return self


class ProjectResponse(BaseModel):
    slug: str
    name: str
    sdlc_path: str | None
    source_type: str
    repo_url: str | None = None
    repo_branch: str
    repo_path: str
    masked_token: str | None = None
    connection_id: int | None = None
    sync_status: str
    sync_error: str | None = None
    schema_version: str | None = None
    profile: str | None = None
    last_synced_at: datetime.datetime | None
    # Whether this project keeps itself current, and how fresh it actually is. Surfaced
    # even when auto_sync is off, so a stale corpus cannot masquerade as a current one.
    auto_sync: bool = False
    last_synced_commit_sha: str | None = None
    document_count: int
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class SyncTriggerResponse(BaseModel):
    slug: str
    sync_status: str
    message: str


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
