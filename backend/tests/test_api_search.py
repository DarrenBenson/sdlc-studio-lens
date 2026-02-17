"""Integration tests for full-text search API endpoint.

Test cases: TC0228-TC0238 from TS0021.
"""

import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.fts import FTS5_CREATE_SQL, fts_insert


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def fts_table(session: AsyncSession) -> None:
    """Create FTS5 virtual table for search tests."""
    await session.execute(text(FTS5_CREATE_SQL))
    await session.commit()


@pytest.fixture
async def project_a(session: AsyncSession) -> Project:
    """Project A for search tests."""
    p = Project(
        slug="project-a",
        name="Project Alpha",
        sdlc_path="/tmp/project-a",
    )
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


@pytest.fixture
async def project_b(session: AsyncSession) -> Project:
    """Project B for search tests."""
    p = Project(
        slug="project-b",
        name="Project Beta",
        sdlc_path="/tmp/project-b",
    )
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


def _make_doc(
    project_id: int,
    doc_type: str,
    doc_id: str,
    title: str,
    content: str,
    status: str | None = "Draft",
) -> Document:
    """Helper to create a Document with specified fields."""
    return Document(
        project_id=project_id,
        doc_type=doc_type,
        doc_id=doc_id,
        title=title,
        status=status,
        content=content,
        file_path=f"{doc_type}s/{doc_id}.md",
        file_hash="a" * 64,
        synced_at=datetime.datetime.now(tz=datetime.UTC),
    )


@pytest.fixture
async def seed_search_data(
    session: AsyncSession,
    fts_table,
    project_a: Project,
    project_b: Project,
) -> None:
    """Seed documents across two projects and index them in FTS5.

    Project A: 3 documents (2 stories, 1 epic) mentioning authentication
    Project B: 2 documents (1 story, 1 plan)
    """
    docs = [
        # Project A - authentication-related documents
        _make_doc(
            project_a.id,
            "story",
            "US0001",
            "User Authentication Flow",
            "The system shall implement authentication using OAuth2. "
            "Users must authenticate before accessing protected resources.",
            status="Done",
        ),
        _make_doc(
            project_a.id,
            "story",
            "US0002",
            "Password Reset",
            "Users can reset their password via email. "
            "This requires authentication token validation.",
            status="In Progress",
        ),
        _make_doc(
            project_a.id,
            "epic",
            "EP0001",
            "Security Module",
            "Epic covering all authentication and authorisation features. "
            "Includes multi-factor authentication support.",
            status="Draft",
        ),
        # Project B - different topic
        _make_doc(
            project_b.id,
            "story",
            "US0010",
            "Dashboard Layout",
            "Build the main dashboard layout with widgets and navigation.",
            status="Done",
        ),
        _make_doc(
            project_b.id,
            "plan",
            "PL0001",
            "Sprint Plan Q1",
            "Plan covering authentication migration and dashboard work.",
            status=None,
        ),
    ]

    session.add_all(docs)
    await session.commit()

    # Refresh to get IDs, then index each document in FTS5
    for doc in docs:
        await session.refresh(doc)
        await fts_insert(session, doc.id, doc.title, doc.content)

    await session.commit()


@pytest.fixture
async def seed_many_documents(
    session: AsyncSession,
    fts_table,
    project_a: Project,
) -> None:
    """Seed 25 documents containing the word 'testing' for pagination tests."""
    docs = []
    for i in range(25):
        docs.append(
            _make_doc(
                project_a.id,
                "story",
                f"US{i:04d}",
                f"Testing Feature {i}",
                f"Document {i} covers testing procedures and test automation.",
                status="Draft",
            )
        )

    session.add_all(docs)
    await session.commit()

    for doc in docs:
        await session.refresh(doc)
        await fts_insert(session, doc.id, doc.title, doc.content)

    await session.commit()


