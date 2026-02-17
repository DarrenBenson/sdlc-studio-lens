"""Integration tests for GET /api/v1/projects/{slug}/documents endpoint.

Test cases: TC0145-TC0158 from TS0012.
"""

import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def project(session: AsyncSession) -> Project:
    """Create a test project."""
    p = Project(slug="testproject", name="Test Project", sdlc_path="/tmp/test")
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


@pytest.fixture
async def seed_documents(session: AsyncSession, project: Project) -> list[Document]:
    """Seed 5 documents with varying types, statuses, and titles."""
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    docs = [
        Document(
            project_id=project.id,
            doc_type="epic",
            doc_id="EP0001-alpha-epic",
            title="Alpha Epic",
            status="Done",
            owner="Darren",
            priority="P0",
            story_points=8,
            content="# Alpha Epic",
            file_path="epics/EP0001-alpha-epic.md",
            file_hash="a" * 64,
            synced_at=now - datetime.timedelta(minutes=5),
        ),
        Document(
            project_id=project.id,
            doc_type="epic",
            doc_id="EP0002-beta-epic",
            title="Beta Epic",
            status="Draft",
            owner="Darren",
            priority="P1",
            story_points=5,
            content="# Beta Epic",
            file_path="epics/EP0002-beta-epic.md",
            file_hash="b" * 64,
            synced_at=now - datetime.timedelta(minutes=4),
        ),
        Document(
            project_id=project.id,
            doc_type="story",
            doc_id="US0001-charlie-story",
            title="Charlie Story",
            status="Done",
            owner="Darren",
            priority="P0",
            story_points=3,
            content="# Charlie Story",
            file_path="stories/US0001-charlie-story.md",
            file_hash="c" * 64,
            synced_at=now - datetime.timedelta(minutes=3),
        ),
        Document(
            project_id=project.id,
            doc_type="story",
            doc_id="US0002-delta-story",
            title="Delta Story",
            status="Draft",
            owner="Darren",
            priority="P2",
            story_points=2,
            content="# Delta Story",
            file_path="stories/US0002-delta-story.md",
            file_hash="d" * 64,
            synced_at=now - datetime.timedelta(minutes=2),
        ),
        Document(
            project_id=project.id,
            doc_type="story",
            doc_id="US0003-echo-story",
            title="Echo Story",
            status="Done",
            owner="Darren",
            priority="P1",
            story_points=5,
            content="# Echo Story",
            file_path="stories/US0003-echo-story.md",
            file_hash="e" * 64,
            synced_at=now - datetime.timedelta(minutes=1),
        ),
    ]
    session.add_all(docs)
    await session.commit()
    return docs


# ---------------------------------------------------------------------------
# TC0145: List documents returns paginated response
# ---------------------------------------------------------------------------


class TestListDocumentsPagination:
    """TC0145: Paginated response structure."""

    async def test_returns_200(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project.slug}/documents")
        assert resp.status_code == 200

    async def test_response_has_items_array(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project.slug}/documents")
        data = resp.json()
        assert isinstance(data["items"], list)

    async def test_response_has_total(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project.slug}/documents")
        data = resp.json()
        assert data["total"] == 5

    async def test_response_has_page(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project.slug}/documents")
        data = resp.json()
        assert data["page"] == 1

    async def test_items_have_expected_fields(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project.slug}/documents")
        data = resp.json()
        item = data["items"][0]
        assert "doc_id" in item
        assert "type" in item
        assert "title" in item
        assert "status" in item
        assert "owner" in item
        assert "updated_at" in item

    async def test_items_exclude_content(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project.slug}/documents")
        data = resp.json()
        item = data["items"][0]
        assert "content" not in item


# ---------------------------------------------------------------------------
# TC0146: Default per_page is 50
# ---------------------------------------------------------------------------


class TestDefaultPerPage:
    """TC0146: Default per_page is 50."""

    async def test_default_per_page_is_50(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project.slug}/documents")
        data = resp.json()
        assert data["per_page"] == 50

    async def test_pages_calculated_correctly(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project.slug}/documents")
        data = resp.json()
        # 5 docs / 50 per page = 1 page
        assert data["pages"] == 1


# ---------------------------------------------------------------------------
# TC0147: Type filter returns only matching type
# ---------------------------------------------------------------------------


class TestTypeFilter:
    """TC0147: Type filter."""

    async def test_filter_by_epic(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project.slug}/documents?type=epic")
        data = resp.json()
        assert data["total"] == 2
        assert all(item["type"] == "epic" for item in data["items"])

    async def test_filter_by_story(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project.slug}/documents?type=story")
        data = resp.json()
        assert data["total"] == 3
        assert all(item["type"] == "story" for item in data["items"])


# ---------------------------------------------------------------------------
# TC0148: Status filter returns only matching status
# ---------------------------------------------------------------------------


