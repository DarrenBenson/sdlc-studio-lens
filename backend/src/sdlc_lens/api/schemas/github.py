"""Pydantic schemas for the GitHub repository selector endpoints (CR-01KXAS75).

The credential is always carried in the request body, never in the URL. Since
CR-01KXAZX9 it may be supplied either as a raw ``access_token`` (a one-off browse
without registering anything) or as a ``connection_id`` naming a stored
connection, whose token the server resolves and decrypts. Exactly one of the two
must be present; the route rejects anything else with a 400 VALIDATION_ERROR.
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


class CredentialRequest(BaseModel):
    """Shared credential fields: exactly one of access_token / connection_id."""

    access_token: str | None = Field(None, min_length=1)
    connection_id: int | None = None

    def has_exactly_one_credential(self) -> bool:
        """True when precisely one of the two credential forms was supplied."""
        return (self.access_token is not None) != (self.connection_id is not None)


class GitHubReposRequest(CredentialRequest):
    """Body for listing repositories."""

    search: str | None = None


class GitHubReposResponse(BaseModel):
    repositories: list[GitHubRepoItem]


class HasSdlcStudioRequest(CredentialRequest):
    """Body for the lazy per-repo sdlc-studio flag."""

    branch: str | None = None


class HasSdlcStudioResponse(BaseModel):
    has_sdlc_studio: bool
