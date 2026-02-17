"""Pydantic schemas for statistics endpoints."""

import datetime

from pydantic import BaseModel


class ProjectSummary(BaseModel):
    slug: str
    name: str
    total_documents: int
    completion_percentage: float
    last_synced_at: datetime.datetime | None


class ProjectStats(BaseModel):
    slug: str
    name: str
    total_documents: int
    by_type: dict[str, int]
    by_status: dict[str, int]
    completion_percentage: float
    last_synced_at: datetime.datetime | None


class AggregateStats(BaseModel):
    total_projects: int
    total_documents: int
    by_type: dict[str, int]
    by_status: dict[str, int]
    completion_percentage: float
    projects: list[ProjectSummary]
