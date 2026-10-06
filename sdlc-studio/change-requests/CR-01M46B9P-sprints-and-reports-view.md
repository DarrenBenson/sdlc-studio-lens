# CR-01M46B9P: Sprints and reports view

> **Status:** Proposed
> **Triaged-by:** Darren Benson; human; v1
> **Created:** 2026-10-05
> **Created-by:** sdlc-studio new
> **Raised-by:** Claude Opus 5.5; agent; v1
> **Affects:** frontend/src/pages/, frontend/src/components/, backend/src/sdlc_lens/api/routes/
> **Priority:** High
> **Type:** Feature
> **Size:** L

## Summary

Give a project a sprint timeline and a page per sprint report: goal and verdict, delivered against planned, known issues, sign-off (who signed, over which fingerprint, or 'unsigned'), and every section of the report. Schema 1 and 2 reports render through adapters; any other renders through a generic section renderer. Units link to their stories and bugs, the retro and the run. Depends on: CR-01M46BKF, CR-01M46B00.

## Impact

This is the page a project manager opens first.

## Acceptance Criteria

- [ ] Every RPT in the sdlc-studio dogfood workspace (schema 1 and 2) renders without error, pinned as fixtures (at least RPT0002, RPT0010, RPT0019)
- [ ] A report whose schema is unknown still renders its sections generically under a 'format not recognised' badge
- [ ] The fingerprint is presented as 'content matches the signed fingerprint', never as an authenticity claim
- [ ] A figure whose source is under `.local/` is labelled 'private run state, not reviewable' rather than linked

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
