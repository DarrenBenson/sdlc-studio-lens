# CR-01M46BKF: Ingest allow-listed structured records alongside the markdown

> **Status:** inbox
> **Created:** 2026-10-05
> **Created-by:** sdlc-studio new
> **Raised-by:** Claude Opus 5.5; agent; v1
> **Affects:** backend/src/sdlc_lens/services/sync_engine.py, backend/src/sdlc_lens/services/github_source.py, backend/src/sdlc_lens/db/models/, backend/alembic/versions/
> **Priority:** High
> **Type:** Feature
> **Size:** L

## Summary

The sync walker admits only `.md` files on all three fetch paths (local walk, tarball, Trees diff), so sprint reports, run records and lesson classes never reach the lens. Introduce one `IngestPolicy` used by every path, a `records` table (project, path, kind, schema, raw, hashes, parsed epoch) with child tables per kind, the caps and refusals set out in RFC-01M46B5Y, and FTS indexing of record text. Depends on: RFC-01M46B5Y.

## Impact

Every sprint, cost, DORA and lessons view depends on this. The deletion and manifest invariants (BG-01KX8BFP) are in the blast radius.

## Acceptance Criteria

- [ ] `reports/RPT*.json`, `reports/runs/RUN-*.json` and `lessons.jsonl` from a fixture project are stored as records on a local, a tarball and an incremental Trees sync alike
- [ ] A file under `.local/`, a symlink and a non-allow-listed `.json` are never admitted on any path, each shown by a test
- [ ] A record over its cap is not parsed and is reported on the project's sync status, never silently dropped
- [ ] A cross-path test shows that adding records does not delete or orphan any markdown document on any fetch path
- [ ] Re-parsing after an adapter change needs only a parser-epoch bump, not a re-download

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
