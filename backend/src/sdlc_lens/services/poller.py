"""Background freshness poller for GitHub projects (CR-01KXCAZJ, RFC-01KXARHK B2).

A GitHub project is only as fresh as the last time somebody pressed Sync. The lens then
serves a stale corpus - stale search, a stale health score, a stale tree - with nothing on
screen saying so.

So poll. One request returns the branch's head commit SHA; compare it with the SHA stored
at the last **successful** sync. Unchanged - the overwhelmingly common case - costs one
cheap request and does nothing at all. Changed runs the (incremental) sync.

Polling is only affordable *because* that re-sync is O(change) rather than O(repo)
(EP-01KXCCA4). A poll that fired a full tarball every few minutes would be worse than the
staleness it cures.

Two hazards shape this module, and both are hazards of SILENCE rather than of crashing:

* **Advancing the stored SHA on a FAILED sync.** The repo would then look unchanged for
  ever afterwards, so the failure would never be retried and the project would stay
  permanently, invisibly stale while reporting nothing wrong. The SHA advances only after
  the sync has actually succeeded.
* **A task that dies takes freshness with it and says nothing.** The app keeps serving; the
  UI still claims auto-sync is on; the data quietly stops moving. So no project's exception
  may escape into the loop, and the loop itself must survive anything a single project can
  do to it.

This is a SCHEDULER, not a second sync path. It reuses `trigger_sync()` (whose atomic
`UPDATE ... WHERE sync_status != 'syncing'` already closes the double-sync race) and
`run_sync_task()` (which already guarantees a project is never left stuck in "syncing").
If this module grows its own copy of either, that is a defect.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import random
from typing import TYPE_CHECKING

from sqlalchemy import select

from sdlc_lens.config import settings
from sdlc_lens.db.models.project import Project
from sdlc_lens.services.project import ProjectNotFoundError
from sdlc_lens.services.sync import SyncInProgressError, run_sync_task, trigger_sync
from sdlc_lens.services.sync_engine import resolve_sync_token

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)

# How much random jitter to apply to a project's poll, as a fraction of the interval. N
# projects on one timer would otherwise fire in lockstep and stampede GitHub every tick.
_JITTER_FRACTION = 0.25

# Marks a sync_error that came from the cheap freshness POLL rather than from a sync. Only
# these are cleared automatically when a later poll succeeds - a real sync error still
# needs a sync to fix it.
_POLL_ERROR_PREFIX = "Freshness poll failed: "


class PollResult:
    """Why nothing happened, or what did. Kept simple - the tests read these."""

    UNCHANGED = "unchanged"
    SYNCED = "synced"
    SYNC_FAILED = "sync_failed"
    ALREADY_SYNCING = "already_syncing"
    SKIPPED = "skipped"
    ERROR = "error"


async def poll_project(
    slug: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> str:
    """Poll one project. Returns a :class:`PollResult` value.

    Raises nothing: a failure here is recorded on the project and reported, never allowed
    to escape into the loop that called us.
    """
    async with session_factory() as session:
        project = (
            await session.execute(select(Project).where(Project.slug == slug))
        ).scalar_one_or_none()

        if project is None:
            return PollResult.SKIPPED
        # A local project has no branch and no remote. Never poll it.
        if project.source_type != "github" or not project.auto_sync or not project.repo_url:
            return PollResult.SKIPPED

        token = await resolve_sync_token(project)
        branch = project.repo_branch or "main"
        repo_url = project.repo_url
        stored_sha = project.last_synced_commit_sha

    # The one cheap question: has this branch moved? Outside the session - a network call
    # should never hold a DB connection open.
    from sdlc_lens.services.github_source import GitHubSourceError, fetch_branch_head_sha

    try:
        head = await fetch_branch_head_sha(repo_url, branch, token)
    except GitHubSourceError as exc:
        # A revoked token, a rate limit, a deleted repo or branch. Record it ON THE
        # PROJECT so the operator can see which one is broken, and report the failure so
        # the loop can back this project off. Do not raise.
        logger.warning("Poll failed for '%s': %s", slug, exc)
        async with session_factory() as session:
            project = (
                await session.execute(select(Project).where(Project.slug == slug))
            ).scalar_one_or_none()
            if project is not None and project.sync_status != "syncing":
                project.sync_status = "error"
                project.sync_error = f"{_POLL_ERROR_PREFIX}{exc}"
                await session.commit()
        return PollResult.ERROR

    if stored_sha == head:
        # Nothing moved. Do NOTHING to the data - in particular do not touch
        # last_synced_at. A poll that "refreshes" the timestamp without refreshing the
        # data is lying to the operator about how current their view is.
        #
        # But DO clear a previous poll failure. Otherwise one rate-limit blip on the cheap
        # head call leaves a perfectly healthy, fully-synced project reporting an error for
        # ever - until the branch happens to move again, which for a finished project may
        # be never.
        await _clear_stale_poll_error(slug, session_factory)
        return PollResult.UNCHANGED

    # The branch moved. Hand off to the ordinary sync path.
    async with session_factory() as session:
        try:
            await trigger_sync(session, slug)
        except SyncInProgressError:
            # A manual sync is already running. trigger_sync's atomic guard just saved us
            # from double-syncing; try again on the next tick.
            return PollResult.ALREADY_SYNCING
        except ProjectNotFoundError:
            # Deleted between our read and the trigger - a real window, since a network
            # call sits between them. This function promises not to raise; keep that
            # promise rather than letting the sweep's belt-and-braces guard absorb it.
            return PollResult.SKIPPED

    result = await run_sync_task(slug, session_factory)

    # Advance the stored SHA when the sync RAN TO COMPLETION - not when every file was
    # perfect. These are different questions, and conflating them is a trap in both
    # directions:
    #
    #   * Advance after a sync that never ran (a hard error, or the empty-source guard)
    #     and the branch looks "unchanged" for ever: the failure is never retried and the
    #     project sits permanently, invisibly stale while reporting nothing wrong.
    #
    #   * DON'T advance after a sync that ran but skipped one undecodable file - which
    #     sets sync_status="error" - and the project re-syncs on EVERY TICK, FOR EVER,
    #     never converging, because the same file will fail identically next time. The
    #     corpus IS materialised at this commit; it is simply as good as it will ever get.
    #
    # `SyncResult.completed` is the honest signal: it is set at the point the sync commits
    # the corpus, whatever the individual files did.
    if result is not None and result.completed:
        async with session_factory() as session:
            project = (
                await session.execute(select(Project).where(Project.slug == slug))
            ).scalar_one_or_none()
            if project is None:
                return PollResult.SKIPPED
            project.last_synced_commit_sha = head
            await session.commit()
        if result.errors:
            logger.info(
                "Poll synced '%s' to %s with %d file error(s); advancing anyway - "
                "re-running would fail identically and never converge",
                slug,
                head[:8],
                result.errors,
            )
        else:
            logger.info("Poll synced '%s' to %s", slug, head[:8])
        return PollResult.SYNCED

    logger.warning(
        "Poll-triggered sync of '%s' never completed; leaving last_synced_commit_sha at "
        "%s so the very next poll retries it",
        slug,
        (stored_sha or "NULL")[:8],
    )
    return PollResult.SYNC_FAILED


async def _clear_stale_poll_error(
    slug: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Undo a previous poll failure once a poll succeeds again.

    A poll failure writes sync_status="error" onto the project so the operator can see
    WHICH project is broken. But nothing else clears it: an unchanged head returns early,
    so one transient rate-limit blip would leave a healthy, fully-synced project reporting
    an error until its branch next moved - which, for a finished project, may be never.

    Only a *poll* error is cleared. A real sync error is left alone: that one still needs
    a sync to fix it, and silently wiping it would hide a genuine failure.
    """
    async with session_factory() as session:
        project = (
            await session.execute(select(Project).where(Project.slug == slug))
        ).scalar_one_or_none()
        if project is None:
            return
        if project.sync_status == "error" and (project.sync_error or "").startswith(
            _POLL_ERROR_PREFIX
        ):
            project.sync_status = "synced"
            project.sync_error = None
            await session.commit()
            logger.info("Poll for '%s' recovered; cleared the stale poll error", slug)


