"""Pydantic schemas for search endpoints."""

from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """A single search result item."""

    doc_id: str
    type: str
    title: str
    project_slug: str
    project_name: str
    status: str | None
    snippet: str
    score: float


class SearchResponse(BaseModel):
    """Response body for the full-text search endpoint."""

    items: list[SearchResultItem]
    total: int
    query: str
    page: int = Field(default=1)
    per_page: int = Field(default=20)
