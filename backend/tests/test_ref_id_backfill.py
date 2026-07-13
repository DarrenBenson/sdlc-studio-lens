"""BG-01KX95DB: legacy rows with ``ref_id IS NULL`` must self-heal.

Migration 007 added ``ref_id`` without a backfill, and ``documents._find_doc_by_clean_id``
now resolves relationship targets via ``Document.ref_id``. On an existing deployment every
unchanged row therefore has ``ref_id = NULL`` and its parent / depends-on / dependents no
longer resolve. This suite pins two guarantees:

(a) a legacy target row (``ref_id = None``) does not resolve as a parent until its
    ``ref_id`` is populated; and
(b) an unchanged re-sync populates ``ref_id`` on such a row instead of hash-skipping it.
"""

import datetime
import hashlib
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.documents import get_related_documents
from sdlc_lens.services.project_config import ProjectConfig
from sdlc_lens.services.sync_engine import PARSER_EPOCH, FileEntry, sync_project
from sdlc_lens.utils.hashing import compute_blob_sha, compute_hash
from sdlc_lens.utils.sdlc_ids import id_head, norm_id


def _entry(content: bytes) -> FileEntry:
    """A manifest entry as a real collector builds it (US-01KXCCMH)."""
    return FileEntry(
        file_hash=compute_hash(content),
        raw=content,
        blob_sha=compute_blob_sha(content),
    )


async def _project(session: AsyncSession) -> Project:
    p = Project(slug="heal", name="Heal", source_type="github", repo_url="https://x/y")
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


def _doc(project_id, doc_type, doc_id, *, epic=None, ref_id="__auto__"):
    return Document(
        project_id=project_id,
        doc_type=doc_type,
        doc_id=doc_id,
        title=doc_id,
        status="Done",
        epic=norm_id(epic) if epic else None,
        ref_id=norm_id(id_head(doc_id)) if ref_id == "__auto__" else ref_id,
        content=f"# {doc_id}",
        file_path=f"{doc_type}s/{doc_id}.md",
        file_hash=f"{doc_id:<64}"[:64],
        synced_at=datetime.datetime.now(tz=datetime.UTC),
    )


# ---------------------------------------------------------------------------
# (a) Resolution: an un-migrated target (ref_id=None) does not resolve as a
#     parent; populating ref_id (as the backfill / re-sync does) heals it.
# ---------------------------------------------------------------------------


class TestLegacyRowResolution:
    @pytest.mark.asyncio
    async def test_null_ref_id_target_does_not_resolve_until_populated(
        self, session: AsyncSession
    ) -> None:
        p = await _project(session)
        # Legacy target row: migration 007 landed but never backfilled ref_id.
        epic = _doc(p.id, "epic", "EP0001-project", ref_id=None)
        child = _doc(p.id, "story", "US0001-register", epic="EP0001")
        session.add_all([epic, child])
        await session.commit()

        # RED symptom: the child's parent cannot be found via the NULL ref_id.
        parents, _c, _d, _dd = await get_related_documents(session, p.id, child)
        assert parents == []

        # Backfill ref_id (what migration 009 / the self-healing sync does).
        epic.ref_id = norm_id(id_head(epic.doc_id))
        await session.commit()

        # GREEN: the parent now resolves.
        parents, _c, _d, _dd = await get_related_documents(session, p.id, child)
        assert [pp.doc_id for pp in parents] == ["EP0001-project"]


# ---------------------------------------------------------------------------
# (b) Sync self-heal: an unchanged file whose row has ref_id=None must be
#     reparsed (not hash-skipped) so ref_id gets populated.
# ---------------------------------------------------------------------------


class TestSyncSelfHealsNullRefId:
    @pytest.mark.asyncio
    async def test_unchanged_file_with_null_ref_id_gets_populated(
        self, session: AsyncSession
    ) -> None:
        p = await _project(session)

        content = b"# EP0001\n\n> **Status:** Draft\n\nEpic content"
        file_hash = hashlib.sha256(content).hexdigest()
        rel_path = "epics/EP0001-test-epic.md"

        # Seed a legacy row: correct hash, but ref_id never backfilled.
        legacy = Document(
            project_id=p.id,
            doc_type="epic",
            doc_id="EP0001-test-epic",
            title="EP0001",
            status="Draft",
            ref_id=None,
            content="Epic content",
            file_path=rel_path,
            file_hash=file_hash,
            synced_at=datetime.datetime.now(tz=datetime.UTC),
        )
        session.add(legacy)
        await session.commit()

        # Re-sync where the file is byte-for-byte unchanged (same hash).
        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=({rel_path: _entry(content)}, ProjectConfig()),
        ):
            await sync_project(p, session)

        doc = (
            await session.execute(select(Document).where(Document.project_id == p.id))
        ).scalar_one()
        # The row must have been reparsed, not skipped: ref_id is now populated.
        assert doc.ref_id == "EP0001"


