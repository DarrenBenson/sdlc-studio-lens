"""Integration tests for POST /api/v1/projects endpoint.

Test cases: TC0001-TC0002, TC0007-TC0018 from TS0001.
"""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def sdlc_dir(tmp_path: Path) -> Path:
    """Create a temporary sdlc-studio directory."""
    d = tmp_path / "sdlc-studio"
    d.mkdir()
    return d


@pytest.fixture
def sdlc_dir_2(tmp_path: Path) -> Path:
    """Create a second temporary sdlc-studio directory."""
    d = tmp_path / "sdlc-studio-2"
    d.mkdir()
    return d


# TC0001: Register project with valid name and path
class TestRegisterProject:
    async def test_returns_201_with_valid_data(self, client: AsyncClient, sdlc_dir: Path) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir)},
        )
        assert response.status_code == 201

    async def test_response_contains_slug(self, client: AsyncClient, sdlc_dir: Path) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir)},
        )
        data = response.json()
        assert data["slug"] == "homelabcmd"

    async def test_response_contains_name(self, client: AsyncClient, sdlc_dir: Path) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir)},
        )
        data = response.json()
        assert data["name"] == "HomelabCmd"

    async def test_response_contains_sdlc_path(self, client: AsyncClient, sdlc_dir: Path) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir)},
        )
        data = response.json()
        assert data["sdlc_path"] == str(sdlc_dir)


# TC0002: Response body field types are correct
class TestResponseFieldTypes:
    async def test_slug_is_string(self, client: AsyncClient, sdlc_dir: Path) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir)},
        )
        data = response.json()
        assert isinstance(data["slug"], str)
        assert len(data["slug"]) > 0

    async def test_document_count_is_integer(self, client: AsyncClient, sdlc_dir: Path) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir)},
        )
        data = response.json()
        assert isinstance(data["document_count"], int)
        assert data["document_count"] >= 0

    async def test_created_at_is_iso_string(self, client: AsyncClient, sdlc_dir: Path) -> None:
        from datetime import datetime

        response = await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir)},
        )
        data = response.json()
        # Should not raise
        datetime.fromisoformat(data["created_at"])


# TC0016: sync_status defaults to never_synced
class TestSyncStatusDefault:
    async def test_sync_status_is_never_synced(self, client: AsyncClient, sdlc_dir: Path) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir)},
        )
        data = response.json()
        assert data["sync_status"] == "never_synced"

    async def test_last_synced_at_is_null(self, client: AsyncClient, sdlc_dir: Path) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir)},
        )
        data = response.json()
        assert data["last_synced_at"] is None


# TC0017: document_count defaults to 0
class TestDocumentCountDefault:
    async def test_document_count_is_zero(self, client: AsyncClient, sdlc_dir: Path) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir)},
        )
        data = response.json()
        assert data["document_count"] == 0


# TC0007: Path validation rejects non-existent directory
class TestPathValidation:
    async def test_nonexistent_path_returns_400(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "TestProject", "sdlc_path": "/data/projects/nonexistent/sdlc-studio"},
        )
        assert response.status_code == 400

    async def test_nonexistent_path_error_code(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "TestProject", "sdlc_path": "/data/projects/nonexistent/sdlc-studio"},
        )
        data = response.json()
        assert data["error"]["code"] == "PATH_NOT_FOUND"

    async def test_nonexistent_path_error_message(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "TestProject", "sdlc_path": "/data/projects/nonexistent/sdlc-studio"},
        )
        data = response.json()
        assert "does not exist" in data["error"]["message"]


# TC0008: Path validation rejects file (not directory)
class TestPathRejectsFile:
    async def test_file_path_returns_400(self, client: AsyncClient, tmp_path: Path) -> None:
        file_path = tmp_path / "not-a-dir.txt"
        file_path.write_text("hello")
        response = await client.post(
            "/api/v1/projects",
            json={"name": "TestProject", "sdlc_path": str(file_path)},
        )
        assert response.status_code == 400

    async def test_file_path_error_code(self, client: AsyncClient, tmp_path: Path) -> None:
        file_path = tmp_path / "not-a-dir.txt"
        file_path.write_text("hello")
        response = await client.post(
            "/api/v1/projects",
            json={"name": "TestProject", "sdlc_path": str(file_path)},
        )
        data = response.json()
        assert data["error"]["code"] == "PATH_NOT_FOUND"


