"""Pydantic schemas for the GitHub repository selector endpoints (CR-01KXAS75).

The access token is always carried in the request body, never in the URL.
"""

from pydantic import BaseModel, Field


class GitHubRepoItem(BaseModel):
    """A single repository the authenticated user can see."""

    full_name: str
    owner: str
    name: str
    private: bool
    default_branch: str
    description: str | None = None


class GitHubReposRequest(BaseModel):
    """Body for listing repositories. Token is here, not in the URL."""

    access_token: str = Field(..., min_length=1)
    search: str | None = None


class GitHubReposResponse(BaseModel):
    repositories: list[GitHubRepoItem]


class HasSdlcStudioRequest(BaseModel):
    """Body for the lazy per-repo sdlc-studio flag. Token is here, not in the URL."""

    access_token: str = Field(..., min_length=1)
    branch: str | None = None


class HasSdlcStudioResponse(BaseModel):
    has_sdlc_studio: bool