async def _due_projects(session_factory: async_sessionmaker[AsyncSession]) -> list[str]:
    """Slugs of the GitHub projects that have opted in to auto-sync."""
    async with session_factory() as session:
        rows = await session.execute(
            select(Project.slug).where(
                Project.auto_sync.is_(True),
                Project.source_type == "github",
            )
        )
        return list(rows.scalars().all())


async def poll_once(
    session_factory: async_sessionmaker[AsyncSession],
    backoff: dict[str, int] | None = None,
) -> dict[str, str]:
    """One sweep over every auto-sync project. Returns {slug: PollResult}.

    Each project is polled inside its own guard. **No project's failure may escape**: one
    expired token must not stop the other projects polling, and must not kill the loop.
    A loop that dies takes freshness with it and says nothing.
    """
    backoff = backoff if backoff is not None else {}
    results: dict[str, str] = {}

    for slug in await _due_projects(session_factory):
        # Exponential backoff: a project failing every tick (an expired token, say) is
        # skipped for a growing number of ticks rather than hammering GitHub for ever.
        if backoff.get(slug, 0) > 0:
            backoff[slug] -= 1
            results[slug] = PollResult.SKIPPED
            continue

        try:
            outcome = await poll_project(slug, session_factory)
        except Exception:
            # Belt and braces. poll_project is written not to raise, but this loop must
            # survive it doing so anyway - the cost of being wrong here is that freshness
            # silently stops for EVERY project.
            logger.exception("Unhandled error polling '%s'; the poller continues", slug)
            outcome = PollResult.ERROR

        results[slug] = outcome

        if outcome in (PollResult.ERROR, PollResult.SYNC_FAILED):
            # Back off 1, 2, 4, 8 ... ticks, capped DIRECTLY at the configured ceiling.
            # (An earlier version capped the *level* at `max_ticks.bit_length()`, which
            # with the defaults topped out at 8 ticks and never reached the configured 12
            # - the ceiling was simply unreachable. Cap the value, not the exponent.)
            max_ticks = max(
                1,
                settings.sync_poll_max_backoff_seconds
                // max(1, settings.sync_poll_interval_seconds),
            )
            previous = backoff.get(f"{slug}:level", 0)
            level = previous + 1
            backoff[f"{slug}:level"] = level
            backoff[slug] = min(2 ** (level - 1), max_ticks)
        else:
            # A success resets the backoff - a project that recovers must not stay
            # throttled.
            backoff.pop(slug, None)
            backoff.pop(f"{slug}:level", None)

    return results


