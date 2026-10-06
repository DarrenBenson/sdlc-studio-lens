# CR-01M46BPJ: DORA and flow view

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

Show the four DORA keys per sprint and over time from the reports' `dora` section, always beside the mapping the project used (a trunk-based project counts pushes to main as deploys), plus deploy-log rows where a project keeps one, and cycle time from status-change dates where they exist. Depends on: CR-01M46B9P.

## Impact

Gives a PM delivery-performance figures with the caveats that make them comparable or not.

## Acceptance Criteria

- [ ] Each DORA figure is shown with its band and mapping text; a 'not measured' value renders as such, never as zero
- [ ] Two projects with different DORA mappings are never placed on one comparative scale without the mapping shown

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
