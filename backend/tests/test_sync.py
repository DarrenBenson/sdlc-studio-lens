"""Filesystem sync service tests.

Test cases: TC0097-TC0109 from TS0007.
Also covers US0008 (hashing) and US0009 (deletion detection).
"""

import hashlib
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.sync_engine import SyncResult, sync_project
from sdlc_lens.utils.hashing import compute_hash

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_md(base: Path, rel_path: str, content: str) -> None:
    """Write a markdown file at base/rel_path, creating dirs as needed."""
    full = base / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")


async def _create_project(
    session: AsyncSession, sdlc_path: str
) -> Project:
    """Insert a project record and return it."""
    project = Project(
        slug="test-project",
        name="Test Project",
        sdlc_path=sdlc_path,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


# ---------------------------------------------------------------------------
# TC0109: SyncResult dataclass
# ---------------------------------------------------------------------------


class TestSyncResult:
    def test_fields_default_to_zero(self) -> None:
        result = SyncResult()
        assert result.added == 0
        assert result.updated == 0
        assert result.skipped == 0
        assert result.deleted == 0
        assert result.errors == 0

    def test_fields_are_integers(self) -> None:
        result = SyncResult(added=1, updated=2, skipped=3, deleted=4, errors=5)
        assert isinstance(result.added, int)
        assert isinstance(result.updated, int)
        assert isinstance(result.skipped, int)
        assert isinstance(result.deleted, int)
        assert isinstance(result.errors, int)


# ---------------------------------------------------------------------------
# TC0106: SHA-256 hash computation (US0008)
# ---------------------------------------------------------------------------


class TestHashComputation:
    def test_known_content(self) -> None:
        content = b"# Test\n\nBody"
        expected = hashlib.sha256(content).hexdigest()
        assert compute_hash(content) == expected

    def test_different_content_different_hash(self) -> None:
        assert compute_hash(b"hello") != compute_hash(b"world")

    def test_hash_is_64_char_hex(self) -> None:
        result = compute_hash(b"test")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)


# ---------------------------------------------------------------------------
# TC0097: Sync adds new documents
# ---------------------------------------------------------------------------


class TestSyncAddsNewDocs:
    @pytest.mark.asyncio
    async def test_adds_five_docs(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "prd.md", "# PRD\n\nContent.")
        _write_md(sdlc, "trd.md", "# TRD\n\nContent.")
        _write_md(
            sdlc,
            "epics/EP0001-project.md",
            "> **Status:** Done\n\n# EP0001: Project\n\nBody.",
        )
        _write_md(
            sdlc,
            "stories/US0001-register.md",
            "> **Status:** Draft\n\n# US0001: Register\n\nBody.",
        )
        _write_md(
            sdlc,
            "stories/US0002-list.md",
            "> **Owner:** Darren\n\n# US0002: List\n\nBody.",
        )

        project = await _create_project(session, str(sdlc))
        result = await sync_project(project.id, str(sdlc), session)

        assert result.added == 5
        assert result.updated == 0
        assert result.skipped == 0
        assert result.deleted == 0

        docs = (
            await session.execute(
                select(Document).where(
                    Document.project_id == project.id
                )
            )
        ).scalars().all()
        assert len(docs) == 5


# ---------------------------------------------------------------------------
# TC0098: Sync updates documents with changed hash
# ---------------------------------------------------------------------------


