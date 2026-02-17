"""Integration tests for GET/PUT/DELETE /api/v1/projects endpoints.

Test cases: TC0019-TC0034 from TS0002.
"""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from sdlc_lens.db.models.document import Document


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def sdlc_dir(tmp_path: Path) -> Path:
    d = tmp_path / "sdlc-studio"
    d.mkdir()
    return d


@pytest.fixture
def sdlc_dir_2(tmp_path: Path) -> Path:
    d = tmp_path / "sdlc-lens"
    d.mkdir()
    return d


@pytest.fixture
def sdlc_dir_3(tmp_path: Path) -> Path:
    d = tmp_path / "sdlc-new"
    d.mkdir()
    return d


async def _register(client: AsyncClient, name: str, sdlc_path: Path) -> dict:
    """Helper to register a project and return the response data."""
    resp = await client.post(
        "/api/v1/projects",
        json={"name": name, "sdlc_path": str(sdlc_path)},
    )
    assert resp.status_code == 201
    return resp.json()


# TC0019: List projects returns all registered projects
class TestListProjects:
    async def test_returns_200_with_all_projects(
        self, client: AsyncClient, sdlc_dir: Path, sdlc_dir_2: Path
    ) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)
        await _register(client, "SDLCLens", sdlc_dir_2)

        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_projects_contain_required_fields(
        self, client: AsyncClient, sdlc_dir: Path
    ) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        response = await client.get("/api/v1/projects")
        data = response.json()
        project = data[0]
        for field in ("slug", "name", "sdlc_path", "sync_status", "document_count", "created_at"):
            assert field in project


# TC0020: List projects returns empty array when none registered
class TestListProjectsEmpty:
    async def test_returns_empty_array(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        assert response.json() == []


# TC0021: List projects includes document_count field
class TestListProjectsDocumentCount:
    async def test_document_count_is_integer(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        response = await client.get("/api/v1/projects")
        data = response.json()
        assert isinstance(data[0]["document_count"], int)
        assert data[0]["document_count"] >= 0


# TC0022: Get project by slug returns project details
class TestGetProject:
    async def test_returns_200_with_project(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        response = await client.get("/api/v1/projects/homelabcmd")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "homelabcmd"
        assert data["name"] == "HomelabCmd"

    async def test_contains_stats_fields(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        response = await client.get("/api/v1/projects/homelabcmd")
        data = response.json()
        assert "sync_status" in data
        assert "document_count" in data


# TC0024: Update project name successfully
class TestUpdateProjectName:
    async def test_updates_name(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        response = await client.put(
            "/api/v1/projects/homelabcmd",
            json={"name": "HomelabCmd v2"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "HomelabCmd v2"
        assert data["slug"] == "homelabcmd"


# TC0025: Update project sdlc_path with path validation
class TestUpdateProjectPath:
    async def test_updates_path(
        self, client: AsyncClient, sdlc_dir: Path, sdlc_dir_3: Path
    ) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        response = await client.put(
            "/api/v1/projects/homelabcmd",
            json={"sdlc_path": str(sdlc_dir_3)},
        )
        assert response.status_code == 200
        data = response.json()
        assert str(sdlc_dir_3) in data["sdlc_path"]


# TC0026: Update with non-existent path returns 400
class TestUpdateInvalidPath:
    async def test_invalid_path_returns_400(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        response = await client.put(
            "/api/v1/projects/homelabcmd",
            json={"sdlc_path": "/nonexistent/path"},
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "PATH_NOT_FOUND"

    async def test_project_unchanged_after_invalid_update(
        self, client: AsyncClient, sdlc_dir: Path
    ) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        await client.put(
            "/api/v1/projects/homelabcmd",
            json={"sdlc_path": "/nonexistent/path"},
        )

        response = await client.get("/api/v1/projects/homelabcmd")
        data = response.json()
        assert str(sdlc_dir) in data["sdlc_path"]


# TC0027: Update with only name (no sdlc_path)
class TestUpdateNameOnly:
    async def test_partial_update_name(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        response = await client.put(
            "/api/v1/projects/homelabcmd",
            json={"name": "New Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert str(sdlc_dir) in data["sdlc_path"]


# TC0028: Update with empty body returns 422
class TestUpdateEmptyBody:
    async def test_empty_body_returns_422(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        response = await client.put("/api/v1/projects/homelabcmd", json={})
        assert response.status_code == 422


# TC0029: Delete project returns 204
class TestDeleteProject:
    async def test_returns_204(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        response = await client.delete("/api/v1/projects/homelabcmd")
        assert response.status_code == 204

    async def test_project_gone_after_delete(self, client: AsyncClient, sdlc_dir: Path) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        await client.delete("/api/v1/projects/homelabcmd")
        response = await client.get("/api/v1/projects/homelabcmd")
        assert response.status_code == 404


# TC0030: Delete cascades to documents table
class TestDeleteCascade:
    async def test_documents_removed_on_project_delete(
        self, client: AsyncClient, sdlc_dir: Path, engine
    ) -> None:
        project_data = await _register(client, "HomelabCmd", sdlc_dir)

        # Insert documents directly via the DB
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as sess:
            from sqlalchemy import select

            from sdlc_lens.db.models.project import Project

            result = await sess.execute(
                select(Project).where(Project.slug == project_data["slug"])
            )
            project = result.scalar_one()

            doc = Document(
                project_id=project.id,
                doc_type="story",
                doc_id="US0001",
                title="Test Story",
                content="# Test",
                file_path="stories/US0001.md",
                file_hash="abc123",
            )
            sess.add(doc)
            await sess.commit()

        # Delete the project
        response = await client.delete("/api/v1/projects/homelabcmd")
        assert response.status_code == 204

        # Verify documents are gone
        async with session_factory() as sess:
            from sqlalchemy import func, select

            count = await sess.execute(select(func.count()).select_from(Document))
            assert count.scalar_one() == 0


# TC0031: Delete project that is currently syncing
class TestDeleteDuringSyncing:
    async def test_delete_allowed_during_sync(
        self, client: AsyncClient, sdlc_dir: Path, engine
    ) -> None:
        await _register(client, "HomelabCmd", sdlc_dir)

        # Set sync_status to syncing directly
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as sess:
            from sqlalchemy import update

            from sdlc_lens.db.models.project import Project

            await sess.execute(
                update(Project).where(Project.slug == "homelabcmd").values(sync_status="syncing")
            )
            await sess.commit()

        response = await client.delete("/api/v1/projects/homelabcmd")
        assert response.status_code == 204


# TC0032: GET unknown slug returns 404
class TestGetNotFound:
    async def test_returns_404(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/projects/nonexistent")
        assert response.status_code == 404

    async def test_error_code(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/projects/nonexistent")
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
        assert "Project not found" in data["error"]["message"]


# TC0033: PUT unknown slug returns 404
class TestPutNotFound:
    async def test_returns_404(self, client: AsyncClient) -> None:
        response = await client.put("/api/v1/projects/nonexistent", json={"name": "Test"})
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"


# TC0034: DELETE unknown slug returns 404
class TestDeleteNotFound:
    async def test_returns_404(self, client: AsyncClient) -> None:
        response = await client.delete("/api/v1/projects/nonexistent")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"
