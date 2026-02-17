"""Integration tests for GET /api/v1/system/health endpoint.

Test cases: TC0046 from TS0003.
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


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
