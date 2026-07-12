"""GitHub repo selector: service + endpoint tests (CR-01KXAS75).

Covers:
  - ``list_repositories`` aggregating the authenticated user's repos with their
    orgs' repos and de-duplicating overlaps.
  - ``repo_has_sdlc_studio`` returning True on 200 / False on 404, and mapping
    auth / rate-limit responses to the shared error hierarchy.
  - The two POST endpoints on the projects router returning the expected shapes,
    with the token supplied in the request body (never in the URL).
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from sdlc_lens.services.github_source import (
    AuthenticationError,
    RateLimitError,
    list_repositories,
    repo_has_sdlc_studio,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _json_response(status_code, payload=None, headers=None) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        json=payload if payload is not None else [],
        headers=headers or {},
        request=httpx.Request("GET", "https://api.github.com/x"),
    )


def _mock_client(get_side_effect) -> AsyncMock:
    client = AsyncMock()
    client.get = AsyncMock(side_effect=get_side_effect)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


_REPO_A = {
    "full_name": "alice/app",
    "name": "app",
    "owner": {"login": "alice"},
    "private": False,
    "default_branch": "main",
    "description": "The app",
}
_REPO_B = {
    "full_name": "alice/lib",
    "name": "lib",
    "owner": {"login": "alice"},
    "private": True,
    "default_branch": "dev",
    "description": None,
}
_REPO_C = {
    "full_name": "acme/service",
    "name": "service",
    "owner": {"login": "acme"},
    "private": True,
    "default_branch": "main",
    "description": "svc",
}


# ---------------------------------------------------------------------------
# list_repositories
# ---------------------------------------------------------------------------


class TestListRepositories:
    @pytest.mark.asyncio
    async def test_aggregates_user_and_org_repos_and_dedupes(self) -> None:
        def fake_get(url, params=None):
            if url.endswith("/user/repos"):
                # _REPO_B is deliberately repeated in the org listing below.
                return _json_response(200, [_REPO_A, _REPO_B])
            if url.endswith("/user/orgs"):
                return _json_response(200, [{"login": "acme"}])
            if url.endswith("/orgs/acme/repos"):
                return _json_response(200, [_REPO_B, _REPO_C])
            raise AssertionError(f"unexpected URL: {url}")

        client = _mock_client(fake_get)
        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client):
            repos = await list_repositories("ghp_token")

        by_name = {r["full_name"]: r for r in repos}
        assert set(by_name) == {"alice/app", "alice/lib", "acme/service"}
        # De-duped: alice/lib appears in both listings but only once.
        assert len(repos) == 3
        # Field mapping.
        assert by_name["alice/app"]["owner"] == "alice"
        assert by_name["alice/app"]["name"] == "app"
        assert by_name["alice/lib"]["private"] is True
        assert by_name["alice/lib"]["default_branch"] == "dev"
        assert by_name["acme/service"]["description"] == "svc"

    @pytest.mark.asyncio
    async def test_missing_token_raises_auth_error(self) -> None:
        with pytest.raises(AuthenticationError):
            await list_repositories("")

    @pytest.mark.asyncio
    async def test_rate_limit_raises_rate_limit_error(self) -> None:
        def fake_get(url, params=None):
            return _json_response(403, [], headers={"x-ratelimit-remaining": "0"})

        client = _mock_client(fake_get)
        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client),
            pytest.raises(RateLimitError),
        ):
            await list_repositories("ghp_token")

    @pytest.mark.asyncio
    async def test_bad_token_raises_auth_error(self) -> None:
        def fake_get(url, params=None):
            return _json_response(401, {"message": "Bad credentials"})

        client = _mock_client(fake_get)
        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client),
            pytest.raises(AuthenticationError),
        ):
            await list_repositories("ghp_bad")

    @pytest.mark.asyncio
    async def test_secondary_rate_limit_raises_rate_limit_error(self) -> None:
        # A secondary/abuse-limit 403 carries Retry-After with a non-zero
        # remaining count; it must map to RateLimitError, not AuthenticationError.
        def fake_get(url, params=None):
            return _json_response(
                403, [], headers={"retry-after": "60", "x-ratelimit-remaining": "42"}
            )

        client = _mock_client(fake_get)
        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client),
            pytest.raises(RateLimitError),
        ):
            await list_repositories("ghp_token")


# ---------------------------------------------------------------------------
# repo_has_sdlc_studio
# ---------------------------------------------------------------------------


class TestRepoHasSdlcStudio:
    @pytest.mark.asyncio
    async def test_returns_true_on_200(self) -> None:
        def fake_get(url, params=None):
            assert url.endswith("/repos/alice/app/contents/sdlc-studio")
            return _json_response(200, [{"name": "epics"}])

        client = _mock_client(fake_get)
        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client):
            result = await repo_has_sdlc_studio("ghp_token", "alice", "app")
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_on_404(self) -> None:
        def fake_get(url, params=None):
            return _json_response(404, {"message": "Not Found"})

        client = _mock_client(fake_get)
        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client):
            result = await repo_has_sdlc_studio("ghp_token", "alice", "app")
        assert result is False

    @pytest.mark.asyncio
    async def test_rate_limit_raises(self) -> None:
        def fake_get(url, params=None):
            return _json_response(403, [], headers={"x-ratelimit-remaining": "0"})

        client = _mock_client(fake_get)
        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client),
            pytest.raises(RateLimitError),
        ):
            await repo_has_sdlc_studio("ghp_token", "alice", "app")

    @pytest.mark.asyncio
    async def test_passes_branch_as_ref(self) -> None:
        captured: dict = {}

        def fake_get(url, params=None):
            captured["params"] = params
            return _json_response(200, [])

        client = _mock_client(fake_get)
        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client):
            await repo_has_sdlc_studio("ghp_token", "alice", "app", "develop")
        assert captured["params"] == {"ref": "develop"}


# ---------------------------------------------------------------------------
# Endpoints (mock the service layer)
# ---------------------------------------------------------------------------


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestListReposEndpoint:
    async def test_returns_repo_list_shape(self, client: AsyncClient) -> None:
        service_return = [
            {
                "full_name": "alice/app",
                "owner": "alice",
                "name": "app",
                "private": False,
                "default_branch": "main",
                "description": "The app",
            }
        ]
        with patch(
            "sdlc_lens.api.routes.projects.list_repositories",
            AsyncMock(return_value=service_return),
        ):
            resp = await client.post(
                "/api/v1/projects/github/repos",
                json={"access_token": "ghp_token"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["repositories"][0]["full_name"] == "alice/app"
        assert data["repositories"][0]["default_branch"] == "main"

    async def test_token_required(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/projects/github/repos", json={})
        assert resp.status_code == 422

    async def test_search_filters_by_name(self, client: AsyncClient) -> None:
        service_return = [
            {
                "full_name": "alice/app",
                "owner": "alice",
                "name": "app",
                "private": False,
                "default_branch": "main",
                "description": None,
            },
            {
                "full_name": "acme/service",
                "owner": "acme",
                "name": "service",
                "private": True,
                "default_branch": "main",
                "description": None,
            },
        ]
        with patch(
            "sdlc_lens.api.routes.projects.list_repositories",
            AsyncMock(return_value=service_return),
        ):
            resp = await client.post(
                "/api/v1/projects/github/repos",
                json={"access_token": "ghp_token", "search": "acme"},
            )
        assert resp.status_code == 200
        names = [r["full_name"] for r in resp.json()["repositories"]]
        assert names == ["acme/service"]

    async def test_rate_limit_returns_429(self, client: AsyncClient) -> None:
        with patch(
            "sdlc_lens.api.routes.projects.list_repositories",
            AsyncMock(side_effect=RateLimitError()),
        ):
            resp = await client.post(
                "/api/v1/projects/github/repos",
                json={"access_token": "ghp_token"},
            )
        assert resp.status_code == 429
        assert resp.json()["error"]["code"] == "RATE_LIMITED"

    async def test_auth_error_returns_401(self, client: AsyncClient) -> None:
        with patch(
            "sdlc_lens.api.routes.projects.list_repositories",
            AsyncMock(side_effect=AuthenticationError()),
        ):
            resp = await client.post(
                "/api/v1/projects/github/repos",
                json={"access_token": "bad"},
            )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "AUTH_FAILED"


class TestHasSdlcStudioEndpoint:
    async def test_returns_true(self, client: AsyncClient) -> None:
        with patch(
            "sdlc_lens.api.routes.projects.repo_has_sdlc_studio",
            AsyncMock(return_value=True),
        ):
            resp = await client.post(
                "/api/v1/projects/github/repos/alice/app/has-sdlc-studio",
                json={"access_token": "ghp_token"},
            )
        assert resp.status_code == 200
        assert resp.json() == {"has_sdlc_studio": True}

    async def test_returns_false(self, client: AsyncClient) -> None:
        with patch(
            "sdlc_lens.api.routes.projects.repo_has_sdlc_studio",
            AsyncMock(return_value=False),
        ):
            resp = await client.post(
                "/api/v1/projects/github/repos/alice/app/has-sdlc-studio",
                json={"access_token": "ghp_token"},
            )
        assert resp.status_code == 200
        assert resp.json() == {"has_sdlc_studio": False}

    async def test_token_in_body_not_url(self, client: AsyncClient) -> None:
        captured: dict = {}

        async def fake_check(access_token, owner, repo, branch=None):
            captured["access_token"] = access_token
            captured["owner"] = owner
            captured["repo"] = repo
            return True

        with patch(
            "sdlc_lens.api.routes.projects.repo_has_sdlc_studio",
            AsyncMock(side_effect=fake_check),
        ):
            resp = await client.post(
                "/api/v1/projects/github/repos/alice/app/has-sdlc-studio",
                json={"access_token": "ghp_secret"},
            )
        assert resp.status_code == 200
        assert captured["access_token"] == "ghp_secret"
        assert captured["owner"] == "alice"
        assert captured["repo"] == "app"

    async def test_rate_limit_returns_429(self, client: AsyncClient) -> None:
        with patch(
            "sdlc_lens.api.routes.projects.repo_has_sdlc_studio",
            AsyncMock(side_effect=RateLimitError()),
        ):
            resp = await client.post(
                "/api/v1/projects/github/repos/alice/app/has-sdlc-studio",
                json={"access_token": "ghp_token"},
            )
        assert resp.status_code == 429
