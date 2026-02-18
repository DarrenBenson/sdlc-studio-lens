"""GitHub API source module tests.

Test cases: TC0294-TC0307 from TS0029.
Now uses tarball-based approach (single API call) instead of
Trees + Blobs (N+1 API calls).
"""

import hashlib
import io
import tarfile
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from sdlc_lens.services.github_source import (
    AuthenticationError,
    GitHubSourceError,
    RateLimitError,
    RepoNotFoundError,
    _extract_md_from_tarball,
    fetch_github_files,
    parse_github_url,
)

# ---------------------------------------------------------------------------
# TC0294: parse_github_url extracts owner/repo from HTTPS URL
# ---------------------------------------------------------------------------


class TestParseGitHubUrl:
    def test_standard_https_url(self) -> None:
        owner, repo = parse_github_url("https://github.com/DarrenBenson/sdlc-studio-lens")
        assert owner == "DarrenBenson"
        assert repo == "sdlc-studio-lens"

    # TC0295: parse_github_url handles trailing slash
    def test_trailing_slash(self) -> None:
        owner, repo = parse_github_url("https://github.com/owner/repo/")
        assert owner == "owner"
        assert repo == "repo"

    # TC0296: parse_github_url handles .git suffix
    def test_git_suffix(self) -> None:
        owner, repo = parse_github_url("https://github.com/owner/repo.git")
        assert owner == "owner"
        assert repo == "repo"

    # TC0297: parse_github_url rejects invalid URLs
    def test_rejects_missing_segments(self) -> None:
        with pytest.raises(ValueError, match="Cannot extract"):
            parse_github_url("https://github.com/")

    def test_rejects_non_url(self) -> None:
        with pytest.raises(ValueError, match="Invalid URL"):
            parse_github_url("not-a-url")

    def test_rejects_single_segment(self) -> None:
        with pytest.raises(ValueError, match="Cannot extract"):
            parse_github_url("https://github.com/onlyone")

    def test_accepts_non_github_host(self) -> None:
        # parse_github_url doesn't enforce github.com host,
        # it just extracts owner/repo from path segments
        owner, repo = parse_github_url("https://gitlab.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"


# ---------------------------------------------------------------------------
# Helpers for building test tarballs
# ---------------------------------------------------------------------------

_CONTENT = b"# Hello"
_CONTENT_HASH = hashlib.sha256(_CONTENT).hexdigest()

# Top-level dir that GitHub includes in tarballs (owner-repo-sha)
_TAR_PREFIX = "owner-repo-abc1234"


def _build_tarball(files: dict[str, bytes]) -> bytes:
    """Build an in-memory gzipped tarball from a dict of {path: content}.

    Paths are prefixed with the GitHub-style top-level directory.
    """
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for path, content in files.items():
            full_path = f"{_TAR_PREFIX}/{path}"
            info = tarfile.TarInfo(name=full_path)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    return buf.getvalue()


def _mock_tarball_response(
    status_code: int = 200,
    tarball_bytes: bytes | None = None,
    headers: dict | None = None,
) -> httpx.Response:
    """Build a mock httpx.Response for tarball downloads."""
    return httpx.Response(
        status_code=status_code,
        content=tarball_bytes or b"",
        headers=headers or {},
        request=httpx.Request("GET", "https://api.github.com/repos/owner/repo/tarball/main"),
    )


# Standard tarball with mixed files
_STANDARD_FILES = {
    "sdlc-studio/stories/US001.md": b"# US001\n\nStory content",
    "sdlc-studio/epics/EP001.md": b"# EP001\n\nEpic content",
    "README.md": b"# README\n\nProject readme",
    "sdlc-studio/script.py": b"print('hello')",
    "sdlc-studio/image.png": b"\x89PNG\r\n",
    "docs/guide.md": b"# Guide\n\nGuide content",
}
_STANDARD_TARBALL = _build_tarball(_STANDARD_FILES)


# ---------------------------------------------------------------------------
# Test _extract_md_from_tarball directly
# ---------------------------------------------------------------------------


class TestExtractMdFromTarball:
    def test_extracts_md_files_within_repo_path(self) -> None:
        result = _extract_md_from_tarball(_STANDARD_TARBALL, "sdlc-studio")
        assert "stories/US001.md" in result
        assert "epics/EP001.md" in result

    def test_excludes_files_outside_repo_path(self) -> None:
        result = _extract_md_from_tarball(_STANDARD_TARBALL, "sdlc-studio")
        assert "README.md" not in result
        assert "docs/guide.md" not in result

    def test_excludes_non_md_files(self) -> None:
        result = _extract_md_from_tarball(_STANDARD_TARBALL, "sdlc-studio")
        for key in result:
            assert key.endswith(".md")
        assert "script.py" not in result
        assert "image.png" not in result

    def test_content_and_hash_correct(self) -> None:
        content = b"# US001\n\nStory content"
        expected_hash = hashlib.sha256(content).hexdigest()

        result = _extract_md_from_tarball(_STANDARD_TARBALL, "sdlc-studio")
        file_hash, file_content = result["stories/US001.md"]

        assert file_content == content
        assert file_hash == expected_hash
        assert len(file_hash) == 64

    def test_empty_repo_path(self) -> None:
        """With empty repo_path, all .md files in the tarball are returned."""
        result = _extract_md_from_tarball(_STANDARD_TARBALL, "")
        assert "README.md" in result
        assert "docs/guide.md" in result
        assert "sdlc-studio/stories/US001.md" in result


# ---------------------------------------------------------------------------
# TC0298: fetch_github_files returns dict for public repo (mock)
# ---------------------------------------------------------------------------


class TestFetchGitHubFiles:
    @pytest.mark.asyncio
    async def test_public_repo_returns_dict(self) -> None:
        """TC0298: Returns a dict mapping paths to (hash, bytes) tuples."""
        resp = _mock_tarball_response(200, _STANDARD_TARBALL)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_github_files(
                "https://github.com/owner/repo",
                branch="main",
                repo_path="sdlc-studio",
            )

        assert isinstance(result, dict)
        assert "stories/US001.md" in result
        assert "epics/EP001.md" in result
        for _path, (file_hash, content) in result.items():
            assert isinstance(file_hash, str)
            assert len(file_hash) == 64  # SHA-256 hex
            assert isinstance(content, bytes)

    # TC0299: fetch_github_files filters by repo_path
    @pytest.mark.asyncio
    async def test_filters_by_repo_path(self) -> None:
        resp = _mock_tarball_response(200, _STANDARD_TARBALL)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_github_files(
                "https://github.com/owner/repo",
                repo_path="sdlc-studio",
            )

        assert "stories/US001.md" in result
        assert "epics/EP001.md" in result
        # Files outside sdlc-studio/ should be excluded
        assert "README.md" not in result
        assert "docs/guide.md" not in result

    # TC0300: fetch_github_files includes Authorization header for private repo
    @pytest.mark.asyncio
    async def test_private_repo_sends_auth_header(self) -> None:
        tarball = _build_tarball({"sdlc-studio/test.md": _CONTENT})
        resp = _mock_tarball_response(200, tarball)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        captured_kwargs: dict = {}

        def capture_client(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return mock_client

        with patch(
            "sdlc_lens.services.github_source.httpx.AsyncClient",
            side_effect=capture_client,
        ):
            await fetch_github_files(
                "https://github.com/owner/repo",
                access_token="ghp_test1234abcd",
            )

        headers = captured_kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer ghp_test1234abcd"

    # TC0301: fetch_github_files handles 404 (repo not found)
    @pytest.mark.asyncio
    async def test_404_raises_repo_not_found(self) -> None:
        resp_404 = _mock_tarball_response(404)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=resp_404)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(RepoNotFoundError),
        ):
            await fetch_github_files("https://github.com/owner/nonexistent")

    # TC0302: fetch_github_files handles 401 (auth failure)
    @pytest.mark.asyncio
    async def test_401_raises_auth_error(self) -> None:
        resp_401 = _mock_tarball_response(401)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=resp_401)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(AuthenticationError),
        ):
            await fetch_github_files(
                "https://github.com/owner/repo",
                access_token="bad-token",
            )

    # TC0303: fetch_github_files handles rate limit 403
    @pytest.mark.asyncio
    async def test_403_rate_limit_raises_rate_limit_error(self) -> None:
        resp_403 = _mock_tarball_response(
            403,
            headers={"x-ratelimit-remaining": "0"},
        )

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=resp_403)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(RateLimitError),
        ):
            await fetch_github_files("https://github.com/owner/repo")

    # TC0304: fetch_github_files decodes content correctly (from tarball)
    @pytest.mark.asyncio
    async def test_content_extraction(self) -> None:
        tarball = _build_tarball({"sdlc-studio/test.md": _CONTENT})
        resp = _mock_tarball_response(200, tarball)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_github_files(
                "https://github.com/owner/repo",
                repo_path="sdlc-studio",
            )

        assert result["test.md"][1] == _CONTENT

    # TC0305: fetch_github_files computes SHA-256 matching local hash
    @pytest.mark.asyncio
    async def test_sha256_matches_local_hash(self) -> None:
        content = b"# Test Document\n"
        expected_hash = hashlib.sha256(content).hexdigest()

        tarball = _build_tarball({"sdlc-studio/doc.md": content})
        resp = _mock_tarball_response(200, tarball)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_github_files(
                "https://github.com/owner/repo",
                repo_path="sdlc-studio",
            )

        file_hash = result["doc.md"][0]
        assert file_hash == expected_hash
        assert len(file_hash) == 64

    # TC0306: fetch_github_files skips non-.md files in tarball
    @pytest.mark.asyncio
    async def test_skips_non_md_files(self) -> None:
        resp = _mock_tarball_response(200, _STANDARD_TARBALL)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_github_files(
                "https://github.com/owner/repo",
                repo_path="sdlc-studio",
            )

        # Only .md files
        for key in result:
            assert key.endswith(".md")
        # script.py and image.png are excluded
        assert "script.py" not in result
        assert "image.png" not in result

    # TC0307: fetch_github_files handles network timeout
    @pytest.mark.asyncio
    async def test_timeout_raises_github_source_error(self) -> None:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(GitHubSourceError, match="[Tt]imeout"),
        ):
            await fetch_github_files("https://github.com/owner/repo")

    # Single API call verification
    @pytest.mark.asyncio
    async def test_single_api_call(self) -> None:
        """Verify the tarball approach uses exactly 1 HTTP request."""
        resp = _mock_tarball_response(200, _STANDARD_TARBALL)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=mock_client):
            await fetch_github_files(
                "https://github.com/owner/repo",
                repo_path="sdlc-studio",
            )

        # Only 1 HTTP call (the tarball download)
        assert mock_client.get.call_count == 1
