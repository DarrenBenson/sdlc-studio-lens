"""API integration tests for GitHub source type endpoints.

Test cases: TC0317-TC0323, TC0326-TC0327 from TS0031.
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
    d = tmp_path / "sdlc-studio"
    d.mkdir()
    return d


async def _register_local(client: AsyncClient, name: str, sdlc_path: Path) -> dict:
    """Register a local project."""
    resp = await client.post(
        "/api/v1/projects",
        json={"name": name, "sdlc_path": str(sdlc_path)},
    )
    assert resp.status_code == 201
    return resp.json()


async def _register_github(
    client: AsyncClient,
    name: str,
    repo_url: str = "https://github.com/owner/repo",
    access_token: str | None = None,
) -> dict:
    """Register a GitHub project."""
    payload: dict = {
        "name": name,
        "source_type": "github",
        "repo_url": repo_url,
    }
    if access_token:
        payload["access_token"] = access_token
    resp = await client.post("/api/v1/projects", json=payload)
    assert resp.status_code == 201
    return resp.json()


# TC0317: POST /projects with source_type=local requires sdlc_path
class TestLocalRequiresSdlcPath:
    async def test_local_without_path_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/projects",
            json={"name": "Test", "source_type": "local"},
        )
        assert resp.status_code == 422


# TC0318: POST /projects with source_type=github requires repo_url
class TestGithubRequiresRepoUrl:
    async def test_github_without_url_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/projects",
            json={"name": "Test", "source_type": "github"},
        )
        assert resp.status_code == 422


# TC0319: POST /projects with source_type=github does not require sdlc_path
class TestGithubNoSdlcPath:
    async def test_github_without_sdlc_path_succeeds(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/projects",
            json={
                "name": "GitHub Test",
                "source_type": "github",
                "repo_url": "https://github.com/owner/repo",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["source_type"] == "github"
        assert data["sdlc_path"] is None


# TC0320: POST /projects with source_type=local ignores repo fields
class TestLocalIgnoresRepoFields:
    async def test_local_accepts_repo_fields(
        self, client: AsyncClient, sdlc_dir: Path
    ) -> None:
        resp = await client.post(
            "/api/v1/projects",
            json={
                "name": "Local Test",
                "source_type": "local",
                "sdlc_path": str(sdlc_dir),
                "repo_url": "https://github.com/owner/repo",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["source_type"] == "local"
        assert str(sdlc_dir) in data["sdlc_path"]


# TC0321: POST /projects defaults source_type to "local" when omitted
class TestDefaultSourceType:
    async def test_defaults_to_local(
        self, client: AsyncClient, sdlc_dir: Path
    ) -> None:
        resp = await client.post(
            "/api/v1/projects",
            json={"name": "Default Test", "sdlc_path": str(sdlc_dir)},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["source_type"] == "local"


# TC0322: GET /projects returns masked access_token
class TestListMasksToken:
    async def test_list_masks_token(self, client: AsyncClient) -> None:
        await _register_github(
            client, "GitHub Test", access_token="ghp_abcdef1234567890"
        )

        resp = await client.get("/api/v1/projects")
        assert resp.status_code == 200
        data = resp.json()
        project = data[0]
        assert project["masked_token"] == "****7890"


# TC0323: GET /projects/{slug} returns masked access_token
class TestGetMasksToken:
    async def test_get_single_masks_token(self, client: AsyncClient) -> None:
        data = await _register_github(
            client, "GitHub Test", access_token="ghp_abcdef1234567890"
        )

        resp = await client.get(f"/api/v1/projects/{data['slug']}")
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["masked_token"] == "****7890"
        assert detail["repo_url"] == "https://github.com/owner/repo"
        assert detail["repo_branch"] == "main"
        assert detail["repo_path"] == "sdlc-studio"


# TC0326: PUT /projects/{slug} updates repo_url
class TestUpdateRepoUrl:
    async def test_updates_repo_url(self, client: AsyncClient) -> None:
        data = await _register_github(client, "GitHub Test")

        resp = await client.put(
            f"/api/v1/projects/{data['slug']}",
            json={"repo_url": "https://github.com/new-owner/new-repo"},
        )
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["repo_url"] == "https://github.com/new-owner/new-repo"


# TC0327: PUT /projects/{slug} updates access_token
class TestUpdateAccessToken:
    async def test_updates_token_and_masks_in_response(
        self, client: AsyncClient
    ) -> None:
        data = await _register_github(
            client, "GitHub Test", access_token="ghp_oldtoken1234"
        )

        resp = await client.put(
            f"/api/v1/projects/{data['slug']}",
            json={"access_token": "ghp_newtoken9876"},
        )
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["masked_token"] == "****9876"

        # Verify the new masked token persists on subsequent GET
        resp2 = await client.get(f"/api/v1/projects/{data['slug']}")
        assert resp2.json()["masked_token"] == "****9876"
