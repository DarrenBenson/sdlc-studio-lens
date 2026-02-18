"""Integration tests for GET /api/v1/projects/{slug}/documents/{type}/{docId}/related.

Test cases: TC0358-TC0370 from US0034.
Also covers AC7 (DocumentDetail story field) and AC8 (DocumentListItem epic/story fields).
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
    p = Project(slug="reltest", name="Relationship Test", sdlc_path="/tmp/reltest")
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


@pytest.fixture
async def hierarchy(session: AsyncSession, project: Project) -> dict[str, Document]:
    """Seed a full hierarchy: epic -> 3 stories -> plans/test-specs.

    EP0007 (epic)
    ├── US0028 (story, epic=EP0007)
    │   ├── PL0028 (plan, story=US0028, epic=EP0007)
    │   └── TS0028 (test-spec, story=US0028, epic=EP0007)
    ├── US0029 (story, epic=EP0007)
    └── US0030 (story, epic=EP0007)

    Also includes a top-level PRD with no parents/children references.
    """
    now = datetime.datetime.now(tz=datetime.UTC)
    docs = {}

    def _doc(doc_type, doc_id, title, epic=None, story=None, **kw):
        d = Document(
            project_id=project.id,
            doc_type=doc_type,
            doc_id=doc_id,
            title=title,
            status=kw.get("status", "Done"),
            owner="Darren",
            epic=epic,
            story=story,
            content=f"# {title}",
            file_path=f"{doc_type}s/{doc_id}.md",
            file_hash=f"{doc_id:<64}"[:64],
            synced_at=now,
        )
        docs[doc_id.split("-")[0]] = d
        return d

    all_docs = [
        _doc("prd", "prd", "Product Requirements"),
        _doc("epic", "EP0007-git-repo-sync", "Git Repository Sync"),
        _doc("story", "US0028-database-schema", "Database Schema", epic="EP0007"),
        _doc("story", "US0029-github-api", "GitHub API Source", epic="EP0007"),
        _doc("story", "US0030-sync-dispatch", "Sync Engine Dispatch", epic="EP0007"),
        _doc(
            "plan",
            "PL0028-database-plan",
            "Database Plan",
            story="US0028",
            epic="EP0007",
        ),
        _doc(
            "test-spec",
            "TS0028-database-tests",
            "Database Tests",
            story="US0028",
            epic="EP0007",
        ),
    ]
    session.add_all(all_docs)
    await session.commit()
    for d in all_docs:
        await session.refresh(d)

    return docs


# ---------------------------------------------------------------------------
# TC0358: GET /related returns 200 with correct parents and children
# ---------------------------------------------------------------------------


class TestRelatedEndpointBasic:
    """TC0358: Basic endpoint behaviour."""

    async def test_returns_200(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US0028-database-schema/related"
        )
        assert resp.status_code == 200

    async def test_response_has_expected_fields(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US0028-database-schema/related"
        )
        data = resp.json()
        assert "doc_id" in data
        assert "type" in data
        assert "title" in data
        assert "parents" in data
        assert "children" in data


# ---------------------------------------------------------------------------
# TC0359: Story's parents include its epic
# ---------------------------------------------------------------------------


class TestStoryParents:
    """TC0359: A story's parents include its epic."""

    async def test_story_has_epic_parent(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US0028-database-schema/related"
        )
        data = resp.json()
        assert len(data["parents"]) == 1
        assert data["parents"][0]["doc_id"] == "EP0007-git-repo-sync"
        assert data["parents"][0]["type"] == "epic"


# ---------------------------------------------------------------------------
# TC0360: Plan's parents include its story and grandparent epic
# ---------------------------------------------------------------------------


class TestPlanParents:
    """TC0360: A plan's parents include story (nearest) then epic."""

    async def test_plan_has_story_and_epic_parents(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/plan/PL0028-database-plan/related"
        )
        data = resp.json()
        assert len(data["parents"]) == 2
        # Nearest ancestor first
        assert data["parents"][0]["doc_id"] == "US0028-database-schema"
        assert data["parents"][0]["type"] == "story"
        assert data["parents"][1]["doc_id"] == "EP0007-git-repo-sync"
        assert data["parents"][1]["type"] == "epic"


# ---------------------------------------------------------------------------
# TC0361: Epic's children include its stories
# ---------------------------------------------------------------------------


class TestEpicChildren:
    """TC0361: An epic's children include its stories."""

    async def test_epic_has_story_children(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/epic/EP0007-git-repo-sync/related"
        )
        data = resp.json()
        child_ids = [c["doc_id"] for c in data["children"]]
        assert "US0028-database-schema" in child_ids
        assert "US0029-github-api" in child_ids
        assert "US0030-sync-dispatch" in child_ids
        assert len(data["children"]) == 3


# ---------------------------------------------------------------------------
# TC0362: Story's children include its plans and test-specs
# ---------------------------------------------------------------------------


