"""Sync engine dispatch and collect_local_files tests.

Test cases: TC0308-TC0316 from TS0030.
"""

import hashlib
import inspect
import threading
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


async def _create_local_project(session: AsyncSession, sdlc_path: str) -> Project:
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
    async def test_returns_files_dict(self, tmp_path: Path) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "stories/US0001-test-story.md", "# US0001\n\n> **Status:** Draft\n\nHere")
        _write_md(sdlc, "epics/EP0001-test-epic.md", "# EP0001\n\nEpic")

        files, errors = await collect_local_files(str(sdlc))

        assert isinstance(files, dict)
        assert errors == 0
        assert "stories/US0001-test-story.md" in files
        assert "epics/EP0001-test-epic.md" in files

        for _rel_path, (file_hash, content) in files.items():
            expected_hash = hashlib.sha256(content).hexdigest()
            assert file_hash == expected_hash
            assert isinstance(content, bytes)

    async def test_excludes_non_md_files(self, tmp_path: Path) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "stories/US0001-test.md", "# US0001\n\nContent")
        (sdlc / "stories").mkdir(exist_ok=True)
        (sdlc / "stories" / "script.py").write_text("print('hello')")

        files, errors = await collect_local_files(str(sdlc))

        for key in files:
            assert key.endswith(".md")

    async def test_skips_excluded_dirs(self, tmp_path: Path) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "stories/US0001-test.md", "# US0001\n\nContent")
        _write_md(sdlc, ".git/config.md", "# Git Config")
        _write_md(sdlc, "node_modules/pkg.md", "# Package")

        files, _ = await collect_local_files(str(sdlc))

        assert ".git/config.md" not in files
        assert "node_modules/pkg.md" not in files

    # TC0315: collect_local_files raises on missing path
    async def test_missing_path_returns_empty(self, tmp_path: Path) -> None:
        # collect_local_files doesn't raise until awaited; the walk fails
        # on a path that doesn't exist. sync_project guards this by checking
        # is_dir() before calling collect_local_files. The offloaded walk
        # re-raises when Path.iterdir() fails.
        nonexistent = str(tmp_path / "nonexistent")
        with pytest.raises((FileNotFoundError, OSError)):
            await collect_local_files(nonexistent)

    # BG-01KX8BY1: the walk + read_bytes work must not block the event loop.
    async def test_walk_runs_off_main_thread(self, tmp_path: Path) -> None:
        import sdlc_lens.services.sync_engine as se

        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "stories/US0001-test.md", "# US0001\n\nContent")

        recorded: dict[str, bool] = {}
        original = se._walk_md_files

        def wrapper(root):
            recorded.setdefault(
                "on_main_thread",
                threading.current_thread() is threading.main_thread(),
            )
            return original(root)

        with patch.object(se, "_walk_md_files", wrapper):
            res = collect_local_files(str(sdlc))
            # After the fix this is a coroutine (offloaded); today it is a
            # plain tuple returned synchronously on the main thread.
            if inspect.iscoroutine(res):
                res = await res
            files, errors = res

        # Offloaded: the blocking walk ran on a NON-main thread.
        assert recorded["on_main_thread"] is False
        # Regression: results unchanged - the expected file is still collected.
        assert "stories/US0001-test.md" in files
        assert errors == 0


# ---------------------------------------------------------------------------
# TC0309: sync_project with local source_type calls collect_local_files
# ---------------------------------------------------------------------------


class TestSyncDispatchLocal:
    async def test_local_project_syncs(self, session: AsyncSession, tmp_path: Path) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(
            sdlc,
            "stories/US0001-test-story.md",
            "# US0001\n\n> **Status:** Draft\n\nStory",
        )

        project = await _create_local_project(session, str(sdlc))
        result = await sync_project(project, session)

        assert isinstance(result, SyncResult)
        assert result.added >= 1
        assert project.sync_status == "synced"

    # TC0311: sync_project add/update/skip/delete behaviour unchanged for local (regression)
    async def test_add_update_skip_delete(self, session: AsyncSession, tmp_path: Path) -> None:
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
        assert r2.added == 1  # US0004
        assert r2.updated == 1  # US0001 (changed)
        assert r2.skipped == 1  # US0002 (unchanged)
        assert r2.deleted == 1  # US0003 (removed)


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
# BG-01KX8B04: run_sync_task must never leave a project stuck in "syncing";
# trigger_sync must transition atomically.
# ---------------------------------------------------------------------------


