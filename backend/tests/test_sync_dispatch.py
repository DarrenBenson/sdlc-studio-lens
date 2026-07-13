"""Sync engine dispatch and collect_local_files tests.

Test cases: TC0308-TC0316 from TS0030.
"""

import hashlib
import inspect
import io
import logging
import tarfile
import threading
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.github_source import GitHubSourceError, RepoNotFoundError
from sdlc_lens.services.project_config import ProjectConfig
from sdlc_lens.services.sync_engine import (
    FileEntry,
    SyncResult,
    collect_local_files,
    sync_project,
)
from sdlc_lens.utils.hashing import compute_blob_sha, compute_hash


def _entry(content: bytes) -> FileEntry:
    """Build a manifest entry exactly as a real collector would (US-01KXCCMH).

    A collector always returns a COMPLETE manifest - every live path - and a tarball or
    local walk always has the bytes, so ``raw`` is set here. Only the incremental
    Trees+Blobs path omits content, for files it knows are unchanged.
    """
    return FileEntry(
        file_hash=compute_hash(content),
        raw=content,
        blob_sha=compute_blob_sha(content),
    )


async def _docs(session: AsyncSession, project_id: int) -> list[Document]:
    """Every document currently stored for a project."""
    res = await session.execute(select(Document).where(Document.project_id == project_id))
    return list(res.scalars().all())


