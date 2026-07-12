"""Integration tests for GET /api/v1/system/health endpoint.

Test cases: TC0046 from TS0003.
"""

import importlib.metadata

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.services.fts import FTS5_CREATE_SQL


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _stamp_revision(session: AsyncSession, revision: str) -> None:
    """Create the alembic_version table and stamp it with a revision."""
    await session.execute(
        text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)")
    )
    await session.execute(
        text("INSERT INTO alembic_version (version_num) VALUES (:v)"), {"v": revision}
    )
    await session.commit()


async def _create_fts(session: AsyncSession) -> None:
    """Create the documents_fts virtual table."""
    await session.execute(text(FTS5_CREATE_SQL))
    await session.commit()


# TC0046: Health check returns 200
class TestHealthCheck:
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/system/health")
        assert response.status_code == 200

    async def test_status_healthy(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/system/health")
        data = response.json()
        assert data["status"] == "healthy"

    async def test_database_connected(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/system/health")
        data = response.json()
        assert data["database"] == "connected"

    async def test_version_present(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/system/health")
        data = response.json()
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0


class TestReadiness:
    """Deeper readiness signals for CD health-gating and monitoring."""

    async def test_healthy_app_reports_ready(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        from sdlc_lens.api.routes.system import head_revision

        await _stamp_revision(session, head_revision())
        await _create_fts(session)

        data = (await client.get("/api/v1/system/health")).json()
        assert data["migration_ok"] is True
        assert data["fts_ok"] is True
        assert data["ready"] is True

    async def test_db_behind_head_not_ready(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        await _stamp_revision(session, "001")  # older than head
        await _create_fts(session)

        response = await client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()
        assert data["migration_ok"] is False
        assert data["ready"] is False
        # A live-but-behind app is still "healthy" (connected), just not ready.
        assert data["status"] == "healthy"

    async def test_missing_fts_degrades_without_500(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        from sdlc_lens.api.routes.system import head_revision

        await _stamp_revision(session, head_revision())
        # Deliberately do not create the documents_fts table.

        response = await client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()
        assert data["fts_ok"] is False
        assert data["ready"] is False

    async def test_version_is_single_sourced(self, client: AsyncClient) -> None:
        data = (await client.get("/api/v1/system/health")).json()
        assert data["version"] == importlib.metadata.version("sdlc-lens")
