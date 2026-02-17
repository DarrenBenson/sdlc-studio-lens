"""Pydantic schemas for system endpoints."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str
