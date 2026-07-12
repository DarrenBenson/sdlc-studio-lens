"""Hardening of the stored GitHub connections feature (review of CR-01KXAZX9).

Five defects found by the adversarial review of the connections commit:

  1. adopting a connection left the project's own PAT in place, so detaching the
     connection silently reverted to a stale (possibly revoked) secret - and the
     per-project token could never be cleared at all;
  2. a stored connection's token could not be rotated (no PUT, and DELETE is
     refused while any project uses it);
  3. encryption is opt-in, so a deployment with no key silently stores PATs in
     plaintext with no warning;
  4. losing the key made ``decrypt_token`` return the CIPHERTEXT, which was then
     sent to GitHub as a Bearer token (and masked as the ciphertext's last-4);
  5. an orphaned ``connection_id`` (possible in prod, where migration 011 adds a
     plain column with no FK) made the sync fall back to an unauthenticated
     fetch, reporting the misleading "Repository not found".
"""

import hashlib
import logging
from unittest.mock import AsyncMock, patch

import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.api.schemas.projects import mask_token
from sdlc_lens.config import settings
from sdlc_lens.db.models.github_connection import GitHubConnection
from sdlc_lens.db.models.project import Project
from sdlc_lens.main import create_app, lifespan
from sdlc_lens.services.github_connection import (
    ConnectionNotFoundError,
    resolve_connection_token,
)
from sdlc_lens.services.github_source import AuthenticationError
from sdlc_lens.services.project import create_project, update_project
from sdlc_lens.services.sync_engine import resolve_sync_token, sync_project
from sdlc_lens.utils.crypto import ENC_PREFIX, decrypt_token, encrypt_token

TEST_KEY = "ND_jjxyhtEE4sCJaXwGCdfFutCSE6aSitXpKL4sSxJQ="
CONNECTION_TOKEN = "ghp_connectionsecret9876"
PROJECT_TOKEN = "ghp_perprojectsecret5432"
NEW_TOKEN = "ghp_rotatedsecret1111"

_CONTENT = b"# EP0001\n\n> **Status:** Draft\n\nEpic"
_FILES = {"epics/EP0001-x.md": (hashlib.sha256(_CONTENT).hexdigest(), _CONTENT)}


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


async def _seed_connection(session: AsyncSession, label: str = "Personal") -> GitHubConnection:
    conn = GitHubConnection(
        label=label,
        login="alice",
        access_token=encrypt_token(CONNECTION_TOKEN),
    )
    session.add(conn)
    await session.commit()
    await session.refresh(conn)
    return conn


async def _stored_token(session: AsyncSession, project_id: int) -> str | None:
    return (
        await session.execute(select(Project.access_token).where(Project.id == project_id))
    ).scalar_one()


# ---------------------------------------------------------------------------
# DEFECT 1: the connection is the single source of the credential.
# ---------------------------------------------------------------------------