class TestRunSyncTaskRecovery:
    """A failure inside run_sync_task must land the project in "error", never
    leave it stuck in "syncing" (which would 409 every future sync)."""

    async def test_sync_project_raising_sets_error_not_syncing(
        self, engine, tmp_path: Path
    ) -> None:
        from sqlalchemy.ext.asyncio import async_sessionmaker

        from sdlc_lens.services.sync import run_sync_task

        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as sess:
            project = Project(
                slug="test-local",
                name="Test Local",
                source_type="local",
                sdlc_path=str(tmp_path),
                sync_status="syncing",
            )
            sess.add(project)
            await sess.commit()

        with patch(
            "sdlc_lens.services.sync.sync_project",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ):
            # run_sync_task must swallow-and-record, not propagate.
            await run_sync_task("test-local", session_factory)

        async with session_factory() as sess:
            refreshed = (
                await sess.execute(select(Project).where(Project.slug == "test-local"))
            ).scalar_one()
            assert refreshed.sync_status == "error"
            assert refreshed.sync_error is not None
            assert "boom" in refreshed.sync_error

    async def test_missing_project_does_not_raise(self, engine) -> None:
        from sqlalchemy.ext.asyncio import async_sessionmaker

        from sdlc_lens.services.sync import run_sync_task

        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        # No project with this slug - should log and return, not raise.
        await run_sync_task("does-not-exist", session_factory)


class TestTriggerSyncAtomicGuard:
    """trigger_sync transitions atomically so a project already syncing is
    rejected and a missing project still 404s."""

    async def test_happy_path_sets_syncing_and_returns_project(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        from sdlc_lens.services.sync import trigger_sync

        project = Project(
            slug="test-local",
            name="Test Local",
            source_type="local",
            sdlc_path=str(tmp_path),
            sync_status="never_synced",
            sync_error="stale error",
        )
        session.add(project)
        await session.commit()

        returned = await trigger_sync(session, "test-local")

        assert returned.slug == "test-local"
        assert returned.sync_status == "syncing"
        assert returned.sync_error is None

    async def test_already_syncing_raises_sync_in_progress(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        from sdlc_lens.services.sync import SyncInProgressError, trigger_sync

        project = Project(
            slug="test-local",
            name="Test Local",
            source_type="local",
            sdlc_path=str(tmp_path),
            sync_status="syncing",
        )
        session.add(project)
        await session.commit()

        with pytest.raises(SyncInProgressError):
            await trigger_sync(session, "test-local")

    async def test_missing_project_raises_not_found(self, session: AsyncSession) -> None:
        from sdlc_lens.services.project import ProjectNotFoundError
        from sdlc_lens.services.sync import trigger_sync

        with pytest.raises(ProjectNotFoundError):
            await trigger_sync(session, "does-not-exist")


# ---------------------------------------------------------------------------
# BG-01KX8BFP: empty source must not wipe existing documents
# ---------------------------------------------------------------------------


class TestEmptySourceGuard:
    """A source returning zero files must not silently delete every document.

    A wrong repo_path/branch, an emptied local directory, or a partial fetch
    returning ``{}`` should be treated as a sync failure - the existing
    documents are preserved and the status is set to "error".
    """

    async def test_empty_source_preserves_existing_docs(self, session: AsyncSession) -> None:
        project = await _create_github_project(session)

        content = b"# EP0001\n\n> **Status:** Draft\n\nEpic content"
        seed_files = {
            "epics/EP0001-test-epic.md": (hashlib.sha256(content).hexdigest(), content),
        }

        # First sync: seed one document.
        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=seed_files,
        ):
            r1 = await sync_project(project, session)
        assert r1.added == 1

        # Second sync: source returns nothing (misconfigured repo / partial fetch).
        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value={},
        ):
            r2 = await sync_project(project, session)

        # (a) Existing documents must be preserved, not wiped.
        assert r2.deleted == 0
        docs = (
            (await session.execute(select(Document).where(Document.project_id == project.id)))
            .scalars()
            .all()
        )
        assert len(docs) == 1

        # (b) Status must reflect the failure with a clear message.
        refreshed = await session.get(Project, project.id)
        assert refreshed.sync_status == "error"
        assert refreshed.sync_error is not None
        assert "no documents" in refreshed.sync_error.lower()

    async def test_single_file_deletion_still_works(self, session: AsyncSession) -> None:
        """A source missing one of two files must delete exactly that one."""
        project = await _create_github_project(session)

        c1 = b"# EP0001\n\n> **Status:** Draft\n\nEpic one"
        c2 = b"# US0001\n\n> **Status:** Draft\n\nStory one"
        seed_files = {
            "epics/EP0001-one.md": (hashlib.sha256(c1).hexdigest(), c1),
            "stories/US0001-one.md": (hashlib.sha256(c2).hexdigest(), c2),
        }
        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=seed_files,
        ):
            await sync_project(project, session)

        # Second sync: one of the two files removed, the other unchanged.
        remaining = {"epics/EP0001-one.md": (hashlib.sha256(c1).hexdigest(), c1)}
        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=remaining,
        ):
            r2 = await sync_project(project, session)

        assert r2.deleted == 1
        assert r2.skipped == 1
        docs = (
            (await session.execute(select(Document).where(Document.project_id == project.id)))
            .scalars()
            .all()
        )
        assert len(docs) == 1
        assert docs[0].doc_id == "EP0001-one"

        refreshed = await session.get(Project, project.id)
        assert refreshed.sync_status == "synced"


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
