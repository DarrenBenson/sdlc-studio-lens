"""Incremental GitHub sync: Trees + Blobs, with a tarball fallback (US-01KXCCTV).

These patch at the **GitHub API boundary** (`fetch_github_tree`, `fetch_github_blobs`,
`fetch_github_files_and_config`) rather than at the collector, so the hybrid path
selection - the actual subject of this story - really runs. Patching the collector would
mock out the very decision under test.

The counting assertions are the point. "Fetch only what changed" is a claim about how
many HTTP requests are made, so a test that does not count requests does not test it.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.db.models.document import Document
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.github_source import RateLimitError, RepoTree
from sdlc_lens.services.sync_engine import MAX_INCREMENTAL_BLOBS, sync_project
from sdlc_lens.utils.hashing import compute_blob_sha

EPIC = b"# EP0001\n\n> **Status:** Draft\n\nEpic one"
STORY = b"# US0001\n\n> **Status:** Draft\n\nStory one"
PLAN = b"# PL0001\n\n> **Status:** Draft\n\nPlan one"

FILES = {
    "epics/EP0001-one.md": EPIC,
    "stories/US0001-one.md": STORY,
    "plans/PL0001-one.md": PLAN,
}


async def _github_project(session: AsyncSession) -> Project:
    project = Project(
        slug="gh",
        name="GH",
        source_type="github",
        repo_url="https://github.com/owner/repo",
        repo_branch="main",
        repo_path="sdlc-studio",
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def _docs(session: AsyncSession, project_id: int) -> list[Document]:
    res = await session.execute(select(Document).where(Document.project_id == project_id))
    return list(res.scalars().all())


def _tarball_return(files: dict[str, bytes]) -> tuple[dict, dict]:
    """What fetch_github_files_and_config returns: (md_files, config_files)."""
    from sdlc_lens.utils.hashing import compute_hash

    return ({p: (compute_hash(c), c) for p, c in files.items()}, {})


def _tree(files: dict[str, bytes], *, truncated: bool = False) -> RepoTree:
    return RepoTree(
        md_blobs={p: compute_blob_sha(c) for p, c in files.items()},
        config_blobs={},
        truncated=truncated,
    )


async def _seed(session: AsyncSession, project: Project, files: dict[str, bytes]) -> None:
    """First sync, via the tarball, so every row lands with a blob_sha.

    Note `added` is not asserted against ``len(files)``: not every .md file becomes a
    document (an `_index.md` never does), and pretending otherwise is exactly the
    assumption that hid the "chase _index.md for ever" bug.
    """
    with patch(
        "sdlc_lens.services.github_source.fetch_github_files_and_config",
        new_callable=AsyncMock,
        return_value=_tarball_return(files),
    ):
        result = await sync_project(project, session)
    assert result.fetch_path == "tarball"
    assert result.added > 0


class TestPathSelection:
    @pytest.mark.asyncio
    async def test_first_sync_uses_the_tarball(self, session: AsyncSession) -> None:
        """Nothing to diff against, and one request beats 1 + N."""
        project = await _github_project(session)

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_github_files_and_config",
                new_callable=AsyncMock,
                return_value=_tarball_return(FILES),
            ),
            patch(
                "sdlc_lens.services.github_source.fetch_github_tree", new_callable=AsyncMock
            ) as tree,
        ):
            result = await sync_project(project, session)

        assert result.fetch_path == "tarball"
        assert result.fetch_reason == "first sync"
        assert tree.await_count == 0, "the first sync should not need a Trees call"
        assert result.added == 3

    @pytest.mark.asyncio
    async def test_a_null_blob_sha_forces_the_tarball_and_is_backfilled(
        self, session: AsyncSession
    ) -> None:
        """The upgrade path: every row from before migration 012 has blob_sha=NULL.

        We cannot diff a row we have no SHA for, so pull everything once. The rows are
        then rewritten (needs_blob_sha_backfill) and the NEXT sync can go incremental.
        """
        project = await _github_project(session)
        await _seed(session, project, FILES)

        # Simulate a pre-012 database.
        for doc in await _docs(session, project.id):
            doc.blob_sha = None
        await session.commit()

        with patch(
            "sdlc_lens.services.github_source.fetch_github_files_and_config",
            new_callable=AsyncMock,
            return_value=_tarball_return(FILES),
        ):
            result = await sync_project(project, session)

        assert result.fetch_path == "tarball"
        assert "backfilling blob SHAs" in result.fetch_reason
        assert all(d.blob_sha is not None for d in await _docs(session, project.id))

        # And now it settles into incremental.
        with (
            patch(
                "sdlc_lens.services.github_source.fetch_github_tree",
                new_callable=AsyncMock,
                return_value=_tree(FILES),
            ),
            patch(
                "sdlc_lens.services.github_source.fetch_github_blobs",
                new_callable=AsyncMock,
                return_value={},
            ) as blobs,
        ):
            result = await sync_project(project, session)

        assert result.fetch_path == "incremental"
        assert blobs.await_args.kwargs["blob_shas"] == {}

    @pytest.mark.asyncio
    async def test_a_stale_parser_epoch_forces_the_tarball(self, session: AsyncSession) -> None:
        """RFC D7. An epoch bump means byte-unchanged files must still RE-PARSE.

        Re-parsing needs real bytes, and the stored `content` column cannot supply them:
        it is body-only, with the frontmatter blockquote stripped. So pull the tarball.
        Miss this and BG-01KXARHJ silently un-fixes itself for every GitHub project.
        """
        project = await _github_project(session)
        await _seed(session, project, FILES)

        for doc in await _docs(session, project.id):
            doc.parser_epoch = 0  # an older parser produced these derived fields
        await session.commit()

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_github_files_and_config",
                new_callable=AsyncMock,
                return_value=_tarball_return(FILES),
            ),
            patch(
                "sdlc_lens.services.github_source.fetch_github_tree", new_callable=AsyncMock
            ) as tree,
        ):
            result = await sync_project(project, session)

        assert result.fetch_path == "tarball"
        assert "parser upgrade" in result.fetch_reason
        assert tree.await_count == 0
        assert result.updated == 3, "every stale-epoch document must be re-parsed"

    @pytest.mark.asyncio
    async def test_over_the_cap_falls_back_to_the_tarball_and_says_so(
        self, session: AsyncSession
    ) -> None:
        """RETRO-0006: a cap must speak.

        Past the cap, one request per blob costs more than a single tarball, so falling
        back BOUNDS the worst case at today's cost. A fallback that happened silently
        would read to the operator as "this is just how it works".
        """
        project = await _github_project(session)

        many = {f"stories/US{i:04d}-x.md": f"# US{i:04d}\n\nBody {i}".encode() for i in range(250)}
        await _seed(session, project, many)

        # Every single one changed.
        changed = {p: c + b"\n\nedited" for p, c in many.items()}

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_github_tree",
                new_callable=AsyncMock,
                return_value=_tree(changed),
            ),
            patch(
                "sdlc_lens.services.github_source.fetch_github_files_and_config",
                new_callable=AsyncMock,
                return_value=_tarball_return(changed),
            ),
            patch(
                "sdlc_lens.services.github_source.fetch_github_blobs", new_callable=AsyncMock
            ) as blobs,
        ):
            result = await sync_project(project, session)

        assert result.fetch_path == "tarball"
        assert str(MAX_INCREMENTAL_BLOBS) in result.fetch_reason
        assert "250" in result.fetch_reason
        assert blobs.await_count == 0, "it must not fetch 250 blobs one at a time"

    @pytest.mark.asyncio
    async def test_a_truncated_tree_falls_back_to_the_tarball(self, session: AsyncSession) -> None:
        """A truncated tree is an INCOMPLETE manifest.

        And an incomplete manifest reads as "those paths were deleted upstream" - which
        would delete documents whose files are perfectly present. Never trust it.
        """
        project = await _github_project(session)
        await _seed(session, project, FILES)

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_github_tree",
                new_callable=AsyncMock,
                # Only ONE path survived truncation. Trusting it would delete the other two.
                return_value=_tree({"epics/EP0001-one.md": EPIC}, truncated=True),
            ),
            patch(
                "sdlc_lens.services.github_source.fetch_github_files_and_config",
                new_callable=AsyncMock,
                return_value=_tarball_return(FILES),
            ),
        ):
            result = await sync_project(project, session)

        assert result.fetch_path == "tarball"
        assert "truncated" in result.fetch_reason
        assert result.deleted == 0, "a truncated tree deleted documents that still exist"
        assert len(await _docs(session, project.id)) == 3


class TestIncrementalFetching:
    @pytest.mark.asyncio
    async def test_nothing_changed_fetches_zero_blobs_and_touches_nothing(
        self, session: AsyncSession
    ) -> None:
        """The whole point of the feature, and the commonest path in the system.

        One Trees call. Zero blob requests. Zero writes. And - critically - ZERO
        DELETIONS: every file is in the manifest but none carries content, which is
        exactly the shape that would be catastrophic if absence-of-content were confused
        with absence-from-source (BG-01KX8BFP).
        """
        project = await _github_project(session)
        await _seed(session, project, FILES)
        before = {d.file_path: d.synced_at for d in await _docs(session, project.id)}

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_github_tree",
                new_callable=AsyncMock,
                return_value=_tree(FILES),
            ) as tree,
            patch(
                "sdlc_lens.services.github_source.fetch_github_blobs",
                new_callable=AsyncMock,
                return_value={},
            ) as blobs,
            patch(
                "sdlc_lens.services.github_source.fetch_github_files_and_config",
                new_callable=AsyncMock,
            ) as tarball,
        ):
            result = await sync_project(project, session)

        assert tree.await_count == 1, "a no-op sync should cost exactly one Trees call"
        assert tarball.await_count == 0, "it fell back to the tarball for no reason"
        assert blobs.await_args.kwargs["blob_shas"] == {}, "it fetched a blob it did not need"

        assert result.fetch_path == "incremental"
        assert result.fetch_reason == "nothing changed upstream"
        assert result.blobs_fetched == 0
        assert (result.added, result.updated, result.deleted, result.errors) == (0, 0, 0, 0)
        assert result.skipped == 3

        assert project.sync_status == "synced"
        after = {d.file_path: d.synced_at for d in await _docs(session, project.id)}
        assert after == before, "documents were rewritten on a no-op sync"

    @pytest.mark.asyncio
    async def test_only_the_changed_files_are_fetched(self, session: AsyncSession) -> None:
        """K changed -> exactly K blob requests, and exactly K documents rewritten."""
        project = await _github_project(session)
        await _seed(session, project, FILES)

        edited = dict(FILES)
        edited["stories/US0001-one.md"] = b"# US0001\n\n> **Status:** Done\n\nStory one EDITED"
        edited["docs/NEW0001-new.md"] = b"# NEW0001\n\nA brand new file"

        untouched_before = next(
            d for d in await _docs(session, project.id) if d.file_path == "epics/EP0001-one.md"
        ).synced_at

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_github_tree",
                new_callable=AsyncMock,
                return_value=_tree(edited),
            ),
            patch(
                "sdlc_lens.services.github_source.fetch_github_blobs",
                new_callable=AsyncMock,
                side_effect=lambda **kw: {
                    p: edited[p] for p in kw["blob_shas"] if not p.startswith("\0")
                },
            ) as blobs,
        ):
            result = await sync_project(project, session)

        requested = set(blobs.await_args.kwargs["blob_shas"])
        assert requested == {"stories/US0001-one.md", "docs/NEW0001-new.md"}, (
            f"fetched the wrong set of blobs: {requested}"
        )

        assert result.fetch_path == "incremental"
        assert result.blobs_fetched == 2
        assert result.updated == 1
        assert result.added == 1
        assert result.skipped == 2  # EP0001 and PL0001, unchanged
        assert result.deleted == 0

        docs = {d.file_path: d for d in await _docs(session, project.id)}
        assert docs["stories/US0001-one.md"].status == "Done", "the changed file was not re-parsed"
        assert docs["epics/EP0001-one.md"].synced_at == untouched_before, (
            "an unchanged document was rewritten"
        )

    @pytest.mark.asyncio
    async def test_a_file_deleted_upstream_is_deleted_locally(self, session: AsyncSession) -> None:
        """Absence from the MANIFEST means deleted. Absence of CONTENT does not."""
        project = await _github_project(session)
        await _seed(session, project, FILES)

        remaining = {p: c for p, c in FILES.items() if p != "plans/PL0001-one.md"}

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_github_tree",
                new_callable=AsyncMock,
                return_value=_tree(remaining),
            ),
            patch(
                "sdlc_lens.services.github_source.fetch_github_blobs",
                new_callable=AsyncMock,
                return_value={},
            ) as blobs,
        ):
            result = await sync_project(project, session)

        assert result.deleted == 1
        assert result.skipped == 2
        assert blobs.await_args.kwargs["blob_shas"] == {}, "a deletion should cost no blob fetches"
        assert {d.file_path for d in await _docs(session, project.id)} == set(remaining)

    @pytest.mark.asyncio
    async def test_a_rate_limit_mid_fetch_leaves_the_corpus_intact(
        self, session: AsyncSession
    ) -> None:
        """A throttled fetch must cost the user NOTHING. Never a partial write."""
        project = await _github_project(session)
        await _seed(session, project, FILES)
        before = {d.file_path: (d.status, d.synced_at) for d in await _docs(session, project.id)}

        edited = dict(FILES)
        edited["stories/US0001-one.md"] = b"# US0001\n\n> **Status:** Done\n\nEDITED"

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_github_tree",
                new_callable=AsyncMock,
                return_value=_tree(edited),
            ),
            patch(
                "sdlc_lens.services.github_source.fetch_github_blobs",
                new_callable=AsyncMock,
                side_effect=RateLimitError("GitHub API rate limit exceeded"),
            ),
        ):
            result = await sync_project(project, session)

        assert project.sync_status == "error"
        assert "rate limit" in (project.sync_error or "").lower()
        assert (result.added, result.updated, result.deleted) == (0, 0, 0)

        after = {d.file_path: (d.status, d.synced_at) for d in await _docs(session, project.id)}
        assert after == before, "a rate-limited sync wrote to the corpus"


class TestConfigIsDiffedForFree:
    @pytest.mark.asyncio
    async def test_unchanged_config_costs_no_blob_request(self, session: AsyncSession) -> None:
        """The Trees response reports the config's blob SHA for free, so use it.

        Re-fetching .config.yaml on every sync would break the "zero blob requests when
        nothing changed" guarantee for the sake of two files that almost never move.
        """
        project = await _github_project(session)
        config_bytes = b"schema_version: 3\n"

        with patch(
            "sdlc_lens.services.github_source.fetch_github_files_and_config",
            new_callable=AsyncMock,
            return_value=(_tarball_return(FILES)[0], {".config.yaml": config_bytes}),
        ):
            await sync_project(project, session)

        stored = json.loads(project.config_blob_shas)
        assert stored == {".config.yaml": compute_blob_sha(config_bytes)}

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_github_tree",
                new_callable=AsyncMock,
                return_value=RepoTree(
                    md_blobs={p: compute_blob_sha(c) for p, c in FILES.items()},
                    config_blobs={".config.yaml": compute_blob_sha(config_bytes)},
                ),
            ),
            patch(
                "sdlc_lens.services.github_source.fetch_github_blobs",
                new_callable=AsyncMock,
                return_value={},
            ) as blobs,
        ):
            result = await sync_project(project, session)

        assert result.blobs_fetched == 0, "an unchanged config was re-fetched"
        assert blobs.await_args.kwargs["blob_shas"] == {}

    @pytest.mark.asyncio
    async def test_a_changed_config_is_refetched(self, session: AsyncSession) -> None:
        """The converse: a config edit must not be ignored just because no doc moved.

        .config.yaml drives status canonicalisation, so silently skipping it would leave
        every document parsed against a stale vocabulary.
        """
        project = await _github_project(session)
        old_config = b"schema_version: 3\n"

        with patch(
            "sdlc_lens.services.github_source.fetch_github_files_and_config",
            new_callable=AsyncMock,
            return_value=(_tarball_return(FILES)[0], {".config.yaml": old_config}),
        ):
            await sync_project(project, session)

        new_config = b"schema_version: 3\nprofile: strict\n"

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_github_tree",
                new_callable=AsyncMock,
                return_value=RepoTree(
                    md_blobs={p: compute_blob_sha(c) for p, c in FILES.items()},
                    config_blobs={".config.yaml": compute_blob_sha(new_config)},
                ),
            ),
            patch(
                "sdlc_lens.services.github_source.fetch_github_blobs",
                new_callable=AsyncMock,
                side_effect=lambda **kw: {k: new_config for k in kw["blob_shas"]},
            ) as blobs,
        ):
            result = await sync_project(project, session)

        requested = list(blobs.await_args.kwargs["blob_shas"])
        assert len(requested) == 1, "the changed config was not re-fetched"
        assert requested[0].endswith(".config.yaml")
        assert result.fetch_path == "incremental"
        assert project.profile == "strict", "the config edit was not applied"


class TestLocalSourceIsUntouched:
    @pytest.mark.asyncio
    async def test_a_local_project_never_calls_github(
        self, session: AsyncSession, tmp_path
    ) -> None:
        sdlc = tmp_path / "sdlc-studio"
        (sdlc / "epics").mkdir(parents=True)
        (sdlc / "epics" / "EP0001-one.md").write_bytes(EPIC)

        project = Project(slug="loc", name="Loc", source_type="local", sdlc_path=str(sdlc))
        session.add(project)
        await session.commit()
        await session.refresh(project)

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_github_tree", new_callable=AsyncMock
            ) as tree,
            patch(
                "sdlc_lens.services.github_source.fetch_github_blobs", new_callable=AsyncMock
            ) as blobs,
        ):
            result = await sync_project(project, session)

        assert tree.await_count == 0
        assert blobs.await_count == 0
        assert result.fetch_path == "local"
        assert result.added == 1

        # And its documents still carry a blob_sha, computed locally.
        doc = (await _docs(session, project.id))[0]
        assert doc.blob_sha == compute_blob_sha(EPIC)


class TestNonDocumentFilesAreNotChasedForever:
    @pytest.mark.asyncio
    async def test_index_md_never_costs_a_blob_request(self, session: AsyncSession) -> None:
        """`_index.md` is in the repo but is NEVER stored as a document.

        `infer_type_and_id` returns None for it, so it never lands in `existing_docs` -
        which means a naive diff calls it "changed" on EVERY sync, FOR EVER. A real
        sdlc-studio repo has one per artefact folder (this one has ten), so a
        "nothing changed" sync would silently re-download ten blobs every single time and
        report "10 file(s) changed" to an operator who changed nothing.

        The local walker already filters these out. The GitHub manifest must agree with it
        about what a live path is, or the two sources disagree about what was deleted.
        """
        project = await _github_project(session)

        with_indexes = dict(FILES)
        with_indexes["epics/_index.md"] = b"# Epics index\n\n- EP0001\n"
        with_indexes["stories/_index.md"] = b"# Stories index\n\n- US0001\n"

        await _seed(session, project, with_indexes)

        # Only the three real documents were stored - the indexes are not documents.
        stored = {d.file_path for d in await _docs(session, project.id)}
        assert stored == set(FILES), f"an _index.md was stored as a document: {stored}"

        # Now a no-op sync, three times over. It must stay at zero blobs, for ever.
        for attempt in range(3):
            with (
                patch(
                    "sdlc_lens.services.github_source.fetch_github_tree",
                    new_callable=AsyncMock,
                    return_value=_tree(with_indexes),
                ),
                patch(
                    "sdlc_lens.services.github_source.fetch_github_blobs",
                    new_callable=AsyncMock,
                    return_value={},
                ) as blobs,
            ):
                result = await sync_project(project, session)

            requested = blobs.await_args.kwargs["blob_shas"]
            assert requested == {}, (
                f"sync #{attempt + 1} re-fetched {list(requested)} on a no-op sync - "
                "an _index.md is being chased for ever"
            )
            assert result.blobs_fetched == 0
            assert result.fetch_reason == "nothing changed upstream", (
                f"sync #{attempt + 1} told the operator {result.fetch_reason!r} "
                "when nothing had changed"
            )
            assert result.deleted == 0, "an _index.md absent from existing_docs was 'deleted'"
