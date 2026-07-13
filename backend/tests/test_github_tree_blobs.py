"""Direct tests for fetch_github_tree / fetch_github_blobs (US-01KXCCTV).

These exist because an independent critic pointed out that EVERY test of the incremental
sync mocked these two functions out and hand-built a ``RepoTree``. So the 148 lines that
actually parse GitHub's responses were never executed: the critic mutated
``truncated=bool(payload["truncated"])`` to ``truncated=False`` - deleting the only
defence against mass deletion on a large repo - and all 771 tests still passed.

A mocked boundary tests the code on YOUR side of it. It says nothing about whether you
read the other side's payload correctly.

So these drive real GitHub JSON payloads through the real functions.
"""

import base64
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from sdlc_lens.services.github_source import (
    AuthenticationError,
    GitHubSourceError,
    RateLimitError,
    fetch_github_blobs,
    fetch_github_tree,
)

REPO = "https://github.com/owner/repo"


def _client_returning(*responses: httpx.Response):
    """An httpx.AsyncClient stub that returns the given responses in order."""
    client = AsyncMock()
    client.get = AsyncMock(side_effect=list(responses))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


def _json(payload: dict, status: int = 200, headers: dict | None = None) -> httpx.Response:
    return httpx.Response(status_code=status, json=payload, headers=headers or {})


def _node(path: str, sha: str, *, type_: str = "blob", mode: str = "100644") -> dict:
    return {"path": path, "sha": sha, "type": type_, "mode": mode}


class TestFetchGitHubTree:
    @pytest.mark.asyncio
    async def test_parses_md_and_config_under_repo_path(self) -> None:
        payload = {
            "tree": [
                _node("sdlc-studio/epics/EP0001-one.md", "sha-epic"),
                _node("sdlc-studio/stories/US0001-one.md", "sha-story"),
                _node("sdlc-studio/.config.yaml", "sha-config"),
                _node("sdlc-studio/.version", "sha-version"),
                _node("README.md", "sha-readme"),  # outside repo_path
                _node("other/docs/X.md", "sha-other"),  # outside repo_path
            ],
            "truncated": False,
        }
        client = _client_returning(_json(payload))

        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client):
            tree = await fetch_github_tree(REPO, "main", "sdlc-studio", "tok")

        assert tree.md_blobs == {
            "epics/EP0001-one.md": "sha-epic",
            "stories/US0001-one.md": "sha-story",
        }
        assert tree.config_blobs == {".config.yaml": "sha-config", ".version": "sha-version"}
        assert tree.truncated is False

        # It asks for the whole tree in one call.
        assert client.get.await_args.kwargs["params"] == {"recursive": "1"}

    @pytest.mark.asyncio
    async def test_truncated_is_read_from_the_payload(self) -> None:
        """The ONLY defence against mass deletion on a big repo.

        A truncated tree is an incomplete manifest, and an incomplete manifest reads as
        "those paths were deleted upstream". If this flag is not carried out of the
        payload, the caller cannot know to fall back - and deletes documents whose files
        are perfectly present.
        """
        payload = {
            "tree": [_node("sdlc-studio/epics/EP0001-one.md", "sha-epic")],
            "truncated": True,
        }
        client = _client_returning(_json(payload))

        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client):
            tree = await fetch_github_tree(REPO, "main", "sdlc-studio", "tok")

        assert tree.truncated is True, "a truncated tree was reported as complete"

    @pytest.mark.asyncio
    async def test_directories_and_submodules_are_excluded(self) -> None:
        """A submodule's SHA is a COMMIT, not a blob. Fetching it fails the whole sync.

        The names here END IN `.md` on purpose. Nothing stops a directory or a submodule
        being called `notes.md`, and if the type filter is dropped, the `.md` suffix check
        happily waves them through - so a fixture whose directories are named `epics/`
        proves nothing. (Found exactly this way: the first version of this test passed
        even with the type filter deleted.)
        """
        payload = {
            "tree": [
                _node("sdlc-studio/notes.md", "sha-dir", type_="tree", mode="040000"),
                _node("sdlc-studio/vendored.md", "sha-commit", type_="commit", mode="160000"),
                _node("sdlc-studio/epics/EP0001-one.md", "sha-epic"),
            ],
            "truncated": False,
        }
        client = _client_returning(_json(payload))

        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client):
            tree = await fetch_github_tree(REPO, "main", "sdlc-studio", "tok")

        assert tree.md_blobs == {"epics/EP0001-one.md": "sha-epic"}
        assert "notes.md" not in tree.md_blobs, "a DIRECTORY entered the blob manifest"
        assert "vendored.md" not in tree.md_blobs, "a SUBMODULE commit SHA entered the manifest"

    @pytest.mark.asyncio
    async def test_symlinks_are_excluded(self) -> None:
        """A symlink is type "blob", mode 120000, and its content is the LINK TARGET.

        The tarball path excludes symlinks (`TarInfo.isfile()` is False). If the Trees
        path includes them the two manifests disagree about which paths are live, and the
        document is ADDED by an incremental sync then DELETED by the next tarball
        fallback, for ever.
        """
        payload = {
            "tree": [
                _node("sdlc-studio/epics/EP0001-one.md", "sha-epic"),
                _node("sdlc-studio/epics/LINK.md", "sha-link", mode="120000"),
            ],
            "truncated": False,
        }
        client = _client_returning(_json(payload))

        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client):
            tree = await fetch_github_tree(REPO, "main", "sdlc-studio", "tok")

        assert "epics/LINK.md" not in tree.md_blobs, "a symlink entered the manifest"
        assert tree.md_blobs == {"epics/EP0001-one.md": "sha-epic"}

    @pytest.mark.asyncio
    async def test_empty_repo_path_takes_the_whole_repo(self) -> None:
        payload = {
            "tree": [_node("epics/EP0001-one.md", "sha-epic"), _node("README.md", "sha-readme")],
            "truncated": False,
        }
        client = _client_returning(_json(payload))

        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client):
            tree = await fetch_github_tree(REPO, "main", "", "tok")

        assert tree.md_blobs == {"epics/EP0001-one.md": "sha-epic", "README.md": "sha-readme"}

    @pytest.mark.asyncio
    async def test_a_prefix_sibling_directory_is_not_swept_in(self) -> None:
        """`sdlc-studio-old/` must not match the `sdlc-studio` prefix."""
        payload = {
            "tree": [
                _node("sdlc-studio/epics/EP0001-one.md", "sha-epic"),
                _node("sdlc-studio-old/epics/EP9999-old.md", "sha-old"),
            ],
            "truncated": False,
        }
        client = _client_returning(_json(payload))

        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client):
            tree = await fetch_github_tree(REPO, "main", "sdlc-studio", "tok")

        assert tree.md_blobs == {"epics/EP0001-one.md": "sha-epic"}

    @pytest.mark.asyncio
    async def test_rate_limit_raises(self) -> None:
        client = _client_returning(
            _json({}, status=403, headers={"x-ratelimit-remaining": "0"}),
        )
        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client),
            pytest.raises(RateLimitError),
        ):
            await fetch_github_tree(REPO, "main", "sdlc-studio", "tok")

    @pytest.mark.asyncio
    async def test_bad_token_raises(self) -> None:
        client = _client_returning(_json({}, status=401))
        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client),
            pytest.raises(AuthenticationError),
        ):
            await fetch_github_tree(REPO, "main", "sdlc-studio", "tok")


