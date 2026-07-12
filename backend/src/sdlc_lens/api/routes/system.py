"""System API routes."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.api.deps import get_db
from sdlc_lens.api.schemas.system import HealthResponse
from sdlc_lens.version import get_version

router = APIRouter(prefix="/system", tags=["system"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@lru_cache(maxsize=1)
def _alembic_dir() -> Path | None:
    """Locate the Alembic scripts directory relative to this package.

    Walks up the directory tree looking for an ``alembic`` folder that holds
    ``env.py`` and a ``versions`` directory. Works both in local checkouts
    (``backend/alembic``) and in the Docker runtime (``/app/alembic``).
    """
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "alembic"
        if (candidate / "env.py").is_file() and (candidate / "versions").is_dir():
            return candidate
    return None


def head_revision() -> str | None:
    """Return the head Alembic revision id from the migration scripts, or None."""
    script_dir = _alembic_dir()
    if script_dir is None:
        return None
    try:
        from alembic.script import ScriptDirectory

        return ScriptDirectory(str(script_dir)).get_current_head()
    except Exception:
        return None


async def _current_revision(db: AsyncSession) -> str | None:
    """Return the revision the DB is stamped at, or None if not stamped."""
    try:
        result = await db.execute(text("SELECT version_num FROM alembic_version"))
        row = result.first()
    except Exception:
        # No alembic_version table => the DB has never been migrated.
        return None
    return row[0] if row else None


async def _fts_present(db: AsyncSession) -> bool:
    """Return True if the documents_fts full-text index exists."""
    try:
        result = await db.execute(
            text("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'documents_fts'")
        )
        return result.first() is not None
    except Exception:
        return False


@router.get("/health", response_model=HealthResponse)
async def health_check(db: DbDep) -> HealthResponse:
    """Check system health, database connectivity and readiness.

    ``status`` reports liveness (the app is up and the DB is reachable), while
    ``ready`` reflects deeper checks - the schema being migrated to head and the
    full-text index being present - for CD health-gating and monitoring.
    """
    try:
        await db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    if db_connected:
        head = head_revision()
        current = await _current_revision(db)
        migration_ok = head is not None and current == head
        fts_ok = await _fts_present(db)
    else:
        migration_ok = False
        fts_ok = False

    return HealthResponse(
        status="healthy" if db_connected else "unhealthy",
        database="connected" if db_connected else "disconnected",
        version=get_version(),
        migration_ok=migration_ok,
        fts_ok=fts_ok,
        ready=db_connected and migration_ok and fts_ok,
    )
