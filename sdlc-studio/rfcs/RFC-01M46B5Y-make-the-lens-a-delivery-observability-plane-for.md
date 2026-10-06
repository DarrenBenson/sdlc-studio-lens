# RFC-01M46B5Y: Make the lens a delivery-observability plane for project managers

> **Status:** Draft
> **Triaged-by:** Darren Benson; human; v1
> **Created:** 2026-10-05
> **Created-by:** sdlc-studio new
> **Raised-by:** Claude Opus 5.5; agent; v1
> **Affects:** backend/src/sdlc_lens/, frontend/src/
> **Size:** M
> **Supersedes:** RFC-01KXDCKH

## Summary

Decide how the lens reads sdlc-studio's delivery evidence and who may see it. Supersedes RFC-01KXDCKH, whose premise (that `.local/` is committed and `verify-report.json` can be relied on) does not hold for a reader without a harness. Evidence available in git: `reports/RPT*.json` (report of record, schema 1 and 2), `reports/runs/RUN-*.json`, `retros/` (incl. VELOCITY.md and evidence/*.jsonl), `reviews/critic-verdicts.md`, `decisions.md`, `lessons.jsonl`, `deploy-log.md`, and each criterion's `Verify:`/`Verified:` lines. Full analysis in RV0003 (the observability gap analysis). Depends on: CR-01M46BQ8.

## Design Options

- **Ingest the committed record (recommended): store reports and run records raw, read them through one adapter per (kind, schema), aggregate across sprints only, never compute a competing figure, never read `.local/`**
- **Re-derive every metric in the lens from the markdown: impossible for DORA (needs git history), tokens and minutes (need `.local/`), and produces numbers that can contradict the signed report**
- **Wait for an upstream export API before building anything: blocks the PM goal on work in another repo**

## Recommendation

Ingest the committed record. One `IngestPolicy` shared by the local, tarball and Trees fetch paths admits an explicit allow-list (`reports/RPT*.json`, `reports/runs/RUN-*.json`, `lessons.jsonl`, optionally `retros/evidence/*.jsonl`); no generic `*.json`, no dot-dirs, no symlinks; caps of 1 MiB per JSON, 5 MiB / 50k lines per JSONL and 50 MiB per project, each breach surfaced on the sync status. Unknown schemas sync and render generically under a 'format not recognised' badge. A figure whose source is under `.local/` is labelled 'private run state, not reviewable'. Money: an admin-maintained price table, labelled an estimate, until reports carry a pricing snapshot upstream. Access: sign in with GitHub through a GitHub App - a viewer sees the projects whose repo their account can read, admins are named by login, sync runs on the app installation token and the stored PATs are retired.

## Open Decisions

| # | Decision | Status |
| --- | --- | --- |
| D1 | Ingest `retros/evidence/*.jsonl` at all, given the run records and reports already carry per-unit actuals and forecasts? Proposed: optional per-project toggle, off by default | Open |
| D2 | When a run has more than one report (RPT0004 was superseded the same day by RPT0005), show the latest per run with the others as history? | Open |
| D3 | Keep the lens price table once reports carry a pricing snapshot, or use the snapshot alone for reports that have one? | Open |
| D4 | Admins by login list only, or also by GitHub org team membership? | Open |

## Acceptance Criteria

- **The RFC records the decisions on evidence source, storage model, money and access, and is Accepted**
- **It spawns or links the CRs that implement it**
- **RFC-01KXDCKH is Superseded with a pointer to this RFC**

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
