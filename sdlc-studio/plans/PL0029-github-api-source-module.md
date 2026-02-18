# PL0029: GitHub API Source Module - Implementation Plan

> **Status:** Done
> **Story:** [US0029: GitHub API Source Module](../stories/US0029-github-api-source-module.md)
> **Epic:** [EP0007: GitHub Repository Sync](../epics/EP0007-github-repository-sync.md)
> **Owner:** Darren
> **Created:** 2026-02-18
> **Language:** Python

## Overview

Create a standalone service module that fetches Markdown files from a GitHub repository using the GitHub REST API (v3). The module parses a repository URL to extract the owner and repo name, lists the directory tree via the Git Trees API, filters for `.md` files under a configurable subdirectory, and downloads each blob's content. The result is a dictionary keyed by relative path with `(hash, content_bytes)` tuples, matching the format the sync engine expects from local filesystem collection. The module handles authentication (optional Bearer token), rate limiting, and common error conditions with a typed exception hierarchy.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | URL parsing | `parse_github_url` extracts owner and repo from `https://github.com/owner/repo` and `https://github.com/owner/repo.git` |
| AC2 | File listing | `fetch_github_files` returns a dict of `{rel_path: (sha256_hash, content_bytes)}` for `.md` files |
| AC3 | Path filtering | Only files under the configured `repo_path` subdirectory are included |
| AC4 | Authentication | Optional access token is sent as `Authorization: Bearer {token}` header |
| AC5 | Error handling | `RepoNotFoundError` for 404, `AuthenticationError` for 401, `RateLimitError` for 403 with rate-limit headers |
| AC6 | Content decoding | Blob content is decoded from base64 and SHA-256 hashed locally |

---

## Technical Context

### Language & Framework
- **HTTP client:** httpx (async)
- **Hashing:** hashlib (SHA-256)
- **GitHub API version:** REST v3 (api.github.com)

### Relevant API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1` | List all files in the repository tree |
| `GET /repos/{owner}/{repo}/git/blobs/{sha}` | Fetch individual file content (base64 encoded) |

### Existing Patterns

The sync engine currently collects files via `_walk_md_files()` in `sync_engine.py` (line 51), which returns a list of `Path` objects. The sync loop builds a `dict[str, tuple[str, bytes]]` mapping `rel_path -> (file_hash, raw_bytes)`. The GitHub source module must produce the same dictionary shape so the sync engine can dispatch between local and GitHub sources transparently.

The hashing utility at `backend/src/sdlc_lens/utils/hashing.py` provides `compute_hash(data: bytes) -> str` which returns a hex-encoded SHA-256 digest.

### Dependencies
- **PL0028:** Project model must have `repo_url`, `repo_branch`, `repo_path`, `access_token` columns

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** The GitHub API interaction is entirely over HTTP, making it straightforward to test with mocked httpx responses. Each error condition (404, 401, 403) has a distinct exception type with clear assertions.

### Test Priority
1. URL parsing (owner/repo extraction, edge cases)
2. Successful file listing with mocked tree + blob responses
3. Path filtering (only files under repo_path)
4. Authentication header sent when token provided
5. Error handling (404, 401, 403, network errors)
6. Base64 content decoding and SHA-256 hashing

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Move httpx to main dependencies | `backend/pyproject.toml` | - | [ ] |
| 2 | Create GitHub source module | `backend/src/sdlc_lens/services/github_source.py` | 1 | [ ] |
| 3 | Write unit tests with mocked httpx | `backend/tests/services/test_github_source.py` | 2 | [ ] |

---

## Implementation Phases

### Phase 1: Dependency Update

**Goal:** Ensure httpx is available as a runtime dependency.

- [ ] Update `backend/pyproject.toml`:
  - Add `"httpx>=0.27.0"` to `dependencies` array (may already be in `dev-dependencies`; ensure it is in main `dependencies`)

**Files:**
- `backend/pyproject.toml`

### Phase 2: GitHub Source Module

**Goal:** Implement the full GitHub file-fetching service.

- [ ] Create `backend/src/sdlc_lens/services/github_source.py`:

