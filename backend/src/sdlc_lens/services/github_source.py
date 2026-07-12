"""GitHub API source - fetch .md files from a GitHub repository."""

from __future__ import annotations

import asyncio
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

# Resource bounds guarding against a huge or gzip-bomb repository. An sdlc-studio
# docs tree is a handful of MB, so these leave generous headroom while capping the
# blast radius on memory.
_MAX_TARBALL_BYTES = 50 * 1024 * 1024  # 50 MB compressed download ceiling.
_MAX_DECOMPRESSED_BYTES = 300 * 1024 * 1024  # 300 MB cumulative decompressed budget.
_MAX_MEMBER_BYTES = 25 * 1024 * 1024  # 25 MB per-file ceiling (.md files are tiny).

# Project metadata files pulled from the repo_path root alongside the .md tree.
_CONFIG_FILENAMES = (".config.yaml", ".version")

# Repo-listing bounds. The Contents/repo-listing calls are cheap individually,
# but an account with hundreds of repos would burn through the rate limit if we
# paginated without end, so cap the aggregate at a sensible ceiling.
_REPOS_PER_PAGE = 100
_MAX_REPOS = 200

# The workspace directory whose presence flags a repo as already following the
# sdlc-studio process.
_SDLC_STUDIO_DIR = "sdlc-studio"


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
        raise RepoNotFoundError(f"Repository not found (HTTP {response.status_code})")
    if response.status_code == 401:
        raise AuthenticationError("Authentication failed - check your access token")
    if response.status_code == 403:
        # A 403 is a rate limit when the primary quota is spent
        # (x-ratelimit-remaining: 0) or a secondary/abuse limit is hit
        # (signalled by a Retry-After header); otherwise it is access-denied.
        remaining = response.headers.get("x-ratelimit-remaining", "")
        if remaining == "0" or "retry-after" in response.headers:
            raise RateLimitError(
                "GitHub API rate limit exceeded - use an access token for higher limits"
            )
        raise AuthenticationError("Access denied (HTTP 403) - repository may be private")
    if response.status_code >= 400:
        raise GitHubSourceError(f"GitHub API error: HTTP {response.status_code}")


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
    md_files, _config = await fetch_github_files_and_config(
        repo_url,
        branch=branch,
        repo_path=repo_path,
        access_token=access_token,
        timeout=timeout,
    )
    return md_files