class TestSyncUpdatesChanged:
    @pytest.mark.asyncio
    async def test_updates_changed_file(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(
            sdlc,
            "epics/EP0001-project.md",
            "> **Status:** Draft\n\n# EP0001: Project\n\nOriginal.",
        )
        project = await _create_project(session, str(sdlc))

        # First sync
        await sync_project(project.id, str(sdlc), session)

        # Change file content
        _write_md(
            sdlc,
            "epics/EP0001-project.md",
            "> **Status:** Done\n\n# EP0001: Project\n\nUpdated.",
        )

        # Second sync
        result = await sync_project(project.id, str(sdlc), session)
        assert result.updated == 1
        assert result.added == 0

        doc = (
            await session.execute(
                select(Document).where(
                    Document.project_id == project.id
                )
            )
        ).scalar_one()
        assert "Updated." in doc.content
        assert doc.status == "Done"


# ---------------------------------------------------------------------------
# TC0099: Sync skips unchanged documents
# ---------------------------------------------------------------------------


class TestSyncSkipsUnchanged:
    @pytest.mark.asyncio
    async def test_skips_unchanged(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "prd.md", "# PRD\n\nContent.")
        project = await _create_project(session, str(sdlc))

        # First sync
        await sync_project(project.id, str(sdlc), session)

        # Second sync without changes
        result = await sync_project(project.id, str(sdlc), session)
        assert result.skipped == 1
        assert result.updated == 0
        assert result.added == 0


# ---------------------------------------------------------------------------
# TC0100: Sync removes deleted documents (US0009)
# ---------------------------------------------------------------------------


class TestSyncDeletesRemoved:
    @pytest.mark.asyncio
    async def test_deletes_removed_file(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "prd.md", "# PRD\n\nContent.")
        _write_md(
            sdlc,
            "stories/US0099-temp.md",
            "# US0099: Temp\n\nBody.",
        )
        project = await _create_project(session, str(sdlc))

        # First sync
        await sync_project(project.id, str(sdlc), session)
        docs = (
            await session.execute(
                select(Document).where(
                    Document.project_id == project.id
                )
            )
        ).scalars().all()
        assert len(docs) == 2

        # Delete one file
        (sdlc / "stories" / "US0099-temp.md").unlink()

        # Second sync
        result = await sync_project(project.id, str(sdlc), session)
        assert result.deleted == 1
        assert result.skipped == 1

        docs = (
            await session.execute(
                select(Document).where(
                    Document.project_id == project.id
                )
            )
        ).scalars().all()
        assert len(docs) == 1


# ---------------------------------------------------------------------------
# TC0101: Sync updates sync_status to "synced"
# ---------------------------------------------------------------------------


class TestSyncStatusSynced:
    @pytest.mark.asyncio
    async def test_status_synced(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "prd.md", "# PRD\n\nContent.")
        project = await _create_project(session, str(sdlc))
        assert project.sync_status == "never_synced"

        await sync_project(project.id, str(sdlc), session)

        await session.refresh(project)
        assert project.sync_status == "synced"


# ---------------------------------------------------------------------------
# TC0102: Sync updates last_synced_at timestamp
# ---------------------------------------------------------------------------


class TestSyncTimestamp:
    @pytest.mark.asyncio
    async def test_last_synced_at_set(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        project = await _create_project(session, str(sdlc))
        assert project.last_synced_at is None

        await sync_project(project.id, str(sdlc), session)

        await session.refresh(project)
        assert project.last_synced_at is not None


# ---------------------------------------------------------------------------
# TC0103: Sync sets sync_status to "error" on failure
# ---------------------------------------------------------------------------


class TestSyncStatusError:
    @pytest.mark.asyncio
    async def test_error_on_bad_path(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        bad_path = str(tmp_path / "nonexistent")
        project = await _create_project(session, bad_path)

        await sync_project(project.id, bad_path, session)

        await session.refresh(project)
        assert project.sync_status == "error"
        assert project.sync_error is not None


# ---------------------------------------------------------------------------
# TC0104: Sync handles empty directory
# ---------------------------------------------------------------------------


class TestSyncEmptyDir:
    @pytest.mark.asyncio
    async def test_empty_dir_syncs(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        project = await _create_project(session, str(sdlc))

        result = await sync_project(project.id, str(sdlc), session)

        assert result.added == 0
        assert result.deleted == 0
        await session.refresh(project)
        assert project.sync_status == "synced"


# ---------------------------------------------------------------------------
# TC0105: Sync handles unreadable files
# ---------------------------------------------------------------------------


class TestSyncUnreadableFile:
    @pytest.mark.asyncio
    async def test_skips_unreadable(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "prd.md", "# PRD\n\nContent.")
        _write_md(sdlc, "trd.md", "# TRD\n\nContent.")

        # Make one file unreadable
        bad = sdlc / "secret.md"
        bad.write_text("secret")
        bad.chmod(0o000)

        project = await _create_project(session, str(sdlc))
        result = await sync_project(project.id, str(sdlc), session)

        assert result.added == 2
        assert result.errors == 1
        # Sync should still succeed overall
        await session.refresh(project)
        assert project.sync_status == "synced"

        # Restore permissions for cleanup
        bad.chmod(0o644)


# ---------------------------------------------------------------------------
# TC0107: Sync populates all document fields
# ---------------------------------------------------------------------------


class TestSyncPopulatesFields:
    @pytest.mark.asyncio
    async def test_all_fields_populated(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(
            sdlc,
            "epics/EP0001-project.md",
            (
                "> **Status:** Done\n"
                "> **Owner:** Darren\n"
                "> **Priority:** P0\n"
                "> **Story Points:** 5\n"
                "> **Epic:** EP0001\n"
                "\n"
                "# EP0001: Project Management\n"
                "\nBody content."
            ),
        )
        project = await _create_project(session, str(sdlc))

        await sync_project(project.id, str(sdlc), session)

        doc = (
            await session.execute(
                select(Document).where(
                    Document.project_id == project.id
                )
            )
        ).scalar_one()

        assert doc.doc_type == "epic"
        assert doc.doc_id == "EP0001-project"
        assert doc.title == "EP0001: Project Management"
        assert doc.status == "Done"
        assert doc.owner == "Darren"
        assert doc.priority == "P0"
        assert doc.story_points == 5
        assert doc.file_path is not None
        assert len(doc.file_hash) == 64
        assert "Body content." in doc.content


# ---------------------------------------------------------------------------
# TC0108: Sync handles re-sync with mixed operations
# ---------------------------------------------------------------------------


class TestSyncMixedOperations:
    @pytest.mark.asyncio
    async def test_mixed_add_update_skip_delete(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "prd.md", "# PRD\n\nOriginal.")
        _write_md(sdlc, "trd.md", "# TRD\n\nContent.")
        _write_md(
            sdlc,
            "stories/US0099-temp.md",
            "# US0099: Temp\n\nBody.",
        )
        project = await _create_project(session, str(sdlc))

        # First sync: 3 added
        result1 = await sync_project(project.id, str(sdlc), session)
        assert result1.added == 3

        # Change prd.md, delete US0099, add new file, keep trd.md
        _write_md(sdlc, "prd.md", "# PRD\n\nUpdated.")
        (sdlc / "stories" / "US0099-temp.md").unlink()
        _write_md(sdlc, "tsd.md", "# TSD\n\nNew.")

        # Second sync: 1 added, 1 updated, 1 skipped, 1 deleted
        result2 = await sync_project(project.id, str(sdlc), session)
        assert result2.added == 1
        assert result2.updated == 1
        assert result2.skipped == 1
        assert result2.deleted == 1


# ---------------------------------------------------------------------------
# Edge cases: _index.md skipped, BOM stripping
# ---------------------------------------------------------------------------


class TestSyncEdgeCases:
    @pytest.mark.asyncio
    async def test_index_files_skipped(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "prd.md", "# PRD\n\nContent.")
        _write_md(sdlc, "stories/_index.md", "# Stories Index\n\nList.")

        project = await _create_project(session, str(sdlc))
        result = await sync_project(project.id, str(sdlc), session)

        # _index.md should be skipped
        assert result.added == 1

    @pytest.mark.asyncio
    async def test_bom_stripped(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        bom_content = "\ufeff# PRD\n\nBOM content."
        (sdlc / "prd.md").write_text(bom_content, encoding="utf-8")

        project = await _create_project(session, str(sdlc))
        await sync_project(project.id, str(sdlc), session)

        doc = (
            await session.execute(
                select(Document).where(
                    Document.project_id == project.id
                )
            )
        ).scalar_one()
        assert doc.title == "PRD"
        assert "\ufeff" not in doc.content


# ---------------------------------------------------------------------------
# US0008 dedicated tests: TC0110-TC0117
# ---------------------------------------------------------------------------


# TC0113: Unchanged files skipped during re-sync (3 files)
class TestUnchangedSkipMultiple:
    @pytest.mark.asyncio
    async def test_three_unchanged_skipped(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "prd.md", "# PRD\n\nContent.")
        _write_md(sdlc, "trd.md", "# TRD\n\nContent.")
        _write_md(sdlc, "tsd.md", "# TSD\n\nContent.")
        project = await _create_project(session, str(sdlc))

        await sync_project(project.id, str(sdlc), session)
        result = await sync_project(project.id, str(sdlc), session)

        assert result.skipped == 3
        assert result.updated == 0
        assert result.added == 0


# TC0115: file_hash stored correctly in database
class TestHashStoredInDb:
    @pytest.mark.asyncio
    async def test_hash_matches_content(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        content = "# PRD\n\nSome content."
        _write_md(sdlc, "prd.md", content)
        project = await _create_project(session, str(sdlc))

        await sync_project(project.id, str(sdlc), session)

        doc = (
            await session.execute(
                select(Document).where(
                    Document.project_id == project.id
                )
            )
        ).scalar_one()

        expected = compute_hash(content.encode("utf-8"))
        assert doc.file_hash == expected
        assert len(doc.file_hash) == 64


# TC0116: Re-sync of 100 unchanged documents in < 2 seconds
class TestResyncPerformance:
    @pytest.mark.asyncio
    async def test_100_unchanged_under_2s(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        import time

        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        for i in range(100):
            _write_md(
                sdlc,
                f"stories/US{i:04d}-story.md",
                f"# US{i:04d}: Story {i}\n\nBody {i}.",
            )
        project = await _create_project(session, str(sdlc))

        # First sync: add all 100
        await sync_project(project.id, str(sdlc), session)

        # Re-sync with no changes
        start = time.monotonic()
        result = await sync_project(project.id, str(sdlc), session)
        elapsed = time.monotonic() - start

        assert result.skipped == 100
        assert result.added == 0
        assert result.updated == 0
        assert elapsed < 2.0


# TC0117: Empty file produces valid hash
class TestEmptyFileHash:
    def test_empty_bytes_hash(self) -> None:
        expected = (
            "e3b0c44298fc1c149afbf4c8996fb924"
            "27ae41e4649b934ca495991b7852b855"
        )
        assert compute_hash(b"") == expected


# ---------------------------------------------------------------------------
# US0009 dedicated tests: TC0128-TC0135
# ---------------------------------------------------------------------------


# TC0128: Detect and delete removed files (3 docs, delete 1)
class TestDeletionDetection:
    @pytest.mark.asyncio
    async def test_selective_deletion(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(
            sdlc,
            "stories/US0001-register.md",
            "# US0001: Register\n\nBody.",
        )
        _write_md(
            sdlc,
            "stories/US0002-list.md",
            "# US0002: List\n\nBody.",
        )
        _write_md(
            sdlc,
            "stories/US0003-sync.md",
            "# US0003: Sync\n\nBody.",
        )
        project = await _create_project(session, str(sdlc))
        await sync_project(project.id, str(sdlc), session)

        # Delete US0002
        (sdlc / "stories" / "US0002-list.md").unlink()
        result = await sync_project(project.id, str(sdlc), session)

        assert result.deleted == 1
        docs = (
            await session.execute(
                select(Document).where(
                    Document.project_id == project.id
                )
            )
        ).scalars().all()
        doc_ids = {d.doc_id for d in docs}
        assert "US0001-register" in doc_ids
        assert "US0003-sync" in doc_ids
        assert "US0002-list" not in doc_ids


# TC0130: Bulk deletion
class TestBulkDeletion:
    @pytest.mark.asyncio
    async def test_bulk_delete(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        # 10 stories + 5 epics = 15 total
        for i in range(10):
            _write_md(
                sdlc,
                f"stories/US{i:04d}-story.md",
                f"# US{i:04d}: Story {i}\n\nBody.",
            )
        for i in range(5):
            _write_md(
                sdlc,
                f"epics/EP{i:04d}-epic.md",
                f"# EP{i:04d}: Epic {i}\n\nBody.",
            )
        project = await _create_project(session, str(sdlc))
        await sync_project(project.id, str(sdlc), session)

        # Delete all stories
        import shutil

        shutil.rmtree(sdlc / "stories")

        result = await sync_project(project.id, str(sdlc), session)
        assert result.deleted == 10
        assert result.skipped == 5

        docs = (
            await session.execute(
                select(Document).where(
                    Document.project_id == project.id
                )
            )
        ).scalars().all()
        assert len(docs) == 5
        assert all(d.doc_type == "epic" for d in docs)


# TC0133: File moved = delete + add
class TestFileMoved:
    @pytest.mark.asyncio
    async def test_move_is_delete_plus_add(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        content = "# US0001: Register\n\nBody."
        _write_md(sdlc, "stories/US0001-register.md", content)
        project = await _create_project(session, str(sdlc))
        await sync_project(project.id, str(sdlc), session)

        # Move file to archive
        (sdlc / "archive" / "stories").mkdir(parents=True)
        (sdlc / "stories" / "US0001-register.md").rename(
            sdlc / "archive" / "stories" / "US0001-register.md"
        )

        result = await sync_project(project.id, str(sdlc), session)
        assert result.deleted >= 1
        assert result.added >= 1


# TC0134: All files deleted = zero documents
class TestAllFilesDeleted:
    @pytest.mark.asyncio
    async def test_all_deleted(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        for i in range(5):
            _write_md(
                sdlc,
                f"stories/US{i:04d}-story.md",
                f"# US{i:04d}: Story\n\nBody.",
            )
        project = await _create_project(session, str(sdlc))
        await sync_project(project.id, str(sdlc), session)

        # Delete all files
        import shutil

        shutil.rmtree(sdlc / "stories")

        result = await sync_project(project.id, str(sdlc), session)
        assert result.deleted == 5

        docs = (
            await session.execute(
                select(Document).where(
                    Document.project_id == project.id
                )
            )
        ).scalars().all()
        assert len(docs) == 0

        await session.refresh(project)
        assert project.sync_status == "synced"


# TC0135: No deletion without sync
class TestNoDeletionWithoutSync:
    @pytest.mark.asyncio
    async def test_docs_persist_without_sync(
        self, session: AsyncSession, tmp_path: Path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        sdlc.mkdir()
        _write_md(sdlc, "prd.md", "# PRD\n\nContent.")
        _write_md(sdlc, "trd.md", "# TRD\n\nContent.")
        project = await _create_project(session, str(sdlc))
        await sync_project(project.id, str(sdlc), session)

        # Delete files from filesystem, but DON'T sync
        (sdlc / "prd.md").unlink()
        (sdlc / "trd.md").unlink()

        # DB still has 2 docs
        docs = (
            await session.execute(
                select(Document).where(
                    Document.project_id == project.id
                )
            )
        ).scalars().all()
        assert len(docs) == 2