# TC0228: Search returns matching documents
class TestSearchReturnsMatchingDocuments:
    async def test_search_returns_matches(
        self, client: AsyncClient, seed_search_data
    ) -> None:
        resp = await client.get("/api/v1/search", params={"q": "authentication"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) > 0
        assert data["total"] > 0

        # Each result has required fields
        item = data["items"][0]
        assert "doc_id" in item
        assert "type" in item
        assert "title" in item
        assert "project_slug" in item
        assert "project_name" in item
        assert "status" in item
        assert "snippet" in item
        assert "score" in item


# TC0229: Results ranked by relevance (score descending)
class TestResultsRankedByRelevance:
    async def test_scores_descending(
        self, client: AsyncClient, seed_search_data
    ) -> None:
        resp = await client.get("/api/v1/search", params={"q": "authentication"})
        assert resp.status_code == 200
        data = resp.json()
        scores = [item["score"] for item in data["items"]]
        assert len(scores) >= 2
        assert scores == sorted(scores, reverse=True)


# TC0230: Snippet includes context with <mark> tags
class TestSnippetContainsMarkTags:
    async def test_snippet_has_mark_tags(
        self, client: AsyncClient, seed_search_data
    ) -> None:
        resp = await client.get("/api/v1/search", params={"q": "authentication"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) > 0
        # At least one snippet should contain <mark> tags
        snippets = [item["snippet"] for item in data["items"]]
        marked = [s for s in snippets if "<mark>" in s and "</mark>" in s]
        assert len(marked) > 0
        # Verify the marked term is present
        assert any("<mark>authentication</mark>" in s.lower() for s in marked) or any(
            "<mark>authentication</mark>" in s for s in marked
        )


# TC0231: Filter by project slug
class TestFilterByProjectSlug:
    async def test_project_filter(
        self, client: AsyncClient, seed_search_data
    ) -> None:
        resp = await client.get(
            "/api/v1/search", params={"q": "authentication", "project": "project-a"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) > 0
        # All results should be from project-a
        for item in data["items"]:
            assert item["project_slug"] == "project-a"


# TC0232: Filter by document type
class TestFilterByDocumentType:
    async def test_type_filter(
        self, client: AsyncClient, seed_search_data
    ) -> None:
        resp = await client.get(
            "/api/v1/search", params={"q": "authentication", "type": "story"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) > 0
        # All results should be stories
        for item in data["items"]:
            assert item["type"] == "story"


# TC0233: Missing query returns 422
class TestMissingQueryReturns422:
    async def test_no_q_param(self, client: AsyncClient, fts_table) -> None:
        resp = await client.get("/api/v1/search")
        assert resp.status_code == 422


# TC0234: No results returns empty list
class TestNoResultsReturnsEmptyList:
    async def test_no_matches(
        self, client: AsyncClient, seed_search_data
    ) -> None:
        resp = await client.get("/api/v1/search", params={"q": "xyznonexistent"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0


# TC0235: Pagination works
class TestPaginationWorks:
    async def test_per_page_limits_results(
        self, client: AsyncClient, seed_many_documents
    ) -> None:
        resp = await client.get(
            "/api/v1/search", params={"q": "testing", "per_page": 10}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        assert data["per_page"] == 10

    async def test_page_two(
        self, client: AsyncClient, seed_many_documents
    ) -> None:
        resp = await client.get(
            "/api/v1/search", params={"q": "testing", "per_page": 10, "page": 2}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        assert data["page"] == 2

    async def test_last_page_partial(
        self, client: AsyncClient, seed_many_documents
    ) -> None:
        resp = await client.get(
            "/api/v1/search", params={"q": "testing", "per_page": 10, "page": 3}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 5
        assert data["total"] == 25


# TC0236: Combined filters (project + type)
class TestCombinedFilters:
    async def test_project_and_type_filter(
        self, client: AsyncClient, seed_search_data
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            params={"q": "authentication", "project": "project-a", "type": "story"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["project_slug"] == "project-a"
            assert item["type"] == "story"

    async def test_combined_excludes_other_types(
        self, client: AsyncClient, seed_search_data
    ) -> None:
        """Filtering by project-a + story should exclude the epic EP0001."""
        resp = await client.get(
            "/api/v1/search",
            params={"q": "authentication", "project": "project-a", "type": "story"},
        )
        data = resp.json()
        doc_ids = [item["doc_id"] for item in data["items"]]
        assert "EP0001" not in doc_ids


# TC0237: Empty query string returns 422
class TestEmptyQueryReturns422:
    async def test_empty_q_param(self, client: AsyncClient, fts_table) -> None:
        resp = await client.get("/api/v1/search", params={"q": ""})
        assert resp.status_code == 422


# TC0238: Response includes query echo
class TestResponseIncludesQueryEcho:
    async def test_query_echoed(
        self, client: AsyncClient, seed_search_data
    ) -> None:
        resp = await client.get("/api/v1/search", params={"q": "authentication"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "authentication"
