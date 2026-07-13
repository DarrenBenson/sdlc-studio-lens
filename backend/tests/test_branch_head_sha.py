"""Direct tests for fetch_branch_head_sha (US-01KXDD5K).

These exist because an independent critic pointed out that all nine references to this
function in the suite were `patch(...)` - **not one test called it**. It then deleted the
single line that makes it work (the `Accept: application/vnd.github.sha` header) and all
803 tests still passed.

Without that header GitHub returns the full commit object: an 18 KB JSON blob, which can
never equal a stored 40-char SHA. Every auto-sync project would re-sync on every tick,
for ever.

The same trap as the previous sprint, in the same shape: a mocked boundary tests the code
on YOUR side of it and says nothing about whether you speak the other side's protocol.
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from sdlc_lens.services.github_source import (
    AuthenticationError,
    GitHubSourceError,
    RateLimitError,
    fetch_branch_head_sha,
)

REPO = "https://github.com/owner/repo"
SHA = "f69d43a4e0bce05a69f7f186a0034af3568ba1aa"


def _client(response: httpx.Response):
    client = AsyncMock()
    client.get = AsyncMock(return_value=response)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


class TestFetchBranchHeadSha:
    @pytest.mark.asyncio
    async def test_asks_for_the_bare_sha_media_type(self) -> None:
        """THE line the whole feature turns on.

        `application/vnd.github.sha` is what makes GitHub return 40 characters instead of
        an 18 KB commit object. Deleting it keeps every other test green.
        """
        client = _client(httpx.Response(200, text=SHA))

        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client):
            got = await fetch_branch_head_sha(REPO, "main", "tok")

        assert got == SHA
        sent = client.get.await_args.kwargs["headers"]
        assert sent["Accept"] == "application/vnd.github.sha", (
            "the bare-SHA media type was not requested - GitHub will return the full "
            "commit object and nothing will ever compare equal"
        )

    @pytest.mark.asyncio
    async def test_one_request_only(self) -> None:
        client = _client(httpx.Response(200, text=SHA))
        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client):
            await fetch_branch_head_sha(REPO, "main", "tok")
        assert client.get.await_count == 1

    @pytest.mark.asyncio
    async def test_a_json_body_is_refused_not_stored(self) -> None:
        """Exactly what a missing Accept header produces. It must not reach the DB.

        `last_synced_commit_sha` is a VARCHAR(40); SQLite would happily store an 18 KB
        JSON blob in it, and every subsequent comparison would fail for ever.
        """
        blob = f'{{"sha":"{SHA}","node_id":"C_kwDO","commit":{{"message":"x"}}}}'
        client = _client(httpx.Response(200, text=blob))

        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client),
            pytest.raises(GitHubSourceError, match="not a commit SHA"),
        ):
            await fetch_branch_head_sha(REPO, "main", "tok")

    @pytest.mark.asyncio
    async def test_an_empty_body_is_refused(self) -> None:
        client = _client(httpx.Response(200, text="   "))
        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client),
            pytest.raises(GitHubSourceError),
        ):
            await fetch_branch_head_sha(REPO, "main", "tok")

    @pytest.mark.asyncio
    async def test_a_truncated_sha_is_refused(self) -> None:
        client = _client(httpx.Response(200, text=SHA[:12]))
        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client),
            pytest.raises(GitHubSourceError, match="not a commit SHA"),
        ):
            await fetch_branch_head_sha(REPO, "main", "tok")

    @pytest.mark.asyncio
    async def test_a_deleted_branch_raises_not_found(self) -> None:
        from sdlc_lens.services.github_source import RepoNotFoundError

        client = _client(httpx.Response(404, json={}))
        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client),
            pytest.raises(RepoNotFoundError),
        ):
            await fetch_branch_head_sha(REPO, "gone", "tok")

    @pytest.mark.asyncio
    async def test_a_revoked_token_raises(self) -> None:
        client = _client(httpx.Response(401, json={}))
        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client),
            pytest.raises(AuthenticationError),
        ):
            await fetch_branch_head_sha(REPO, "main", "bad")

    @pytest.mark.asyncio
    async def test_a_rate_limit_raises(self) -> None:
        client = _client(httpx.Response(403, json={}, headers={"x-ratelimit-remaining": "0"}))
        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client),
            pytest.raises(RateLimitError),
        ):
            await fetch_branch_head_sha(REPO, "main", "tok")
