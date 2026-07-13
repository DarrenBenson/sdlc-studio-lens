# CR-01KXCAZJ: Commit-SHA poll trigger to keep GitHub projects fresh

> **Status:** Complete
> **Verification depth:** functional
> **Triaged-by:** Darren; human; v3
> **Depends on:** CR-01KXCAHV
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Related:** RFC-01KXARHK (Accepted; source of D2)
> **Priority:** Medium
> **Type:** Feature

## Summary

Implements RFC-01KXARHK decision **D2** (axis choice **B2**).

A GitHub project is only as fresh as the last time somebody pressed Sync. The lens then quietly serves a
stale corpus - stale search results, a stale health score, a stale tree - with nothing on screen saying so.
The operator cannot tell "this project has no open bugs" from "this project had no open bugs when I last
remembered to sync it".

Poll the branch head instead. One call returns the branch's head commit SHA; compare it against the SHA
stored at last sync. Unchanged (the overwhelmingly common case) costs **one cheap request and does
nothing**. Changed runs the incremental sync from CR-01KXCAHV. That is what makes polling affordable: it is
only viable *because* the re-sync it triggers is O(change), not O(repo). Hence the hard dependency.

Webhooks (RFC B3) would give lower latency but need the lens reachable from GitHub, and it lives on
`lens.home.lan` behind NPM. The RFC deferred them; this CR does not revisit that.

## Impact

Turns the lens from a snapshot you must remember to refresh into a view that tracks the repo. It also
closes the honesty gap: even with polling off, the operator should be able to see how old the data is.

**Effort:** M

## Acceptance Criteria

- [ ] **A background poller runs in-process** (RFC D2) as an asyncio task in the FastAPI app - single container, single Uvicorn worker, so no duplicate-poll problem and no external scheduler to own. It starts with the app and shuts down cleanly with it (no task left orphaned on reload, no shutdown hang)
- [ ] **Polling is per-project opt-in** via a new `projects.auto_sync` column (default **off**), toggleable in the UI. An existing project's behaviour does not change until the operator asks for it
- [ ] **The interval is configurable** (default 300s; **`0` disables the poller entirely**), and project polls are **jittered** so N projects do not stampede GitHub in lockstep on every tick
- [ ] **An unchanged repo costs one request and changes nothing.** The head SHA is compared against a stored `last_synced_commit_sha`; equal means no sync, no writes, no `synced_at` churn. Proven by a test asserting exactly one HTTP call and zero document writes
- [ ] **A moved repo triggers the incremental sync** from CR-01KXCAHV, and `last_synced_commit_sha` advances **only on a successful sync** - a failed sync must not record the new SHA, or the failure is never retried and the corpus stays silently stale forever
- [ ] **A failing poll is contained and visible.** A revoked token, a rate limit, a deleted repo or a deleted branch sets that project's `sync_status=error` with a legible message, **does not kill the poller**, and does not stop other projects polling. Repeated failures back off rather than hammering
- [ ] **Local-source projects are never polled.** No timer, no request
- [ ] **Freshness is legible in the UI** whether or not polling is on: the project surfaces when it last synced and whether auto-sync is active, so "no open bugs" can be distinguished from "stale data". Silence about staleness is the bug this CR exists to fix
- [ ] Tests cover: unchanged head (1 call, 0 writes); changed head (incremental sync runs); failed sync does **not** advance the stored SHA; a failing project does not stop the others; `interval=0` starts no poller; local projects are skipped; clean startup and shutdown

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | Darren | Spawned from RFC-01KXARHK (Accepted); carries decision D2 |
