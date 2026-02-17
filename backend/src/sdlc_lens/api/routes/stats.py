"""Aggregate statistics API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.api.deps import get_db
from sdlc_lens.api.schemas.stats import AggregateStats
from sdlc_lens.services.stats import get_aggregate_stats

router = APIRouter(prefix="/stats", tags=["stats"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=AggregateStats)
async def aggregate_stats(db: DbDep) -> AggregateStats:
    """Get aggregate statistics across all projects."""
    stats = await get_aggregate_stats(db)
    return AggregateStats(**stats)
