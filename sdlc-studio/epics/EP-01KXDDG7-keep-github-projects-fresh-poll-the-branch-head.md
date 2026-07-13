# EP-01KXDDG7: Keep GitHub projects fresh: poll the branch head, sync only when it moves

> **Status:** Done
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Triaged-by:** Darren; human; v3
> **Change Request:** [CR-01KXCAZJ](../change-requests/CR-01KXCAZJ-commit-sha-poll-trigger-to-keep-github-projects.md)
> **Depends on:** EP-01KXCCA4
> **Priority:** Medium

## Summary

Implements RFC-01KXARHK decision **D2** (axis choice **B2**).

A GitHub project is only as fresh as the last time somebody pressed Sync. The lens then quietly serves a
stale corpus - stale search, a stale health score, a stale tree - with nothing on screen saying so. The
operator cannot tell *"this project has no open bugs"* from *"this project had no open bugs when I last
remembered to sync it"*.

Poll the branch head instead. One call returns the head commit SHA; compare it against the SHA stored at
the last successful sync. Unchanged - the overwhelmingly common case - costs **one cheap request and does
nothing at all**. Changed runs the incremental sync from EP-01KXCCA4.

**That dependency is the whole reason this is affordable.** Polling is only viable because the re-sync it
triggers is O(change), not O(repo): a poll that fired a full tarball every few minutes would be worse than
the staleness it cures.

## Reuse, do not reinvent

`services/sync.py` already has the two things a poller needs, and they were built for exactly this hazard:

- `trigger_sync()` performs an **atomic** `UPDATE ... WHERE sync_status != 'syncing'`, so a poll that fires
  while a manual sync is running cannot double-sync. The race is already closed - use it rather than adding
  a second, weaker guard.
- `run_sync_task()` already guarantees a project is never left stuck in `syncing`, whatever fails.

The poller is therefore a *scheduler*, not a second sync path. If it grows its own copy of either
behaviour, that is a defect.

## Story Breakdown

- [x] [US-01KXDD5K: Poll the branch head SHA: one cheap call, and only advance it on a successful sync](../stories/US-01KXDD5K-poll-the-branch-head-sha-one-cheap-call.md)
- [x] [US-01KXDD0K: Run the poller in-process, isolated per project, and shut it down cleanly](../stories/US-01KXDD0K-run-the-poller-in-process-isolated-per-project.md)
- [x] [US-01KXDDA0: Make auto-sync opt-in and make staleness legible in the UI](../stories/US-01KXDDA0-make-auto-sync-opt-in-and-make-staleness.md)

## Acceptance Criteria

- [ ] An unchanged repo costs **exactly one** HTTP request and performs **zero** writes - no document churn, no `synced_at` churn
- [ ] A moved repo triggers the incremental sync, and `last_synced_commit_sha` advances **only on success** - a failed sync must not record the new SHA, or the failure is never retried and the corpus stays silently stale for ever
- [ ] Polling is **per-project opt-in** (`auto_sync`, default off). Existing projects behave exactly as they do today until the operator asks otherwise
- [ ] The interval is configurable; **`0` disables the poller entirely**; project polls are jittered so N projects do not stampede GitHub on every tick
- [ ] A failing project (revoked token, rate limit, deleted repo or branch) sets its own `sync_status=error`, **does not kill the poller**, and **does not stop other projects polling**. Repeated failures back off
- [ ] **Local-source projects are never polled.** No timer, no request
- [ ] The poller starts with the app and **shuts down cleanly** - no orphaned task, no hang on reload
- [ ] Staleness is legible in the UI whether or not polling is on, so "no open bugs" can be told apart from "stale data"
- [ ] Mutation-checked: the SHA-advance-only-on-success rule and the per-project isolation must each be provably load-bearing

## Risks

- **A poller is a loop that runs unattended for ever.** Its failure mode is not a crash but a *quiet* one:
  a task that dies takes freshness with it and says nothing. Every failure path must be observable, and the
  loop itself must be unkillable by any single project's error.
- **Advancing the stored SHA on a failed sync is the subtle disaster.** The repo would then look
  "unchanged" for ever after, so the failure is never retried and the project is stale permanently while
  reporting nothing wrong. This is the sharpest edge in the epic and gets its own AC and mutation.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCAZJ (RFC D2); three stories |