```python
"""GitHub repository source - fetch Markdown files via GitHub REST API."""

from __future__ import annotations

import base64
import logging
import re
from typing import TYPE_CHECKING

import httpx

from sdlc_lens.utils.hashing import compute_hash

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_GITHUB_API = "https://api.github.com"
_URL_PATTERN = re.compile(
    r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/.]+?)(?:\.git)?/?$"
)


# --- Exception hierarchy ---

class GitHubSourceError(Exception):
    """Base exception for GitHub source operations."""

    def __init__(self, message: str = "GitHub source error"):
        self.message = message
        super().__init__(self.message)


class RepoNotFoundError(GitHubSourceError):
    """Repository does not exist or is not accessible."""

    def __init__(self, message: str = "Repository not found"):
        super().__init__(message)


class AuthenticationError(GitHubSourceError):
    """Invalid or expired access token."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class RateLimitError(GitHubSourceError):
    """GitHub API rate limit exceeded."""

    def __init__(self, message: str = "GitHub API rate limit exceeded"):
        super().__init__(message)


# --- Public functions ---

def parse_github_url(url: str) -> tuple[str, str]:
    """Extract owner and repo name from a GitHub URL.

    Accepts:
        https://github.com/owner/repo
        https://github.com/owner/repo.git
        https://github.com/owner/repo/

    Returns:
        Tuple of (owner, repo).

    Raises:
        ValueError: If the URL does not match the expected pattern.
    """
    match = _URL_PATTERN.match(url.strip())
    if not match:
        msg = f"Invalid GitHub URL: {url}"
        raise ValueError(msg)
    return match.group("owner"), match.group("repo")


def _build_headers(access_token: str | None = None) -> dict[str, str]:
    """Build HTTP headers for GitHub API requests."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _check_response(response: httpx.Response) -> None:
    """Check response status and raise typed exceptions."""
    if response.status_code == 401:
        raise AuthenticationError
    if response.status_code == 403:
        remaining = response.headers.get("x-ratelimit-remaining", "")
        if remaining == "0":
            raise RateLimitError
        raise AuthenticationError(
            "Access denied - check repository visibility and token permissions"
        )
    if response.status_code == 404:
        raise RepoNotFoundError


async def fetch_github_files(
    repo_url: str,
    branch: str,
    repo_path: str,
    access_token: str | None = None,
) -> dict[str, tuple[str, bytes]]:
    """Fetch Markdown files from a GitHub repository.

    Args:
        repo_url: Full GitHub repository URL.
        branch: Branch name to fetch from.
        repo_path: Subdirectory path within the repo (e.g. "sdlc-studio").
        access_token: Optional GitHub personal access token.

    Returns:
        Dict mapping relative path (relative to repo_path) to
        (sha256_hex_hash, raw_bytes) tuples.

    Raises:
        RepoNotFoundError: Repository does not exist (404).
        AuthenticationError: Invalid token (401) or access denied (403).
        RateLimitError: API rate limit exceeded (403 with x-ratelimit-remaining=0).
        GitHubSourceError: Other GitHub API errors.
    """
    owner, repo = parse_github_url(repo_url)
    headers = _build_headers(access_token)

    # Normalise repo_path: strip leading/trailing slashes
    prefix = repo_path.strip("/")
    if prefix:
        prefix += "/"

    async with httpx.AsyncClient(
        base_url=_GITHUB_API,
        headers=headers,
        timeout=30.0,
    ) as client:
        # Step 1: Get recursive tree
        tree_url = f"/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        tree_response = await client.get(tree_url)
        _check_response(tree_response)

        if tree_response.status_code != 200:
            msg = f"Unexpected status {tree_response.status_code} from tree API"
            raise GitHubSourceError(msg)

        tree_data = tree_response.json()
        tree_items = tree_data.get("tree", [])

        # Step 2: Filter for .md blobs under repo_path
        md_blobs: list[tuple[str, str]] = []  # (rel_path, blob_sha)
        for item in tree_items:
            if item.get("type") != "blob":
                continue
            path: str = item["path"]
            if not path.endswith(".md"):
                continue
            if prefix and not path.startswith(prefix):
                continue
            # Compute relative path (relative to repo_path)
            rel_path = path[len(prefix):] if prefix else path
            md_blobs.append((rel_path, item["sha"]))

        # Step 3: Fetch each blob's content
        result: dict[str, tuple[str, bytes]] = {}
        for rel_path, blob_sha in md_blobs:
            blob_url = f"/repos/{owner}/{repo}/git/blobs/{blob_sha}"
            blob_response = await client.get(blob_url)
            _check_response(blob_response)

            if blob_response.status_code != 200:
                logger.warning(
                    "Failed to fetch blob %s: status %d",
                    blob_sha,
                    blob_response.status_code,
                )
                continue

            blob_data = blob_response.json()
            content_b64 = blob_data.get("content", "")
            raw = base64.b64decode(content_b64)
            file_hash = compute_hash(raw)
            result[rel_path] = (file_hash, raw)

        logger.info(
            "Fetched %d Markdown files from %s/%s (branch: %s, path: %s)",
            len(result),
            owner,
            repo,
            branch,
            repo_path,
        )

    return result
```

