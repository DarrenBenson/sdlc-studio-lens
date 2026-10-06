# CR-01M46BEX: Read a skill 6.1 workspace correctly, from one vocabulary source

> **Status:** Proposed
> **Triaged-by:** Darren Benson; human; v1
> **Created:** 2026-10-05
> **Created-by:** sdlc-studio new
> **Raised-by:** Claude Opus 5.5; agent; v1
> **Affects:** backend/src/sdlc_lens/utils/sdlc_status.py, backend/src/sdlc_lens/utils/inference.py, backend/src/sdlc_lens/utils/sdlc_ids.py, backend/src/sdlc_lens/services/parser.py, backend/src/sdlc_lens/services/health_check.py, backend/src/sdlc_lens/services/sync_engine.py, frontend/src/components/StatusBadge.tsx, frontend/src/pages/DocumentList.tsx, frontend/src/pages/ProjectDetail.tsx, frontend/src/lib/buildTree.ts
> **Priority:** High
> **Type:** Feature
> **Size:** M

## Summary

The lens copies the skill's status vocabulary and id prefixes as frozen at 4.0.0, and the frontend repeats them in four more places. Against a 6.1 workspace it misses: epic `Superseded`; the `issue` (IS) and `charter` (SC) types and their vocabularies; report (RPT), handoff (HO), decision (D####) and lesson ids; `archive/<release>/` index folders; and the 6.x headers `Size`, `Affects`, `Estimated-by`, `Delivered-by`. Serve the vocabulary from the backend (`GET /api/v1/vocab`) and have every frontend copy consume it; add the 6.1 health rules (missing `reviews/LATEST.md`, stale index stamp, unsigned report). Depends on: CR-01M46BAX.

## Impact

Projects on skill 5.x/6.x show wrong statuses, unknown types and misleading completion figures today.

## Acceptance Criteria

- [ ] A fixture workspace copied from a 6.1 project syncs with every artefact typed correctly (no `other`), including IS, SC and RPT files and rows under `archive/<release>/`
- [ ] Epic `Superseded`, story `Won't Implement` and charter `Spent` count as terminal in the completion figure, shown by a stats test
- [ ] The four frontend vocabulary copies are removed and the UI reads `/api/v1/vocab`; a test fails if a status in the backend vocabulary has no badge colour
- [ ] `Size`, `Affects`, `Estimated-by` and `Delivered-by` are stored as named fields and shown on the document view
- [ ] The parser epoch is bumped so existing projects re-parse on the next sync

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
