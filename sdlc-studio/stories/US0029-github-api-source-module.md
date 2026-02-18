# US0029: GitHub API Source Module

> **Status:** Done
> **Epic:** [EP0007: Git Repository Sync](../epics/EP0007-git-repository-sync.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-18

## User Story

**As a** SDLC Developer (Darren)
**I want** a module that fetches SDLC documents from a GitHub repository via the GitHub API
**So that** the sync engine can ingest Markdown files from remote repositories without cloning them locally

## Context

### Persona Reference
**Darren** - Hosts some SDLC projects in GitHub repositories and wants to track them in the dashboard without manual file copying.
[Full persona details](../personas.md#darren)

### Background
The GitHub API provides endpoints to list repository file trees and fetch individual blob contents. The Git Trees API (`GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1`) returns all files in a repository in a single request. Individual blob content is fetched via `GET /repos/{owner}/{repo}/git/blobs/{sha}` and returned as base64-encoded data. This module wraps these two endpoints using httpx (async HTTP client), filters for `.md` files within the configured `repo_path`, computes SHA-256 hashes of the decoded content, and returns the same `dict[str, tuple[str, bytes]]` format used by the local filesystem walker. This ensures the sync engine can consume files from either source identically.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Tech Stack | Python 3.12 async | httpx AsyncClient for HTTP calls |
| TRD | Architecture | Sync engine expects dict[str, tuple[str, bytes]] | Output format must match local walker |
| PRD | Security | Access tokens handled securely | Bearer token in Authorization header; never logged |
| PRD | KPI | Sync completes within reasonable time | Efficient API usage; minimise requests |

---

## Acceptance Criteria

### AC1: Fetch from public repository
- **Given** a public GitHub repository URL and branch
- **When** I call the GitHub source module with no access token
- **Then** it returns a dict of relative file paths to (sha256_hash, content_bytes) for all `.md` files within repo_path

### AC2: Fetch from private repository
- **Given** a private GitHub repository URL, branch, and valid access token
- **When** I call the GitHub source module with the token
- **Then** it returns the same dict format with `.md` files from the private repository

### AC3: URL parsing
- **Given** a URL like `https://github.com/owner/repo` or `https://github.com/owner/repo.git`
- **When** the module parses it
- **Then** it correctly extracts `owner` and `repo` (stripping any `.git` suffix)

### AC4: Path filtering
- **Given** a repository with files in multiple directories
- **When** repo_path is set to `sdlc-studio`
- **Then** only `.md` files under `sdlc-studio/` are returned, with paths relative to repo_path

### AC5: Error handling - repository not found
- **Given** a URL pointing to a non-existent repository
- **When** the module attempts to fetch the tree
- **Then** it raises a descriptive error indicating the repository was not found (HTTP 404)

### AC6: Error handling - authentication failure
- **Given** an invalid or expired access token
- **When** the module attempts to fetch from a private repository
- **Then** it raises a descriptive error indicating authentication failed (HTTP 401/403)

### AC7: Error handling - rate limit
- **Given** the GitHub API returns HTTP 403 with rate limit headers
- **When** the module encounters this response
- **Then** it raises a descriptive error indicating rate limiting, including the reset time if available

### AC8: httpx dependency added
- **Given** the backend pyproject.toml
- **When** I inspect the runtime dependencies
- **Then** httpx is listed as a dependency

---

## Scope

### In Scope
- New module `services/github_source.py`
- httpx AsyncClient for GitHub API requests
- Git Trees API to list repository contents
- Git Blobs API to fetch file content (base64 decoded)
- SHA-256 hash computation of file content
- Owner/repo extraction from GitHub URL
- Optional Bearer token authentication
- Error handling for 404, 401/403, rate limiting, and network errors
- Adding httpx to pyproject.toml dependencies

### Out of Scope
- Git clone or local checkout
- GitHub webhook integration
- GitHub App authentication (only personal access tokens)
- Caching of API responses
- Pagination of tree results (recursive tree returns all in one request)
- Support for non-GitHub Git hosts (GitLab, Bitbucket)

---

## Technical Notes

### Module Structure
```python
# services/github_source.py

import hashlib
import base64
from urllib.parse import urlparse

import httpx


class GitHubSourceError(Exception):
    """Base error for GitHub source operations."""


class GitHubRepoNotFoundError(GitHubSourceError):
    """Repository not found (404)."""


class GitHubAuthError(GitHubSourceError):
    """Authentication failed (401/403)."""


class GitHubRateLimitError(GitHubSourceError):
    """Rate limit exceeded."""


def parse_github_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL."""


async def collect_github_files(
    repo_url: str,
    branch: str = "main",
    repo_path: str = "sdlc-studio",
    access_token: str | None = None,
) -> dict[str, tuple[str, bytes]]:
    """Fetch .md files from a GitHub repo.

    Returns dict mapping relative_path -> (sha256_hex, content_bytes).
    """
```

### API Endpoints Used
1. **Tree listing:** `GET https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1`
   - Returns all files with their paths, modes, types, and SHAs
   - Filter for `type == "blob"` and path ending in `.md` within `repo_path`

2. **Blob content:** `GET https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}`
   - Returns `{ "content": "<base64>", "encoding": "base64" }`
   - Decode with `base64.b64decode()`

### Headers
```python
headers = {
    "Accept": "application/vnd.github.v3+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if access_token:
    headers["Authorization"] = f"Bearer {access_token}"
```

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Repository URL with trailing `.git` | Stripped before parsing |
| Repository URL with trailing slash | Handled gracefully |
| repo_path with leading/trailing slashes | Normalised before filtering |
| Empty repository (no files) | Returns empty dict |
| No `.md` files in repo_path | Returns empty dict |
| Very large repository (thousands of files) | Only `.md` blobs fetched; tree listing is a single request |
| Binary file with `.md` extension | Content decoded as bytes; parser will handle downstream |
| Network timeout | httpx.TimeoutException raised; caught and wrapped |
| GitHub API returns 500 | Wrapped as GitHubSourceError with status code |
| access_token is empty string | Treated as no token (not sent in header) |

---

## Test Scenarios

- [ ] parse_github_url extracts owner/repo from standard URL
- [ ] parse_github_url handles .git suffix
- [ ] parse_github_url handles trailing slash
- [ ] parse_github_url raises error for non-GitHub URL
- [ ] collect_github_files returns correct dict format
- [ ] collect_github_files filters to .md files only
- [ ] collect_github_files filters to files within repo_path
- [ ] collect_github_files returns paths relative to repo_path
- [ ] SHA-256 hash matches content
- [ ] Authorization header included when token provided
- [ ] Authorization header absent when no token
- [ ] 404 response raises GitHubRepoNotFoundError
- [ ] 401 response raises GitHubAuthError
- [ ] 403 with rate limit raises GitHubRateLimitError
- [ ] Network timeout raises descriptive error
- [ ] httpx added to pyproject.toml

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0028](US0028-database-schema-github-source.md) | Schema | Project model with repo_url, repo_branch, repo_path, access_token fields | Not Started |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| httpx | Library | To be added |
| GitHub API v3 | External API | Available |

---

## Estimation

**Story Points:** {{TBD}}
**Complexity:** High

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-18 | Claude | Initial story creation from EP0007 |
