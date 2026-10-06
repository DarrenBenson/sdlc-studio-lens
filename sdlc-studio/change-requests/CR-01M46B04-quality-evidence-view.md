# CR-01M46B04: Quality evidence view

> **Status:** Proposed
> **Triaged-by:** Darren Benson; human; v1
> **Created:** 2026-10-05
> **Created-by:** sdlc-studio new
> **Raised-by:** Claude Opus 5.5; agent; v1
> **Affects:** frontend/src/pages/, backend/src/sdlc_lens/services/, backend/src/sdlc_lens/api/routes/
> **Priority:** Medium
> **Type:** Feature
> **Size:** M

## Summary

Per unit and per sprint: acceptance criteria verified, failed, manual or unverified; the independent review verdict (latest row wins), with reviewer and author shown and a same-person review flagged; known issues carried and waivers in force. Add quality filters (for example 'Done but not verified') to the document list. Depends on: CR-01M46B00, CR-01M46B9P.

## Impact

Makes 'Done' inspectable: the loudest thing on screen is a finished unit whose evidence does not support it.

## Acceptance Criteria

- [ ] A Done story with an unverified or failed criterion is flagged on its page, in the sprint view and by a document-list filter
- [ ] A unit whose recorded reviewer equals its author is flagged

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