class TestStatusFilter:
    """TC0148: Status filter."""

    async def test_filter_by_done(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project.slug}/documents?status=Done")
        data = resp.json()
        assert data["total"] == 3
        assert all(item["status"] == "Done" for item in data["items"])

    async def test_filter_by_draft(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project.slug}/documents?status=Draft")
        data = resp.json()
        assert data["total"] == 2
        assert all(item["status"] == "Draft" for item in data["items"])


# ---------------------------------------------------------------------------
# TC0149: Combined type + status filter
# ---------------------------------------------------------------------------


class TestCombinedFilters:
    """TC0149: Combined filters."""

    async def test_type_and_status_combined(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents?type=story&status=Done"
        )
        data = resp.json()
        assert data["total"] == 2
        assert all(item["type"] == "story" for item in data["items"])
        assert all(item["status"] == "Done" for item in data["items"])

    async def test_combined_filter_total_reflects_both(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents?type=epic&status=Draft"
        )
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Beta Epic"


# ---------------------------------------------------------------------------
# TC0150: Sort by title ascending
# ---------------------------------------------------------------------------


class TestSortTitle:
    """TC0150: Sort by title ascending."""

    async def test_sort_title_asc(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents?sort=title&order=asc"
        )
        data = resp.json()
        titles = [item["title"] for item in data["items"]]
        assert titles == sorted(titles)

    async def test_sort_title_desc(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents?sort=title&order=desc"
        )
        data = resp.json()
        titles = [item["title"] for item in data["items"]]
        assert titles == sorted(titles, reverse=True)


# ---------------------------------------------------------------------------
# TC0151: Default sort is synced_at descending
# ---------------------------------------------------------------------------


class TestDefaultSort:
    """TC0151: Default sort is synced_at descending (most recent first)."""

    async def test_default_sort_most_recent_first(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project.slug}/documents")
        data = resp.json()
        # Echo Story was synced most recently (1 min ago), Alpha least recently (5 min ago)
        assert data["items"][0]["title"] == "Echo Story"
        assert data["items"][-1]["title"] == "Alpha Epic"


# ---------------------------------------------------------------------------
# TC0152: Pagination page 2 returns correct offset
# ---------------------------------------------------------------------------


class TestPaginationOffset:
    """TC0152: Page 2 with per_page=2."""

    async def test_page_2_returns_correct_items(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents?per_page=2&page=2"
        )
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2
        assert data["total"] == 5
        assert data["pages"] == 3  # ceil(5/2)

    async def test_last_page_has_remaining_items(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents?per_page=2&page=3"
        )
        data = resp.json()
        assert len(data["items"]) == 1  # 5 total, page 3 of 3


# ---------------------------------------------------------------------------
# TC0153: Total count correct with filters applied
# ---------------------------------------------------------------------------


class TestFilteredTotalCount:
    """TC0153: Total count with filters."""

    async def test_total_reflects_filter(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(f"/api/v1/projects/{project.slug}/documents?type=story")
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3


# ---------------------------------------------------------------------------
# TC0154: 404 for unknown project slug
# ---------------------------------------------------------------------------


class TestUnknownProject:
    """TC0154: 404 for unknown project slug."""

    async def test_returns_404(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/projects/nonexistent/documents")
        assert resp.status_code == 404

    async def test_error_code(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/projects/nonexistent/documents")
        data = resp.json()
        assert data["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# TC0155: Empty project returns empty items
# ---------------------------------------------------------------------------


class TestEmptyProject:
    """TC0155: Empty project returns empty items."""

    async def test_empty_items(self, client: AsyncClient, project: Project) -> None:
        resp = await client.get(f"/api/v1/projects/{project.slug}/documents")
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["pages"] == 0


# ---------------------------------------------------------------------------
# TC0156: per_page capped at 100
# ---------------------------------------------------------------------------


class TestPerPageCapped:
    """TC0156: per_page capped at 100."""

    async def test_per_page_capped(
        self, client: AsyncClient, project: Project, seed_documents: list[Document]
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents?per_page=200"
        )
        data = resp.json()
        assert data["per_page"] == 100


# ---------------------------------------------------------------------------
# TC0157: per_page zero or negative returns 422
# ---------------------------------------------------------------------------


class TestPerPageInvalid:
    """TC0157: per_page zero or negative returns 422."""

    async def test_per_page_zero(
        self, client: AsyncClient, project: Project
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents?per_page=0"
        )
        assert resp.status_code == 422

    async def test_per_page_negative(
        self, client: AsyncClient, project: Project
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents?per_page=-1"
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# TC0158: Invalid sort field returns 422
# ---------------------------------------------------------------------------


class TestInvalidSortField:
    """TC0158: Invalid sort field returns 422."""

    async def test_invalid_sort_returns_422(
        self, client: AsyncClient, project: Project
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents?sort=invalid_field"
        )
        assert resp.status_code == 422
