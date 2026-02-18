"""Pydantic schemas for document endpoints."""

import datetime
from enum import Enum

from pydantic import BaseModel


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
    epic: str | None
    story: str | None
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
    story: str | None
    metadata: dict | None
    content: str
    file_path: str
    file_hash: str
    synced_at: datetime.datetime

    model_config = {"from_attributes": True}


class RelatedDocumentItem(BaseModel):
    doc_id: str
    type: str
    title: str
    status: str | None


class DocumentRelationships(BaseModel):
    doc_id: str
    type: str
    title: str
    parents: list[RelatedDocumentItem]
    children: list[RelatedDocumentItem]