**Design decisions:**
- **httpx.AsyncClient** with context manager ensures connections are properly closed.
- **`compute_hash`** reuses the existing utility to maintain consistency with local file hashing.
- **Relative paths** are computed by stripping the `repo_path` prefix, producing the same path format as `Path.relative_to(root)` does for local files.
- **Base64 decoding** is necessary because the GitHub Blobs API returns content in base64 encoding.
- **Rate limit detection** checks the `x-ratelimit-remaining` header to distinguish rate limiting from other 403 errors.

**Files:**
- `backend/src/sdlc_lens/services/github_source.py`

### Phase 3: Testing

**Goal:** Comprehensive unit tests with mocked HTTP responses.

- [ ] Create `backend/tests/services/test_github_source.py`:

**Test cases:**

| # | Test | Description |
|---|------|-------------|
| 1 | `test_parse_github_url_standard` | `https://github.com/owner/repo` returns `("owner", "repo")` |
| 2 | `test_parse_github_url_with_git_suffix` | `https://github.com/owner/repo.git` returns `("owner", "repo")` |
| 3 | `test_parse_github_url_with_trailing_slash` | `https://github.com/owner/repo/` returns `("owner", "repo")` |
| 4 | `test_parse_github_url_invalid` | `https://gitlab.com/foo/bar` raises `ValueError` |
| 5 | `test_fetch_files_success` | Mocked tree + blob responses return correct dict |
| 6 | `test_fetch_files_filters_by_path` | Only files under `repo_path` are returned |
| 7 | `test_fetch_files_filters_non_md` | `.py`, `.json` files are excluded |
| 8 | `test_fetch_files_with_token` | Authorization header includes Bearer token |
| 9 | `test_fetch_files_without_token` | No Authorization header when token is None |
| 10 | `test_fetch_files_repo_not_found` | 404 response raises `RepoNotFoundError` |
| 11 | `test_fetch_files_auth_error` | 401 response raises `AuthenticationError` |
| 12 | `test_fetch_files_rate_limit` | 403 with `x-ratelimit-remaining: 0` raises `RateLimitError` |
| 13 | `test_fetch_files_base64_decoding` | Content is correctly decoded from base64 |
| 14 | `test_fetch_files_hash_matches` | SHA-256 hash matches `compute_hash()` output |

**Mocking strategy:** Use `pytest-httpx` or `respx` to intercept httpx requests. Mock the tree endpoint to return a JSON structure with several items (mix of blob/tree types, md/non-md extensions, paths inside and outside `repo_path`). Mock blob endpoints to return base64-encoded Markdown content.

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | `test_parse_github_url_*` tests | `test_github_source.py` | Pending |
| AC2 | `test_fetch_files_success` verifies dict shape | `test_github_source.py` | Pending |
| AC3 | `test_fetch_files_filters_by_path` | `test_github_source.py` | Pending |
| AC4 | `test_fetch_files_with_token` checks header | `test_github_source.py` | Pending |
| AC5 | `test_fetch_files_repo_not_found`, `_auth_error`, `_rate_limit` | `test_github_source.py` | Pending |
| AC6 | `test_fetch_files_base64_decoding` | `test_github_source.py` | Pending |

---

## Edge Case Handling

| # | Edge Case | Handling Strategy | Phase |
|---|-----------|-------------------|-------|
| 1 | Repository with thousands of files | Tree API returns all items in one call; only `.md` files under `repo_path` are processed further | Phase 2 |
| 2 | Truncated tree response | GitHub returns `truncated: true` when tree > 100k items; log a warning, process available items | Phase 2 |
| 3 | Empty repository (no files) | Tree returns empty array; function returns empty dict | Phase 2 |
| 4 | repo_path does not exist in tree | No files match the prefix; function returns empty dict (not an error) | Phase 2 |
| 5 | Blob with non-UTF-8 content | Raw bytes are stored as-is; decoding is the sync engine's responsibility | Phase 2 |
| 6 | Network timeout | httpx raises `TimeoutException`; propagates as-is (sync engine catches generic exceptions) | Phase 2 |
| 7 | repo_path with leading/trailing slashes | Normalised by stripping before comparison | Phase 2 |

**Coverage:** 7/7 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| GitHub API rate limit (60/hr unauthenticated, 5000/hr authenticated) | High | Encourage token use for private repos; document rate limits |
| Large repos with many .md files (N+1 blob requests) | Medium | Each blob is a separate request; acceptable for typical SDLC repos (< 100 files). Future optimisation: use archive API for bulk download |
| httpx not in main dependencies | Low | Task 1 explicitly moves httpx from dev to main dependencies |
| GitHub API changes | Low | Pin `X-GitHub-Api-Version: 2022-11-28` header for stability |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit tests written and passing (all 14 test cases)
- [ ] Edge cases handled
- [ ] httpx in main dependencies
- [ ] Exception hierarchy documented
- [ ] Ruff linting passes

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-18 | Darren | Initial plan created |
