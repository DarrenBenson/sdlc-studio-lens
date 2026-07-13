# RETRO-0008: Poll-trigger sprint: the critic found three HIGH bugs in a 300-line feature

> **Date:** 2026-07-13
> **Batch:** CR-01KXCAZJ
> **Goal:** Keep GitHub projects fresh by polling the branch head and syncing only when it moves.
> **Delivered:** 1 / 1   **Blocked:** 0

## Delivered

- **CR-01KXCAZJ - the freshness poller.** One cheap call per tick asks "has this branch moved?"; unchanged
  costs one request and does nothing. Changed runs the incremental sync from EP-01KXCCA4 - which is the only
  reason polling is affordable at all. Per-project opt-in (`auto_sync`, default off), configurable interval
  (`0` disables entirely), sequential sweep with a jittered period, per-project isolation and backoff, clean
  lifespan start/stop.
- **BG-01KXDFGD (High, pre-existing)** - a project interrupted mid-sync was stuck in `syncing` for ever and
  could never sync again. Found while building the poller; fixed here.

## What went well

- **The incremental sync paid for itself immediately.** The poll is only viable because a re-sync is
  O(change). Last sprint's work is what made this one a 300-line feature instead of an unaffordable one.
- **Reusing `trigger_sync`'s atomic guard** rather than writing a second, weaker one meant the double-sync
  race was closed before it was opened.

## What was hard / what stalled

- **The critic found THREE confirmed HIGH bugs in ~300 lines**, and two of them were interaction bugs I
  created myself:
  1. **`fetch_branch_head_sha` had zero real coverage.** Every one of the nine references to it in the suite
     was a `patch(...)`. Deleting the single line that makes it work - the `Accept:
     application/vnd.github.sha` header - kept **all 803 tests green**. Without it GitHub returns an 18 KB
     JSON commit object, which can never equal a stored 40-char SHA: every auto-sync project would re-sync
     **on every tick, for ever**. This is the *same trap as the previous sprint*, in the same shape.
  2. **A partially-successful sync never converged.** In US-01KXCCMH *I* made `sync_engine` set
     `sync_status="error"` when any file fails. The poller advanced the SHA only on `"synced"`. So a repo
     with one undecodable `.md` could never advance - re-syncing every few ticks, for ever, permanently at
     `error`. "Did the sync run?" and "was every file perfect?" are different questions, and I had conflated
     them **across two sprints**.
  3. **Shutdown bricked a project.** `CancelledError` is a `BaseException`, so `run_sync_task`'s
     `except Exception` missed it and left the project in `syncing` - which `trigger_sync` refuses for ever,
     and which nothing resets. This app ships by container redeploy; every deploy was a chance to
     permanently lock a project out.
- **I stamped `Verified: yes` on an AC the test did not test.** AC5 claimed *"N projects' polls are jittered
  rather than firing in lockstep"*. The code jitters the **loop's sleep**; inside a sweep the projects poll
  back-to-back. The test creates **zero projects**. The code is fine - a sequential sweep cannot stampede -
  but the AC described behaviour that does not exist, and the verifier agreed with the AC rather than with
  reality. Under this project's own doctrine that is the defect.

## Lessons

- **A new function that only ever appears inside `patch(...)` is untested, however many tests "cover" it.**
  Grep the test suite for the symbol: if every hit is a mock, the function has no executable guard at all.
  This is the second sprint running that this exact shape has shipped a HIGH bug.
  <!-- promote the durable, cross-project ones: lessons add --global -->
- **"It failed" and "it did not run" are different, and a caller that conflates them will loop for ever.**
  A status field answering *"was everything perfect?"* cannot also answer *"is a retry worth anything?"* -
  and a retry loop keyed on the wrong one never converges.
- **`except Exception` does not catch a cancellation.** Any cleanup that releases a lock must catch
  `BaseException` and re-raise, or a routine shutdown leaks the lock permanently.
- **A lock with no expiry and no reaper is a trap.** The `syncing` guard was correct and well-tested; it
  simply had no way out if its owner died. Any status that BLOCKS an operation needs an answer to "what
  clears this if the holder never returns?"
- **When an AC and the code disagree, the verifier will side with whichever one you wrote the test against.**
  A `Verified: yes` is only as honest as the match between the AC's words and the test's assertions.

## Metrics

- Units: 1/1. Backend tests 785 -> 819 (+34). Frontend 250. Migration 014 (verified up **and** down).
  ruff + tsc + eslint clean.
- **Critic: 1 round, 7 findings - 3 HIGH, 2 MEDIUM, 2 LOW. All confirmed. 0 rejected as false.**
  Two were interaction bugs spanning two sprints; one (BG-01KXDFGD) was a latent production bug.
- Mutation: 9 mutants, 9 killed - including the header deletion that had kept 803 tests green.