# ---------------------------------------------------------------------------
# (c) BG-01KXARHJ: a parser-epoch bump must self-heal document-derived fields.
#     A byte-unchanged file whose row predates the current PARSER_EPOCH is
#     reparsed even though its hash matches AND its ref_id is already set, so
#     stale doc_type / canonical status recompute after an app upgrade. A row
#     already at the current epoch still hash-skips (no perpetual re-parse).
# ---------------------------------------------------------------------------


class TestSyncSelfHealsStaleParserEpoch:
    @pytest.mark.asyncio
    async def test_legacy_epoch_row_is_reparsed_even_with_ref_id_set(
        self, session: AsyncSession
    ) -> None:
        p = await _project(session)

        # A plan file, byte-for-byte unchanged since it was last synced by an
        # older parser. Its status carries a parenthetical the old canonicaliser
        # kept verbatim; the current one reduces it to the "Complete" token.
        content = b"# PL0001\n\n> **Status:** Complete (81/88 tests passing)\n\nPlan body"
        file_hash = hashlib.sha256(content).hexdigest()
        rel_path = "plans/PL0001-migrate.md"

        # Seed a legacy (epoch 0) row: correct hash and a populated ref_id (so the
        # ref_id-null guard does NOT fire), but a stale stored doc_type ("other")
        # and a stale raw status string.
        legacy = Document(
            project_id=p.id,
            doc_type="other",
            doc_id="PL0001-migrate",
            title="PL0001",
            status="Complete (81/88 tests passing)",
            ref_id=norm_id(id_head("PL0001-migrate")),
            parser_epoch=0,
            content="Plan body",
            file_path=rel_path,
            file_hash=file_hash,
            # blob_sha MUST be set, or this test proves nothing. Leaving it NULL makes
            # `needs_blob_sha_backfill` fire and drive the reparse, so the test passes
            # green while the `stale_epoch` clause it exists to prove is INERT - deleting
            # `and not stale_epoch` from sync_engine left all 755 tests passing. Every
            # other reason-to-reparse must be defused so that ONLY the stale epoch is
            # left to do the work.
            blob_sha=compute_blob_sha(content),
            synced_at=datetime.datetime.now(tz=datetime.UTC),
        )
        session.add(legacy)
        await session.commit()

        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=({rel_path: _entry(content)}, ProjectConfig()),
        ):
            result = await sync_project(p, session)

        doc = (
            await session.execute(select(Document).where(Document.project_id == p.id))
        ).scalar_one()
        # Re-parsed, not hash-skipped: epoch advanced, status canonicalised,
        # doc_type corrected from the stale "other" to the inferred "plan".
        assert doc.parser_epoch == PARSER_EPOCH
        assert doc.status == "Complete"
        assert doc.doc_type == "plan"
        assert result.updated == 1
        assert result.skipped == 0

    @pytest.mark.asyncio
    async def test_current_epoch_unchanged_row_is_skipped(self, session: AsyncSession) -> None:
        p = await _project(session)

        content = b"# PL0002\n\n> **Status:** Complete\n\nPlan body"
        file_hash = hashlib.sha256(content).hexdigest()
        rel_path = "plans/PL0002-other.md"

        # A row already at the current epoch with a matching hash and a set
        # ref_id. Its doc_type is deliberately "other": if it were reparsed the
        # sync would correct it to "plan", so an unchanged doc_type proves a skip.
        current = Document(
            project_id=p.id,
            doc_type="other",
            doc_id="PL0002-other",
            title="PL0002",
            status="Complete",
            ref_id=norm_id(id_head("PL0002-other")),
            parser_epoch=PARSER_EPOCH,
            content="Plan body",
            file_path=rel_path,
            file_hash=file_hash,
            # A fully-current row carries its blob_sha too (US-01KXCC76). Leaving it
            # NULL here would make the row eligible for the blob_sha self-heal and it
            # would be reparsed rather than skipped - which is the correct behaviour for
            # a genuinely NULL row, and is covered by its own test. This test is about
            # the epoch/ref_id skip, so the fixture must represent a row that is current
            # in every respect.
            blob_sha=compute_blob_sha(content),
            synced_at=datetime.datetime.now(tz=datetime.UTC),
        )
        session.add(current)
        await session.commit()

        with patch(
            "sdlc_lens.services.sync_engine.collect_github_files",
            new_callable=AsyncMock,
            return_value=({rel_path: _entry(content)}, ProjectConfig()),
        ):
            result = await sync_project(p, session)

        doc = (
            await session.execute(select(Document).where(Document.project_id == p.id))
        ).scalar_one()
        assert result.skipped == 1
        assert result.updated == 0
        # Not reparsed: the deliberately-stale doc_type survives.
        assert doc.doc_type == "other"
