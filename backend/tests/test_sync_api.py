"""Integration tests for POST /api/v1/projects/{slug}/sync endpoint.

Test cases: TC0035-TC0045, TC0047 from TS0003.
"""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker

from sdlc_lens.db.models.project import Project


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def sdlc_dir(tmp_path: Path) -> Path:
    d = tmp_path / "sdlc-studio"
    d.mkdir()
    return d


async def _register(client: AsyncClient, name: str, sdlc_path: Path) -> dict:
    """Helper to register a project and return the response data."""
    resp = await client.post(
        "/api/v1/projects",
        json={"name": name, "sdlc_path": str(sdlc_path)},
    )
    assert resp.status_code == 201
    return resp.json()


async def _set_sync_status(engine, slug: str, status: str, sync_error: str | None = None) -> None:
    """Helper to set sync status directly in the database."""
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as sess:
        await sess.execute(
            update(Project)
            .where(Project.slug == slug)
            .values(sync_status=status, sync_error=sync_error)
        )
        await sess.commit()


# TC0035: Sync trigger returns 202 for valid project
class TestSyncTrigger:
    async def test_returns_202(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)
        response = await client.post("/api/v1/projects/homelabcmd/sync")
        assert response.status_code == 202

    async def test_response_body_fields(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)
        response = await client.post("/api/v1/projects/homelabcmd/sync")
        data = response.json()
        assert data["slug"] == "homelabcmd"
        assert data["sync_status"] == "syncing"
        assert data["message"] == "Sync started"


# TC0036: Sync trigger for non-existent project returns 404
class TestSyncTriggerNotFound:
    async def test_returns_404(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/projects/nonexistent/sync")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"


# TC0037: Sync status transitions to synced on success
class TestSyncTransitionToSynced:
    async def test_status_becomes_synced(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)
        await client.post("/api/v1/projects/homelabcmd/sync")

        response = await client.get("/api/v1/projects/homelabcmd")
        data = response.json()
        assert data["sync_status"] == "synced"

    async def test_last_synced_at_is_set(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)
        await client.post("/api/v1/projects/homelabcmd/sync")

        response = await client.get("/api/v1/projects/homelabcmd")
        data = response.json()
        assert data["last_synced_at"] is not None


# TC0038: last_synced_at updated on re-sync
class TestLastSyncedAtUpdated:
    async def test_timestamp_updated_on_resync(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        # First sync
        await client.post("/api/v1/projects/homelabcmd/sync")
        resp1 = await client.get("/api/v1/projects/homelabcmd")
        first_ts = resp1.json()["last_synced_at"]

        # Second sync
        await client.post("/api/v1/projects/homelabcmd/sync")
        resp2 = await client.get("/api/v1/projects/homelabcmd")
        second_ts = resp2.json()["last_synced_at"]

        assert second_ts >= first_ts


# TC0039: Sync status transitions to error on failure
class TestSyncTransitionToError:
    async def test_status_becomes_error(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        # Remove the directory so sync fails
        sdlc_dir.rmdir()

        await client.post("/api/v1/projects/homelabcmd/sync")

        response = await client.get("/api/v1/projects/homelabcmd")
        data = response.json()
        assert data["sync_status"] == "error"

    async def test_sync_error_is_populated(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)
        sdlc_dir.rmdir()

        await client.post("/api/v1/projects/homelabcmd/sync")

        response = await client.get("/api/v1/projects/homelabcmd")
        data = response.json()
        assert data["sync_error"] is not None
        assert len(data["sync_error"]) > 0


# TC0040: sync_error cleared on new sync attempt
class TestSyncErrorCleared:
    async def test_error_cleared_on_resync(
        self, client: AsyncClient, sdlc_dir: Path, engine
    ) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        # Set error state directly
        await _set_sync_status(engine, "homelabcmd", "error", "Previous failure")

        # Re-sync (directory still exists)
        response = await client.post("/api/v1/projects/homelabcmd/sync")
        assert response.status_code == 202

        # Check error is cleared after sync completes
        resp = await client.get("/api/v1/projects/homelabcmd")
        data = resp.json()
        assert data["sync_error"] is None


# TC0041: Concurrent sync returns 409
class TestConcurrentSync:
    async def test_returns_409_when_syncing(
        self, client: AsyncClient, sdlc_dir: Path, engine
    ) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        # Set syncing status directly to simulate in-progress sync
        await _set_sync_status(engine, "homelabcmd", "syncing")

        response = await client.post("/api/v1/projects/homelabcmd/sync")
        assert response.status_code == 409

    async def test_error_code_sync_in_progress(
        self, client: AsyncClient, sdlc_dir: Path, engine
    ) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)
        await _set_sync_status(engine, "homelabcmd", "syncing")

        response = await client.post("/api/v1/projects/homelabcmd/sync")
        data = response.json()
        assert data["error"]["code"] == "SYNC_IN_PROGRESS"
        assert "Sync already running" in data["error"]["message"]


# TC0042: Multiple rapid sync triggers
class TestMultipleRapidSyncTriggers:
    async def test_first_202_second_409(self, client: AsyncClient, sdlc_dir: Path, engine) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        # First sync succeeds
        first = await client.post("/api/v1/projects/homelabcmd/sync")
        assert first.status_code == 202

        # Simulate sync still in progress (background task completed in test)
        await _set_sync_status(engine, "homelabcmd", "syncing")

        second = await client.post("/api/v1/projects/homelabcmd/sync")
        assert second.status_code == 409


# TC0043: Sync status queryable via project detail
class TestSyncStatusQueryable:
    async def test_syncing_status_visible(
        self, client: AsyncClient, sdlc_dir: Path, engine
    ) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)
        await _set_sync_status(engine, "homelabcmd", "syncing")

        response = await client.get("/api/v1/projects/homelabcmd")
        data = response.json()
        assert data["sync_status"] == "syncing"


# TC0044: Re-sync from synced state
class TestResyncFromSynced:
    async def test_resync_returns_202(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        # First sync
        await client.post("/api/v1/projects/homelabcmd/sync")
        resp = await client.get("/api/v1/projects/homelabcmd")
        assert resp.json()["sync_status"] == "synced"

        # Re-sync
        response = await client.post("/api/v1/projects/homelabcmd/sync")
        assert response.status_code == 202
        assert response.json()["sync_status"] == "syncing"


# TC0045: Re-sync from error state
class TestResyncFromError:
    async def test_resync_from_error_returns_202(
        self, client: AsyncClient, sdlc_dir: Path, engine
    ) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)
        await _set_sync_status(engine, "homelabcmd", "error", "Previous failure")

        response = await client.post("/api/v1/projects/homelabcmd/sync")
        assert response.status_code == 202
        assert response.json()["sync_status"] == "syncing"


# TC0047: Sync with zero documents in directory
class TestSyncEmptyDirectory:
    async def test_synced_with_zero_docs(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        # sdlc_dir is empty (no .md files)
        await client.post("/api/v1/projects/homelabcmd/sync")

        response = await client.get("/api/v1/projects/homelabcmd")
        data = response.json()
        assert data["sync_status"] == "synced"
        assert data["document_count"] == 0