class TestAdoptingConnectionPurgesProjectToken:
    async def test_create_with_connection_stores_no_project_token(
        self, session: AsyncSession
    ) -> None:
        conn = await _seed_connection(session)
        project = await create_project(
            session,
            name="Wired Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            access_token=PROJECT_TOKEN,
            connection_id=conn.id,
        )

        assert project.connection_id == conn.id
        assert await _stored_token(session, project.id) is None

    async def test_update_adopting_a_connection_nulls_the_project_token(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        conn = await _seed_connection(session)
        project = await create_project(
            session,
            name="Legacy Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            access_token=PROJECT_TOKEN,
        )
        assert await _stored_token(session, project.id) is not None

        resp = await client.put(
            f"/api/v1/projects/{project.slug}",
            json={"connection_id": conn.id},
        )

        assert resp.status_code == 200
        assert resp.json()["connection_id"] == conn.id
        # The connection now owns the credential: the project's copy is gone.
        assert resp.json()["masked_token"] is None
        assert await _stored_token(session, project.id) is None

    async def test_detaching_does_not_revert_to_the_replaced_token(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        conn = await _seed_connection(session)
        project = await create_project(
            session,
            name="Rotating Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            access_token=PROJECT_TOKEN,
        )

        await client.put(f"/api/v1/projects/{project.slug}", json={"connection_id": conn.id})
        detached = await client.put(
            f"/api/v1/projects/{project.slug}", json={"connection_id": None}
        )

        assert detached.status_code == 200
        assert detached.json()["connection_id"] is None
        await session.refresh(project)
        # No silent fall-back to the (possibly revoked) token the connection replaced.
        assert project.access_token is None
        assert await resolve_sync_token(project) is None

    async def test_explicit_null_access_token_clears_the_stored_token(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        project = await create_project(
            session,
            name="Purge Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            access_token=PROJECT_TOKEN,
        )

        # An explicit null is a real edit, not an empty body.
        resp = await client.put(
            f"/api/v1/projects/{project.slug}",
            json={"access_token": None},
        )

        assert resp.status_code == 200
        assert resp.json()["masked_token"] is None
        assert await _stored_token(session, project.id) is None

    async def test_omitted_access_token_leaves_it_alone(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        project = await create_project(
            session,
            name="Untouched Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            access_token=PROJECT_TOKEN,
        )

        resp = await client.put(
            f"/api/v1/projects/{project.slug}",
            json={"name": "Untouched Repo v2"},
        )

        assert resp.status_code == 200
        assert resp.json()["masked_token"] == f"****{PROJECT_TOKEN[-4:]}"
        assert decrypt_token(await _stored_token(session, project.id)) == PROJECT_TOKEN

    async def test_service_level_clear_access_token_flag(self, session: AsyncSession) -> None:
        project = await create_project(
            session,
            name="Service Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            access_token=PROJECT_TOKEN,
        )

        await update_project(session, project.slug, clear_access_token=True)
        assert await _stored_token(session, project.id) is None

    async def test_empty_body_is_still_rejected(self, client: AsyncClient) -> None:
        project_resp = await client.post(
            "/api/v1/projects",
            json={
                "name": "Empty Body Repo",
                "source_type": "github",
                "repo_url": "https://github.com/owner/repo",
            },
        )
        slug = project_resp.json()["slug"]

        resp = await client.put(f"/api/v1/projects/{slug}", json={})
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# DEFECT 2: rotation is a one-field edit.
# ---------------------------------------------------------------------------


class TestRotateConnection:
    async def test_rotation_revalidates_and_replaces_the_stored_token(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        conn = await _seed_connection(session)
        assert conn.last_validated_at is None

        with patch(
            "sdlc_lens.services.github_connection.get_authenticated_login",
            AsyncMock(return_value="alice-renamed"),
        ) as mock_login:
            resp = await client.put(
                f"/api/v1/connections/{conn.id}",
                json={"access_token": NEW_TOKEN},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == conn.id
        assert body["login"] == "alice-renamed"
        assert body["masked_token"] == f"****{NEW_TOKEN[-4:]}"
        assert body["last_validated_at"] is not None
        # The raw token never comes back out.
        assert NEW_TOKEN not in resp.text
        assert "access_token" not in resp.text
        # The NEW token is what was validated against GitHub.
        assert mock_login.call_args.args[0] == NEW_TOKEN

        await session.refresh(conn)
        assert conn.access_token.startswith(ENC_PREFIX)
        assert decrypt_token(conn.access_token) == NEW_TOKEN

    async def test_rotation_works_while_a_project_still_uses_the_connection(
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

        with patch(
            "sdlc_lens.services.github_connection.get_authenticated_login",
            AsyncMock(return_value="alice"),
        ):
            resp = await client.put(
                f"/api/v1/connections/{conn.id}",
                json={"access_token": NEW_TOKEN},
            )

        assert resp.status_code == 200
        await session.refresh(conn)
        assert decrypt_token(conn.access_token) == NEW_TOKEN

    async def test_invalid_new_token_is_rejected_and_nothing_changes(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        conn = await _seed_connection(session)

        with patch(
            "sdlc_lens.services.github_connection.get_authenticated_login",
            AsyncMock(side_effect=AuthenticationError("Bad credentials")),
        ):
            resp = await client.put(
                f"/api/v1/connections/{conn.id}",
                json={"access_token": "ghp_bad"},
            )

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_TOKEN"

        await session.refresh(conn)
        # The OLD token survives untouched.
        assert decrypt_token(conn.access_token) == CONNECTION_TOKEN
        assert conn.login == "alice"
        assert conn.last_validated_at is None

    async def test_unknown_id_returns_404(self, client: AsyncClient) -> None:
        resp = await client.put("/api/v1/connections/999", json={"access_token": NEW_TOKEN})
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    async def test_empty_token_is_rejected(
        self, client: AsyncClient, session: AsyncSession
    ) -> None:
        conn = await _seed_connection(session)
        resp = await client.put(f"/api/v1/connections/{conn.id}", json={"access_token": ""})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# DEFECT 3: a loud startup warning when encryption is not configured.
# ---------------------------------------------------------------------------


class TestPlaintextStartupWarning:
    async def test_warns_when_no_encryption_key_is_configured(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        monkeypatch.setattr(settings, "token_encryption_key", None)

        with caplog.at_level(logging.WARNING, logger="sdlc_lens.main"):
            async with lifespan(create_app()):
                pass

        warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert warnings, "expected a startup warning when no encryption key is set"
        message = warnings[0].getMessage()
        assert "plaintext" in message.lower()
        assert "SDLC_LENS_TOKEN_ENCRYPTION_KEY" in message

    async def test_silent_when_the_key_is_configured(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        # The autouse with_key fixture has configured a key.
        with caplog.at_level(logging.WARNING, logger="sdlc_lens.main"):
            async with lifespan(create_app()):
                pass

        assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []


# ---------------------------------------------------------------------------
# DEFECT 4: a lost key must never send ciphertext to GitHub.
# ---------------------------------------------------------------------------


class TestLostKeyNeverLeaksCiphertext:
    def test_decrypt_returns_none_when_the_key_is_gone(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        stored = encrypt_token(CONNECTION_TOKEN)
        assert stored is not None and stored.startswith(ENC_PREFIX)

        # The key is dropped from the environment (e.g. a redeploy forgot it).
        monkeypatch.setattr(settings, "token_encryption_key", None)

        with caplog.at_level(logging.ERROR, logger="sdlc_lens.utils.crypto"):
            assert decrypt_token(stored) is None

        errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert errors, "expected a clear error when an encrypted value cannot be decrypted"
        assert "key" in errors[0].getMessage().lower()

    def test_mask_shows_nothing_rather_than_the_ciphertexts_last_4(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        stored = encrypt_token(CONNECTION_TOKEN)
        monkeypatch.setattr(settings, "token_encryption_key", None)

        masked = mask_token(stored)
        assert masked is None
        assert masked != f"****{stored[-4:]}"

    async def test_resolve_connection_token_raises_instead_of_returning_ciphertext(
        self, session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        conn = await _seed_connection(session)
        monkeypatch.setattr(settings, "token_encryption_key", None)

        with pytest.raises(AuthenticationError) as exc_info:
            await resolve_connection_token(session, conn.id)

        message = str(exc_info.value).lower()
        assert "decrypt" in message
        # It blames the missing key, not the user's PAT.
        assert "bad credentials" not in message

    async def test_revalidate_never_sends_the_ciphertext_to_github(
        self, client: AsyncClient, session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        conn = await _seed_connection(session)
        stored = conn.access_token
        monkeypatch.setattr(settings, "token_encryption_key", None)

        with patch(
            "sdlc_lens.services.github_connection.get_authenticated_login",
            AsyncMock(return_value="alice"),
        ) as mock_login:
            resp = await client.post(f"/api/v1/connections/{conn.id}/validate")

        # Nothing was transmitted to GitHub at all.
        mock_login.assert_not_awaited()
        assert resp.status_code == 401
        message = resp.json()["error"]["message"]
        assert "decrypt" in message.lower()
        assert stored not in resp.text

    async def test_sync_fails_loudly_rather_than_bearer_the_ciphertext(
        self, session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        conn = await _seed_connection(session)
        project = await create_project(
            session,
            name="Keyless Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            connection_id=conn.id,
        )
        monkeypatch.setattr(settings, "token_encryption_key", None)

        with patch(
            "sdlc_lens.services.github_source.fetch_github_files_and_config",
            new_callable=AsyncMock,
            return_value=(_FILES, {}),
        ) as mock_fetch:
            await sync_project(project, session)

        mock_fetch.assert_not_awaited()
        refreshed = await session.get(Project, project.id)
        assert refreshed.sync_status == "error"
        assert "decrypt" in refreshed.sync_error.lower()

    def test_wrong_key_still_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Regression guard for the existing rotated-key behaviour.
        other = Fernet.generate_key().decode()
        stored = f"{ENC_PREFIX}{Fernet(other).encrypt(CONNECTION_TOKEN.encode()).decode()}"
        monkeypatch.setattr(settings, "token_encryption_key", TEST_KEY)
        assert decrypt_token(stored) is None


# ---------------------------------------------------------------------------
# DEFECT 5: an orphaned connection_id must fail the sync, not fall back.
# ---------------------------------------------------------------------------


async def _orphan_connection_id(session: AsyncSession, project: Project, orphan_id: int) -> None:
    """Point a project at a connection id that does not exist.

    Prod has no foreign key here (migration 011 adds a plain nullable column,
    since SQLite cannot ALTER-add an FK), but the test schema is built by
    ``create_all`` under ``PRAGMA foreign_keys=ON``, which does create one. The
    pragma is dropped for the write so the prod-possible orphan is constructible.
    """
    await session.execute(text("PRAGMA foreign_keys=OFF"))
    await session.execute(
        text("UPDATE projects SET connection_id = :cid WHERE id = :pid"),
        {"cid": orphan_id, "pid": project.id},
    )
    await session.commit()
    await session.execute(text("PRAGMA foreign_keys=ON"))
    await session.refresh(project)


class TestOrphanedConnectionId:
    async def test_resolve_sync_token_raises_on_an_orphan(self, session: AsyncSession) -> None:
        project = await create_project(
            session,
            name="Orphan Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            access_token=PROJECT_TOKEN,
        )
        await _orphan_connection_id(session, project, 999)
        assert project.connection_id == 999

        with pytest.raises(ConnectionNotFoundError) as exc_info:
            await resolve_sync_token(project)

        message = str(exc_info.value)
        assert "999" in message
        assert "connection" in message.lower()

    async def test_sync_fails_naming_the_missing_connection(self, session: AsyncSession) -> None:
        project = await create_project(
            session,
            name="Orphan Sync Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            access_token=PROJECT_TOKEN,
        )
        await _orphan_connection_id(session, project, 999)

        with patch(
            "sdlc_lens.services.github_source.fetch_github_files_and_config",
            new_callable=AsyncMock,
            return_value=(_FILES, {}),
        ) as mock_fetch:
            await sync_project(project, session)

        # No silent unauthenticated fetch, and no misleading "Repository not found":
        # the error names the real cause, the missing connection.
        mock_fetch.assert_not_awaited()
        refreshed = await session.get(Project, project.id)
        assert refreshed.sync_status == "error"
        assert "999" in refreshed.sync_error
        assert "connection" in refreshed.sync_error.lower()
        assert "repository" not in refreshed.sync_error.lower()
