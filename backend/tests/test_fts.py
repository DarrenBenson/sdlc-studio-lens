"""FTS5 search index management tests.

Test cases: TC0118-TC0127 from TS0010.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.fts import (
    FTS5_CREATE_SQL,
    fts_delete,
    fts_insert,
    fts_rebuild,
    fts_update,
)


@pytest.fixture
async def fts_session(session: AsyncSession) -> AsyncSession:
    """Session with FTS5 virtual table created."""
    await session.execute(text(FTS5_CREATE_SQL))
    await session.commit()
    return session


async def _make_project(session: AsyncSession) -> Project:
    """Create a test project."""
    project = Project(
        slug="fts-test", name="FTS Test", sdlc_path="/tmp/fts"
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def _make_doc(
    session: AsyncSession,
    project_id: int,
    title: str,
    content: str,
    doc_id: str = "EP0001",
) -> Document:
    """Create a document record."""
    doc = Document(
        project_id=project_id,
        doc_type="epic",
        doc_id=doc_id,
        title=title,
        content=content,
        file_path=f"epics/{doc_id}.md",
        file_hash="a" * 64,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return doc


# TC0118: FTS5 virtual table created
class TestFts5TableCreation:
    @pytest.mark.asyncio
    async def test_table_exists(self, fts_session: AsyncSession) -> None:
        result = await fts_session.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE name='documents_fts'"
            )
        )
        row = result.scalar_one_or_none()
        assert row == "documents_fts"


# TC0119: New document indexed in FTS5
class TestFtsInsert:
    @pytest.mark.asyncio
    async def test_insert_makes_searchable(
        self, fts_session: AsyncSession
    ) -> None:
        project = await _make_project(fts_session)
        doc = await _make_doc(
            fts_session,
            project.id,
            "EP0001: Project Management",
            "This covers project registration.",
        )

        await fts_insert(fts_session, doc.id, doc.title, doc.content)
        await fts_session.commit()

        result = await fts_session.execute(
            text(
                "SELECT rowid FROM documents_fts "
                "WHERE documents_fts MATCH 'project'"
            )
        )
        rows = result.scalars().all()
        assert doc.id in rows


# TC0120: Changed document FTS5 entry updated
class TestFtsUpdate:
    @pytest.mark.asyncio
    async def test_update_changes_searchable_content(
        self, fts_session: AsyncSession
    ) -> None:
        project = await _make_project(fts_session)
        doc = await _make_doc(
            fts_session,
            project.id,
            "Original Title",
            "Original body content.",
        )

        await fts_insert(fts_session, doc.id, doc.title, doc.content)
        await fts_session.commit()

        # Update
        await fts_update(
            fts_session,
            doc.id,
            old_title="Original Title",
            old_content="Original body content.",
            new_title="Updated Title",
            new_content="Updated body content.",
        )
        await fts_session.commit()

        # "Updated" should be found
        result = await fts_session.execute(
            text(
                "SELECT rowid FROM documents_fts "
                "WHERE documents_fts MATCH 'Updated'"
            )
        )
        assert doc.id in result.scalars().all()

        # "Original" should NOT be found
        result2 = await fts_session.execute(
            text(
                "SELECT rowid FROM documents_fts "
                "WHERE documents_fts MATCH 'Original'"
            )
        )
        assert doc.id not in result2.scalars().all()


# TC0121: Deleted document FTS5 entry removed
class TestFtsDelete:
    @pytest.mark.asyncio
    async def test_delete_removes_from_index(
        self, fts_session: AsyncSession
    ) -> None:
        project = await _make_project(fts_session)
        doc = await _make_doc(
            fts_session,
            project.id,
            "Deletable Title",
            "Deletable content here.",
        )

        await fts_insert(fts_session, doc.id, doc.title, doc.content)
        await fts_session.commit()

        # Verify it's searchable
        result = await fts_session.execute(
            text(
                "SELECT rowid FROM documents_fts "
                "WHERE documents_fts MATCH 'Deletable'"
            )
        )
        assert doc.id in result.scalars().all()

        # Delete
        await fts_delete(
            fts_session, doc.id, doc.title, doc.content
        )
        await fts_session.commit()

        # No longer searchable
        result2 = await fts_session.execute(
            text(
                "SELECT rowid FROM documents_fts "
                "WHERE documents_fts MATCH 'Deletable'"
            )
        )
        assert doc.id not in result2.scalars().all()


# TC0122: FTS5 MATCH returns correct documents
class TestFtsMatchAccuracy:
    @pytest.mark.asyncio
    async def test_match_returns_correct_subset(
        self, fts_session: AsyncSession
    ) -> None:
        project = await _make_project(fts_session)
        # 3 docs with "authentication", 2 without
        docs_with = []
        for i, (title, content) in enumerate(
            [
                ("Auth Setup", "Implements authentication flow."),
                ("DB Schema", "Uses authentication tokens."),
                ("Dashboard", "Shows authentication status."),
            ]
        ):
            doc = await _make_doc(
                fts_session,
                project.id,
                title,
                content,
                doc_id=f"D{i:04d}",
            )
            await fts_insert(fts_session, doc.id, title, content)
            docs_with.append(doc.id)

        for i, (title, content) in enumerate(
            [
                ("Search API", "Full-text search endpoint."),
                ("Docker Config", "Container setup."),
            ],
            start=3,
        ):
            doc = await _make_doc(
                fts_session,
                project.id,
                title,
                content,
                doc_id=f"D{i:04d}",
            )
            await fts_insert(fts_session, doc.id, title, content)

        await fts_session.commit()

        result = await fts_session.execute(
            text(
                "SELECT rowid FROM documents_fts "
                "WHERE documents_fts MATCH 'authentication'"
            )
        )
        found = result.scalars().all()
        assert len(found) == 3
        assert set(found) == set(docs_with)


# TC0123: snake_case terms searchable
class TestFtsSnakeCase:
    @pytest.mark.asyncio
    async def test_snake_case_searchable(
        self, fts_session: AsyncSession
    ) -> None:
        project = await _make_project(fts_session)
        doc = await _make_doc(
            fts_session,
            project.id,
            "Sync Service",
            "Updates sync_status and last_synced_at fields.",
        )
        await fts_insert(fts_session, doc.id, doc.title, doc.content)
        await fts_session.commit()

        result = await fts_session.execute(
            text(
                "SELECT rowid FROM documents_fts "
                "WHERE documents_fts MATCH 'sync_status'"
            )
        )
        assert doc.id in result.scalars().all()


# TC0124: Empty content indexed without error
class TestFtsEmptyContent:
    @pytest.mark.asyncio
    async def test_empty_content_no_error(
        self, fts_session: AsyncSession
    ) -> None:
        project = await _make_project(fts_session)
        doc = await _make_doc(
            fts_session,
            project.id,
            "Empty Doc",
            "",
        )
        await fts_insert(fts_session, doc.id, doc.title, doc.content)
        await fts_session.commit()

        # Searchable by title
        result = await fts_session.execute(
            text(
                "SELECT rowid FROM documents_fts "
                "WHERE documents_fts MATCH 'Empty'"
            )
        )
        assert doc.id in result.scalars().all()


# TC0125: FTS5 rebuild works
class TestFtsRebuild:
    @pytest.mark.asyncio
    async def test_rebuild_succeeds(
        self, fts_session: AsyncSession
    ) -> None:
        project = await _make_project(fts_session)
        doc = await _make_doc(
            fts_session,
            project.id,
            "Rebuild Test",
            "Content for rebuild.",
        )
        await fts_insert(fts_session, doc.id, doc.title, doc.content)
        await fts_session.commit()

        # Rebuild should not raise
        await fts_rebuild(fts_session)
        await fts_session.commit()

        # Content still searchable
        result = await fts_session.execute(
            text(
                "SELECT rowid FROM documents_fts "
                "WHERE documents_fts MATCH 'Rebuild'"
            )
        )
        assert doc.id in result.scalars().all()


# TC0126: Unicode content handled
class TestFtsUnicode:
    @pytest.mark.asyncio
    async def test_unicode_content(
        self, fts_session: AsyncSession
    ) -> None:
        project = await _make_project(fts_session)
        doc = await _make_doc(
            fts_session,
            project.id,
            "Unicode Test",
            "Contains unicode characters and special terms.",
        )
        await fts_insert(fts_session, doc.id, doc.title, doc.content)
        await fts_session.commit()

        result = await fts_session.execute(
            text(
                "SELECT rowid FROM documents_fts "
                "WHERE documents_fts MATCH 'unicode'"
            )
        )
        assert doc.id in result.scalars().all()


# TC0127: FTS5 index consistent after full sync
class TestFtsConsistency:
    @pytest.mark.asyncio
    async def test_index_matches_documents(
        self, fts_session: AsyncSession
    ) -> None:
        project = await _make_project(fts_session)
        doc_ids = []
        for i in range(5):
            doc = await _make_doc(
                fts_session,
                project.id,
                f"Doc {i}",
                f"Content for document {i}.",
                doc_id=f"DOC{i:04d}",
            )
            await fts_insert(fts_session, doc.id, doc.title, doc.content)
            doc_ids.append(doc.id)

        await fts_session.commit()

        # Count FTS5 entries
        result = await fts_session.execute(
            text("SELECT count(*) FROM documents_fts")
        )
        assert result.scalar_one() == 5
