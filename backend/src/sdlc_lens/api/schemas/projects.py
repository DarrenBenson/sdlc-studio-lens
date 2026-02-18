"""Pydantic schemas for project endpoints."""

import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


def mask_token(token: str | None) -> str | None:
    """Mask an access token, showing only the last 4 characters."""
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

    @model_validator(mode="after")
    def at_least_one_field(self) -> "ProjectUpdate":
        fields = [
            self.name, self.sdlc_path, self.source_type,
            self.repo_url, self.repo_branch, self.repo_path,
            self.access_token,
        ]
        if all(f is None for f in fields):
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
    sync_status: str
    sync_error: str | None = None
    last_synced_at: datetime.datetime | None
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
