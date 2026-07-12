"""Pydantic schemas for system endpoints."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str
    # Deeper readiness signals for CD health-gating and monitoring. The
    # original status/database/version fields are retained for backwards
    # compatibility; `ready` reflects the combined readiness checks.
    migration_ok: bool
    fts_ok: bool
    ready: bool