async def fetch_github_files_and_config(
    repo_url: str,
    branch: str = "main",
    repo_path: str = "sdlc-studio",
    access_token: str | None = None,
    timeout: httpx.Timeout | None = None,
) -> tuple[dict[str, tuple[str, bytes]], dict[str, bytes]]:
    """Fetch .md files and the project config files in a single tarball download.

    Returns a tuple of ``(md_files, config_files)`` where ``md_files`` is the
    same ``{relative_path: (hash, raw_bytes)}`` mapping as
    :func:`fetch_github_files` and ``config_files`` maps each present
    ``.config.yaml`` / ``.version`` at the ``repo_path`` root to its raw bytes.
    The config mapping is empty when neither file is present.

    Raises the same errors as :func:`fetch_github_files` for the download.
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
            raise GitHubSourceError(f"Timeout downloading repository tarball: {exc}") from exc
        except httpx.ConnectError as exc:
            raise GitHubSourceError(f"Cannot connect to GitHub API: {exc}") from exc

        _handle_error_response(response)

        # Reject an oversized download before decompressing it. Check the declared
        # Content-Length first (cheap, avoids buffering a hostile body), then the
        # actual buffered length as a backstop when the header is absent or lies.
        declared = response.headers.get("content-length", "")
        if declared.isdigit() and int(declared) > _MAX_TARBALL_BYTES:
            raise GitHubSourceError(
                f"Repository tarball too large: {int(declared)} bytes exceeds the "
                f"{_MAX_TARBALL_BYTES}-byte download limit"
            )
        content = response.content
        if len(content) > _MAX_TARBALL_BYTES:
            raise GitHubSourceError(
                f"Repository tarball too large: {len(content)} bytes exceeds the "
                f"{_MAX_TARBALL_BYTES}-byte download limit"
            )

        # Extract .md and config files from the tarball. Gzip decompression and
        # the in-memory tarball walk are synchronous CPU/IO work, so offload
        # them to a worker thread to keep the event loop responsive during a sync.
        md_files, config_files = await asyncio.to_thread(
            _extract_all_from_tarball, content, repo_path
        )

        logger.info(
            "Found %d .md files in %s/%s (branch: %s, path: %s)",
            len(md_files),
            owner,
            repo,
            branch,
            repo_path,
        )

        return md_files, config_files


def _extract_all_from_tarball(
    tarball_bytes: bytes,
    repo_path: str,
) -> tuple[dict[str, tuple[str, bytes]], dict[str, bytes]]:
    """Extract both the .md tree and the root config files from one tarball."""
    md_files = _extract_md_from_tarball(tarball_bytes, repo_path)
    config_files = _extract_config_from_tarball(tarball_bytes, repo_path)
    return md_files, config_files


def _extract_md_from_tarball(
    tarball_bytes: bytes,
    repo_path: str,
) -> dict[str, tuple[str, bytes]]:
    """Extract .md files from a gzipped tarball.

    GitHub tarballs have a top-level directory like `owner-repo-sha/`.
    Files within `repo_path` are extracted with paths relative to that
    subdirectory.

    Iteration is streamed (one member at a time) and bounded: a single member
    larger than ``_MAX_MEMBER_BYTES`` or a cumulative decompressed size beyond
    ``_MAX_DECOMPRESSED_BYTES`` aborts with a :class:`GitHubSourceError`, so a
    gzip-bomb archive cannot exhaust memory.
    """
    result: dict[str, tuple[str, bytes]] = {}
    total_decompressed = 0

    with tarfile.open(fileobj=io.BytesIO(tarball_bytes), mode="r:gz") as tar:
        for member in tar:
            if not member.isfile():
                continue

            # Bound decompression using each member's declared size, checked before
            # any data is read, so an oversized member is refused up front.
            if member.size > _MAX_MEMBER_BYTES:
                raise GitHubSourceError(
                    f"Tarball member {member.name!r} too large: {member.size} bytes "
                    f"exceeds the {_MAX_MEMBER_BYTES}-byte per-file limit"
                )
            total_decompressed += member.size
            if total_decompressed > _MAX_DECOMPRESSED_BYTES:
                raise GitHubSourceError(
                    f"Decompressed tarball exceeds the {_MAX_DECOMPRESSED_BYTES}-byte "
                    "budget - repository too large to sync"
                )

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
            rel_path = inner_path[len(prefix) :] if prefix else inner_path
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


def _extract_config_from_tarball(
    tarball_bytes: bytes,
    repo_path: str,
) -> dict[str, bytes]:
    """Extract the ``.config.yaml`` / ``.version`` files at the repo_path root.

    Mirrors :func:`_extract_md_from_tarball`'s path handling but targets the two
    project-metadata files sitting at the root of ``repo_path``. Returns a
    ``{filename: raw_bytes}`` mapping containing only the files that are present.
    The per-member size bound is applied for parity with the .md walk; these
    files are tiny in practice.
    """
    result: dict[str, bytes] = {}

    with tarfile.open(fileobj=io.BytesIO(tarball_bytes), mode="r:gz") as tar:
        for member in tar:
            if not member.isfile():
                continue

            # Strip the top-level directory (e.g. "owner-repo-abc1234/")
            parts = member.name.split("/", 1)
            if len(parts) < 2:
                continue
            inner_path = parts[1]

            prefix = f"{repo_path}/" if repo_path else ""
            if prefix and not inner_path.startswith(prefix):
                continue

            rel_path = inner_path[len(prefix) :] if prefix else inner_path
            if rel_path not in _CONFIG_FILENAMES:
                continue

            if member.size > _MAX_MEMBER_BYTES:
                raise GitHubSourceError(
                    f"Tarball member {member.name!r} too large: {member.size} bytes "
                    f"exceeds the {_MAX_MEMBER_BYTES}-byte per-file limit"
                )

            file_obj = tar.extractfile(member)
            if file_obj is None:
                continue
            result[rel_path] = file_obj.read()

    return result


# ---------------------------------------------------------------------------
# Repository browsing (CR-01KXAS75)
# ---------------------------------------------------------------------------


def _repo_item(raw: dict) -> dict:
    """Normalise a GitHub repository object to the fields we expose.

    Returns ``{full_name, owner, name, private, default_branch, description}``.
    """
    owner = (raw.get("owner") or {}).get("login") or ""
    name = raw.get("name") or ""
    full_name = raw.get("full_name") or (f"{owner}/{name}" if owner and name else name)
    return {
        "full_name": full_name,
        "owner": owner,
        "name": name,
        "private": bool(raw.get("private", False)),
        "default_branch": raw.get("default_branch") or "main",
        "description": raw.get("description"),
    }


async def _collect_repos(
    client: httpx.AsyncClient,
    url: str,
    into: dict[str, dict],
    params: dict,
) -> None:
    """Paginate a repo-listing endpoint into ``into`` (keyed by full_name).

    Stops at the ``_MAX_REPOS`` aggregate cap, when a short page signals the end,
    or when a page comes back empty. De-duplicates against whatever is already in
    ``into`` so overlapping user/org listings collapse to a single entry.
    """
    page = 1
    while len(into) < _MAX_REPOS:
        resp = await client.get(url, params={**params, "page": page})
        _handle_error_response(resp)
        batch = resp.json()
        if not batch:
            break
        for raw in batch:
            item = _repo_item(raw)
            if item["full_name"]:
                into.setdefault(item["full_name"], item)
        if len(batch) < params["per_page"]:
            break
        page += 1


async def _fetch_org_logins(client: httpx.AsyncClient) -> list[str]:
    """Return the login names of the orgs the authenticated user belongs to."""
    resp = await client.get(f"{_API_BASE}/user/orgs", params={"per_page": _REPOS_PER_PAGE})
    _handle_error_response(resp)
    return [org.get("login") for org in resp.json() if org.get("login")]


async def list_repositories(
    access_token: str,
    timeout: httpx.Timeout | None = None,
) -> list[dict]:
    """List the repositories the authenticated user can see.

    Aggregates the user's own repos (``GET /user/repos``) with the repos of each
    org they belong to (``GET /user/orgs`` then ``GET /orgs/{org}/repos``),
    de-duplicated by ``full_name`` and capped at ``_MAX_REPOS`` to stay within
    the rate limit. Pagination stops early on a short/empty page.

    Each entry is ``{full_name, owner, name, private, default_branch,
    description}``. Results are sorted case-insensitively by ``full_name``.

    Raises:
        AuthenticationError: If no token is supplied, or the token is rejected.
        RateLimitError: If the API rate limit is exceeded.
        GitHubSourceError: On other API/transport errors.
    """
    if not access_token:
        raise AuthenticationError("An access token is required to list repositories")

    headers = _build_headers(access_token)
    effective_timeout = timeout or _DEFAULT_TIMEOUT
    repos: dict[str, dict] = {}

    async with httpx.AsyncClient(
        headers=headers,
        timeout=effective_timeout,
        follow_redirects=True,
    ) as client:
        try:
            await _collect_repos(
                client,
                f"{_API_BASE}/user/repos",
                repos,
                params={"per_page": _REPOS_PER_PAGE, "sort": "full_name"},
            )
            for org in await _fetch_org_logins(client):
                if len(repos) >= _MAX_REPOS:
                    break
                await _collect_repos(
                    client,
                    f"{_API_BASE}/orgs/{org}/repos",
                    repos,
                    params={"per_page": _REPOS_PER_PAGE},
                )
        except httpx.TimeoutException as exc:
            raise GitHubSourceError(f"Timeout listing repositories: {exc}") from exc
        except httpx.ConnectError as exc:
            raise GitHubSourceError(f"Cannot connect to GitHub API: {exc}") from exc

    return sorted(repos.values(), key=lambda r: r["full_name"].lower())


async def get_authenticated_login(
    access_token: str,
    timeout: httpx.Timeout | None = None,
) -> str:
    """Return the GitHub login the supplied token authenticates as.

    A single ``GET /user`` call, used to validate a token before it is stored as
    a connection (CR-01KXAZX9) and to re-validate it later. An expired or revoked
    token comes back as 401 and is surfaced as :class:`AuthenticationError`, so
    an invalid credential is never persisted.

    Raises:
        AuthenticationError: If no token is supplied, or the token is rejected.
        RateLimitError: If the API rate limit is exceeded.
        GitHubSourceError: On other API/transport errors, or if GitHub returns
            no login for the token.
    """
    if not access_token:
        raise AuthenticationError("An access token is required")

    headers = _build_headers(access_token)
    effective_timeout = timeout or _DEFAULT_TIMEOUT

    async with httpx.AsyncClient(
        headers=headers,
        timeout=effective_timeout,
        follow_redirects=True,
    ) as client:
        try:
            response = await client.get(f"{_API_BASE}/user")
        except httpx.TimeoutException as exc:
            raise GitHubSourceError(f"Timeout validating access token: {exc}") from exc
        except httpx.ConnectError as exc:
            raise GitHubSourceError(f"Cannot connect to GitHub API: {exc}") from exc

        # /user has no repository to be "not found"; a 404 here means the token
        # cannot see the endpoint at all, which is an authentication failure.
        if response.status_code == 404:
            raise AuthenticationError("Authentication failed - check your access token")
        _handle_error_response(response)

        login = (response.json() or {}).get("login")
        if not login:
            raise GitHubSourceError("GitHub returned no login for this access token")
        return str(login)


async def repo_has_sdlc_studio(
    access_token: str | None,
    owner: str,
    repo: str,
    branch: str | None = None,
    timeout: httpx.Timeout | None = None,
) -> bool:
    """Check whether a repo contains an ``sdlc-studio/`` workspace directory.

    A single cheap Contents API call
    (``GET /repos/{owner}/{repo}/contents/sdlc-studio``). This is the per-repo
    flag, meant to be called lazily for visible rows only - never for every repo
    in a listing, which would blow the rate limit.

    Returns True on 200 (the directory exists), False on 404 (absent, or the repo
    is not accessible).

    Raises:
        AuthenticationError: If the token is rejected.
        RateLimitError: If the API rate limit is exceeded.
        GitHubSourceError: On other API/transport errors.
    """
    headers = _build_headers(access_token)
    effective_timeout = timeout or _DEFAULT_TIMEOUT
    params = {"ref": branch} if branch else None

    async with httpx.AsyncClient(
        headers=headers,
        timeout=effective_timeout,
        follow_redirects=True,
    ) as client:
        url = f"{_API_BASE}/repos/{owner}/{repo}/contents/{_SDLC_STUDIO_DIR}"
        try:
            response = await client.get(url, params=params)
        except httpx.TimeoutException as exc:
            raise GitHubSourceError(f"Timeout checking repository contents: {exc}") from exc
        except httpx.ConnectError as exc:
            raise GitHubSourceError(f"Cannot connect to GitHub API: {exc}") from exc

        if response.status_code == 404:
            return False
        _handle_error_response(response)
        return True