async def _poll_loop(session_factory: async_sessionmaker[AsyncSession], interval: int) -> None:
    """The unattended loop. Never exits except by cancellation."""
    backoff: dict[str, int] = {}
    logger.info("Freshness poller started (interval=%ds)", interval)
    try:
        while True:
            # Jitter so N lenses (or N projects) do not stampede GitHub on the same second.
            await asyncio.sleep(interval * (1 + random.uniform(0, _JITTER_FRACTION)))  # noqa: S311
            try:
                await poll_once(session_factory, backoff)
            except Exception:
                # The loop must outlive ANY failure. If it dies, freshness stops for every
                # project and nothing says so.
                logger.exception("Poll sweep failed; the poller continues")
    except asyncio.CancelledError:
        logger.info("Freshness poller stopped")
        raise


def start_poller(session_factory: async_sessionmaker[AsyncSession]) -> asyncio.Task | None:
    """Start the poller, or return None when it is disabled.

    `interval = 0` creates NO TASK AT ALL. The feature is genuinely off rather than idling
    - a disabled poller should cost nothing and be visibly absent, not merely quiet.
    """
    interval = settings.sync_poll_interval_seconds
    if interval <= 0:
        logger.info("Freshness poller disabled (sync_poll_interval_seconds=%s)", interval)
        return None
    return asyncio.create_task(_poll_loop(session_factory, interval), name="sdlc-lens-poller")


async def stop_poller(task: asyncio.Task | None, grace_seconds: float = 10.0) -> None:
    """Cancel and AWAIT the poller, so shutdown leaves no orphan behind.

    A grace period first, because a cancellation delivered into a poll-triggered sync is
    a CancelledError - a BaseException - which for a long time slipped past
    `run_sync_task`'s recovery block and left the project stuck in "syncing". Nothing
    resets a stuck "syncing" mid-flight and `trigger_sync` refuses one for ever, so a
    routine container redeploy could permanently lock a project out of syncing.

    That hole is closed in `run_sync_task` (which now catches BaseException, unsticks the
    project, and re-raises). This grace period is the second belt: give an in-flight sync
    a moment to finish properly rather than tearing it down mid-write.
    """
    if task is None:
        return
    task.cancel()
    try:
        await asyncio.wait_for(asyncio.shield(_await_quietly(task)), timeout=grace_seconds)
    except TimeoutError:
        logger.warning("Poller did not stop within %.0fs; abandoning it", grace_seconds)


async def _await_quietly(task: asyncio.Task) -> None:
    with contextlib.suppress(asyncio.CancelledError):
        await task


async def reset_stuck_syncing(session_factory: async_sessionmaker[AsyncSession]) -> int:
    """Unstick any project left mid-sync by a hard stop. Returns how many were freed.

    `trigger_sync` refuses a project whose status is already "syncing" - the atomic guard
    that stops a double-sync. But a process killed mid-sync (a container redeploy, an OOM,
    a SIGKILL) leaves that status behind with no task to clear it, and NOTHING else ever
    resets it. The project is then permanently locked out: the manual sync 409s, the poller
    409s, and only DB surgery recovers it.

    A "syncing" status at STARTUP cannot be genuine - no sync can have survived the
    process that was running it. So clear it, loudly.
    """
    async with session_factory() as session:
        stuck = (
            (await session.execute(select(Project).where(Project.sync_status == "syncing")))
            .scalars()
            .all()
        )
        for project in stuck:
            logger.warning(
                "Project '%s' was left mid-sync by a hard stop; clearing it so it can sync again",
                project.slug,
            )
            project.sync_status = "error"
            project.sync_error = (
                "The previous sync was interrupted before it finished (the app stopped). "
                "No documents were lost; sync again to bring it up to date."
            )
        if stuck:
            await session.commit()
        return len(stuck)
