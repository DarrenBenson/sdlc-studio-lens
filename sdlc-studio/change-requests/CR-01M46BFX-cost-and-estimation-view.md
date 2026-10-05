# CR-01M46BFX: Cost and estimation view

> **Status:** inbox
> **Created:** 2026-10-05
> **Created-by:** sdlc-studio new
> **Raised-by:** Claude Opus 5.5; agent; v1
> **Affects:** frontend/src/pages/, backend/src/sdlc_lens/services/, backend/src/sdlc_lens/api/routes/
> **Priority:** High
> **Type:** Feature
> **Size:** M

## Summary

Per sprint and as trends: forecast against actual for points, minutes and tokens with the ratio; tokens by model; calibration (tokens and minutes per point); velocity. Money is tokens priced through an admin-maintained price table, always labelled an estimate, with unpriced models flagged; when a report carries a pricing snapshot (upstream CR) that snapshot is used instead. Depends on: CR-01M46B9P.

## Impact

Answers 'what did this cost and how good are our estimates' without a harness.

## Acceptance Criteria

- [ ] For a fixture project the sprint figures shown equal the report of record's figures exactly
- [ ] Money is shown only with an 'estimate' label and the price table's date; a model with no price is listed as unpriced, never as zero
- [ ] A trend chart covers every signed sprint of the project in order

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
