# BG-01KXDFGD: A project interrupted mid-sync is stuck in "syncing" for ever and can never sync again

> **Status:** Fixed
> **Severity:** High
> **Verification depth:** functional
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Triaged-by:** Darren; human; v3
> **Related:** CR-01KXCAZJ (found while building it), US-01KXDD0K (fixed here)

## Summary

`trigger_sync()` refuses any project whose `sync_status` is already `"syncing"` - the atomic guard that
stops a double-sync. But **nothing anywhere resets a stuck `"syncing"`**. A grep confirms it: that value is
only ever *set*, never cleared on startup.

So a process killed mid-sync - a container redeploy, an OOM, a SIGKILL - leaves the status behind with no
task alive to clear it. The project is then **permanently locked out of syncing**: the manual sync 409s,
the poller 409s, and only surgery on the database recovers it.

`run_sync_task`'s recovery block caught `Exception`. **`asyncio.CancelledError` is a `BaseException`**, so
a cancellation - exactly what an app shutdown delivers into an in-flight sync - sailed straight past it.

The freshness poller (CR-01KXCAZJ) turned this from theoretical into likely. A manual sync runs as a
FastAPI `BackgroundTask` inside the request lifecycle, which Uvicorn's graceful shutdown waits for. The
poller is a bare asyncio task that is cancelled immediately. **This app ships by container redeploy, so
every deploy became a chance to brick an auto-sync project.**

## Steps to Reproduce

Confirmed by an independent critic:

```
poll-triggered sync in flight; app shuts down
-> sync_status after shutdown: syncing
-> trigger_sync now raises SyncInProgressError, for ever
```

The project cannot be synced again by any route the UI offers.

## Proposed Fix

Two layers, because either alone is insufficient:

1. **`run_sync_task` catches `BaseException`**, unsticks the project, and re-raises the cancellation. This
   handles a graceful cancellation. It cannot handle a SIGKILL - no handler runs at all.
2. **Startup resets any project left in `"syncing"`.** A `"syncing"` status *at startup* cannot be genuine:
   no sync survived the process that was running it. So clear it, loudly, and tell the operator their data
   is intact and a re-sync will bring it current. This is the layer that survives a hard kill.

`stop_poller` also gains a grace period, so an in-flight sync is given a moment to finish properly rather
than being torn down mid-write.

The startup reset is best-effort: housekeeping must never stop the app from **booting**. A database that is
not ready yet is a reason to log and carry on, not to take the whole service down.

## Acceptance Criteria

- [x] A cancelled sync leaves the project in a syncable state, not `"syncing"`
- [x] A project stranded by a hard stop is freed at startup and can sync again
- [x] A healthy project is not disturbed by the reset
- [x] Startup housekeeping failing does not prevent the app booting
- [x] Mutation-checked: reverting `except BaseException` to `except Exception` turns a test red
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_poller.py -q -k TestShutdownDoesNotBrickAProject

## Lessons

- **`except Exception` does not catch a cancellation.** Any cleanup that must run on shutdown - and
  "release the lock I took" always must - has to catch `BaseException` and re-raise. An `except Exception`
  recovery block around work that can be cancelled is a lock leak waiting for a deploy.
- **A lock with no expiry and no reaper is a trap.** The `"syncing"` guard was correct and well-tested; it
  simply had no way back out if its owner died. Any status that BLOCKS an operation needs an answer to
  "what clears this if the thing holding it never returns?"

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | Darren | Found by an independent adversarial critic while reviewing the freshness poller. Pre-existing, but the poller made it likely on every redeploy. Fixed in the same change. |
