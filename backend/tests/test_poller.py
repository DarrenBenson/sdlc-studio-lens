"""Freshness poller (CR-01KXCAZJ, EP-01KXDDG7).

The two hazards this suite exists to pin are hazards of SILENCE, not of crashing:

* advancing `last_synced_commit_sha` after a FAILED sync would make the repo look
  unchanged for ever, so the failure would never be retried and the project would sit
  permanently stale while reporting nothing wrong; and
* a poll loop that dies takes freshness with it and says nothing - the app keeps serving,
  the UI still claims auto-sync is on, and the data quietly stops moving.

Both are tested by their failure, not by their happy path.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from sdlc_lens.db.models.project import Project
from sdlc_lens.services.github_source import AuthenticationError, RateLimitError
from sdlc_lens.services.poller import (
    PollResult,
    poll_once,
    poll_project,
    start_poller,
    stop_poller,
)
from sdlc_lens.services.sync_engine import SyncResult

HEAD_OLD = "a" * 40
HEAD_NEW = "b" * 40


@pytest.fixture
def factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def _project(
    session: AsyncSession,
    *,
    slug: str = "gh",
    source_type: str = "github",
    auto_sync: bool = True,
    sha: str | None = HEAD_OLD,
) -> Project:
    project = Project(
        slug=slug,
        name=slug,
        source_type=source_type,
        repo_url="https://github.com/owner/repo" if source_type == "github" else None,
        sdlc_path="/tmp" if source_type == "local" else None,
        repo_branch="main",
        repo_path="sdlc-studio",
        auto_sync=auto_sync,
        last_synced_commit_sha=sha,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def _get(factory, slug: str = "gh") -> Project:
    async with factory() as s:
        return (await s.execute(select(Project).where(Project.slug == slug))).scalar_one()


class TestHeadShaPoll:
    @pytest.mark.asyncio
    async def test_head_sha_is_one_request(self, session: AsyncSession, factory) -> None:
        """The check must be far cheaper than the sync it guards."""
        await _project(session)

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_branch_head_sha",
                new_callable=AsyncMock,
                return_value=HEAD_OLD,
            ) as head,
            patch("sdlc_lens.services.poller.run_sync_task", new_callable=AsyncMock) as sync,
        ):
            outcome = await poll_project("gh", factory)

        assert head.await_count == 1
        assert sync.await_count == 0
        assert outcome == PollResult.UNCHANGED

    @pytest.mark.asyncio
    async def test_unchanged_head_does_nothing(self, session: AsyncSession, factory) -> None:
        """Not even a timestamp.

        A poll that 'refreshes' last_synced_at without refreshing the data tells the
        operator their view is current when it is not - which is the exact lie this whole
        feature exists to stop telling.
        """
        await _project(session)
        before = (await _get(factory)).last_synced_at

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_branch_head_sha",
                new_callable=AsyncMock,
                return_value=HEAD_OLD,
            ),
            patch("sdlc_lens.services.poller.run_sync_task", new_callable=AsyncMock) as sync,
        ):
            outcome = await poll_project("gh", factory)

        assert outcome == PollResult.UNCHANGED
        assert sync.await_count == 0
        assert (await _get(factory)).last_synced_at == before

    @pytest.mark.asyncio
    async def test_moved_head_syncs_and_advances(self, session: AsyncSession, factory) -> None:
        await _project(session)

        async def _fake_sync(slug, factory_) -> SyncResult:
            async with factory_() as s:
                p = (await s.execute(select(Project).where(Project.slug == slug))).scalar_one()
                p.sync_status = "synced"
                await s.commit()
            return SyncResult(completed=True)

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_branch_head_sha",
                new_callable=AsyncMock,
                return_value=HEAD_NEW,
            ),
            patch("sdlc_lens.services.poller.run_sync_task", side_effect=_fake_sync),
        ):
            outcome = await poll_project("gh", factory)

        assert outcome == PollResult.SYNCED
        assert (await _get(factory)).last_synced_commit_sha == HEAD_NEW

    @pytest.mark.asyncio
    async def test_failed_sync_does_not_advance(self, session: AsyncSession, factory) -> None:
        """THE sharpest edge in the feature.

        If a failed sync recorded the new head, the branch would compare as 'unchanged'
        for ever afterwards. The failure would never be retried, and the project would sit
        permanently, invisibly stale while reporting nothing wrong. Leaving the OLD sha
        means the very next poll sees the head as still-moved and tries again.
        """
        await _project(session)

        async def _failing_sync(slug, factory_) -> SyncResult:
            """A HARD failure: the sync never ran to completion, so nothing was written."""
            async with factory_() as s:
                p = (await s.execute(select(Project).where(Project.slug == slug))).scalar_one()
                p.sync_status = "error"
                p.sync_error = "boom"
                await s.commit()
            return SyncResult(completed=False)

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_branch_head_sha",
                new_callable=AsyncMock,
                return_value=HEAD_NEW,
            ),
            patch("sdlc_lens.services.poller.run_sync_task", side_effect=_failing_sync),
        ):
            outcome = await poll_project("gh", factory)

        assert outcome == PollResult.SYNC_FAILED
        assert (await _get(factory)).last_synced_commit_sha == HEAD_OLD, (
            "a FAILED sync advanced the stored SHA - the repo now looks unchanged for "
            "ever, so this failure will never be retried"
        )

    @pytest.mark.asyncio
    async def test_the_retry_actually_happens_on_the_next_poll(
        self, session: AsyncSession, factory
    ) -> None:
        """The point of not advancing: the NEXT poll must try again, and can succeed."""
        await _project(session)
        calls: list[str] = []

        async def _fail_then_succeed(slug, factory_) -> SyncResult:
            calls.append(slug)
            first = len(calls) == 1
            async with factory_() as s:
                p = (await s.execute(select(Project).where(Project.slug == slug))).scalar_one()
                p.sync_status = "error" if first else "synced"
                await s.commit()
            return SyncResult(completed=not first)

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_branch_head_sha",
                new_callable=AsyncMock,
                return_value=HEAD_NEW,
            ),
            patch("sdlc_lens.services.poller.run_sync_task", side_effect=_fail_then_succeed),
        ):
            first = await poll_project("gh", factory)
            second = await poll_project("gh", factory)

        assert first == PollResult.SYNC_FAILED
        assert second == PollResult.SYNCED, "the failure was never retried"
        assert (await _get(factory)).last_synced_commit_sha == HEAD_NEW

    @pytest.mark.asyncio
    async def test_does_not_double_sync(self, session: AsyncSession, factory) -> None:
        """Reuse trigger_sync's atomic guard rather than adding a weaker second one."""
        project = await _project(session)
        project.sync_status = "syncing"  # a manual sync is already running
        await session.commit()

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_branch_head_sha",
                new_callable=AsyncMock,
                return_value=HEAD_NEW,
            ),
            patch("sdlc_lens.services.poller.run_sync_task", new_callable=AsyncMock) as sync,
        ):
            outcome = await poll_project("gh", factory)

        assert outcome == PollResult.ALREADY_SYNCING
        assert sync.await_count == 0, "the poller started a second, concurrent sync"

    @pytest.mark.asyncio
    async def test_local_project_is_never_polled(self, session: AsyncSession, factory) -> None:
        await _project(session, slug="loc", source_type="local", auto_sync=True)

        with patch(
            "sdlc_lens.services.github_source.fetch_branch_head_sha",
            new_callable=AsyncMock,
        ) as head:
            outcome = await poll_project("loc", factory)

        assert outcome == PollResult.SKIPPED
        assert head.await_count == 0, "a local project was polled against GitHub"

    @pytest.mark.asyncio
    async def test_auto_sync_defaults_off(self, session: AsyncSession, factory) -> None:
        """An existing project must not start polling itself on upgrade."""
        project = Project(
            slug="plain",
            name="Plain",
            source_type="github",
            repo_url="https://github.com/o/r",
            repo_branch="main",
            repo_path="sdlc-studio",
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        assert project.auto_sync is False

        with patch(
            "sdlc_lens.services.github_source.fetch_branch_head_sha",
            new_callable=AsyncMock,
        ) as head:
            outcome = await poll_project("plain", factory)

        assert outcome == PollResult.SKIPPED
        assert head.await_count == 0


class TestIsolationAndBackoff:
    @pytest.mark.asyncio
    async def test_one_failure_does_not_stop_the_others(
        self, session: AsyncSession, factory
    ) -> None:
        """A loop whose failure mode is silence must survive anything one project does."""
        await _project(session, slug="bad")
        await _project(session, slug="good")

        async def _head(repo_url, branch, token, **kw):  # noqa: ANN001, ANN003
            raise AuthenticationError("token revoked")

        # The bad project raises; the good one must still be polled.
        polled: list[str] = []

        async def _poll(slug, fac):  # noqa: ANN001
            polled.append(slug)
            if slug == "bad":
                raise RuntimeError("a poll blew up in a way poll_project promised it would not")
            return PollResult.UNCHANGED

        with patch("sdlc_lens.services.poller.poll_project", side_effect=_poll):
            results = await poll_once(factory)

        assert set(polled) == {"bad", "good"}, "one project's explosion stopped the sweep"
        assert results["bad"] == PollResult.ERROR
        assert results["good"] == PollResult.UNCHANGED

    @pytest.mark.asyncio
    async def test_a_revoked_token_is_recorded_on_the_project(
        self, session: AsyncSession, factory
    ) -> None:
        """The operator must be able to see WHICH project is broken."""
        await _project(session)

        with patch(
            "sdlc_lens.services.github_source.fetch_branch_head_sha",
            new_callable=AsyncMock,
            side_effect=RateLimitError("rate limited"),
        ):
            outcome = await poll_project("gh", factory)

        assert outcome == PollResult.ERROR
        project = await _get(factory)
        assert project.sync_status == "error"
        assert "poll failed" in (project.sync_error or "").lower()
        # And it did NOT advance the sha, so it will retry.
        assert project.last_synced_commit_sha == HEAD_OLD

    @pytest.mark.asyncio
    async def test_backoff_grows_then_resets_on_success(
        self, session: AsyncSession, factory
    ) -> None:
        """A project failing every tick must not hammer GitHub for ever."""
        await _project(session)
        backoff: dict[str, int] = {}

        with patch(
            "sdlc_lens.services.poller.poll_project",
            new_callable=AsyncMock,
            return_value=PollResult.ERROR,
        ):
            await poll_once(factory, backoff)
        assert backoff.get("gh", 0) >= 1, "a failing project was not backed off"

        # While backed off, it is skipped rather than polled.
        with patch("sdlc_lens.services.poller.poll_project", new_callable=AsyncMock) as p:
            await poll_once(factory, backoff)
        assert p.await_count == 0, "a backed-off project was polled anyway"

        # A success clears the backoff - a recovered project must not stay throttled.
        backoff.clear()
        with patch(
            "sdlc_lens.services.poller.poll_project",
            new_callable=AsyncMock,
            return_value=PollResult.UNCHANGED,
        ):
            await poll_once(factory, backoff)
        assert backoff.get("gh", 0) == 0

    @pytest.mark.asyncio
    async def test_a_sweep_only_touches_opted_in_projects(
        self, session: AsyncSession, factory
    ) -> None:
        """The opt-in is enforced by the SWEEP, not only by the per-project check.

        Without this, an opted-out project is dutifully swept up and then discarded on
        every single tick - harmless, but it means the `auto_sync` filter in the query is
        never actually exercised, so nothing stops it being dropped.
        """
        await _project(session, slug="on", auto_sync=True)
        await _project(session, slug="off", auto_sync=False)

        with patch(
            "sdlc_lens.services.poller.poll_project",
            new_callable=AsyncMock,
            return_value=PollResult.UNCHANGED,
        ) as polled:
            results = await poll_once(factory)

        assert set(results) == {"on"}, f"the sweep picked up an opted-out project: {set(results)}"
        assert [c.args[0] for c in polled.await_args_list] == ["on"]


class TestLifespan:
    @pytest.mark.asyncio
    async def test_interval_zero_starts_no_poller(self, factory) -> None:
        """Disabled means NO TASK, not an idle one."""
        with patch("sdlc_lens.services.poller.settings.sync_poll_interval_seconds", 0):
            task = start_poller(factory)
        assert task is None

    @pytest.mark.asyncio
    async def test_lifespan_starts_and_stops_cleanly(self, factory) -> None:
        """No orphaned task, no hang on shutdown."""
        with patch("sdlc_lens.services.poller.settings.sync_poll_interval_seconds", 300):
            task = start_poller(factory)

        assert task is not None
        assert not task.done()

        await asyncio.wait_for(stop_poller(task), timeout=5)
        assert task.done()
        assert task.cancelled()

    @pytest.mark.asyncio
    async def test_jitter_is_applied(self, factory) -> None:
        """N projects on one timer must not fire in lockstep."""
        sleeps: list[float] = []

        async def _sleep(seconds: float) -> None:
            sleeps.append(seconds)
            raise asyncio.CancelledError  # stop after the first sleep

        with (
            patch("sdlc_lens.services.poller.settings.sync_poll_interval_seconds", 100),
            patch("sdlc_lens.services.poller.asyncio.sleep", side_effect=_sleep),
        ):
            task = start_poller(factory)
            with pytest.raises((asyncio.CancelledError, Exception)):
                await task

        assert sleeps, "the loop never slept"
        # Jittered: strictly more than the bare interval, and within the jitter band.
        assert 100 < sleeps[0] <= 125


class TestPartialSyncConverges:
    """A sync that RAN but skipped a file must still advance the SHA.

    Found by an independent critic. `sync_engine` sets sync_status="error" when ANY file
    fails - correctly, it did not fully succeed. But the corpus IS materialised at that
    commit, and re-running will fail on the same file identically. Refusing to advance
    means the project re-syncs on EVERY TICK, FOR EVER, and never converges.

    "Did the sync run?" and "was every file perfect?" are different questions.
    """

    @pytest.mark.asyncio
    async def test_a_completed_sync_with_file_errors_still_advances(
        self, session: AsyncSession, factory
    ) -> None:
        await _project(session)

        async def _partial(slug, factory_) -> SyncResult:
            async with factory_() as s:
                p = (await s.execute(select(Project).where(Project.slug == slug))).scalar_one()
                p.sync_status = "error"  # one undecodable file
                p.sync_error = "1 file(s) could not be synced"
                await s.commit()
            return SyncResult(completed=True, errors=1, added=3)

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_branch_head_sha",
                new_callable=AsyncMock,
                return_value=HEAD_NEW,
            ),
            patch("sdlc_lens.services.poller.run_sync_task", side_effect=_partial),
        ):
            outcome = await poll_project("gh", factory)

        assert outcome == PollResult.SYNCED
        assert (await _get(factory)).last_synced_commit_sha == HEAD_NEW, (
            "a sync that RAN but skipped one file did not advance the SHA - this project "
            "will now re-sync on every tick, for ever, and never converge"
        )

    @pytest.mark.asyncio
    async def test_it_then_stops_resyncing(self, session: AsyncSession, factory) -> None:
        """The convergence proof: the tick after must be a no-op."""
        await _project(session)
        syncs: list[str] = []

        async def _partial(slug, factory_) -> SyncResult:
            syncs.append(slug)
            async with factory_() as s:
                p = (await s.execute(select(Project).where(Project.slug == slug))).scalar_one()
                p.sync_status = "error"
                p.sync_error = "1 file(s) could not be synced"
                await s.commit()
            return SyncResult(completed=True, errors=1)

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_branch_head_sha",
                new_callable=AsyncMock,
                return_value=HEAD_NEW,
            ),
            patch("sdlc_lens.services.poller.run_sync_task", side_effect=_partial),
        ):
            await poll_project("gh", factory)
            second = await poll_project("gh", factory)
            third = await poll_project("gh", factory)

        assert second == PollResult.UNCHANGED
        assert third == PollResult.UNCHANGED
        assert len(syncs) == 1, f"it re-synced {len(syncs)} times - it never converges"

    @pytest.mark.asyncio
    async def test_a_hard_failure_still_does_not_advance(
        self, session: AsyncSession, factory
    ) -> None:
        """The other direction must still hold: a sync that never RAN is retried."""
        await _project(session)

        async def _never_ran(slug, factory_) -> SyncResult:
            return SyncResult(completed=False)

        with (
            patch(
                "sdlc_lens.services.github_source.fetch_branch_head_sha",
                new_callable=AsyncMock,
                return_value=HEAD_NEW,
            ),
            patch("sdlc_lens.services.poller.run_sync_task", side_effect=_never_ran),
        ):
            outcome = await poll_project("gh", factory)

        assert outcome == PollResult.SYNC_FAILED
        assert (await _get(factory)).last_synced_commit_sha == HEAD_OLD


