"""Tests for the optional allowed_project_base allowlist guard (BG-01KX8BJY).

When SDLC_LENS_ALLOWED_PROJECT_BASE is configured, local sdlc_path values must
resolve to a location within that base. When unset, behaviour is unchanged.
"""

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.config import settings
from sdlc_lens.services.project import (
    PathNotFoundError,
    create_project,
    update_project,
)


@pytest.fixture
def allowed_base(tmp_path: Path) -> Path:
    base = tmp_path / "allowed"
    base.mkdir()
    return base


class TestCreateProjectAllowlist:
    async def test_path_inside_base_is_accepted(
        self, session: AsyncSession, allowed_base: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "allowed_project_base", str(allowed_base))
        inside = allowed_base / "my-project"
        inside.mkdir()

        project = await create_project(session, "Inside Project", str(inside))

        assert project.sdlc_path == str(inside.resolve())

    async def test_path_outside_base_is_rejected(
        self,
        session: AsyncSession,
        allowed_base: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(settings, "allowed_project_base", str(allowed_base))
        outside = tmp_path / "outside"
        outside.mkdir()

        with pytest.raises(PathNotFoundError) as exc_info:
            await create_project(session, "Outside Project", str(outside))

        assert "allowed base" in str(exc_info.value).lower()

    async def test_arbitrary_dir_accepted_when_base_unset(
        self,
        session: AsyncSession,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Default (unset) allowlist: backward-compatible, any valid dir allowed.
        monkeypatch.setattr(settings, "allowed_project_base", None)
        arbitrary = tmp_path / "anywhere"
        arbitrary.mkdir()

        project = await create_project(session, "Anywhere Project", str(arbitrary))

        assert project.sdlc_path == str(arbitrary.resolve())


class TestUpdateProjectAllowlist:
    async def test_update_path_outside_base_is_rejected(
        self,
        session: AsyncSession,
        allowed_base: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(settings, "allowed_project_base", str(allowed_base))
        inside = allowed_base / "start"
        inside.mkdir()
        project = await create_project(session, "Updatable", str(inside))

        outside = tmp_path / "elsewhere"
        outside.mkdir()

        with pytest.raises(PathNotFoundError) as exc_info:
            await update_project(session, project.slug, sdlc_path=str(outside))

        assert "allowed base" in str(exc_info.value).lower()

    async def test_update_path_inside_base_is_accepted(
        self,
        session: AsyncSession,
        allowed_base: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(settings, "allowed_project_base", str(allowed_base))
        inside = allowed_base / "start"
        inside.mkdir()
        project = await create_project(session, "Updatable Two", str(inside))

        new_inside = allowed_base / "moved"
        new_inside.mkdir()

        updated = await update_project(session, project.slug, sdlc_path=str(new_inside))

        assert updated.sdlc_path == str(new_inside.resolve())
