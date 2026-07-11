"""Tests for the optional allowed_project_base allowlist guard (BG-01KX8BJY).

When SDLC_LENS_ALLOWED_PROJECT_BASE is configured, local sdlc_path values must
resolve to a location within that base. When unset, behaviour is unchanged.
"""

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.config import settings
from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.project import (
    PathNotFoundError,
    create_project,
    update_project,
)
from sdlc_lens.services.sync_engine import sync_project


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


class TestUpdateProjectTwoStepBypass:
    """BG-01KX95QP: the allowlist must not be bypassable via a two-step update.

    Attack: stash an out-of-base sdlc_path on a github project (path stored
    unvalidated for non-local sources), then flip source_type to 'local' in a
    later call that supplies no sdlc_path, so the sdlc_path validation branch is
    skipped and the out-of-base path becomes live for a local sync.
    """

    async def test_transition_to_local_revalidates_stored_path(
        self,
        session: AsyncSession,
        allowed_base: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(settings, "allowed_project_base", str(allowed_base))
        outside = tmp_path / "outside"
        outside.mkdir()

        # Step 1: github project with an out-of-base sdlc_path stored unvalidated.
        project = await create_project(
            session,
            "Bypass Attempt",
            source_type="github",
            repo_url="https://github.com/acme/repo",
        )
        project = await update_project(session, project.slug, sdlc_path=str(outside))
        assert project.source_type == "github"

        # Step 2: flip to local WITHOUT supplying sdlc_path - must be rejected
        # because the resulting local project would point outside the base.
        with pytest.raises(PathNotFoundError) as exc_info:
            await update_project(session, project.slug, source_type="local")

        assert "allowed base" in str(exc_info.value).lower()

    async def test_transition_to_local_with_inbase_stored_path_is_accepted(
        self,
        session: AsyncSession,
        allowed_base: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(settings, "allowed_project_base", str(allowed_base))
        inside = allowed_base / "legit"
        inside.mkdir()

        project = await create_project(
            session,
            "Legit Transition",
            source_type="github",
            repo_url="https://github.com/acme/repo",
        )
        project = await update_project(session, project.slug, sdlc_path=str(inside))

        updated = await update_project(session, project.slug, source_type="local")

        assert updated.source_type == "local"
        assert updated.sdlc_path == str(inside.resolve())

    async def test_transition_to_local_unchanged_when_base_unset(
        self,
        session: AsyncSession,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # With no allowlist configured, a transition to local is unrestricted.
        monkeypatch.setattr(settings, "allowed_project_base", None)
        anywhere = tmp_path / "anywhere"
        anywhere.mkdir()

        project = await create_project(
            session,
            "Unset Base Transition",
            source_type="github",
            repo_url="https://github.com/acme/repo",
        )
        project = await update_project(session, project.slug, sdlc_path=str(anywhere))

        updated = await update_project(session, project.slug, source_type="local")

        assert updated.source_type == "local"
        assert updated.sdlc_path == str(anywhere.resolve())


class TestSyncProjectAllowlistDefence:
    """BG-01KX95QP: sync_project re-applies the allowlist as defence in depth."""

    async def test_sync_refuses_out_of_base_stored_path(
        self,
        session: AsyncSession,
        allowed_base: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(settings, "allowed_project_base", str(allowed_base))
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "PRD-secret.md").write_text("# Secret", encoding="utf-8")

        # Construct a project directly with an out-of-base local path to model a
        # path that slipped through earlier validation.
        project = Project(
            slug="tainted",
            name="Tainted",
            source_type="local",
            sdlc_path=str(outside),
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        result = await sync_project(project, session)

        assert result.added == 0
        refreshed = await session.get(Project, project.id)
        assert refreshed.sync_status == "error"
        # No documents harvested from outside the allowed base.
        docs = (
            await session.execute(
                Document.__table__.select().where(Document.project_id == project.id)
            )
        ).all()
        assert docs == []

    async def test_sync_walks_in_base_path_when_configured(
        self,
        session: AsyncSession,
        allowed_base: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(settings, "allowed_project_base", str(allowed_base))
        inside = allowed_base / "docs"
        inside.mkdir()
        (inside / "PRD-app.md").write_text("# App PRD", encoding="utf-8")

        project = Project(
            slug="clean",
            name="Clean",
            source_type="local",
            sdlc_path=str(inside),
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        result = await sync_project(project, session)

        refreshed = await session.get(Project, project.id)
        assert refreshed.sync_status == "synced"
        assert result.added >= 1
