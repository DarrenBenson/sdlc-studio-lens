# US-01KXCC76: Store a git blob SHA per document

> **Status:** Ready
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
- **Verify:** pytest backend/tests/test_migrations.py -k blob_sha

### AC2: The blob SHA is computed correctly - it matches real git

- **Given** git's blob SHA is `sha1("blob {len}\0" + bytes)`, not a bare sha1 of the content
- **When** the helper computes a SHA for known bytes
- **Then** it equals the value `git hash-object` produces for the same bytes, including for empty files and files containing a BOM or non-ASCII text
- **Verify:** pytest backend/tests/services/test_sync_engine.py -k blob_sha_matches_git

### AC3: Both existing sync paths populate it

- **Given** the tarball path already has the raw bytes in hand, and the local path walks real files
- **When** either sync runs
- **Then** every added or updated document is written with its `blob_sha` populated
- **Verify:** pytest backend/tests/services/test_sync_engine.py -k blob_sha_populated

### AC4: Nothing else changes

- **Given** this story is pure groundwork
- **When** the full backend suite runs
- **Then** it passes unmodified - no existing test is edited to accommodate the new column
- **Verify:** shell cd backend && PYTHONPATH=src python -m pytest -q

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCAHV (RFC D1) |
