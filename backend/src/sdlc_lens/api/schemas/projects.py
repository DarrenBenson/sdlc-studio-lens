"""Pydantic schemas for project endpoints."""

import datetime

from pydantic import BaseModel, Field, model_validator


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    sdlc_path: str = Field(..., min_length=1)


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    sdlc_path: str | None = Field(None, min_length=1)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "ProjectUpdate":
        if self.name is None and self.sdlc_path is None:
            msg = "At least one of 'name' or 'sdlc_path' must be provided"
            raise ValueError(msg)
        return self


class ProjectResponse(BaseModel):
    slug: str
    name: str
    sdlc_path: str
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
