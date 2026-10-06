# CR-01M46BC2: Portfolio roll-up across projects

> **Status:** Proposed
> **Triaged-by:** Darren Benson; human; v1
> **Created:** 2026-10-05
> **Created-by:** sdlc-studio new
> **Raised-by:** Claude Opus 5.5; agent; v1
> **Affects:** frontend/src/pages/Dashboard.tsx, backend/src/sdlc_lens/services/stats.py, backend/src/sdlc_lens/api/routes/
> **Priority:** Medium
> **Type:** Feature
> **Size:** L

## Summary

Replace the dashboard's project cards with a portfolio view: per project, last sprint and goal verdict, cost trend, DORA headline with its mapping, open known issues, unsigned reports, skill and schema version, and sync freshness. Projects with no sprint records show a degraded tile, not an error. Built on summary tables, not JSON scans. Depends on: CR-01M46B9P, CR-01M46BFX, CR-01M46BPJ, CR-01M46BZJ.

## Impact

Lets someone responsible for several projects see which needs attention.

## Acceptance Criteria

- [ ] The portfolio lists only projects the viewer may read
- [ ] A project on an older skill version with no reports shows a 'no sprint records' tile
- [ ] The view loads from summary tables, shown by a test that it issues no per-record JSON parse

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
