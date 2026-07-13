# US-01KXCCTV: Fetch only changed blobs via Trees and Blobs, with a tarball fallback

> **Status:** Done
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Triaged-by:** Darren; human; v3
> **Epic:** EP-01KXCCA4
> **Change Request:** [CR-01KXCAHV](../change-requests/CR-01KXCAHV-incremental-github-sync-hybrid-tarball-plus-trees-and.md)
> **Depends on:** US-01KXCCMH
> **Persona:** Priya Nair (Engineering amigo)
> **Priority:** High
> **Story Points:** 5

## User Story

**As an** operator syncing a GitHub project
**I want** a re-sync to download only the files that actually changed
**So that** keeping the lens fresh costs a few small requests instead of the whole repository, every time

## Background

The payoff story. With the blob SHA stored (US-01KXCC76) and the manifest able to carry contentless entries
(US-01KXCCMH), the incremental path becomes: one Trees call (`?recursive=1`) → diff blob SHAs against the DB →
fetch only the changed blobs → hand `sync_project` a **complete manifest** in which unchanged files carry
`raw=None`.

The tarball does not go away. It is the cold start, the backfill, the repair path, and the escape hatch when
too much has changed (RFC-01KXARHK, D3/D5). Keeping it is what bounds the worst case at today's cost rather
than worse than it.

## Acceptance Criteria

### AC1: A re-sync with no changes fetches zero blobs and touches nothing

- **Given** a synced GitHub project whose repo has not moved
- **When** a sync runs
- **Then** exactly one Trees request is issued, **zero** blob requests, and the result reports zero added, zero updated and **zero deleted**
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_incremental_sync.py -q -k nothing_changed_fetches_zero_blobs
- **Verified:** yes (2026-07-13)

### AC2: A re-sync with K changes fetches exactly K blobs

- **Given** a synced GitHub project in which three files changed and one was added
- **When** a sync runs
- **Then** exactly four blob requests are issued, exactly four documents are written, and every other document is skipped and left byte-identical
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_incremental_sync.py -q -k only_the_changed_files_are_fetched
- **Verified:** yes (2026-07-13)

### AC3: Deletions upstream propagate

- **Given** a file removed from the repo
- **When** a sync runs
- **Then** it is absent from the Trees manifest and the document is deleted locally
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_incremental_sync.py -q -k deleted_upstream_is_deleted_locally
- **Verified:** yes (2026-07-13)

### AC4: Path selection follows the hybrid rules, and the fallback speaks

- **Given** the tarball is the cold start, the backfill and the escape hatch
- **When** a sync runs on a project that is (a) syncing for the first time, (b) holds any document with a NULL `blob_sha`, (c) holds any document below `PARSER_EPOCH` (RFC D7), or (d) has more changed blobs than the cap
- **Then** the **tarball** path runs, and the sync result **names which path ran and why** - a cap that silently diverts work is a cap that lies (RETRO-0006: "a cap must speak")
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_incremental_sync.py -q -k TestPathSelection
- **Verified:** yes (2026-07-13)

### AC5: An upgraded install self-heals

- **Given** an install upgraded from a version with no `blob_sha` - every document NULL
- **When** the next sync runs
- **Then** it takes the tarball path once, backfilling every `blob_sha`, and the sync after that is incremental
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_incremental_sync.py -q -k null_blob_sha_forces_the_tarball
- **Verified:** yes (2026-07-13)

### AC6: A rate limit or a revoked token leaves the corpus intact

- **Given** GitHub returns 403/429, or the token has been revoked, part-way through fetching blobs
- **When** the sync fails
- **Then** `RateLimitError` / `AuthenticationError` is raised, `sync_status` becomes `error` with a legible message, and **not one document is added, updated or deleted** - a throttled fetch never partial-writes
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_incremental_sync.py -q -k rate_limit_mid_fetch
- **Verified:** yes (2026-07-13)

### AC7: Local projects are untouched

- **Given** a local-source project
- **When** a sync runs
- **Then** no Trees call, no blob call, and no blob-SHA diffing occurs; behaviour is byte-for-byte what it was
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_incremental_sync.py -q -k TestLocalSourceIsUntouched
- **Verified:** yes (2026-07-13)

### AC8: A stale parser epoch forces the tarball, so BG-01KXARHJ stays fixed

- **Given** `PARSER_EPOCH` is bumped by an app upgrade and no file in the repo has changed
- **When** the next sync runs on a GitHub project
- **Then** it takes the **tarball** path (not incremental), every document re-parses from real bytes, and the derived fields (`doc_type`, `status`, `ref_id`, `epic`, `story`, `depends_on`, `aliases`) all recompute. The sync after that is incremental again. Stored `content` is body-only and is never used as a re-parse source (RFC D7)
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_incremental_sync.py -q -k stale_parser_epoch_forces_the_tarball
- **Verified:** yes (2026-07-13)

### AC9: The whole thing is mutation-checked

- **Given** RETRO-0006's critic found three real defects that 976 passing tests missed
- **When** the empty-source guard and the deletion loop are each mutated
- **Then** a test goes red for each
- **Verify:** manual mutate each path-selection guard; all must be killed
- **Verified:** manual (2026-07-13) - 4 mutants, 4 killed: drop the stale-epoch tarball trigger (RFC D7); trust a truncated tree; remove the incremental cap; drop the NULL blob_sha trigger. Each turned exactly one test red. Restored: 771 pass.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCAHV (RFC D3/D5) |
