# CR-01KX8YMC: Health-check alignment with schema v3 vocabulary and types

> **Status:** Proposed
> **Triaged-by:** Darren; human; v3
> **Depends on:** CR-01KX8Y32
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio new
> **Raised-by:** Tomas Reinholt; persona; v3
> **Priority:** Medium
> **Type:** Improvement

## Summary

The health-check rules engine (`services/health_check.py`) uses a `[A-Z]{2}\d{4}` regex and hardcoded
status sets, so it misfires on ULID ids and new statuses and misflags CR/RFC/retro/review documents
as orphaned or incomplete. Route the rules through the CR-A id matcher and the CR-C status
canonicaliser, update the terminal/inactive status sets to the v3 vocabulary, and exempt/relabel the
new types. Optionally add additive v3-aware rules.

## Impact

On any v3 or new-type project the health score becomes noise - false orphan and incompleteness
findings - which defeats the feature's purpose of surfacing real documentation gaps.

**Effort:** S

## Acceptance Criteria

- [ ] Health rules use the shared id matcher and the status canonicaliser, and the v3 terminal/inactive status sets (Complete/Fixed/Verified/Closed/Won't-*/Superseded)
- [ ] CR, RFC, retro, review, and decision documents are not misflagged as orphaned or incomplete
- [ ] (Optional, additive) rules flag untriaged `inbox` findings and Done stories whose ACs lack a `Verify:` line
- [ ] Tests run the health check over a schema-v3 fixture project and assert no false findings on the new types

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | Tomas Reinholt | Raised |
