"""Integration tests for the health check API endpoint."""

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
    p = Project(
        slug="health-test",
        name="Health Test Project",
        sdlc_path="/tmp/health",
        last_synced_at=datetime.datetime(2026, 2, 17, 10, 0, 0, tzinfo=datetime.UTC),
    )
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


def _make_doc(
    project_id: int,
    doc_type: str,
    doc_id: str,
    *,
    title: str | None = None,
    status: str | None = "Draft",
    owner: str | None = "Darren",
    priority: str | None = "P0",
    story_points: int | None = 5,
    epic: str | None = None,
    story: str | None = None,
    content: str = "# Title\n\nThis document has sufficient content for the health check.",
) -> Document:
    return Document(
        project_id=project_id,
        doc_type=doc_type,
        doc_id=doc_id,
        title=title or f"{doc_id} title",
        status=status,
        owner=owner,
        priority=priority,
        story_points=story_points,
        epic=epic,
        story=story,
        content=content,
        file_path=f"{doc_type}s/{doc_id}.md",
        file_hash="a" * 64,
        synced_at=datetime.datetime.now(tz=datetime.UTC),
    )


class TestHealthCheckEndpoint:
    async def test_returns_health_check_for_project(
        self, client: AsyncClient, session: AsyncSession, project: Project
    ):
        """Healthy project returns score and empty findings."""
        docs = [
            _make_doc(project.id, "prd", "PRD-main"),
            _make_doc(project.id, "trd", "TRD-main"),
            _make_doc(project.id, "epic", "EP0001", status="Done"),
            _make_doc(
                project.id, "story", "US0001", epic="EP0001", status="Done"
            ),
            _make_doc(project.id, "plan", "PL0001", story="US0001", status="Done"),
            _make_doc(project.id, "test-spec", "TS0001", story="US0001", status="Done"),
        ]
        session.add_all(docs)
        await session.commit()

        resp = await client.get("/api/v1/projects/health-test/health-check")
        assert resp.status_code == 200

        data = resp.json()
        assert data["project_slug"] == "health-test"
        assert data["total_documents"] == 6
        assert data["score"] == 100
        assert data["findings"] == []
        assert data["summary"] == {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

    async def test_returns_findings_for_unhealthy_project(
        self, client: AsyncClient, session: AsyncSession, project: Project
    ):
        """Project with issues returns findings."""
        docs = [
            _make_doc(
                project.id,
                "story",
                "US0001",
                status=None,
                owner=None,
                priority=None,
                story_points=None,
            ),
        ]
        session.add_all(docs)
        await session.commit()

        resp = await client.get("/api/v1/projects/health-test/health-check")
        assert resp.status_code == 200

        data = resp.json()
        assert data["score"] < 100
        assert len(data["findings"]) > 0
        assert data["summary"]["critical"] >= 1  # MISSING_PRD

        # Verify finding structure
        finding = data["findings"][0]
        assert "rule_id" in finding
        assert "severity" in finding
        assert "category" in finding
        assert "message" in finding
        assert "affected_documents" in finding
        assert "suggested_fix" in finding

    async def test_returns_404_for_unknown_project(self, client: AsyncClient):
        resp = await client.get("/api/v1/projects/nonexistent/health-check")
        assert resp.status_code == 404
        data = resp.json()
        assert data["error"]["code"] == "NOT_FOUND"

    async def test_empty_project_returns_perfect_score(
        self, client: AsyncClient, project: Project
    ):
        """Project with no documents returns score 100."""
        resp = await client.get("/api/v1/projects/health-test/health-check")
        assert resp.status_code == 200

        data = resp.json()
        assert data["score"] == 100
        assert data["total_documents"] == 0
        assert data["findings"] == []

    async def test_affected_documents_include_doc_details(
        self, client: AsyncClient, session: AsyncSession, project: Project
    ):
        """Affected documents include doc_id, doc_type, and title."""
        docs = [
            _make_doc(project.id, "epic", "EP0001", title="Lonely Epic"),
        ]
        session.add_all(docs)
        await session.commit()

        resp = await client.get("/api/v1/projects/health-test/health-check")
        data = resp.json()

        # Find the EPIC_NO_STORIES finding
        epic_findings = [
            f for f in data["findings"] if f["rule_id"] == "EPIC_NO_STORIES"
        ]
        assert len(epic_findings) == 1
        affected = epic_findings[0]["affected_documents"]
        assert len(affected) == 1
        assert affected[0]["doc_id"] == "EP0001"
        assert affected[0]["doc_type"] == "epic"
        assert affected[0]["title"] == "Lonely Epic"
