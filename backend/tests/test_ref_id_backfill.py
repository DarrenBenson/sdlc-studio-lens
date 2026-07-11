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
from sdlc_lens.services.sync_engine import sync_project
from sdlc_lens.utils.sdlc_ids import id_head, norm_id


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
            return_value=({rel_path: (file_hash, content)}, ProjectConfig()),
        ):
            await sync_project(p, session)

        doc = (
            await session.execute(select(Document).where(Document.project_id == p.id))
        ).scalar_one()
        # The row must have been reparsed, not skipped: ref_id is now populated.
        assert doc.ref_id == "EP0001"
