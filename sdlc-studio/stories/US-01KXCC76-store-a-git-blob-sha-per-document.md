# US-01KXCC76: Store a git blob SHA per document

> **Status:** Done
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Triaged-by:** Darren; human; v3
> **Epic:** EP-01KXCCA4
> **Change Request:** [CR-01KXCAHV](../change-requests/CR-01KXCAHV-incremental-github-sync-hybrid-tarball-plus-trees-and.md)
> **Persona:** Priya Nair (Engineering amigo)
> **Priority:** High
> **Story Points:** 2

## User Story

**As a** sync engine about to ask GitHub what changed
**I want** each stored document to carry the git blob SHA it was built from
**So that** I can diff a Trees response against what I hold, without downloading anything

## Background

GitHub's Trees API returns, for every path, the **git blob SHA** - `sha1("blob {len}\0" + bytes)`. To use it
as a change detector we must hold the same value per document.

We cannot reuse `documents.file_hash`: it is a **sha256 of the bytes**, a different algorithm over a different
preimage. And we should not recompute the blob SHA from the stored `content` column, because that column is
already-decoded text - reconstructing the original bytes would mean re-encoding and re-adding any stripped BOM,
a round-trip that is fragile in exactly the way that produces a silent, undetectable mismatch.

So: store it (RFC-01KXARHK, D1).

This story changes **no behaviour**. It adds a column, populates it on every existing sync path, and stops.
Nothing reads it yet.

## Acceptance Criteria

### AC1: The column exists, nullable, with a migration

- **Given** existing installs hold documents with no blob SHA
- **When** the migration runs
- **Then** `documents.blob_sha` exists and is nullable, and existing rows are left NULL (meaning "unknown"); the migration is reversible
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_blob_sha.py -q -k TestMigration012
- **Verified:** yes (2026-07-13)

### AC2: The blob SHA is computed correctly - it matches real git

- **Given** git's blob SHA is `sha1("blob {len}\0" + bytes)`, not a bare sha1 of the content
- **When** the helper computes a SHA for known bytes
- **Then** it equals the value `git hash-object` produces for the same bytes, including for empty files and files containing a BOM or non-ASCII text
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_blob_sha.py -q -k matches_git
- **Verified:** yes (2026-07-13)

### AC3: Every document ends up with a blob_sha - including a SKIPPED one

- **Given** the sync skips a byte-unchanged file *before* it rebuilds that document's attributes
- **When** a database migrated from before 012 (every row `blob_sha=NULL`) syncs, and **not one byte on disk has changed**
- **Then** those rows are **still backfilled**. A NULL `blob_sha` makes a row ineligible for the byte-unchanged skip (`needs_blob_sha_backfill`), exactly as a NULL `ref_id` already does. The backfill then **settles**: the following sync skips normally rather than rewriting forever
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_sync.py -q -k TestSyncPopulatesBlobSha

> **This AC previously read "every *added or updated* document is written with its `blob_sha` populated".**
> A skipped document is neither added nor updated, so the AC was satisfiable while the upgrade path was
> completely broken - and it was: an independent critic proved every pre-existing row stayed NULL forever,
> which would have meant incremental sync never engaging for a single real install. 752 tests and four
> green ACs saw nothing, because the suite only ever exercised a fresh database and a changed file, never
> the one state that mattered. **An AC that enumerates the paths it checks silently exempts the path it
> forgot.** State the invariant ("every document ends up with a blob_sha"), not the paths.
- **Verified:** yes (2026-07-13)

### AC4: No behaviour changes, and no test is WEAKENED

- **Given** this story is groundwork - nothing reads `blob_sha` yet
- **When** the full backend suite runs
- **Then** it passes, and no test's assertion is weakened to accommodate the new column
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest -q

> **Honesty note - the original wording was "passes unmodified - no existing test is edited", and two were.**
> Both are fixture repairs, not weakened assertions, and both are stated here rather than quietly absorbed:
>
> 1. `test_github_connections.py::test_upgrade_head_reaches_011` hardcoded `assert version == "011"`, which
>    pins the migration head and breaks on *any* new migration. Replaced with alembic's actual current head,
>    derived from `ScriptDirectory`. The schema assertions that genuinely prove 011 applied are untouched -
>    and it now never needs editing again.
> 2. `test_ref_id_backfill.py::test_current_epoch_unchanged_row_is_skipped` hand-builds a `Document` with no
>    `blob_sha`, so it was NULL - which under the new self-heal correctly makes the row eligible for a
>    backfill rather than a skip. The fixture now sets `blob_sha`, because it is meant to represent a row
>    that is current *in every respect*. Its assertion (`doc_type` stays `"other"`, proving a skip) is
>    unchanged, and the NULL-row behaviour it accidentally depended on is now covered by its own test.
>
> Neither edit loosens a check. Had either required loosening one, the design would have been wrong.
- **Verified:** yes (2026-07-13)

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCAHV (RFC D1) |
