"""Integration tests for statistics API endpoints.

Test cases: TC0187-TC0199 from TS0017.
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
async def project_a(session: AsyncSession) -> Project:
    """Project Alpha with a mix of document types and statuses."""
    p = Project(
        slug="project-alpha",
        name="Project Alpha",
        sdlc_path="/tmp/alpha",
        last_synced_at=datetime.datetime(2026, 2, 17, 10, 30, 0, tzinfo=datetime.UTC),
    )
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


@pytest.fixture
async def project_b(session: AsyncSession) -> Project:
    """Project Beta with stories only."""
    p = Project(
        slug="project-beta",
        name="Project Beta",
        sdlc_path="/tmp/beta",
        last_synced_at=datetime.datetime(2026, 2, 17, 12, 0, 0, tzinfo=datetime.UTC),
    )
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


@pytest.fixture
async def empty_project(session: AsyncSession) -> Project:
    """Project with zero documents."""
    p = Project(
        slug="empty-project",
        name="Empty Project",
        sdlc_path="/tmp/empty",
    )
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


def _make_doc(project_id: int, doc_type: str, doc_id: str, status: str | None) -> Document:
    """Helper to create a Document with minimal required fields."""
    return Document(
        project_id=project_id,
        doc_type=doc_type,
        doc_id=doc_id,
        title=f"{doc_id} title",
        status=status,
        content=f"# {doc_id}",
        file_path=f"{doc_type}s/{doc_id}.md",
        file_hash="f" * 64,
        synced_at=datetime.datetime.now(tz=datetime.UTC),
    )


@pytest.fixture
async def seed_project_a(session: AsyncSession, project_a: Project) -> None:
    """Seed project A: 3 Done stories, 1 Draft story, 2 Done epics, 1 prd (null status), 1 trd (null status), 2 Done plans = 10 docs."""
    docs = [
        _make_doc(project_a.id, "story", "US0001", "Done"),
        _make_doc(project_a.id, "story", "US0002", "Done"),
        _make_doc(project_a.id, "story", "US0003", "Done"),
        _make_doc(project_a.id, "story", "US0004", "Draft"),
        _make_doc(project_a.id, "epic", "EP0001", "Done"),
        _make_doc(project_a.id, "epic", "EP0002", "Done"),
        _make_doc(project_a.id, "prd", "prd", None),
        _make_doc(project_a.id, "trd", "trd", None),
        _make_doc(project_a.id, "plan", "PL0001", "Done"),
        _make_doc(project_a.id, "plan", "PL0002", "Done"),
    ]
    session.add_all(docs)
    await session.commit()


@pytest.fixture
async def seed_project_b(session: AsyncSession, project_b: Project) -> None:
    """Seed project B: 2 Done stories, 1 In Progress story = 3 docs."""
    docs = [
        _make_doc(project_b.id, "story", "US0010", "Done"),
        _make_doc(project_b.id, "story", "US0011", "Done"),
        _make_doc(project_b.id, "story", "US0012", "In Progress"),
    ]
    session.add_all(docs)
    await session.commit()


# --- Per-project stats ---


# TC0187: Per-project stats returns total document count
class TestPerProjectTotalDocuments:
    async def test_total_documents(self, client: AsyncClient, seed_project_a) -> None:
        resp = await client.get("/api/v1/projects/project-alpha/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_documents"] == 10


# TC0188: Per-project by_type counts
class TestPerProjectByType:
    async def test_by_type_counts(self, client: AsyncClient, seed_project_a) -> None:
        resp = await client.get("/api/v1/projects/project-alpha/stats")
        data = resp.json()
        assert data["by_type"]["story"] == 4
        assert data["by_type"]["epic"] == 2
        assert data["by_type"]["prd"] == 1
        assert data["by_type"]["trd"] == 1
        assert data["by_type"]["plan"] == 2


# TC0189: Per-project by_status counts
class TestPerProjectByStatus:
    async def test_by_status_counts(self, client: AsyncClient, seed_project_a) -> None:
        resp = await client.get("/api/v1/projects/project-alpha/stats")
        data = resp.json()
        assert data["by_status"]["Done"] == 7
        assert data["by_status"]["Draft"] == 1


# TC0190: Per-project includes slug, name, last_synced_at
class TestPerProjectFields:
    async def test_includes_project_fields(self, client: AsyncClient, seed_project_a, project_a) -> None:
        resp = await client.get("/api/v1/projects/project-alpha/stats")
        data = resp.json()
        assert data["slug"] == "project-alpha"
        assert data["name"] == "Project Alpha"
        assert data["last_synced_at"] is not None


# TC0191: Null status grouped in by_status
class TestNullStatusInByStatus:
    async def test_null_status_grouped(self, client: AsyncClient, seed_project_a) -> None:
        resp = await client.get("/api/v1/projects/project-alpha/stats")
        data = resp.json()
        # prd and trd have null status - should appear under null key
        assert data["by_status"].get("null") == 2 or data["by_status"].get(None) == 2 or data["by_status"].get("Unknown") == 2


# TC0195: Completion percentage calculated correctly
class TestCompletionPercentage:
    async def test_completion_formula(self, client: AsyncClient, seed_project_a) -> None:
        """Project A: 3 Done stories out of 4 total = 75.0%."""
        resp = await client.get("/api/v1/projects/project-alpha/stats")
        data = resp.json()
        assert data["completion_percentage"] == 75.0


# TC0196: No stories means completion 0.0
class TestNoStoriesCompletion:
    async def test_no_stories_zero_completion(self, client: AsyncClient, session: AsyncSession, empty_project) -> None:
        """Project with epics only, no stories."""
        docs = [
            _make_doc(empty_project.id, "epic", "EP0001", "Done"),
            _make_doc(empty_project.id, "epic", "EP0002", "Done"),
        ]
        session.add_all(docs)
        await session.commit()

        resp = await client.get("/api/v1/projects/empty-project/stats")
        data = resp.json()
        assert data["completion_percentage"] == 0.0


# TC0197: All stories Done means 100.0
class TestAllStoriesDone:
    async def test_all_done_100(self, client: AsyncClient, seed_project_b) -> None:
        """Project B has 2 Done + 1 In Progress = 66.7% (not all Done).
        Let's seed a project with all Done stories separately."""
        pass

    async def test_all_stories_done(self, client: AsyncClient, session: AsyncSession, empty_project) -> None:
        docs = [
            _make_doc(empty_project.id, "story", "US0001", "Done"),
            _make_doc(empty_project.id, "story", "US0002", "Done"),
            _make_doc(empty_project.id, "story", "US0003", "Done"),
        ]
        session.add_all(docs)
        await session.commit()

        resp = await client.get("/api/v1/projects/empty-project/stats")
        data = resp.json()
        assert data["completion_percentage"] == 100.0


