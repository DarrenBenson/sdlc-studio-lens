# CR-01M46BT9: Lessons, decisions and retros view

> **Status:** inbox
> **Created:** 2026-10-05
> **Created-by:** sdlc-studio new
> **Raised-by:** Claude Opus 5.5; agent; v1
> **Affects:** frontend/src/pages/, backend/src/sdlc_lens/services/, backend/src/sdlc_lens/api/routes/
> **Priority:** Medium
> **Type:** Feature
> **Size:** M

## Summary

A decision register (D#### with status and supersession), lesson classes from `lessons.jsonl` (rule, state, hits by run), and retros with Keep / Stop / Try and the known issues carried, each linked to its sprint and units. Depends on: CR-01M46BKF, CR-01M46B00.

## Impact

Lets a reviewer see what the team learned and decided, and whether lessons keep recurring.

## Acceptance Criteria

- [ ] Every decision row and lesson class in a fixture project is listed with its status/state
- [ ] A lesson class shows the runs that hit it, linked to their sprint pages
- [ ] A retro's Try items tagged `[LC-###]` link to that lesson class

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