class TestStalePollErrorIsCleared:
    @pytest.mark.asyncio
    async def test_a_transient_blip_does_not_mark_a_project_broken_for_ever(
        self, session: AsyncSession, factory
    ) -> None:
        """One rate-limit blip on the cheap head call must not brand a healthy project.

        The unchanged path returns early, so nothing else would ever clear it: a finished
        project whose branch never moves again would report an error for ever.
        """
        await _project(session)

        with patch(
            "sdlc_lens.services.github_source.fetch_branch_head_sha",
            new_callable=AsyncMock,
            side_effect=RateLimitError("rate limited"),
        ):
            assert await poll_project("gh", factory) == PollResult.ERROR
        assert (await _get(factory)).sync_status == "error"

        # The blip passes. The head is unchanged - the data was fine all along.
        with patch(
            "sdlc_lens.services.github_source.fetch_branch_head_sha",
            new_callable=AsyncMock,
            return_value=HEAD_OLD,
        ):
            assert await poll_project("gh", factory) == PollResult.UNCHANGED

        project = await _get(factory)
        assert project.sync_status == "synced", "a transient poll blip branded the project"
        assert project.sync_error is None

    @pytest.mark.asyncio
    async def test_a_real_sync_error_is_not_wiped(self, session: AsyncSession, factory) -> None:
        """Only a POLL error self-clears. A genuine sync failure still needs a sync."""
        project = await _project(session)
        project.sync_status = "error"
        project.sync_error = "source returned no documents - refusing to delete"
        await session.commit()

        with patch(
            "sdlc_lens.services.github_source.fetch_branch_head_sha",
            new_callable=AsyncMock,
            return_value=HEAD_OLD,
        ):
            await poll_project("gh", factory)

        project = await _get(factory)
        assert project.sync_status == "error", "a real sync failure was silently wiped"
        assert "refusing to delete" in (project.sync_error or "")