# TC0009: Duplicate slug rejection
class TestDuplicateSlug:
    async def test_duplicate_returns_409(
        self, client: AsyncClient, sdlc_dir: Path, sdlc_dir_2: Path
    ) -> None:
        await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir)},
        )
        response = await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir_2)},
        )
        assert response.status_code == 409

    async def test_duplicate_error_code(
        self, client: AsyncClient, sdlc_dir: Path, sdlc_dir_2: Path
    ) -> None:
        await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir)},
        )
        response = await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir_2)},
        )
        data = response.json()
        assert data["error"]["code"] == "CONFLICT"

    async def test_duplicate_error_message(
        self, client: AsyncClient, sdlc_dir: Path, sdlc_dir_2: Path
    ) -> None:
        await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir)},
        )
        response = await client.post(
            "/api/v1/projects",
            json={"name": "HomelabCmd", "sdlc_path": str(sdlc_dir_2)},
        )
        data = response.json()
        assert "slug already exists" in data["error"]["message"]


# TC0010: Duplicate slug from different name (same slug output)
class TestDuplicateSlugDifferentName:
    async def test_slug_collision_returns_409(
        self, client: AsyncClient, sdlc_dir: Path, sdlc_dir_2: Path
    ) -> None:
        await client.post(
            "/api/v1/projects",
            json={"name": "Hello World", "sdlc_path": str(sdlc_dir)},
        )
        response = await client.post(
            "/api/v1/projects",
            json={"name": "Hello_World", "sdlc_path": str(sdlc_dir_2)},
        )
        assert response.status_code == 409


# TC0011: Missing name field returns 422
class TestMissingName:
    async def test_missing_name_returns_422(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"sdlc_path": "/some/path"},
        )
        assert response.status_code == 422


# TC0012: Missing sdlc_path field returns 422
class TestMissingSdlcPath:
    async def test_missing_path_returns_422(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "TestProject"},
        )
        assert response.status_code == 422


# TC0013: Empty name string returns 422
class TestEmptyName:
    async def test_empty_name_returns_422(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "", "sdlc_path": "/some/path"},
        )
        assert response.status_code == 422


# TC0014: Very long name returns 422
class TestLongName:
    async def test_name_over_200_chars_returns_422(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "A" * 201, "sdlc_path": "/some/path"},
        )
        assert response.status_code == 422


# TC0015: Path with trailing slash accepted
class TestTrailingSlash:
    async def test_trailing_slash_accepted(self, client: AsyncClient, sdlc_dir: Path) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "TestProject", "sdlc_path": str(sdlc_dir) + "/"},
        )
        assert response.status_code == 201


# TC0018: Name-only special characters returns 422 (empty slug)
class TestSpecialCharsOnlyName:
    async def test_only_special_chars_returns_422(
        self, client: AsyncClient, sdlc_dir: Path
    ) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "!!!", "sdlc_path": str(sdlc_dir)},
        )
        assert response.status_code == 422


class TestAutoSyncField:
    """CR-01KXCAZJ: auto-sync is opt-in, and freshness must be legible."""

    async def test_auto_sync_defaults_off_in_the_response(
        self, client: AsyncClient, sdlc_dir: Path
    ) -> None:
        resp = await client.post(
            "/api/v1/projects", json={"name": "Auto Off", "sdlc_path": str(sdlc_dir)}
        )
        assert resp.status_code == 201
        assert resp.json()["auto_sync"] is False, "a new project polls itself without being asked"

    async def test_auto_sync_can_be_toggled(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await client.post(
            "/api/v1/projects", json={"name": "Toggle Me", "sdlc_path": str(sdlc_dir)}
        )

        resp = await client.put("/api/v1/projects/toggle-me", json={"auto_sync": True})
        assert resp.status_code == 200
        assert resp.json()["auto_sync"] is True

        resp = await client.get("/api/v1/projects/toggle-me")
        assert resp.json()["auto_sync"] is True

        resp = await client.put("/api/v1/projects/toggle-me", json={"auto_sync": False})
        assert resp.json()["auto_sync"] is False

    async def test_freshness_is_in_the_response_regardless_of_auto_sync(
        self, client: AsyncClient, sdlc_dir: Path
    ) -> None:
        """The honesty gap exists whether or not polling is on."""
        await client.post("/api/v1/projects", json={"name": "Fresh", "sdlc_path": str(sdlc_dir)})

        body = (await client.get("/api/v1/projects/fresh")).json()
        assert "last_synced_at" in body
        assert "auto_sync" in body
