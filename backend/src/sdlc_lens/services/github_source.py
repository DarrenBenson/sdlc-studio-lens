"""GitHub API source - fetch .md files from a GitHub repository."""

from __future__ import annotations

import io
import logging
import tarfile
from urllib.parse import urlparse

import httpx

from sdlc_lens.utils.hashing import compute_hash

logger = logging.getLogger(__name__)

_API_BASE = "https://api.github.com"
_DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_TARBALL_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


class GitHubSourceError(Exception):
    """Base error for GitHub source operations."""

    def __init__(self, message: str = "GitHub source error"):
        self.message = message
        super().__init__(self.message)


class RepoNotFoundError(GitHubSourceError):
    """Repository does not exist or is not accessible."""

    def __init__(self, message: str = "Repository not found"):
        super().__init__(message)


class AuthenticationError(GitHubSourceError):
    """Access token is invalid or missing for a private repository."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class RateLimitError(GitHubSourceError):
    """GitHub API rate limit exceeded."""

    def __init__(self, message: str = "GitHub API rate limit exceeded"):
        super().__init__(message)


def parse_github_url(url: str) -> tuple[str, str]:
    """Extract owner and repo name from a GitHub URL.

    Accepts URLs like:
        https://github.com/owner/repo
        https://github.com/owner/repo.git
        https://github.com/owner/repo/

    Returns:
        Tuple of (owner, repo).

    Raises:
        ValueError: If the URL is not a valid GitHub repository URL.
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        msg = f"Invalid URL: {url}"
        raise ValueError(msg)

    # Strip leading/trailing slashes, remove .git suffix
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]

    parts = path.split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        msg = f"Cannot extract owner/repo from URL: {url}"
        raise ValueError(msg)

    return parts[0], parts[1]


def _build_headers(access_token: str | None) -> dict[str, str]:
    """Build HTTP headers for GitHub API requests."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _handle_error_response(response: httpx.Response) -> None:
    """Raise appropriate error for non-2xx responses."""
    if response.status_code == 404:
        raise RepoNotFoundError(
            f"Repository not found (HTTP {response.status_code})"
        )
    if response.status_code == 401:
        raise AuthenticationError(
            "Authentication failed - check your access token"
        )
    if response.status_code == 403:
        # Check if rate limited
        remaining = response.headers.get("x-ratelimit-remaining", "")
        if remaining == "0":
            raise RateLimitError(
                "GitHub API rate limit exceeded - use an access token for higher limits"
            )
        raise AuthenticationError(
            "Access denied (HTTP 403) - repository may be private"
        )
    if response.status_code >= 400:
        raise GitHubSourceError(
            f"GitHub API error: HTTP {response.status_code}"
        )


async def fetch_github_files(
    repo_url: str,
    branch: str = "main",
    repo_path: str = "sdlc-studio",
    access_token: str | None = None,
    timeout: httpx.Timeout | None = None,
) -> dict[str, tuple[str, bytes]]:
    """Fetch .md files from a GitHub repository via tarball download.

    Downloads the repository as a tarball (single API request), then
    extracts .md files from the specified subdirectory. Returns the same
    dict format as the local filesystem walker:
    {relative_path: (sha256_hash, raw_bytes)}.

    This approach uses 1 API call instead of N+1 (tree + per-blob),
    staying well within unauthenticated rate limits (60/hour).

    Args:
        repo_url: Full GitHub repository URL.
        branch: Branch name to fetch from.
        repo_path: Subdirectory path within the repo.
        access_token: Optional PAT for private repositories.
        timeout: Optional httpx timeout override.

    Returns:
        Dict mapping relative file paths to (hash, content) tuples.

    Raises:
        GitHubSourceError: On API errors.
        RepoNotFoundError: If repo does not exist.
        AuthenticationError: If token is invalid.
        RateLimitError: If rate limit is exceeded.
    """
    owner, repo = parse_github_url(repo_url)
    headers = _build_headers(access_token)
    effective_timeout = timeout or _TARBALL_TIMEOUT

    # Normalise repo_path: strip leading/trailing slashes
    repo_path = repo_path.strip("/")

    async with httpx.AsyncClient(
        headers=headers,
        timeout=effective_timeout,
        follow_redirects=True,
    ) as client:
        tarball_url = f"{_API_BASE}/repos/{owner}/{repo}/tarball/{branch}"
        logger.debug("Fetching tarball: %s", tarball_url)

        try:
            response = await client.get(tarball_url)
        except httpx.TimeoutException as exc:
            raise GitHubSourceError(
                f"Timeout downloading repository tarball: {exc}"
            ) from exc
        except httpx.ConnectError as exc:
            raise GitHubSourceError(
                f"Cannot connect to GitHub API: {exc}"
            ) from exc

        _handle_error_response(response)

        # Extract .md files from the tarball
        result = _extract_md_from_tarball(response.content, repo_path)

        logger.info(
            "Found %d .md files in %s/%s (branch: %s, path: %s)",
            len(result), owner, repo, branch, repo_path,
        )

        return result


def _extract_md_from_tarball(
    tarball_bytes: bytes,
    repo_path: str,
) -> dict[str, tuple[str, bytes]]:
    """Extract .md files from a gzipped tarball.

    GitHub tarballs have a top-level directory like `owner-repo-sha/`.
    Files within `repo_path` are extracted with paths relative to that
    subdirectory.
    """
    result: dict[str, tuple[str, bytes]] = {}

    with tarfile.open(fileobj=io.BytesIO(tarball_bytes), mode="r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            if not member.name.endswith(".md"):
                continue

            # Strip the top-level directory (e.g. "owner-repo-abc1234/")
            parts = member.name.split("/", 1)
            if len(parts) < 2:
                continue
            inner_path = parts[1]

            # Filter by repo_path prefix
            prefix = f"{repo_path}/" if repo_path else ""
            if prefix and not inner_path.startswith(prefix):
                continue

            # Compute path relative to repo_path
            rel_path = inner_path[len(prefix):] if prefix else inner_path
            if not rel_path:
                continue

            # Read file content
            file_obj = tar.extractfile(member)
            if file_obj is None:
                continue
            raw = file_obj.read()

            file_hash = compute_hash(raw)
            result[rel_path] = (file_hash, raw)

    return result
