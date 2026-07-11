# CR-01KX95HS: Centralise terminal-status / canonicalisation logic (duplicated and drifted across 3 modules)

> **Status:** Proposed
> **Triaged-by:** Darren; human; v3
> **Priority:** Medium
> **Type:** Improvement
> **Date:** 2026-07-11
> **Created-by:** sdlc-studio file
> **Raised-by:** Priya Nair; persona; v3

## Summary

Status vocabulary and terminality are re-implemented in three places that have already diverged: `health_check._TERMINAL_BY_TYPE` (omits a `workflow` entry) + its private `_norm_status`; `stats._TERMINAL_STATUSES` (omits `Superseded`); and the intended single source of truth `sdlc_status.canonical_status`/`TERMINAL_STATUS`. Concrete drift: a Superseded workflow whose parent story is Done is falsely flagged `STALE_ARTEFACT_STATUS` (`health_check)`, and a Superseded story is undercounted in completion stats. A code comment already promises 'CR-C will centralise this'.

## Acceptance Criteria

- [ ] `health_check` and stats route terminality/canonicalisation through `sdlc_status` (`canonical_status` + `TERMINAL_STATUS`/`is_done)`; `_norm_status`, `_TERMINAL_BY_TYPE`, `_UNIVERSAL_TERMINAL`, and `stats._TERMINAL_STATUSES` are removed
- [ ] A Superseded workflow under a Done story is NOT flagged stale; a Superseded story is treated consistently in stats
- [ ] Tests cover the previously-drifted cases

## Impact

Three independent status truths guarantee ongoing drift: a change to any terminal rule must be made in health_check, stats, AND sdlc_status. Concrete bugs already exist (false stale flags on Superseded workflows; undercounted Superseded stories). Centralising closes a whole defect class.

**Effort:** M

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Raised |
