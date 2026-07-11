# CR-01KX8B83: Low-severity crs (consolidated)

> **Status:** Proposed
> **Depends on:** CR-01KX8BBH, BG-01KX8BY1
> **Triaged-by:** Darren; human; v3
> **Priority:** Low
> **Type:** Improvement
> **Date:** 2026-07-11
> **Consolidation:** low-severity-crs
> **Created-by:** sdlc-studio file
> **Raised-by:** Priya Nair; persona; v3

## Summary

A themed consolidation of Low-severity findings that individually do not warrant a standalone artefact (triage noise control, schema v3). Triage the batch, then action or reject as one.

## Consolidated Findings

- **Hardening sweep: error swallowing, observability and CI supply-chain**: Consolidated Low findings. (a) project.py:137 get_document_count swallows OperationalError and returns 0 on a now-stale 'table may not exist' rationale, masking real DB faults. (b) sync_engine.py:210 swallows all _rebuild_fts_if_exists failures at DEBUG after status is already 'synced', so a genuine FTS rebuild failure leaves a silently stale search index. (c) frontend/src/api/client.ts:23 - fetchProjects/fetchProject/fetchRelatedDocuments/fetchAggregateStats throw a bare status instead of extractErrorMessage, discarding the canonical error body. (d) .github/workflows/release.yml:8 grants top-level contents:write/packages:write to all jobs incl. test, and pins actions to mutable major tags rather than commit SHAs.
- **Efficiency and dead-code cleanups (FTS, project counts, docstring)**: Consolidated Low findings. (a) fts.py:21-48 - fts_insert/fts_update/fts_delete are never called from application code (only fts_rebuild is wired at sync_engine.py:208) yet carry a full unit-test suite, giving false confidence that incremental indexing works. (b) projects.py:117 - GET /api/v1/projects runs a SELECT COUNT(*) per project (get_document_count) instead of one grouped query. (c) sync_engine.py:147 docstring (and MEMORY.md) claim a Trees+Blobs API while the code downloads a single tarball.

## Impact

Individually minor, but together they erode trust in the system's signals: swallowed DB/FTS errors mask real faults behind a healthy-looking status; the frontend discards the canonical error body; unpinned over-privileged CI is a supply-chain exposure; and tested-but-unwired FTS code gives false confidence that incremental indexing works.

**Effort:** M

## Acceptance Criteria

- [ ] `get_document_count` (project.py:137) no longer swallows genuine DB errors - the broad `except OperationalError` is removed or narrowed and logged
- [ ] A real FTS rebuild failure (sync_engine.py:210) is logged at WARNING or higher; the guard is narrowed to the table-existence check only
- [ ] All `client.ts` non-ok responses (fetchProjects/fetchProject/fetchRelatedDocuments/fetchAggregateStats) are routed through `extractErrorMessage`
- [ ] CI actions in `.github/workflows/release.yml` are pinned to commit SHAs, and job permissions are least-privilege (`contents: read` on the test job)

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Consolidation opened |
