# US-01KXDD0K: Run the poller in-process, isolated per project, and shut it down cleanly

> **Status:** Done
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Triaged-by:** Darren; human; v3
> **Epic:** EP-01KXDDG7
> **Change Request:** [CR-01KXCAZJ](../change-requests/CR-01KXCAZJ-commit-sha-poll-trigger-to-keep-github-projects.md)
> **Depends on:** US-01KXDD5K
> **Persona:** Priya Nair (Engineering amigo)
> **Priority:** Medium
> **Story Points:** 3

## User Story

**As an** operator running the lens in a single container
**I want** the poller to live inside the app, survive any one project's failure, and stop when the app stops
**So that** freshness is automatic without me owning a scheduler, and a bad token on one project cannot take it down

## Background

RFC-01KXARHK D2: an **in-process asyncio task**. The deployment is one container running one Uvicorn worker,
so there is no multi-worker duplicate-poll problem and no external scheduler to own.

The danger with any unattended loop is that **its failure mode is silence**. A task that raises and dies
does not crash the app - it simply stops polling, for ever, and nothing says so. Freshness quietly reverts
to "whenever someone last pressed Sync", which is the exact condition this epic exists to end, now with the
added insult that the UI claims auto-sync is on.

So: every project's poll is isolated; no single project's exception can escape into the loop; and repeated
failures back off instead of hammering a rate limit every tick.

## Acceptance Criteria

### AC1: The poller starts with the app and stops cleanly with it

- **Given** an in-process background task
- **When** the app starts and later shuts down
- **Then** the task starts in the FastAPI lifespan and is cancelled and awaited on shutdown - no orphaned task, no hang on reload
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_poller.py -q -k lifespan
- **Verified:** yes (2026-07-13)

### AC2: `interval = 0` starts no poller at all

- **Given** an operator who does not want polling
- **When** the interval is configured as `0`
- **Then** no task is created - the feature is genuinely off, not merely idle
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_poller.py -q -k interval_zero_starts_no_poller
- **Verified:** yes (2026-07-13)

### AC3: One project's failure cannot stop the others, or the loop

- **Given** a revoked token, a rate limit, a deleted repo or a deleted branch
- **When** that project's poll raises
- **Then** its own `sync_status` becomes `error` with a legible message, **the other projects still poll**, and the loop survives to the next tick. An exception must never escape a per-project poll
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_poller.py -q -k one_failure_does_not_stop_the_others
- **Verified:** yes (2026-07-13)

### AC4: Repeated failures back off

- **Given** a project failing every tick (an expired token, say)
- **When** it keeps failing
- **Then** its poll interval backs off rather than hammering GitHub - and a later success resets the backoff
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_poller.py -q -k backoff
- **Verified:** yes (2026-07-13)

### AC5: The sweep's period is jittered, and the sweep itself is sequential

- **Given** the sweep polls projects **sequentially**, one after another - so N projects cannot stampede GitHub in parallel, whatever the timing
- **When** the loop waits between sweeps
- **Then** the wait is jittered, so N *lenses* (or N restarts of the same lens) do not align on the same second and hit GitHub together
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_poller.py -q -k jitter

> **This AC was wrong, and it was stamped `Verified: yes` on a test that did not test it.**
> It originally read *"Given N projects on one timer ... their polls are jittered rather than firing
> in lockstep"* - but the code jitters the **loop's sleep**, not each project's poll, and inside a sweep
> the projects are polled back-to-back with no delay. They *do* fire in lockstep. The test
> (`test_jitter_is_applied`) creates **zero projects** and only asserts the loop sleep lies in the jitter
> band, so it could never have caught the discrepancy.
>
> An independent critic found it. The code is fine - a sequential sweep cannot stampede anything - but
> the AC described behaviour the code does not have, and the verifier agreed with the AC rather than with
> reality. Under this project's own doctrine (*never hand-stamp `Verified:` for an AC a machine did not
> check*) the AC is the defect. Restated to what is actually true and actually checked.
- **Verified:** yes (2026-07-13)

### AC6: The poller is mutation-checked on isolation

- **Given** a loop whose failure mode is silence (LL0010)
- **When** the per-project exception guard is removed
- **Then** a test goes red - proving the guard is load-bearing, not decorative
- **Verify:** manual remove the per-project try/except, run the suite, confirm red, revert

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCAZJ (RFC D2) |
