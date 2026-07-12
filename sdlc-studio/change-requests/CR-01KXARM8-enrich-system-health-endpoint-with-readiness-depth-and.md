# CR-01KXARM8: Enrich system health endpoint with readiness depth and single-source the version

> **Status:** Complete
> **Verification depth:** functional
> **Triaged-by:** Darren; human; v3
> **Created:** 2026-07-12
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Priority:** Medium
> **Type:** Improvement

## Summary

`GET /api/v1/system/health` (`api/routes/system.py`) does a single `SELECT 1` DB check and returns
`{status, database, version}`. It passes even when the app is only half-serviceable - e.g. a
half-applied migration or a missing FTS index. As CD moves toward automation (homelab RFC0006
health-gates deploys and the reconcile agent reports health to Uptime Kuma), a deploy should be
gated on a deeper readiness signal than "the DB accepts a query". Separately, the app version is
hardcoded in four places (`api/routes/system.py`, `main.py`, `backend/pyproject.toml`,
`frontend/package.json`) and hand-synced each release - currently consistent (0.2.1) but drift-prone
(it briefly diverged during the 0.2.x bumps).

Add readiness depth to the health endpoint and derive the backend version from a single source.

## Impact

The health endpoint is the CD gate and the monitoring signal (Uptime Kuma, the reconcile agent, and
the deploy verification used for 0.2.0). A shallow check lets a broken-but-listening container pass
CD; single-sourcing the version stops the four copies silently diverging and mislabelling a release.
Both directly support the automated release-to-deploy work in the homelab RFC0006.

**Effort:** S

## Acceptance Criteria

- [ ] The health endpoint reports **migration state** (the current Alembic revision equals head) and fails readiness when the DB is behind head
- [ ] The health endpoint reports whether the **FTS index** (`documents_fts`) is present; a missing index degrades readiness (not a hard 500)
- [ ] Liveness vs readiness are distinguishable (either a `ready` boolean in the response, or a separate `/readyz` alongside a cheap `/healthz`) so an orchestrator can tell "alive" from "ready to serve"
- [ ] The backend version is derived from a single source (`importlib.metadata.version` / pyproject) - `system.py` and `main.py` no longer hardcode it
- [ ] Tests cover: healthy, DB-behind-head, and FTS-missing states, plus the version-derivation

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-12 | Priya Nair | Raised |