class TestStoryChildren:
    """TC0362: A story's children include plans and test-specs."""

    async def test_story_has_plan_and_spec_children(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US0028-database-schema/related"
        )
        data = resp.json()
        child_ids = [c["doc_id"] for c in data["children"]]
        assert "PL0028-database-plan" in child_ids
        assert "TS0028-database-tests" in child_ids
        assert len(data["children"]) == 2


# ---------------------------------------------------------------------------
# TC0363: Leaf document (plan) has empty children
# ---------------------------------------------------------------------------


class TestLeafDocumentChildren:
    """TC0363: A plan (leaf node) has no children."""

    async def test_plan_has_no_children(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/plan/PL0028-database-plan/related"
        )
        data = resp.json()
        assert data["children"] == []


# ---------------------------------------------------------------------------
# TC0364: Top-level document (epic) has empty parents
# ---------------------------------------------------------------------------


class TestTopLevelDocumentParents:
    """TC0364: An epic has no parents."""

    async def test_epic_has_no_parents(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/epic/EP0007-git-repo-sync/related"
        )
        data = resp.json()
        assert data["parents"] == []


# ---------------------------------------------------------------------------
# TC0365: PRD has empty parents and children
# ---------------------------------------------------------------------------


class TestPrdRelationships:
    """TC0365: A PRD has no parents and no children."""

    async def test_prd_has_no_parents_or_children(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/prd/prd/related"
        )
        data = resp.json()
        assert data["parents"] == []
        assert data["children"] == []


# ---------------------------------------------------------------------------
# TC0366: Missing parent reference returns partial chain
# ---------------------------------------------------------------------------


class TestMissingParentReference:
    """TC0366: If a referenced parent doesn't exist, chain is partial."""

    async def test_missing_story_parent(
        self, session: AsyncSession, project: Project, client: AsyncClient
    ) -> None:
        """Plan references US9999 which doesn't exist."""
        now = datetime.datetime.now(tz=datetime.UTC)
        doc = Document(
            project_id=project.id,
            doc_type="plan",
            doc_id="PL9999-orphan-plan",
            title="Orphan Plan",
            status="Done",
            story="US9999",
            epic="EP0007",
            content="# Orphan Plan",
            file_path="plans/PL9999-orphan-plan.md",
            file_hash="z" * 64,
            synced_at=now,
        )
        session.add(doc)
        await session.commit()

        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/plan/PL9999-orphan-plan/related"
        )
        data = resp.json()
        # Story US9999 doesn't exist, so parent chain is empty (no error)
        assert data["parents"] == []


# ---------------------------------------------------------------------------
# TC0367: Non-existent document returns 404
# ---------------------------------------------------------------------------


class TestDocumentNotFound:
    """TC0367: 404 for non-existent document."""

    async def test_returns_404(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US9999-nonexistent/related"
        )
        assert resp.status_code == 404

    async def test_error_format(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US9999-nonexistent/related"
        )
        data = resp.json()
        assert data["error"]["code"] == "NOT_FOUND"
        assert "story/US9999" in data["error"]["message"]


# ---------------------------------------------------------------------------
# TC0368: Non-existent project returns 404
# ---------------------------------------------------------------------------


class TestProjectNotFound:
    """TC0368: 404 for non-existent project."""

    async def test_returns_404(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/projects/nonexistent/documents/story/US0028/related"
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TC0369: Children sorted by type then doc_id
# ---------------------------------------------------------------------------


class TestChildrenSortOrder:
    """TC0369: Children sorted by type then doc_id."""

    async def test_children_sort_order(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/story/US0028-database-schema/related"
        )
        data = resp.json()
        children = data["children"]
        # plan comes before test-spec alphabetically
        types = [c["type"] for c in children]
        assert types == sorted(types)


# ---------------------------------------------------------------------------
# TC0370: DocumentDetail response includes story field (AC7)
# ---------------------------------------------------------------------------


class TestDocumentDetailStoryField:
    """TC0370: DocumentDetail includes story field."""

    async def test_detail_has_story_field(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/plan/PL0028-database-plan"
        )
        data = resp.json()
        assert "story" in data
        assert data["story"] == "US0028"

    async def test_detail_story_null_when_absent(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents/epic/EP0007-git-repo-sync"
        )
        data = resp.json()
        assert "story" in data
        assert data["story"] is None


# ---------------------------------------------------------------------------
# TC0371: DocumentListItem includes epic and story fields (AC8)
# ---------------------------------------------------------------------------


class TestDocumentListEpicStoryFields:
    """TC0371: DocumentListItem includes epic and story fields."""

    async def test_list_items_have_epic_and_story(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents?type=plan"
        )
        data = resp.json()
        assert data["total"] >= 1
        item = data["items"][0]
        assert "epic" in item
        assert "story" in item

    async def test_list_story_has_epic_populated(
        self, client: AsyncClient, project: Project, hierarchy: dict
    ) -> None:
        resp = await client.get(
            f"/api/v1/projects/{project.slug}/documents?type=story"
        )
        data = resp.json()
        # All stories in hierarchy have epic=EP0007
        for item in data["items"]:
            assert item["epic"] == "EP0007"
