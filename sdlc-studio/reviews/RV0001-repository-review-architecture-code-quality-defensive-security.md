# RV-0001: Repository review - architecture, code quality, defensive security

> **Date:** 2026-07-11
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Type:** review generate (repository on-ramp)

## Scope

Read-only audit of the SDLC Studio Lens implementation across three legs, each run under its
review seat's lens:

- **Architecture** (Engineering seat - Priya Nair): module boundaries, async/resource management,
  error-handling consistency, config/secrets, API surface, performance.
- **Code quality** (QA seat - Tomas Reinholt): correctness defects, dead code, test quality
  (can-the-tests-fail).
- **Defensive security** (Engineering seat): input validation at trust boundaries, injection
  classes, secrets at rest/in-transit, Docker and CI hardening. Remediation-only posture - no
  proof-of-concept exploits; no secret value copied into any artefact.

Surface reviewed: `backend/src/sdlc_lens/` (~3.4k LOC), `frontend/src/` (~5.5k LOC), `Dockerfile`,
`entrypoint.sh`, `docker-compose*.yml`, `.github/workflows/release.yml`. Every finding below was
re-verified at its cited `file:line` before filing.

## System overview

FastAPI (SQLAlchemy 2.0 async + SQLite) backend that syncs SDLC markdown from a local directory
or a GitHub repo, parses frontmatter, indexes it in FTS5, and serves a React SPA for browsing,
dashboards, search and health checks. Single-container deploy: FastAPI serves both the API and the
built frontend. The parser, health-check, FTS, sync and github_source areas are genuinely
well-tested (real SQLite FTS5, real tarball extraction, edge cases exercised); the material gaps
are concentrated in the SPA static-file handler, the sync delete/state-machine paths, and
error-shape consistency.

## Per-leg assessment

| Leg | Verdict | Headline |
| --- | --- | --- |
| Architecture | Needs work | No global exception handler (error-shape contract only half-honoured); sync mass-deletes on an empty source; blocking I/O on the event loop. |
| Code quality | Solid, with gaps | Strong, honest test suites overall; but incremental FTS functions are tested yet never wired in (false confidence), and a failed sync can lock a project in `syncing`. |
| Defensive security | Needs work | Path traversal in the SPA fallback (LFI reaching the token-bearing DB); unrestricted `sdlc_path` harvests host `.md` files; PAT stored plaintext at rest; CI over-privileged/unpinned. |

## Findings

All findings filed through `file_finding.py` (ids tool-allocated). Medium-and-above are individual
artefacts; Low findings were auto-consolidated by the triage layer (`low_consolidation`) into two
themed CRs. All are in the `inbox` triage lane pending triage.

| ID | Title | Type | Severity | Leg |
| --- | --- | --- | --- | --- |
| BG-01KX8B82 | Path traversal in SPA fallback route serves arbitrary files | Bug | High | Security/Arch |
| BG-01KX8BFP | Sync deletes all documents when the source returns empty (data loss) | Bug | High | Arch |
| BG-01KX8BE8 | Canonical error shape not applied to 422/500 responses | Bug | High | Arch |
| BG-01KX8BJY | Unrestricted `sdlc_path` harvests arbitrary host `.md` files | Bug | Medium | Security |
| BG-01KX8B04 | Failed sync can leave a project permanently stuck in `syncing` | Bug | Medium | Code quality |
| BG-01KX8BY1 | Blocking tarball extraction / filesystem walk on the event loop | Bug | Medium | Arch |
| CR-01KX8BBH | Encrypt the GitHub access token at rest | CR | Medium | Security |
| CR-01KX8BYH | Remove the N+1 query pattern in the aggregate stats endpoint | CR | Medium | Arch |
| CR-01KX8B1W | Low-severity bugs (consolidated): buildTree infinite recursion | CR | Low | Code quality |
| CR-01KX8B83 | Low-severity CRs (consolidated): error-swallow/observability/CI + efficiency/dead-code | CR | Low | All |

### Dedup matches

- **Path traversal** was independently reported by the Architecture and Security legs (same handler,
  `main.py:46-48`) - filed once (BG-01KX8B82); the related "SPA catch-all returns HTML 200 for
  unknown `/api` paths instead of JSON 404" is folded into its remediation (same handler, same fix).
- **Token plaintext at rest** was reported by both Architecture and Security legs
  (`project.py:97` / model `:28`) - filed once (CR-01KX8BBH).
- The **non-atomic sync check-then-set** (`sync.py:36-41`) is folded into BG-01KX8B04 (same state
  machine, adjacent fix).

## Limitations

- Runtime repro was not performed (FastAPI/the app stack was not launched in the audit
  environment); findings are verified by code inspection at the cited `file:line`. The path
  traversal, mass-delete, and stuck-`syncing` bugs each warrant a written regression test as part
  of their fix.
- **Secret scan:** no committed secret value was located in source - the GitHub PAT is
  user-supplied at runtime and stored in the DB, not in the repo. There was therefore no value to
  run `review_generate.py scan --secret` against. CR-01KX8BBH addresses the at-rest exposure.
- Dependency-version health and a full CI run were not executed; treat those as unaudited.

## Top five priorities (in order)

1. **BG-01KX8B82 - Path traversal in the SPA fallback.** Highest impact: unauthenticated LAN read
   of arbitrary container files, including the SQLite DB holding GitHub tokens. Contain the path
   (`is_relative_to` the static root) or delegate to `StaticFiles(html=True)`.
2. **BG-01KX8BFP - Sync mass-delete on empty source.** Silent, non-recoverable data loss on a
   misconfigured `repo_path`/branch or an emptied directory. Add the empty-source guard before the
   delete pass.
3. **BG-01KX8BE8 - Canonical error shape on 422/500.** Register global exception handlers so the
   API contract holds off the happy path (the frontend already expects `error.message`).
4. **BG-01KX8B04 - Stuck-`syncing` recovery.** Wrap `run_sync_task` so a failure sets
   `sync_status='error'`; make the status transition atomic. Prevents a permanent 409 lockout.
5. **BG-01KX8BJY + CR-01KX8BBH - `sdlc_path` allowlist + token encryption.** Close the two
   data-exposure paths: constrain `sdlc_path` to an allowlisted base, and encrypt the PAT at rest.

## Verdict

The core sync/parse/search/health engine is well-built and honestly tested, but the HTTP edge (SPA
static handler, error-shape contract) and the sync delete/state-machine paths carry real
correctness and security defects - three of them High. None is a regression from the schema-v3
upgrade; all pre-date it. Recommend triaging the six bugs first (the three High before any release),
then the two Medium CRs, then the two Low consolidations. Route each through the normal pipeline
(triage the `inbox` findings -> plan -> implement -> verify) with a regression test per bug.

**Next action:** `/sdlc-studio bug` triage on BG-01KX8B82 (path traversal) - or run
`/sdlc-studio status` to see the full findings backlog.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | Priya Nair | Created via `new` (deterministic) |
| 2026-07-11 | Priya Nair | Filled report: 3 legs, 10 findings filed, top-5 priorities |