class TestFetchGitHubBlobs:
    @pytest.mark.asyncio
    async def test_decodes_base64_content(self) -> None:
        body = b"# EP0001\n\n> **Status:** Draft\n\nEpic"
        client = _client_returning(
            _json({"encoding": "base64", "content": base64.b64encode(body).decode()}),
        )
        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client):
            got = await fetch_github_blobs(REPO, {"epics/EP0001-one.md": "sha-epic"}, "tok")

        assert got == {"epics/EP0001-one.md": body}

    @pytest.mark.asyncio
    async def test_no_blobs_means_no_requests(self) -> None:
        """The no-op sync: zero blob requests, and we must not even open a client."""
        client = _client_returning()
        with patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client):
            got = await fetch_github_blobs(REPO, {}, "tok")

        assert got == {}
        assert client.get.await_count == 0

    @pytest.mark.asyncio
    async def test_an_unexpected_encoding_is_refused_not_guessed(self) -> None:
        """GitHub returns `encoding: "none"` for very large blobs. Do not guess."""
        client = _client_returning(_json({"encoding": "none", "content": ""}))
        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client),
            pytest.raises(GitHubSourceError, match="encoding"),
        ):
            await fetch_github_blobs(REPO, {"epics/EP0001-one.md": "sha"}, "tok")

    @pytest.mark.asyncio
    async def test_one_failure_fails_the_whole_fetch_and_returns_nothing(self) -> None:
        """All-or-nothing. A partial corpus is worse than no sync at all.

        The caller writes what it is given; if it were handed 3 of 5 changed files it
        would happily store a corpus that matches no commit that ever existed.
        """
        good = base64.b64encode(b"# ok").decode()
        client = AsyncMock()
        client.get = AsyncMock(
            side_effect=[
                _json({"encoding": "base64", "content": good}),
                _json({}, status=403, headers={"x-ratelimit-remaining": "0"}),
                _json({"encoding": "base64", "content": good}),
            ]
        )
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client),
            pytest.raises(RateLimitError),
        ):
            await fetch_github_blobs(
                REPO,
                {"a.md": "sha-a", "b.md": "sha-b", "c.md": "sha-c"},
                "tok",
                concurrency=1,
            )

    @pytest.mark.asyncio
    async def test_an_oversized_blob_is_refused(self) -> None:
        huge = base64.b64encode(b"x" * (26 * 1024 * 1024)).decode()
        client = _client_returning(_json({"encoding": "base64", "content": huge}))
        with (
            patch("sdlc_lens.services.github_source.httpx.AsyncClient", return_value=client),
            pytest.raises(GitHubSourceError, match="too large"),
        ):
            await fetch_github_blobs(REPO, {"big.md": "sha"}, "tok")
