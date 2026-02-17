"""Pydantic schemas for document endpoints."""

import datetime
import json
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class SortField(str, Enum):
    title = "title"
    type = "type"
    status = "status"
    updated_at = "updated_at"


class DocumentListItem(BaseModel):
    doc_id: str
    type: str
    title: str
    status: str | None
    owner: str | None
    priority: str | None
    story_points: int | None
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class PaginatedDocuments(BaseModel):
    items: list[DocumentListItem]
    total: int
    page: int
    per_page: int
    pages: int


class DocumentDetail(BaseModel):
    doc_id: str
    type: str
    title: str
    status: str | None
    owner: str | None
    priority: str | None
    story_points: int | None
    epic: str | None
    metadata: dict | None
    content: str
    file_path: str
    file_hash: str
    synced_at: datetime.datetime

    model_config = {"from_attributes": True}
