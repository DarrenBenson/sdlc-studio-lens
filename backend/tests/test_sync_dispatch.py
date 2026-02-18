"""Sync engine dispatch and collect_local_files tests.

Test cases: TC0308-TC0316 from TS0030.
"""

import hashlib
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.github_source import GitHubSourceError, RepoNotFoundError
from sdlc_lens.services.sync_engine import SyncResult, collect_local_files, sync_project

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_md(base: Path, rel_path: str, content: str) -> None:
    """Write a markdown file at base/rel_path, creating dirs as needed."""
    full = base / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")


async def _create_local_project(
    session: AsyncSession, sdlc_path: str
) -> Project:
    """Insert a local project record."""
    project = Project(
        slug="test-local",
        name="Test Local",
        source_type="local",
        sdlc_path=sdlc_path,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def _create_github_project(session: AsyncSession) -> Project:
    """Insert a GitHub project record."""
    project = Project(
        slug="test-github",
        name="Test GitHub",
        source_type="github",
        repo_url="https://github.com/owner/repo",
        repo_branch="main",
        repo_path="sdlc-studio",
        access_token="ghp_test1234",
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


# ---------------------------------------------------------------------------
# TC0308: collect_local_files returns same dict as old inline code
# ---------------------------------------------------------------------------


class TestCollectLocalFiles:
    def test_returns_files_dict(self, tmp_path: Path) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "stories/US0001-test-story.md", "# US0001\n\n> **Status:** Draft\n\nHere")
        _write_md(sdlc, "epics/EP0001-test-epic.md", "# EP0001\n\nEpic")

        files, errors = collect_local_files(str(sdlc))

        assert isinstance(files, dict)
        assert errors == 0
        assert "stories/US0001-test-story.md" in files
        assert "epics/EP0001-test-epic.md" in files

        for _rel_path, (file_hash, content) in files.items():
            expected_hash = hashlib.sha256(content).hexdigest()
            assert file_hash == expected_hash
            assert isinstance(content, bytes)

    def test_excludes_non_md_files(self, tmp_path: Path) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "stories/US0001-test.md", "# US0001\n\nContent")
        (sdlc / "stories").mkdir(exist_ok=True)
        (sdlc / "stories" / "script.py").write_text("print('hello')")

        files, errors = collect_local_files(str(sdlc))

        for key in files:
            assert key.endswith(".md")

    def test_skips_excluded_dirs(self, tmp_path: Path) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "stories/US0001-test.md", "# US0001\n\nContent")
        _write_md(sdlc, ".git/config.md", "# Git Config")
        _write_md(sdlc, "node_modules/pkg.md", "# Package")

        files, _ = collect_local_files(str(sdlc))

        assert ".git/config.md" not in files
        assert "node_modules/pkg.md" not in files

    # TC0315: collect_local_files raises on missing path
    def test_missing_path_returns_empty(self, tmp_path: Path) -> None:
        # collect_local_files doesn't raise, _walk_md_files will fail
        # on a path that doesn't exist. The sync_project handles this
        # by checking is_dir() before calling collect_local_files.
        # For the function itself, it will raise when Path.iterdir() fails.
        nonexistent = str(tmp_path / "nonexistent")
        with pytest.raises((FileNotFoundError, OSError)):
            collect_local_files(nonexistent)


# ---------------------------------------------------------------------------
# TC0309: sync_project with local source_type calls collect_local_files
# ---------------------------------------------------------------------------


