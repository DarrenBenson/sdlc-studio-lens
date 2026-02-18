"""Pydantic schemas for the health check API endpoint."""

from pydantic import BaseModel


class AffectedDocumentSchema(BaseModel):
    doc_id: str
    doc_type: str
    title: str


class HealthFindingSchema(BaseModel):
    rule_id: str
    severity: str
    category: str
    message: str
    affected_documents: list[AffectedDocumentSchema]
    suggested_fix: str


class HealthCheckResponse(BaseModel):
    project_slug: str
    checked_at: str
    total_documents: int
    findings: list[HealthFindingSchema]
    summary: dict[str, int]
    score: int
