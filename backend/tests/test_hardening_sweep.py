"""CR-01KX8B83 hardening sweep - error swallowing and observability.

Covers:
- get_document_count no longer swallows a genuine DB error (it must propagate).
- _rebuild_fts_if_exists returns cleanly when the FTS table is absent, and logs a
  real rebuild failure at WARNING instead of swallowing it at DEBUG.
"""

import logging
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.services import fts as fts_module
from sdlc_lens.services.project import get_document_count
from sdlc_lens.services.sync_engine import _rebuild_fts_if_exists


async def test_get_document_count_propagates_db_error() -> None:
    """A real DB fault must surface, not be masked by returning 0."""
    session = AsyncMock(spec=AsyncSession)
    session.execute.side_effect = OperationalError("SELECT count", {}, Exception("db is locked"))

    with pytest.raises(OperationalError):
        await get_document_count(session, project_id=1)


async def test_rebuild_fts_absent_table_returns_cleanly(session: AsyncSession) -> None:
    """No FTS table present -> clean early return, no error, no warning."""
    # session fixture has no documents_fts table
    await _rebuild_fts_if_exists(session)  # must not raise


async def test_rebuild_fts_failure_logged_at_warning(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A genuine rebuild failure is logged at WARNING, not swallowed at DEBUG."""
    from sdlc_lens.services.fts import FTS5_CREATE_SQL

    await session.execute(text(FTS5_CREATE_SQL))
    await session.commit()

    async def _boom(_session: AsyncSession) -> None:
        raise RuntimeError("rebuild exploded")

    monkeypatch.setattr(fts_module, "fts_rebuild", _boom)

    with caplog.at_level(logging.WARNING, logger="sdlc_lens.services.sync_engine"):
        await _rebuild_fts_if_exists(session)  # must not raise

    warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert any("FTS5 rebuild failed" in r.getMessage() for r in warnings)
