"""Tests for GitHub access-token encryption at rest (CR-01KX8BBH).

The PAT must be stored as Fernet ciphertext when an encryption key is
configured, must round-trip back to the plaintext for the GitHub API call,
and must stay fully backward compatible when no key is set (plaintext) and
for legacy plaintext rows written before encryption was enabled.
"""

import hashlib
from unittest.mock import AsyncMock, patch

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.config import settings
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.project import create_project, update_project
from sdlc_lens.services.sync_engine import sync_project
from sdlc_lens.utils.crypto import ENC_PREFIX, decrypt_token, encrypt_token

# A stable, valid urlsafe-base64 Fernet key for tests.
TEST_KEY = "ND_jjxyhtEE4sCJaXwGCdfFutCSE6aSitXpKL4sSxJQ="
PLAINTEXT_TOKEN = "ghp_supersecrettoken1234"


@pytest.fixture
def with_key(monkeypatch: pytest.MonkeyPatch) -> str:
    """Configure an encryption key for the duration of a test."""
    monkeypatch.setattr(settings, "token_encryption_key", TEST_KEY)
    return TEST_KEY


@pytest.fixture
def without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure no encryption key is configured (opt-in default)."""
    monkeypatch.setattr(settings, "token_encryption_key", None)


# ---------------------------------------------------------------------------
# Crypto helper unit behaviour
# ---------------------------------------------------------------------------


class TestCryptoHelper:
    def test_encrypt_produces_prefixed_ciphertext(self, with_key: str) -> None:
        stored = encrypt_token(PLAINTEXT_TOKEN)
        assert stored is not None
        assert stored.startswith(ENC_PREFIX)
        assert PLAINTEXT_TOKEN not in stored

    def test_round_trip(self, with_key: str) -> None:
        stored = encrypt_token(PLAINTEXT_TOKEN)
        assert decrypt_token(stored) == PLAINTEXT_TOKEN

    def test_none_passes_through(self, with_key: str) -> None:
        assert encrypt_token(None) is None
        assert decrypt_token(None) is None

    def test_legacy_plaintext_decrypts_to_itself_with_key(self, with_key: str) -> None:
        # A value stored before encryption carries no prefix and must be
        # returned unchanged even though a key is now configured.
        assert decrypt_token(PLAINTEXT_TOKEN) == PLAINTEXT_TOKEN

    def test_passthrough_without_key(self, without_key: None) -> None:
        assert encrypt_token(PLAINTEXT_TOKEN) == PLAINTEXT_TOKEN
        assert decrypt_token(PLAINTEXT_TOKEN) == PLAINTEXT_TOKEN


# ---------------------------------------------------------------------------
# (a) Round-trip through the DB when a key is configured
# ---------------------------------------------------------------------------


class TestCreateStoresCiphertext:
    async def test_created_project_stores_ciphertext(
        self, session: AsyncSession, with_key: str
    ) -> None:
        project = await create_project(
            session,
            name="Secret Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            access_token=PLAINTEXT_TOKEN,
        )

        # The raw column value must be ciphertext, not the plaintext.
        raw = (
            await session.execute(select(Project.access_token).where(Project.id == project.id))
        ).scalar_one()
        assert raw != PLAINTEXT_TOKEN
        assert raw.startswith(ENC_PREFIX)

        # And it must round-trip back to the original plaintext.
        assert decrypt_token(raw) == PLAINTEXT_TOKEN
        # Sanity: Fernet can decrypt the stripped ciphertext directly.
        Fernet(TEST_KEY).decrypt(raw[len(ENC_PREFIX) :].encode())

    async def test_update_stores_ciphertext(self, session: AsyncSession, with_key: str) -> None:
        project = await create_project(
            session,
            name="Update Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            access_token="ghp_original0000",
        )
        await update_project(session, project.slug, access_token=PLAINTEXT_TOKEN)

        raw = (
            await session.execute(select(Project.access_token).where(Project.id == project.id))
        ).scalar_one()
        assert raw.startswith(ENC_PREFIX)
        assert decrypt_token(raw) == PLAINTEXT_TOKEN


# ---------------------------------------------------------------------------
# (b) Sync path receives the DECRYPTED real token
# ---------------------------------------------------------------------------


class TestSyncReceivesPlaintext:
    async def test_github_source_called_with_plaintext(
        self, session: AsyncSession, with_key: str
    ) -> None:
        project = await create_project(
            session,
            name="Sync Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            access_token=PLAINTEXT_TOKEN,
        )
        # Confirm it is actually encrypted at rest before syncing.
        assert project.access_token.startswith(ENC_PREFIX)

        content = b"# EP0001\n\n> **Status:** Draft\n\nEpic"
        mock_files = {"epics/EP0001-x.md": (hashlib.sha256(content).hexdigest(), content)}

        with patch(
            "sdlc_lens.services.github_source.fetch_github_files",
            new_callable=AsyncMock,
            return_value=mock_files,
        ) as mock_fetch:
            result = await sync_project(project, session)

        assert result.added == 1
        # The real GitHub client must receive the decrypted plaintext token.
        assert mock_fetch.call_args.kwargs["access_token"] == PLAINTEXT_TOKEN


# ---------------------------------------------------------------------------
# (c) Backward compat: no key configured -> plaintext stored, sync works
# ---------------------------------------------------------------------------


class TestNoKeyBackwardCompat:
    async def test_plaintext_stored_and_sync_works(
        self, session: AsyncSession, without_key: None
    ) -> None:
        project = await create_project(
            session,
            name="Plain Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            access_token=PLAINTEXT_TOKEN,
        )

        raw = (
            await session.execute(select(Project.access_token).where(Project.id == project.id))
        ).scalar_one()
        assert raw == PLAINTEXT_TOKEN

        content = b"# EP0001\n\n> **Status:** Draft\n\nEpic"
        mock_files = {"epics/EP0001-x.md": (hashlib.sha256(content).hexdigest(), content)}

        with patch(
            "sdlc_lens.services.github_source.fetch_github_files",
            new_callable=AsyncMock,
            return_value=mock_files,
        ) as mock_fetch:
            result = await sync_project(project, session)

        assert result.added == 1
        assert mock_fetch.call_args.kwargs["access_token"] == PLAINTEXT_TOKEN


# ---------------------------------------------------------------------------
# (d) Legacy plaintext row decrypts to itself even when a key IS set
# ---------------------------------------------------------------------------


class TestLegacyPlaintextRow:
    async def test_legacy_row_syncs_with_key_set(
        self, session: AsyncSession, with_key: str
    ) -> None:
        # Simulate a row written before encryption: raw plaintext in the column.
        project = Project(
            slug="legacy-repo",
            name="Legacy Repo",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            repo_branch="main",
            repo_path="sdlc-studio",
            access_token=PLAINTEXT_TOKEN,  # unprefixed legacy plaintext
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        content = b"# EP0001\n\n> **Status:** Draft\n\nEpic"
        mock_files = {"epics/EP0001-x.md": (hashlib.sha256(content).hexdigest(), content)}

        with patch(
            "sdlc_lens.services.github_source.fetch_github_files",
            new_callable=AsyncMock,
            return_value=mock_files,
        ) as mock_fetch:
            result = await sync_project(project, session)

        assert result.added == 1
        # Legacy plaintext must pass through unchanged to the client.
        assert mock_fetch.call_args.kwargs["access_token"] == PLAINTEXT_TOKEN


# ---------------------------------------------------------------------------
# Masking: the API-facing mask must show the real last-4, never ciphertext.
# ---------------------------------------------------------------------------


class TestMaskingDecryptsFirst:
    def test_mask_shows_real_last4_of_encrypted_value(self, with_key: str) -> None:
        from sdlc_lens.api.schemas.projects import mask_token

        stored = encrypt_token(PLAINTEXT_TOKEN)
        masked = mask_token(stored)
        assert masked == f"****{PLAINTEXT_TOKEN[-4:]}"
        assert ENC_PREFIX not in (masked or "")