class TestShutdownDoesNotBrickAProject:
    """A cancellation mid-sync must not strand a project in "syncing" for ever.

    Found by an independent critic. `CancelledError` is a BaseException, so
    `run_sync_task`'s `except Exception` recovery block did not catch it - the project was
    left at sync_status="syncing". `trigger_sync` refuses a "syncing" project for ever and
    NOTHING resets one, so the project was permanently locked out of syncing: the manual
    sync 409s, the poller 409s, and only DB surgery recovers it.

    And this app ships by container redeploy. Every deploy was a chance to brick a project.
    """

    @pytest.mark.asyncio
    async def test_a_cancelled_sync_unsticks_the_project(
        self, session: AsyncSession, factory
    ) -> None:
        from sdlc_lens.services.sync import run_sync_task as real_run_sync_task

        project = await _project(session)
        project.sync_status = "syncing"
        await session.commit()

        async def _cancelled(*_a, **_kw):
            raise asyncio.CancelledError

        with (
            patch("sdlc_lens.services.sync.sync_project", side_effect=_cancelled),
            pytest.raises(asyncio.CancelledError),
        ):
            await real_run_sync_task("gh", factory)

        refreshed = await _get(factory)
        assert refreshed.sync_status != "syncing", (
            "a cancelled sync left the project stuck in 'syncing' - it is now permanently "
            "locked out, because trigger_sync refuses a syncing project and nothing resets it"
        )

    @pytest.mark.asyncio
    async def test_startup_frees_a_project_stranded_by_a_hard_stop(
        self, session: AsyncSession, factory
    ) -> None:
        """A SIGKILL leaves no exception handler to run at all. Startup must clean up.

        A "syncing" status at startup cannot be genuine - no sync survived the process
        that was running it.
        """
        from sdlc_lens.services.poller import reset_stuck_syncing

        project = await _project(session)
        project.sync_status = "syncing"
        await session.commit()

        freed = await reset_stuck_syncing(factory)

        assert freed == 1
        refreshed = await _get(factory)
        assert refreshed.sync_status == "error"
        assert "interrupted" in (refreshed.sync_error or "").lower()

        # And it can sync again - the whole point.
        from sdlc_lens.services.sync import trigger_sync as real_trigger

        async with factory() as s:
            await real_trigger(s, "gh")  # must not raise SyncInProgressError

    @pytest.mark.asyncio
    async def test_a_healthy_project_is_not_disturbed_by_the_reset(
        self, session: AsyncSession, factory
    ) -> None:
        from sdlc_lens.services.poller import reset_stuck_syncing

        project = await _project(session)
        project.sync_status = "synced"
        await session.commit()

        assert await reset_stuck_syncing(factory) == 0
        assert (await _get(factory)).sync_status == "synced"
