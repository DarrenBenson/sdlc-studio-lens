"""Integration tests for GET /api/v1/projects/{slug}/documents/{type}/{doc_id}.

Test cases: TC0159-TC0168 from TS0013.
"""

import json

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
async def doc_with_metadata(session: AsyncSession, project: Project) -> Document:
    """A document with extra metadata fields."""
    doc = Document(
        project_id=project.id,
        doc_type="story",
        doc_id="US0001-register-project",
        title="Register a New Project",
        status="Done",
        owner="Darren",
        priority="P0",
        story_points=5,
        epic="EP0001",
        metadata_json=json.dumps({"sprint": "Sprint 1", "created": "2026-02-17"}),
        content="# US0001: Register a New Project\n\n> **Status:** Done\n\nStory content here.",
        file_path="stories/US0001-register-project.md",
        file_hash="a1b2c3d4" + "0" * 56,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return doc


@pytest.fixture
async def doc_no_optionals(session: AsyncSession, project: Project) -> Document:
    """A document with null optional fields and no metadata."""
    doc = Document(
        project_id=project.id,
        doc_type="prd",
        doc_id="prd",
        title="Product Requirements Document",
        status=None,
        owner=None,
        priority=None,
        story_points=None,
        epic=None,
        metadata_json=None,
        content="# PRD\n\nContent.",
        file_path="prd.md",
        file_hash="f" * 64,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return doc


# ---------------------------------------------------------------------------
# TC0159: GET document returns full content
# ---------------------------------------------------------------------------


class TestDocumentFullContent:
    """TC0159: Full content retrieval."""

    async def test_returns_200(
        self, client: AsyncClient, project: Project, doc_with_metadata: Document
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US0001-register-project"
        )
        assert resp.status_code == 200

    async def test_content_field_present(
        self, client: AsyncClient, project: Project, doc_with_metadata: Document
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US0001-register-project"
        )
        data = resp.json()
        assert "content" in data
        assert "# US0001" in data["content"]

    async def test_content_is_full_markdown(
        self, client: AsyncClient, project: Project, doc_with_metadata: Document
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US0001-register-project"
        )
        data = resp.json()
        assert data["content"] == doc_with_metadata.content


# ---------------------------------------------------------------------------
# TC0160: Response has all standard fields
# ---------------------------------------------------------------------------


class TestDocumentStandardFields:
    """TC0160: All standard fields present."""

    async def test_all_fields_present(
        self, client: AsyncClient, project: Project, doc_with_metadata: Document
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US0001-register-project"
        )
        data = resp.json()
        assert data["doc_id"] == "US0001-register-project"
        assert data["type"] == "story"
        assert data["title"] == "Register a New Project"
        assert data["status"] == "Done"
        assert data["owner"] == "Darren"
        assert data["priority"] == "P0"
        assert data["story_points"] == 5
        assert data["epic"] == "EP0001"


# ---------------------------------------------------------------------------
# TC0161: Metadata JSON contains non-standard frontmatter
# ---------------------------------------------------------------------------


class TestDocumentMetadata:
    """TC0161: Metadata JSON field."""

    async def test_metadata_contains_sprint(
        self, client: AsyncClient, project: Project, doc_with_metadata: Document
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US0001-register-project"
        )
        data = resp.json()
        assert data["metadata"]["sprint"] == "Sprint 1"
        assert data["metadata"]["created"] == "2026-02-17"


# ---------------------------------------------------------------------------
# TC0162: 404 for unknown doc_id
# ---------------------------------------------------------------------------


class TestUnknownDocId:
    """TC0162: 404 for unknown doc_id."""

    async def test_returns_404(
        self, client: AsyncClient, project: Project, doc_with_metadata: Document
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US9999-nonexistent"
        )
        assert resp.status_code == 404

    async def test_error_code(
        self, client: AsyncClient, project: Project, doc_with_metadata: Document
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US9999-nonexistent"
        )
        data = resp.json()
        assert data["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# TC0163: 404 for unknown project slug
# ---------------------------------------------------------------------------


class TestUnknownProjectSlug:
    """TC0163: 404 for unknown project slug."""

    async def test_returns_404(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/projects/nonexistent/documents/story/US0001-register-project"
        )
        assert resp.status_code == 404

    async def test_error_code(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/projects/nonexistent/documents/story/US0001-register-project"
        )
        data = resp.json()
        assert data["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# TC0164: 404 for type mismatch
# ---------------------------------------------------------------------------


class TestTypeMismatch:
    """TC0164: Type in URL must match doc_type."""

    async def test_wrong_type_returns_404(
        self, client: AsyncClient, project: Project, doc_with_metadata: Document
    ) -> None:
        # Doc is type "story" but we request "epic"
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/epic/US0001-register-project"
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TC0165: Null optional fields returned correctly
# ---------------------------------------------------------------------------


class TestNullOptionalFields:
    """TC0165: Null optional fields."""

    async def test_null_fields(
        self, client: AsyncClient, project: Project, doc_no_optionals: Document
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/prd/prd"
        )
        data = resp.json()
        assert data["status"] is None
        assert data["owner"] is None
        assert data["priority"] is None
        assert data["story_points"] is None
        assert data["epic"] is None


# ---------------------------------------------------------------------------
# TC0166: file_path and file_hash present
# ---------------------------------------------------------------------------


class TestFilePathAndHash:
    """TC0166: file_path and file_hash in response."""

    async def test_file_path_present(
        self, client: AsyncClient, project: Project, doc_with_metadata: Document
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US0001-register-project"
        )
        data = resp.json()
        assert data["file_path"] == "stories/US0001-register-project.md"

    async def test_file_hash_present(
        self, client: AsyncClient, project: Project, doc_with_metadata: Document
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US0001-register-project"
        )
        data = resp.json()
        assert len(data["file_hash"]) == 64


# ---------------------------------------------------------------------------
# TC0167: synced_at timestamp present
# ---------------------------------------------------------------------------


class TestSyncedAtTimestamp:
    """TC0167: synced_at timestamp."""

    async def test_synced_at_present(
        self, client: AsyncClient, project: Project, doc_with_metadata: Document
    ) -> None:
        from datetime import datetime

        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US0001-register-project"
        )
        data = resp.json()
        assert "synced_at" in data
        # Should be a valid ISO datetime
        datetime.fromisoformat(data["synced_at"])


# ---------------------------------------------------------------------------
# TC0168: Empty metadata returns null
# ---------------------------------------------------------------------------


class TestEmptyMetadata:
    """TC0168: Empty metadata returns null."""

    async def test_null_metadata_returns_null(
        self, client: AsyncClient, project: Project, doc_no_optionals: Document
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/prd/prd"
        )
        data = resp.json()
        assert data["metadata"] is None
