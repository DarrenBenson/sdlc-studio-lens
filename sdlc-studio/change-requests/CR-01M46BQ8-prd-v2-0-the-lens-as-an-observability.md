# CR-01M46BQ8: PRD v2.0: the lens as an observability plane, with a project-manager persona

> **Status:** inbox
> **Created:** 2026-10-05
> **Created-by:** sdlc-studio new
> **Raised-by:** Claude Opus 5.5; agent; v1
> **Affects:** sdlc-studio/prd.md, sdlc-studio/personas.md, sdlc-studio/personas/
> **Priority:** High
> **Type:** Documentation
> **Size:** S

## Summary

The PRD (v1.3.0, 2026-02-19) predates the v3 work (connections, incremental sync, poller) and frames the only user as a developer on a homelab. The new goal is a full observability plane for anyone reviewing an sdlc-studio project, including a project manager with no harness and no code access: sprint reports, cost and estimation, DORA, quality evidence, lessons and decisions, across a portfolio. Depends on: CR-01M46BAX.

## Impact

Every following CR's acceptance criteria are judged against this PRD and persona; without them the PM goal is not a requirement anywhere.

## Acceptance Criteria

- [ ] The PRD is at v2.0 and its feature inventory lists the shipped v3 features and the observability-plane features as Not Started
- [ ] A goal-directed (Cooper) persona for a project manager / reviewer exists, with no harness or repo-write access as a stated constraint, and `validate.py personas` reports it well-formed
- [ ] The flat developer persona is rewritten against the Cooper model (the `migrate` content-model finding clears)

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
