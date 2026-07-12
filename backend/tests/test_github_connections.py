"""Stored GitHub connections (CR-01KXAZX9).

A GitHub PAT becomes a first-class, reusable, validated entity instead of a
per-project column the operator re-pastes on every repo. This suite pins:

  - creation validates the token against ``GET /user`` and stores the resolved
    login; an invalid token is REJECTED and nothing is persisted;
  - the masked-token invariant: no response body from any connections endpoint
    carries the raw PAT;
  - duplicate label -> 409, delete-in-use -> 409 naming the projects,
    delete-unused -> 204, unknown id -> 404;
  - revalidation refreshes ``last_validated_at``; a now-invalid token -> 401;
  - the repo-browse endpoints accept ``connection_id`` as an alternative to a
    raw ``access_token``, resolving and decrypting the stored token server-side;
  - sync token precedence: the connection's token wins when ``connection_id`` is
    set, otherwise the per-project token still works (no migration of secrets);
  - ``alembic upgrade head`` reaches revision 011.
"""

import hashlib
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.config import settings
from sdlc_lens.db.models.github_connection import GitHubConnection
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.github_source import (
    AuthenticationError,
    get_authenticated_login,
)
from sdlc_lens.services.project import create_project
from sdlc_lens.services.sync_engine import sync_project
from sdlc_lens.utils.crypto import encrypt_token

# A stable, valid urlsafe-base64 Fernet key so the stored token is real ciphertext.
TEST_KEY = "ND_jjxyhtEE4sCJaXwGCdfFutCSE6aSitXpKL4sSxJQ="
RAW_TOKEN = "ghp_liveconnectionsecret9876"
OTHER_TOKEN = "ghp_perprojectsecret5432"


@pytest.fixture(autouse=True)
def with_key(monkeypatch: pytest.MonkeyPatch) -> str:
    """Encrypt stored tokens for every test in this module."""
    monkeypatch.setattr(settings, "token_encryption_key", TEST_KEY)
    return TEST_KEY


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# httpx mocking helpers (mirrors tests/test_github_repo_selector.py)
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


def _client_factory(get_side_effect, captured: dict):
    """Build an httpx.AsyncClient replacement that records its constructor kwargs."""
    mock = _mock_client(get_side_effect)

    def factory(*args, **kwargs):
        captured["headers"] = kwargs.get("headers")
        return mock

    return factory


async def _seed_connection(session: AsyncSession, label: str = "Personal") -> GitHubConnection:
    """Insert a stored connection directly (token encrypted at rest)."""
    conn = GitHubConnection(
        label=label,
        login="alice",
        access_token=encrypt_token(RAW_TOKEN),
    )
    session.add(conn)
    await session.commit()
    await session.refresh(conn)
    return conn


# ---------------------------------------------------------------------------
# get_authenticated_login (service)
# ---------------------------------------------------------------------------


class TestGetAuthenticatedLogin:
    async def test_returns_login_on_200(self) -> None:
        captured: dict = {}

        def fake_get(url, params=None):
            assert url.endswith("/user")
            return _json_response(200, {"login": "alice", "id": 1})

        with patch(
            "sdlc_lens.services.github_source.httpx.AsyncClient",
            side_effect=_client_factory(fake_get, captured),
        ):
            login = await get_authenticated_login(RAW_TOKEN)

        assert login == "alice"
        assert captured["headers"]["Authorization"] == f"Bearer {RAW_TOKEN}"

    async def test_bad_token_raises_authentication_error(self) -> None:
        def fake_get(url, params=None):
            return _json_response(401, {"message": "Bad credentials"})

        captured: dict = {}
        with (
            patch(
                "sdlc_lens.services.github_source.httpx.AsyncClient",
                side_effect=_client_factory(fake_get, captured),
            ),
            pytest.raises(AuthenticationError),
        ):
            await get_authenticated_login("ghp_bad")

    async def test_empty_token_raises_authentication_error(self) -> None:
        with pytest.raises(AuthenticationError):
            await get_authenticated_login("")


# ---------------------------------------------------------------------------
# POST /api/v1/connections
# ---------------------------------------------------------------------------