def _build_github_tarball(files: dict[str, bytes]) -> bytes:
    """Build an in-memory gzipped tarball with a GitHub-style top-level dir."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for path, content in files.items():
            info = tarfile.TarInfo(name=f"owner-repo-abc1234/{path}")
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    return buf.getvalue()


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

        for _rel_path, entry in files.items():
            assert entry.file_hash == hashlib.sha256(entry.raw).hexdigest()
            assert isinstance(entry.raw, bytes)
            # A local walk always has the bytes, so it is never a contentless entry,
            # and it carries the git blob SHA like every other collector (US-01KXCCMH).
            assert entry.raw is not None
            assert entry.blob_sha == compute_blob_sha(entry.raw)

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
            "stories/US0001-test.md": _entry(b"# US0001\n\n> **Status:** Draft\n\nContent"),
        }

        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=(mock_files, ProjectConfig()),
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
# CR-01KX95WV: github sync reads .config.yaml / .version from the tarball
# ---------------------------------------------------------------------------


class TestSyncDispatchGitHubConfig:
    """A github project's ``.config.yaml`` must be honoured just like a local one:
    schema_version/profile land on the project and the custom status vocabulary
    canonicalises project-defined statuses to themselves."""

    async def test_github_config_populates_project_and_vocab(self, session: AsyncSession) -> None:
        project = await _create_github_project(session)

        tarball = _build_github_tarball(
            {
                "sdlc-studio/.config.yaml": (
                    b"schema_version: 3\nprofile: full\nstatus_vocab:\n  story:\n    - Gated\n"
                ),
                "sdlc-studio/.version": b"schema_version: 3\n",
                "sdlc-studio/stories/US0001-register.md": (
                    b"> **Status:** Gated - waiting on review\n\n# US0001: Register\n\nBody."
                ),
            }
        )
        resp = httpx.Response(
            status_code=200,
            content=tarball,
            request=httpx.Request("GET", "https://api.github.com/repos/owner/repo/tarball/main"),
        )
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "sdlc_lens.services.github_source.httpx.AsyncClient",
            return_value=mock_client,
        ):
            await sync_project(project, session)

        assert project.schema_version == "3"
        assert project.profile == "full"

        doc = (
            (await session.execute(select(Document).where(Document.project_id == project.id)))
            .scalars()
            .one()
        )
        # The project-defined "Gated" status canonicalises to itself.
        assert doc.status == "Gated"

    async def test_github_missing_config_does_not_fail_sync(self, session: AsyncSession) -> None:
        project = await _create_github_project(session)

        tarball = _build_github_tarball(
            {
                "sdlc-studio/stories/US0001-register.md": (
                    b"> **Status:** Draft\n\n# US0001: Register\n\nBody."
                ),
            }
        )
        resp = httpx.Response(
            status_code=200,
            content=tarball,
            request=httpx.Request("GET", "https://api.github.com/repos/owner/repo/tarball/main"),
        )
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "sdlc_lens.services.github_source.httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await sync_project(project, session)

        assert result.added == 1
        assert project.sync_status == "synced"
        assert project.schema_version is None


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
            "epics/EP0001-test-epic.md": _entry(content),
        }

        # First sync: seed one document.
        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=(seed_files, ProjectConfig()),
        ):
            r1 = await sync_project(project, session)
        assert r1.added == 1

        # Second sync: source returns nothing (misconfigured repo / partial fetch).
        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=({}, ProjectConfig()),
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
            "epics/EP0001-one.md": _entry(c1),
            "stories/US0001-one.md": _entry(c2),
        }
        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=(seed_files, ProjectConfig()),
        ):
            await sync_project(project, session)

        # Second sync: one of the two files removed, the other unchanged.
        remaining = {"epics/EP0001-one.md": _entry(c1)}
        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=(remaining, ProjectConfig()),
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
        mock_files = {"epics/EP0001-test-epic.md": _entry(content)}

        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=(mock_files, ProjectConfig()),
        ):
            result = await sync_project(project, session)

        assert result.added == 1

        # Verify document was created in DB
        db_result = await session.execute(
            select(Document).where(Document.project_id == project.id)
        )
        docs = db_result.scalars().all()
        assert len(docs) == 1
        assert docs[0].file_hash == compute_hash(content)
        assert docs[0].doc_id == "EP0001-test-epic"


# ---------------------------------------------------------------------------
# US-01KXCCMH: the manifest is complete; only the CONTENT is optional.
#
# These pin the contract that makes an incremental sync safe. The dangerous design is
# to hand sync_project only the CHANGED files: on a no-op sync that dict is empty, the
# empty-source guard reads it as "the source is empty" (regressing BG-01KX8BFP, a High
# severity silent-data-loss bug) and the deletion loop considers every document gone.
#
# Instead every live path stays in the manifest and unchanged files carry raw=None.
# ---------------------------------------------------------------------------


def _contentless(content: bytes) -> FileEntry:
    """A manifest entry for a file the fetcher KNOWS is unchanged, so did not download.

    hash and blob_sha still describe the real file - that is precisely how the fetcher
    knew it was unchanged - but the bytes were never pulled over the wire.
    """
    return FileEntry(
        file_hash=compute_hash(content),
        raw=None,
        blob_sha=compute_blob_sha(content),
    )


class TestContentlessManifestEntries:
    @pytest.mark.asyncio
    async def test_a_fully_contentless_manifest_deletes_nothing(
        self, session: AsyncSession
    ) -> None:
        """The no-op incremental sync: every file unchanged, so NOTHING was fetched.

        This is the exact shape that would be catastrophic under the naive design. The
        manifest is full, but not a single entry carries bytes. Nothing may be deleted,
        the empty-source guard must NOT fire, and the sync must succeed.
        """
        project = await _create_github_project(session)

        c1 = b"# EP0001\n\n> **Status:** Draft\n\nEpic one"
        c2 = b"# US0001\n\n> **Status:** Draft\n\nStory one"
        paths = {"epics/EP0001-one.md": c1, "stories/US0001-one.md": c2}

        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=({p: _entry(c) for p, c in paths.items()}, ProjectConfig()),
        ):
            await sync_project(project, session)

        before = (
            (await session.execute(select(Document).where(Document.project_id == project.id)))
            .scalars()
            .all()
        )
        assert len(before) == 2
        synced_at = {d.file_path: d.synced_at for d in before}

        # Re-sync. Nothing changed, so the fetcher pulled ZERO blobs.
        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=({p: _contentless(c) for p, c in paths.items()}, ProjectConfig()),
        ):
            result = await sync_project(project, session)

        assert result.deleted == 0, "a no-op incremental sync deleted documents"
        assert result.added == 0
        assert result.updated == 0
        assert result.errors == 0
        assert result.skipped == 2
        assert project.sync_status == "synced", "the empty-source guard fired on a healthy sync"

        after = (
            (await session.execute(select(Document).where(Document.project_id == project.id)))
            .scalars()
            .all()
        )
        assert len(after) == 2
        # Untouched, not merely un-deleted.
        assert {d.file_path: d.synced_at for d in after} == synced_at

    @pytest.mark.asyncio
    async def test_deletion_is_keyed_on_the_manifest_not_on_what_was_fetched(
        self, session: AsyncSession
    ) -> None:
        """A file absent from the MANIFEST is deleted; a file merely not FETCHED is not.

        The distinction the whole design turns on.
        """
        project = await _create_github_project(session)

        c1 = b"# EP0001\n\n> **Status:** Draft\n\nEpic one"
        c2 = b"# US0001\n\n> **Status:** Draft\n\nStory one"
        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=(
                {"epics/EP0001-one.md": _entry(c1), "stories/US0001-one.md": _entry(c2)},
                ProjectConfig(),
            ),
        ):
            await sync_project(project, session)

        # US0001 is deleted upstream (gone from the manifest). EP0001 is unchanged, so
        # it is in the manifest but was not fetched.
        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=({"epics/EP0001-one.md": _contentless(c1)}, ProjectConfig()),
        ):
            result = await sync_project(project, session)

        assert result.deleted == 1
        assert result.skipped == 1
        remaining = (
            (await session.execute(select(Document).where(Document.project_id == project.id)))
            .scalars()
            .all()
        )
        assert [d.file_path for d in remaining] == ["epics/EP0001-one.md"]

    @pytest.mark.asyncio
    async def test_a_contentless_entry_that_needs_reparsing_fails_loud(
        self, session: AsyncSession, caplog
    ) -> None:
        """If a document needs a reparse but arrived with no bytes, SAY SO. Never skip.

        This state is a bug in the fetch path (it must supply bytes for anything needing
        a reparse - RFC-01KXARHK D7). It cannot be repaired by re-parsing the stored
        `content` column, because that column is body-only: the frontmatter blockquote
        carrying status/epic/story is stripped before storage (parser.py:183).

        A silent skip here would leave the document on stale derived fields for ever
        while the sync cheerfully reported success - BG-01KXARHJ, resurrected. A tool
        must fail loud rather than report a success it did not achieve (LL0008).
        """
        project = await _create_github_project(session)

        old = b"# EP0001\n\n> **Status:** Draft\n\nOld"
        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=({"epics/EP0001-one.md": _entry(old)}, ProjectConfig()),
        ):
            await sync_project(project, session)

        # A broken fetcher: the file CHANGED (different hash) but no bytes were supplied.
        new = b"# EP0001\n\n> **Status:** Done\n\nNew"
        broken = FileEntry(
            file_hash=compute_hash(new),  # says it changed...
            raw=None,  # ...but gave us nothing to parse
            blob_sha=compute_blob_sha(new),
        )
        with (
            caplog.at_level(logging.ERROR),
            patch(
                "sdlc_lens.services.sync_engine.collect_github_files",
                new_callable=AsyncMock,
                return_value=({"epics/EP0001-one.md": broken}, ProjectConfig()),
            ),
        ):
            result = await sync_project(project, session)

        assert result.errors == 1, "a contentless entry needing a reparse was swallowed"
        assert result.updated == 0
        assert "needs a reparse but arrived with no content" in caplog.text
        # And it is NOT deleted - a fetch bug must never cost the user a document.
        assert result.deleted == 0
        docs = (
            (await session.execute(select(Document).where(Document.project_id == project.id)))
            .scalars()
            .all()
        )
        assert len(docs) == 1
        # The stale row is left exactly as it was rather than half-written.
        assert docs[0].status == "Draft"


# ---------------------------------------------------------------------------
# BG-01KX8BFP class: a path that EXISTS but cannot be READ is not a deletion.
#
# Found by an independent critic, and live on main before this change: the local walker
# dropped an unreadable file from the manifest, and the deletion loop reads absence from
# the manifest as "gone upstream" - so a single `chmod 000` DESTROYED the document while
# the file sat intact on disk, and the sync still reported `synced`.
# ---------------------------------------------------------------------------


class TestUnreadableFileIsNotADeletion:
    @pytest.mark.asyncio
    async def test_unreadable_file_keeps_its_document(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "epics/EP0001-one.md", "# EP0001\n\n> **Status:** Draft\n\nEpic one")
        _write_md(sdlc, "stories/US0001-one.md", "# US0001\n\n> **Status:** Draft\n\nStory one")

        project = await _create_local_project(session, str(sdlc))
        await sync_project(project, session)
        assert len({d.file_path for d in (await _docs(session, project.id))}) == 2

        # The file is still there. We simply cannot read it this run.
        victim = sdlc / "stories" / "US0001-one.md"
        victim.chmod(0o000)
        try:
            result = await sync_project(project, session)
        finally:
            victim.chmod(0o644)

        assert victim.exists(), "precondition: the file was never deleted from disk"
        assert result.deleted == 0, "an UNREADABLE file was treated as a DELETED file"

        paths = {d.file_path for d in (await _docs(session, project.id))}
        assert paths == {"epics/EP0001-one.md", "stories/US0001-one.md"}, (
            "the document for an unreadable-but-present file was destroyed"
        )

    @pytest.mark.asyncio
    async def test_a_sync_with_errors_does_not_report_success(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        """LL0008: never report a success you did not achieve.

        A sync that could not read a file left that document un-updated. Saying "synced"
        with a fresh timestamp tells the operator their view is current when it is not -
        and it is what made the data loss above invisible.
        """
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "epics/EP0001-one.md", "# EP0001\n\n> **Status:** Draft\n\nEpic one")
        _write_md(sdlc, "stories/US0001-one.md", "# US0001\n\n> **Status:** Draft\n\nStory one")

        project = await _create_local_project(session, str(sdlc))
        await sync_project(project, session)

        victim = sdlc / "stories" / "US0001-one.md"
        victim.chmod(0o000)
        try:
            result = await sync_project(project, session)
        finally:
            victim.chmod(0o644)

        assert result.errors == 1
        assert project.sync_status == "error", "a sync that skipped a file claimed success"
        assert project.sync_error is not None
        assert "could not be synced" in project.sync_error

    @pytest.mark.asyncio
    async def test_a_clean_sync_still_reports_synced(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        """The converse: no errors, no false alarm."""
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "epics/EP0001-one.md", "# EP0001\n\n> **Status:** Draft\n\nEpic one")

        project = await _create_local_project(session, str(sdlc))
        result = await sync_project(project, session)

        assert result.errors == 0
        assert project.sync_status == "synced"
        assert project.sync_error is None


class TestManifestBlobShaIsChecked:
    @pytest.mark.asyncio
    async def test_a_blob_sha_that_contradicts_its_bytes_is_refused(
        self, session: AsyncSession, caplog
    ) -> None:
        """A source that lies about a blob SHA must not poison the row.

        We store the manifest's blob_sha rather than recomputing it, so an incorrect
        value would be written verbatim - and the skip condition never revisits a
        non-NULL blob_sha, so it would be wrong FOR EVER: the path would look changed on
        every future sync (defeating incremental sync) or unchanged for ever (the
        document silently never updates again).
        """
        project = await _create_github_project(session)

        content = b"# EP0001\n\n> **Status:** Draft\n\nEpic content"
        liar = FileEntry(
            file_hash=compute_hash(content),
            raw=content,
            blob_sha="0" * 40,  # not this content's blob SHA
        )

        with (
            caplog.at_level(logging.ERROR),
            patch(
                "sdlc_lens.services.sync_engine.collect_github_files",
                new_callable=AsyncMock,
                return_value=({"epics/EP0001-one.md": liar}, ProjectConfig()),
            ),
        ):
            result = await sync_project(project, session)

        assert result.added == 0, "a blob_sha contradicting its own bytes was stored"
        assert result.errors == 1
        assert "does not match its bytes" in caplog.text
        assert await _docs(session, project.id) == []
