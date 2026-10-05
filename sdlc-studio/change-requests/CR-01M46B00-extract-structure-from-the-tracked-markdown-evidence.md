# CR-01M46B00: Extract structure from the tracked markdown evidence

> **Status:** inbox
> **Created:** 2026-10-05
> **Created-by:** sdlc-studio new
> **Raised-by:** Claude Opus 5.5; agent; v1
> **Affects:** backend/src/sdlc_lens/services/parser.py, backend/src/sdlc_lens/services/documents.py, backend/src/sdlc_lens/db/models/
> **Priority:** Medium
> **Type:** Feature
> **Size:** M

## Summary

Several evidence sources are markdown tables or lines that the lens stores only as prose: `reviews/critic-verdicts.md`, `decisions.md`, `retros/VELOCITY.md`, `deploy-log.md`, and each acceptance criterion's `Verify:` / `Verified:` lines. Parse them into rows, and add the retro <-> run <-> report relationships (a retro's `Run:`/`Batch:`, a report's `run_id`/`retro_id`). Depends on: CR-01M46BEX, CR-01M46BKF.

## Impact

Quality, lessons and cost views need these rows; today a 'Done but never verified' story is invisible.

## Acceptance Criteria

- [ ] Each criterion of a story is stored with its Verified state (yes, no, stale, manual or none) and date, shown by a parser test over the lens's own stories
- [ ] critic-verdicts, decisions, VELOCITY and deploy-log tables parse into rows, with `SUPERSEDED unit=` lines retiring the row they name
- [ ] A retro links to its run, report and batch units, and a unit links back to the retros and reports that name it

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