class TestCreateConnection:
    async def test_validates_token_and_stores_resolved_login(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        with patch(
            "sdlc_lens.services.github_connection.get_authenticated_login",
            AsyncMock(return_value="alice"),
        ):
            resp = await client.post(
                "/api/v1/connections",
                json={"label": "Personal", "access_token": RAW_TOKEN},
            )

        assert resp.status_code == 201
        body = resp.json()
        assert body["label"] == "Personal"
        assert body["login"] == "alice"
        assert body["masked_token"] == f"****{RAW_TOKEN[-4:]}"
        assert body["id"] > 0
        assert body["created_at"]
        assert body["last_validated_at"]

        # Persisted, with the token encrypted at rest (never the raw value).
        stored = (await session.execute(select(GitHubConnection))).scalar_one()
        assert stored.login == "alice"
        assert stored.access_token != RAW_TOKEN
        assert RAW_TOKEN not in stored.access_token

    async def test_invalid_token_is_rejected_and_nothing_is_persisted(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        with patch(
            "sdlc_lens.services.github_connection.get_authenticated_login",
            AsyncMock(side_effect=AuthenticationError("Bad credentials")),
        ):
            resp = await client.post(
                "/api/v1/connections",
                json={"label": "Personal", "access_token": "ghp_bad"},
            )

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_TOKEN"

        rows = (await session.execute(select(GitHubConnection))).scalars().all()
        assert rows == []

    async def test_duplicate_label_returns_409(self, client: AsyncClient) -> None:
        with patch(
            "sdlc_lens.services.github_connection.get_authenticated_login",
            AsyncMock(return_value="alice"),
        ):
            first = await client.post(
                "/api/v1/connections",
                json={"label": "Personal", "access_token": RAW_TOKEN},
            )
            second = await client.post(
                "/api/v1/connections",
                json={"label": "Personal", "access_token": "ghp_another000"},
            )

        assert first.status_code == 201
        assert second.status_code == 409
        assert second.json()["error"]["code"] == "LABEL_EXISTS"


# ---------------------------------------------------------------------------
# The masked-token invariant: NO endpoint response ever carries the raw token.
# ---------------------------------------------------------------------------


class TestRawTokenNeverLeaves:
    async def test_no_connections_response_contains_the_raw_token(
        self, client: AsyncClient
    ) -> None:
        bodies: list[str] = []

        with patch(
            "sdlc_lens.services.github_connection.get_authenticated_login",
            AsyncMock(return_value="alice"),
        ):
            created = await client.post(
                "/api/v1/connections",
                json={"label": "Personal", "access_token": RAW_TOKEN},
            )
            bodies.append(created.text)
            conn_id = created.json()["id"]

            listed = await client.get("/api/v1/connections")
            bodies.append(listed.text)

            revalidated = await client.post(f"/api/v1/connections/{conn_id}/validate")
            bodies.append(revalidated.text)

            deleted = await client.delete(f"/api/v1/connections/{conn_id}")
            bodies.append(deleted.text)

        assert created.status_code == 201
        assert listed.status_code == 200
        assert revalidated.status_code == 200
        assert deleted.status_code == 204

        for body in bodies:
            assert RAW_TOKEN not in body
            # Nor any leak of the encrypted-at-rest form.
            assert "enc:v1:" not in body
            # Nor an "access_token" field of any kind.
            assert "access_token" not in body


# ---------------------------------------------------------------------------
# GET /api/v1/connections
# ---------------------------------------------------------------------------


class TestListConnections:
    async def test_empty_list(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/connections")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_lists_stored_connections(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        await _seed_connection(session, "Personal")
        resp = await client.get("/api/v1/connections")

        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert items[0]["label"] == "Personal"
        assert items[0]["login"] == "alice"
        assert items[0]["masked_token"] == f"****{RAW_TOKEN[-4:]}"
        assert items[0]["last_validated_at"] is None


# ---------------------------------------------------------------------------
# POST /api/v1/connections/{id}/validate
# ---------------------------------------------------------------------------


class TestValidateConnection:
    async def test_refreshes_last_validated_at(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        conn = await _seed_connection(session)
        assert conn.last_validated_at is None

        captured: dict = {}

        async def fake_login(token, *args, **kwargs):
            captured["token"] = token
            return "alice"

        with patch(
            "sdlc_lens.services.github_connection.get_authenticated_login",
            AsyncMock(side_effect=fake_login),
        ):
            resp = await client.post(f"/api/v1/connections/{conn.id}/validate")

        assert resp.status_code == 200
        assert resp.json()["last_validated_at"] is not None
        assert RAW_TOKEN not in resp.text
        # The stored ciphertext must be decrypted before it hits GitHub.
        assert captured["token"] == RAW_TOKEN

    async def test_now_invalid_token_returns_401(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        conn = await _seed_connection(session)

        with patch(
            "sdlc_lens.services.github_connection.get_authenticated_login",
            AsyncMock(side_effect=AuthenticationError("Bad credentials")),
        ):
            resp = await client.post(f"/api/v1/connections/{conn.id}/validate")

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_TOKEN"

    async def test_unknown_id_returns_404(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/connections/999/validate")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# DELETE /api/v1/connections/{id}
# ---------------------------------------------------------------------------


class TestDeleteConnection:
    async def test_unused_connection_deletes(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        conn = await _seed_connection(session)

        resp = await client.delete(f"/api/v1/connections/{conn.id}")
        assert resp.status_code == 204

        rows = (await session.execute(select(GitHubConnection))).scalars().all()
        assert rows == []

    async def test_in_use_connection_returns_409_naming_projects(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        conn = await _seed_connection(session)
        session.add(
            Project(
                slug="acme-docs",
                name="Acme Docs",
                source_type="github",
                repo_url="https://github.com/acme/docs",
                connection_id=conn.id,
            )
        )
        await session.commit()

        resp = await client.delete(f"/api/v1/connections/{conn.id}")

        assert resp.status_code == 409
        error = resp.json()["error"]
        assert error["code"] == "CONNECTION_IN_USE"
        assert "acme-docs" in error["message"]

        # Still there.
        rows = (await session.execute(select(GitHubConnection))).scalars().all()
        assert len(rows) == 1

    async def test_unknown_id_returns_404(self, client: AsyncClient) -> None:
        resp = await client.delete("/api/v1/connections/999")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# Browse endpoints: connection_id as an alternative to a raw access_token.
# ---------------------------------------------------------------------------


class TestBrowseByConnection:
    async def test_list_repos_by_connection_id_uses_decrypted_token(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        conn = await _seed_connection(session)
        captured: dict = {}

        def fake_get(url, params=None):
            if url.endswith("/user/repos"):
                return _json_response(
                    200,
                    [
                        {
                            "full_name": "alice/app",
                            "name": "app",
                            "owner": {"login": "alice"},
                            "private": False,
                            "default_branch": "main",
                            "description": None,
                        }
                    ],
                )
            if url.endswith("/user/orgs"):
                return _json_response(200, [])
            raise AssertionError(f"unexpected URL: {url}")

        with patch(
            "sdlc_lens.services.github_source.httpx.AsyncClient",
            side_effect=_client_factory(fake_get, captured),
        ):
            resp = await client.post(
                "/api/v1/projects/github/repos",
                json={"connection_id": conn.id},
            )

        assert resp.status_code == 200
        assert resp.json()["repositories"][0]["full_name"] == "alice/app"
        # The decrypted PAT must reach GitHub, not the stored ciphertext.
        assert captured["headers"]["Authorization"] == f"Bearer {RAW_TOKEN}"

    async def test_list_repos_by_raw_token_still_works(self, client: AsyncClient) -> None:
        with patch(
            "sdlc_lens.api.routes.projects.list_repositories",
            AsyncMock(return_value=[]),
        ) as mock_list:
            resp = await client.post(
                "/api/v1/projects/github/repos",
                json={"access_token": "ghp_oneoff123"},
            )

        assert resp.status_code == 200
        assert mock_list.call_args.args[0] == "ghp_oneoff123"

    async def test_neither_token_nor_connection_returns_400(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/projects/github/repos", json={})
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"

    async def test_both_token_and_connection_returns_400(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        conn = await _seed_connection(session)
        resp = await client.post(
            "/api/v1/projects/github/repos",
            json={"access_token": "ghp_oneoff123", "connection_id": conn.id},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"

    async def test_unknown_connection_id_returns_404(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/projects/github/repos",
            json={"connection_id": 999},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    async def test_has_sdlc_studio_by_connection_id_uses_decrypted_token(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        conn = await _seed_connection(session)
        captured: dict = {}

        def fake_get(url, params=None):
            assert url.endswith("/repos/alice/app/contents/sdlc-studio")
            return _json_response(200, [{"name": "epics"}])

        with patch(
            "sdlc_lens.services.github_source.httpx.AsyncClient",
            side_effect=_client_factory(fake_get, captured),
        ):
            resp = await client.post(
                "/api/v1/projects/github/repos/alice/app/has-sdlc-studio",
                json={"connection_id": conn.id},
            )

        assert resp.status_code == 200
        assert resp.json() == {"has_sdlc_studio": True}
        assert captured["headers"]["Authorization"] == f"Bearer {RAW_TOKEN}"

    async def test_has_sdlc_studio_by_raw_token_still_works(self, client: AsyncClient) -> None:
        with patch(
            "sdlc_lens.api.routes.projects.repo_has_sdlc_studio",
            AsyncMock(return_value=False),
        ) as mock_check:
            resp = await client.post(
                "/api/v1/projects/github/repos/alice/app/has-sdlc-studio",
                json={"access_token": "ghp_oneoff123"},
            )

        assert resp.status_code == 200
        assert resp.json() == {"has_sdlc_studio": False}
        assert mock_check.call_args.args[0] == "ghp_oneoff123"

    async def test_has_sdlc_studio_neither_returns_400(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/projects/github/repos/alice/app/has-sdlc-studio",
            json={},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Project wiring + sync token precedence.
# ---------------------------------------------------------------------------

_CONTENT = b"# EP0001\n\n> **Status:** Draft\n\nEpic"
_FILES = {"epics/EP0001-x.md": (hashlib.sha256(_CONTENT).hexdigest(), _CONTENT)}


class TestSyncTokenPrecedence:
    async def test_connection_token_wins_when_connection_id_set(
        self, session: AsyncSession
    ) -> None:
        conn = await _seed_connection(session)
        project = await create_project(
            session,
            name="Connected Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            access_token=OTHER_TOKEN,
            connection_id=conn.id,
        )
        assert project.connection_id == conn.id

        with patch(
            "sdlc_lens.services.github_source.fetch_github_files_and_config",
            new_callable=AsyncMock,
            return_value=(_FILES, {}),
        ) as mock_fetch:
            result = await sync_project(project, session)

        assert result.added == 1
        assert mock_fetch.call_args.kwargs["access_token"] == RAW_TOKEN

    async def test_falls_back_to_project_token_without_connection(
        self, session: AsyncSession
    ) -> None:
        project = await create_project(
            session,
            name="Legacy Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            access_token=OTHER_TOKEN,
        )
        assert project.connection_id is None

        with patch(
            "sdlc_lens.services.github_source.fetch_github_files_and_config",
            new_callable=AsyncMock,
            return_value=(_FILES, {}),
        ) as mock_fetch:
            result = await sync_project(project, session)

        assert result.added == 1
        assert mock_fetch.call_args.kwargs["access_token"] == OTHER_TOKEN


class TestProjectConnectionWiring:
    async def test_create_and_update_project_accept_connection_id(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        conn = await _seed_connection(session)

        created = await client.post(
            "/api/v1/projects",
            json={
                "name": "Wired Repo",
                "source_type": "github",
                "repo_url": "https://github.com/owner/repo",
                "connection_id": conn.id,
            },
        )
        assert created.status_code == 201
        assert created.json()["connection_id"] == conn.id
        assert RAW_TOKEN not in created.text

        cleared = await client.put(
            f"/api/v1/projects/{created.json()['slug']}",
            json={"connection_id": None, "name": "Wired Repo 2"},
        )
        assert cleared.status_code == 200

    async def test_create_project_with_unknown_connection_id_returns_404(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/api/v1/projects",
            json={
                "name": "Ghost Repo",
                "source_type": "github",
                "repo_url": "https://github.com/owner/repo",
                "connection_id": 999,
            },
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# Migration: alembic upgrade head reaches 011 with the new table + column.
# ---------------------------------------------------------------------------


class TestMigration011:
    def test_upgrade_head_reaches_011(self, tmp_path) -> None:
        import sqlite3
        from pathlib import Path

        from alembic import command
        from alembic.config import Config

        backend_root = Path(__file__).resolve().parents[1]
        db_file = tmp_path / "migrate.db"

        # Build the config in memory rather than from alembic.ini: loading the ini
        # would run fileConfig(), which disables every existing logger and would
        # silently break log-assertion tests later in the session.
        cfg = Config()
        cfg.set_main_option("script_location", str(backend_root / "alembic"))
        cfg.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{db_file}")
        command.upgrade(cfg, "head")

        conn = sqlite3.connect(db_file)
        try:
            version = conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]
            tables = {
                r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            project_cols = {r[1] for r in conn.execute("PRAGMA table_info(projects)")}
            conn_cols = {r[1] for r in conn.execute("PRAGMA table_info(github_connections)")}
        finally:
            conn.close()

        assert version == "011"
        assert "github_connections" in tables
        assert "connection_id" in project_cols
        assert {
            "id",
            "label",
            "login",
            "access_token",
            "created_at",
            "last_validated_at",
        } <= conn_cols
