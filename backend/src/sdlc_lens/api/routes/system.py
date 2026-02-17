"""System API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.api.deps import get_db
from sdlc_lens.api.schemas.system import HealthResponse

router = APIRouter(prefix="/system", tags=["system"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("/health", response_model=HealthResponse)
async def health_check(db: DbDep) -> HealthResponse:
    """Check system health and database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        database=db_status,
        version="0.1.0",
    )