class TestSyncDispatchLocal:
    async def test_local_project_syncs(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(
            sdlc, "stories/US0001-test-story.md",
            "# US0001\n\n> **Status:** Draft\n\nStory",
        )

        project = await _create_local_project(session, str(sdlc))
        result = await sync_project(project, session)

        assert isinstance(result, SyncResult)
        assert result.added >= 1
        assert project.sync_status == "synced"

    # TC0311: sync_project add/update/skip/delete behaviour unchanged for local (regression)
    async def test_add_update_skip_delete(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        md = "# US0001\n\n> **Status:** Draft\n\nOriginal"
        _write_md(sdlc, "stories/US0001-new-story.md", md)
        md2 = "# US0002\n\n> **Status:** Draft\n\nKeep"
        _write_md(sdlc, "stories/US0002-other-story.md", md2)
        md3 = "# US0003\n\n> **Status:** Draft\n\nRemove"
        _write_md(sdlc, "stories/US0003-remove-story.md", md3)

        project = await _create_local_project(session, str(sdlc))

        # First sync: all added
        r1 = await sync_project(project, session)
        assert r1.added == 3
        assert r1.deleted == 0

        # Modify one, remove one, keep one, add new
        mod = "# US0001\n\n> **Status:** Done\n\nModified"
        _write_md(sdlc, "stories/US0001-new-story.md", mod)
        (sdlc / "stories" / "US0003-remove-story.md").unlink()
        new = "# US0004\n\n> **Status:** Draft\n\nNew"
        _write_md(sdlc, "stories/US0004-brand-new.md", new)

        r2 = await sync_project(project, session)
        assert r2.added == 1      # US0004
        assert r2.updated == 1    # US0001 (changed)
        assert r2.skipped == 1    # US0002 (unchanged)
        assert r2.deleted == 1    # US0003 (removed)


# ---------------------------------------------------------------------------
# TC0310: sync_project with github source_type calls collect_github_files
# ---------------------------------------------------------------------------


class TestSyncDispatchGitHub:
    async def test_github_project_dispatches(self, session: AsyncSession) -> None:
        project = await _create_github_project(session)

        mock_files = {
            "stories/US0001-test.md": (
                hashlib.sha256(b"# US0001\n\n> **Status:** Draft\n\nContent").hexdigest(),
                b"# US0001\n\n> **Status:** Draft\n\nContent",
            ),
        }

        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=mock_files,
        ) as mock_collect:
            result = await sync_project(project, session)
            mock_collect.assert_called_once_with(project)

        assert result.added == 1
        assert project.sync_status == "synced"

    # TC0312: sync_project handles github source error gracefully
    async def test_github_error_handled(self, session: AsyncSession) -> None:
        project = await _create_github_project(session)

        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            side_effect=RepoNotFoundError("Repository not found"),
        ):
            result = await sync_project(project, session)

        # Should not crash, error status should be set
        assert isinstance(result, SyncResult)
        # Re-fetch project to check status
        refreshed = await session.get(Project, project.id)
        assert refreshed.sync_status == "error"
        assert "not found" in (refreshed.sync_error or "").lower()

    # TC0313: sync_project sets error status on github fetch failure
    async def test_github_error_sets_status(self, session: AsyncSession) -> None:
        project = await _create_github_project(session)

        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            side_effect=GitHubSourceError("API error: HTTP 500"),
        ):
            await sync_project(project, session)

        refreshed = await session.get(Project, project.id)
        assert refreshed.sync_status == "error"
        assert refreshed.sync_error is not None


# ---------------------------------------------------------------------------
# TC0314: run_sync_task passes project to sync_project
# ---------------------------------------------------------------------------


class TestRunSyncTask:
    async def test_passes_project_object(self, engine, tmp_path: Path) -> None:
        """Verify run_sync_task loads the project and passes it to sync_project."""
        from sqlalchemy.ext.asyncio import async_sessionmaker

        from sdlc_lens.services.sync import run_sync_task

        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "stories/US0001-test.md", "# US0001\n\n> **Status:** Draft\n\nContent")

        # Create project via a session from the factory
        async with session_factory() as sess:
            project = Project(
                slug="test-local",
                name="Test Local",
                source_type="local",
                sdlc_path=str(sdlc),
                sync_status="syncing",
            )
            sess.add(project)
            await sess.commit()

        with patch(
            "sdlc_lens.services.sync.sync_project",
            new_callable=AsyncMock,
            return_value=SyncResult(added=1),
        ) as mock_sync:
            await run_sync_task("test-local", session_factory)
            mock_sync.assert_called_once()
            # The first argument should be a Project instance
            call_args = mock_sync.call_args
            assert isinstance(call_args[0][0], Project)
            assert call_args[0][0].slug == "test-local"


# ---------------------------------------------------------------------------
# TC0316: sync_project works with pre-built files dict from any source
# ---------------------------------------------------------------------------


class TestSyncPrebuiltDict:
    async def test_processes_dict_from_github(self, session: AsyncSession) -> None:
        """Verify the sync pipeline processes a pre-built files dict correctly."""
        project = await _create_github_project(session)

        content = b"# EP0001\n\n> **Status:** Draft\n\nEpic content"
        file_hash = hashlib.sha256(content).hexdigest()
        mock_files = {"epics/EP0001-test-epic.md": (file_hash, content)}

        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=mock_files,
        ):
            result = await sync_project(project, session)

        assert result.added == 1

        # Verify document was created in DB
        db_result = await session.execute(
            select(Document).where(Document.project_id == project.id)
        )
        docs = db_result.scalars().all()
        assert len(docs) == 1
        assert docs[0].file_hash == file_hash
        assert docs[0].doc_id == "EP0001-test-epic"