# TC0198: Zero-document project returns zeroes
class TestZeroDocumentProject:
    async def test_zero_documents(self, client: AsyncClient, empty_project) -> None:
        resp = await client.get("/api/v1/projects/empty-project/stats")
        data = resp.json()
        assert data["total_documents"] == 0
        assert data["by_type"] == {}
        assert data["by_status"] == {}
        assert data["completion_percentage"] == 0.0


# TC0199: 404 for unknown project slug
class TestUnknownProjectStats:
    async def test_404_unknown_slug(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/projects/nonexistent/stats")
        assert resp.status_code == 404


# --- Aggregate stats ---


# TC0192: Aggregate total_projects and total_documents
class TestAggregateTotals:
    async def test_totals(self, client: AsyncClient, seed_project_a, seed_project_b) -> None:
        resp = await client.get("/api/v1/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_projects"] == 2
        assert data["total_documents"] == 13  # 10 + 3


# TC0193: Aggregate by_type sums across projects
class TestAggregateByType:
    async def test_aggregate_by_type(self, client: AsyncClient, seed_project_a, seed_project_b) -> None:
        resp = await client.get("/api/v1/stats")
        data = resp.json()
        # project_a: 4 stories, project_b: 3 stories = 7
        assert data["by_type"]["story"] == 7
        assert data["by_type"]["epic"] == 2


# TC0194: Aggregate projects array with per-project summaries
class TestAggregateProjectsArray:
    async def test_projects_array(self, client: AsyncClient, seed_project_a, seed_project_b) -> None:
        resp = await client.get("/api/v1/stats")
        data = resp.json()
        assert len(data["projects"]) == 2
        slugs = {p["slug"] for p in data["projects"]}
        assert "project-alpha" in slugs
        assert "project-beta" in slugs
        # Each entry has expected fields
        for proj in data["projects"]:
            assert "slug" in proj
            assert "name" in proj
            assert "total_documents" in proj
            assert "completion_percentage" in proj


# Aggregate completion: weighted average
class TestAggregateCompletion:
    async def test_weighted_completion(self, client: AsyncClient, seed_project_a, seed_project_b) -> None:
        """Project A: 3/4 Done stories. Project B: 2/3 Done stories.
        Overall: 5/7 = 71.4%."""
        resp = await client.get("/api/v1/stats")
        data = resp.json()
        expected = round(5 / 7 * 100, 1)
        assert data["completion_percentage"] == expected


# Aggregate with zero projects
class TestAggregateZeroProjects:
    async def test_zero_projects(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_projects"] == 0
        assert data["total_documents"] == 0
        assert data["projects"] == []
        assert data["completion_percentage"] == 0.0
