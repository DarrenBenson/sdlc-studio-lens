# US-01KXCCTV: Fetch only changed blobs via Trees and Blobs, with a tarball fallback

> **Status:** Ready
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
- **Verify:** pytest backend/tests/services/test_github_source.py -k incremental_no_changes

### AC2: A re-sync with K changes fetches exactly K blobs

- **Given** a synced GitHub project in which three files changed and one was added
- **When** a sync runs
- **Then** exactly four blob requests are issued, exactly four documents are written, and every other document is skipped and left byte-identical
- **Verify:** pytest backend/tests/services/test_github_source.py -k incremental_changed_subset

### AC3: Deletions upstream propagate

- **Given** a file removed from the repo
- **When** a sync runs
- **Then** it is absent from the Trees manifest and the document is deleted locally
- **Verify:** pytest backend/tests/services/test_github_source.py -k incremental_deletes

### AC4: Path selection follows the hybrid rules, and the fallback speaks

- **Given** the tarball is the cold start, the backfill and the escape hatch
- **When** a sync runs on a project that is (a) syncing for the first time, (b) holds any document with a NULL `blob_sha`, or (c) has more changed blobs than the cap
- **Then** the **tarball** path runs, and the sync result **names which path ran and why** - a cap that silently diverts work is a cap that lies (RETRO-0006: "a cap must speak")
- **Verify:** pytest backend/tests/services/test_sync_engine.py -k hybrid_path_selection

### AC5: An upgraded install self-heals

- **Given** an install upgraded from a version with no `blob_sha` - every document NULL
- **When** the next sync runs
- **Then** it takes the tarball path once, backfilling every `blob_sha`, and the sync after that is incremental
- **Verify:** pytest backend/tests/services/test_sync_engine.py -k upgrade_backfills_blob_sha

### AC6: A rate limit or a revoked token leaves the corpus intact

- **Given** GitHub returns 403/429, or the token has been revoked, part-way through fetching blobs
- **When** the sync fails
- **Then** `RateLimitError` / `AuthenticationError` is raised, `sync_status` becomes `error` with a legible message, and **not one document is added, updated or deleted** - a throttled fetch never partial-writes
- **Verify:** pytest backend/tests/services/test_github_source.py -k incremental_rate_limited_preserves_corpus

### AC7: Local projects are untouched

- **Given** a local-source project
- **When** a sync runs
- **Then** no Trees call, no blob call, and no blob-SHA diffing occurs; behaviour is byte-for-byte what it was
- **Verify:** pytest backend/tests/services/test_sync_engine.py -k local_source_unaffected

### AC8: The parser epoch still re-parses unchanged files

- **Given** `PARSER_EPOCH` is bumped and no file in the repo has changed
- **When** an incremental sync runs
- **Then** every stale document re-parses from stored content, with **zero** blob requests issued - the incremental path did not un-fix BG-01KXARHJ
- **Verify:** pytest backend/tests/services/test_sync_engine.py -k incremental_epoch_reparse_no_fetch

### AC9: The whole thing is mutation-checked

- **Given** RETRO-0006's critic found three real defects that 976 passing tests missed
- **When** the empty-source guard and the deletion loop are each mutated
- **Then** a test goes red for each
- **Verify:** manual run the mutation check over sync_engine.py's guard and deletion loop; both must be killed, not survived

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCAHV (RFC D3/D5) |
