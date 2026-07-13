# US-01KXDD5K: Poll the branch head SHA: one cheap call, and only advance it on a successful sync

> **Status:** Done
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Triaged-by:** Darren; human; v3
> **Epic:** EP-01KXDDG7
> **Change Request:** [CR-01KXCAZJ](../change-requests/CR-01KXCAZJ-commit-sha-poll-trigger-to-keep-github-projects.md)
> **Persona:** Priya Nair (Engineering amigo)
> **Priority:** Medium
> **Story Points:** 3

## User Story

**As a** lens keeping a GitHub project fresh
**I want** to ask GitHub one cheap question - "has this branch moved?" - before doing anything
**So that** staying current costs almost nothing on the overwhelmingly common day when nothing changed

## Background

The freshness check must be far cheaper than the sync it guards, or polling is not worth having. One call to
the branch's head commit returns a SHA; compare it with the SHA stored at the **last successful sync**.

The trap is in that word *successful*. If the stored SHA advances when the sync **fails**, the repo looks
"unchanged" for ever afterwards - so the failure is never retried, and the project stays silently stale
while reporting nothing wrong. A staleness feature whose failure mode is permanent, invisible staleness is
worse than no feature. Advance the SHA **only** after the sync has actually succeeded.

## Acceptance Criteria

### AC1: A head-SHA poll is one request and no content

- **Given** the check must be cheaper than the sync
- **When** `fetch_branch_head_sha` runs
- **Then** it issues exactly one GitHub request and returns the branch's head commit SHA; it downloads no tree and no blobs
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_poller.py -q -k head_sha_is_one_request
- **Verified:** yes (2026-07-13)

### AC2: An unchanged head does nothing at all

- **Given** a project whose stored `last_synced_commit_sha` equals the branch head
- **When** the poll runs
- **Then** no sync is triggered, no document is written, and `last_synced_at` does **not** move - a poll that "refreshes" the timestamp without refreshing the data is lying to the operator
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_poller.py -q -k unchanged_head_does_nothing
- **Verified:** yes (2026-07-13)

### AC3: A moved head triggers the sync and advances the SHA

- **Given** the branch head differs from the stored SHA
- **When** the poll runs
- **Then** a sync is triggered, and on success `last_synced_commit_sha` becomes the new head
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_poller.py -q -k moved_head_syncs_and_advances
- **Verified:** yes (2026-07-13)

### AC4: A FAILED sync must NOT advance the stored SHA

- **Given** the sharpest edge in the epic: advancing on failure makes the repo look unchanged for ever, so the failure is never retried and the project is permanently, invisibly stale
- **When** the triggered sync ends in `sync_status=error`
- **Then** `last_synced_commit_sha` is left exactly as it was, so the very next poll sees the head as still-moved and tries again
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_poller.py -q -k failed_sync_does_not_advance
- **Verified:** yes (2026-07-13)

### AC5: The poller reuses the existing atomic sync guard

- **Given** `trigger_sync()` already performs an atomic `UPDATE ... WHERE sync_status != 'syncing'`, closing the double-sync race
- **When** a poll fires while a manual sync is already running
- **Then** it does not start a second sync, and it does so by **reusing that guard** rather than adding a weaker second one
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_poller.py -q -k does_not_double_sync
- **Verified:** yes (2026-07-13)

### AC6: Local projects are never polled

- **Given** a local-source project has no branch and no remote
- **When** the poller sweeps
- **Then** it issues no request for that project at all
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_poller.py -q -k local_project_is_never_polled
- **Verified:** yes (2026-07-13)

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCAZJ |
