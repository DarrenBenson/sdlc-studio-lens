# BG-01M46B27: Production compose file pins a stale image tag

> **Status:** inbox
> **Created:** 2026-10-05
> **Created-by:** sdlc-studio new
> **Raised-by:** Claude Opus 5.5; agent; v1
> **Affects:** docker-compose.prod.yml, .github/workflows/ci.yml
> **Severity:** Medium
> **Points:** 1

## Summary

`docker-compose.prod.yml` pulls `ghcr.io/darrenbenson/sdlc-studio-lens:0.1.0-alpha.1`, while `backend/pyproject.toml` and `frontend/package.json` are at 0.6.1. A production deploy from the compose file runs a months-old image with none of the v3 work.

## Steps to Reproduce

1. Read `docker-compose.prod.yml` image line. 2. Compare with `version` in `backend/pyproject.toml`. 3. They differ (0.1.0-alpha.1 vs 0.6.1).

## Proposed Fix

Pin the tag to the released version (or an `${SDLC_LENS_VERSION}` variable defaulting to it) and add a CI step that fails when the pinned tag and the package version disagree.

## Acceptance Criteria

- [ ] **AC1** The prod compose image tag equals the package version, or is a variable whose documented default equals it
- [ ] **AC2** CI fails when the compose tag and `backend/pyproject.toml` version disagree, shown by a test or a deliberately broken fixture

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
