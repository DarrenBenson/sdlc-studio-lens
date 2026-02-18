"""GitHub source schema and model tests.

Test cases: TC0290-TC0293 from TS0028, TC0324-TC0325, TC0328-TC0330 from TS0031.
"""

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.api.schemas.projects import ProjectCreate, ProjectResponse, mask_token
from sdlc_lens.db.models.project import Project

# ---------------------------------------------------------------------------
# TC0324-TC0325: Token masking
# ---------------------------------------------------------------------------


class TestMaskToken:
    # TC0324: Token masking shows "****" + last 4 chars
    def test_masks_long_token(self) -> None:
        assert mask_token("ghp_abcdef1234567890") == "****7890"

    def test_masks_short_token(self) -> None:
        assert mask_token("abc") == "****"

    def test_masks_exactly_four_chars(self) -> None:
        assert mask_token("abcd") == "****"

    def test_masks_five_chars(self) -> None:
        assert mask_token("abcde") == "****bcde"

    # TC0325: Token masking returns null for null token
    def test_returns_none_for_none(self) -> None:
        assert mask_token(None) is None

    def test_returns_none_for_empty_string(self) -> None:
        assert mask_token("") is None


# ---------------------------------------------------------------------------
# TC0328-TC0329: ProjectCreate conditional validation
# ---------------------------------------------------------------------------


class TestProjectCreateValidation:
    # TC0328: ProjectCreate validation rejects github without repo_url
    def test_github_without_repo_url_raises(self) -> None:
        with pytest.raises(ValidationError, match="repo_url"):
            ProjectCreate(name="Test", source_type="github")

    # TC0329: ProjectCreate validation rejects local without sdlc_path
    def test_local_without_sdlc_path_raises(self) -> None:
        with pytest.raises(ValidationError, match="sdlc_path"):
            ProjectCreate(name="Test", source_type="local")

    def test_local_with_sdlc_path_succeeds(self) -> None:
        result = ProjectCreate(name="Test", source_type="local", sdlc_path="/data/test")
        assert result.source_type == "local"
        assert result.sdlc_path == "/data/test"

    def test_github_with_repo_url_succeeds(self) -> None:
        result = ProjectCreate(
            name="Test",
            source_type="github",
            repo_url="https://github.com/owner/repo",
        )
        assert result.source_type == "github"
        assert result.repo_url == "https://github.com/owner/repo"
        assert result.repo_branch == "main"
        assert result.repo_path == "sdlc-studio"


# ---------------------------------------------------------------------------
# TC0330: ProjectResponse includes source_type and repo fields
# ---------------------------------------------------------------------------


class TestProjectResponse:
    def test_github_project_response(self) -> None:
        resp = ProjectResponse(
            slug="test-github",
            name="Test GitHub",
            sdlc_path=None,
            source_type="github",
            repo_url="https://github.com/owner/repo",
            repo_branch="develop",
            repo_path="docs",
            masked_token="****1234",
            sync_status="never_synced",
            last_synced_at=None,
            document_count=0,
            created_at="2026-02-18T00:00:00Z",
        )
        data = resp.model_dump()
        assert data["source_type"] == "github"
        assert data["repo_url"] == "https://github.com/owner/repo"
        assert data["repo_branch"] == "develop"
        assert data["repo_path"] == "docs"
        assert data["masked_token"] == "****1234"
        assert data["sdlc_path"] is None


# ---------------------------------------------------------------------------
# TC0290-TC0293: Project model field acceptance and defaults
# ---------------------------------------------------------------------------


class TestProjectModel:
    # TC0290: Project model accepts github source_type fields
    async def test_github_fields_accepted(self, session: AsyncSession) -> None:
        project = Project(
            slug="test-github",
            name="Test GitHub",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            repo_branch="develop",
            repo_path="docs",
            access_token="ghp_xxxx1234",
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        assert project.source_type == "github"
        assert project.repo_url == "https://github.com/owner/repo"
        assert project.repo_branch == "develop"
        assert project.repo_path == "docs"
        assert project.access_token == "ghp_xxxx1234"

    # TC0291: sdlc_path is nullable for github projects
    async def test_sdlc_path_nullable(self, session: AsyncSession) -> None:
        project = Project(
            slug="test-null-path",
            name="Null Path",
            source_type="github",
            repo_url="https://github.com/owner/repo",
            sdlc_path=None,
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        assert project.sdlc_path is None

    # TC0292: source_type defaults to "local" when not specified
    async def test_source_type_defaults_to_local(self, session: AsyncSession) -> None:
        project = Project(
            slug="test-default",
            name="Default Source",
            sdlc_path="/data/test",
        )
        session.add(project)
        await session.commit()

        # Re-fetch to get server default
        await session.refresh(project)
        assert project.source_type == "local"

    # TC0293: repo_branch defaults to "main" when not specified
    async def test_repo_branch_defaults_to_main(self, session: AsyncSession) -> None:
        project = Project(
            slug="test-branch",
            name="Branch Default",
            sdlc_path="/data/test",
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        assert project.repo_branch == "main"
