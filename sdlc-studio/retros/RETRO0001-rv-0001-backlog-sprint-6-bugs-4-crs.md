# RETRO-0001: RV-0001 backlog sprint - 6 bugs + 4 CRs delivered

> **Date:** 2026-07-11
> **Batch:** bugs Open + crs Proposed (RV-0001 review backlog)
> **Goal:** done
> **Delivered:** 10 / 10   **Blocked:** 0
> **Raised-by:** Priya Nair; persona; v3

## Delivered

4 waves, file-conflict-ordered, each unit TDD (failing test first) then green commit.

- **BG-01KX8B82** (High) - SPA static handler contains the path (`is_relative_to` the static root) and returns a canonical JSON 404 for `/api` (incl. bare `/api`); closes the LFI.
- **BG-01KX8BFP** (High) - sync refuses to mass-delete when the source returns zero files; sets `status=error` instead of silently wiping documents.
- **BG-01KX8BE8** (High) - global `RequestValidationError` (422) + catch-all `Exception` (500) handlers emit the canonical `{error:{code,message}}` shape; no detail leak.
- **BG-01KX8BJY** (Medium) - config-gated `sdlc_path` allowlist (`SDLC_LENS_ALLOWED_PROJECT_BASE`); backward-compatible.
- **BG-01KX8B04** (Medium) - `run_sync_task` failure recovery (never stuck `syncing`) + atomic conditional UPDATE for the transition.
- **BG-01KX8BY1** (Medium) - blocking tarball extract + filesystem walk moved off the event loop via `asyncio.to_thread`.
- **CR-01KX8BBH** (Medium) - optional Fernet encryption of the GitHub PAT at rest (`SDLC_LENS_TOKEN_ENCRYPTION_KEY`), decrypt-on-use, decrypt-then-mask.
- **CR-01KX8BYH** (Medium) - aggregate stats via a fixed 4 grouped queries (was 3*N); completion from true integer counts, not a rounded percentage.
- **CR-01KX8B1W** (Low) - buildTree self/cycle guard (forest invariant); no more RangeError blank-screen.
- **CR-01KX8B83** (Low) - drop stale error swallow in `get_document_count`; FTS rebuild failure logs at WARNING; `client.ts` routes 4 more calls through `extractErrorMessage`; `release.yml` least-privilege per-job perms + all 7 actions pinned to verified commit SHAs.

## Blocked / deferred

- None blocked. Three out-of-scope follow-ups surfaced by the closing review (see Lessons).

## What went well

- Parallel per-wave TDD subagents on distinct files delivered 9 of 10 units with zero merge conflict; the file-conflict wave ordering (encoded as `Depends on:`) held.
- The closing adversarial review (independent QA seat) verified 4 tests actually bite via revert-and-red, and found zero defects - the fixes were real, not green-by-tautology.
- Suites grew from 611 (442+169) to 659 tests, all green; ruff + tsc clean.

## What was hard / what stalled

- No venv/node_modules existed - had to bootstrap the toolchain (uv venv, npm install) before any TDD.
- Parallel agents each ran the full suite mid-flight and saw transient "flaky"/failing counts caused by siblings' in-progress edits, not real isolation bugs; the integrated re-run was deterministic.
- `file_finding.py` omits the schema-v3 `Raised-by:` line and CR impact/effort; bugs also needed a `Verification depth` field before they could reach `Fixed`. All hand-added.

## Lessons

- **A cannot-fail test hides in plausible fixtures:** the `../../etc/passwd` traversal test passed even with containment removed (it resolves to a non-existent file). The `../secret.txt` case is the one that bites. Always revert-and-red a security test. <!-- promote: lessons add --global -->
- **Parallelise TDD by file surface, integrate serially:** disjoint-file waves let agents run concurrently, but only the orchestrator's post-wave full-suite run is authoritative - ignore agents' mid-flight suite counts.
- **Out-of-scope follow-ups (filed for later, not this sprint):** (1) `mask_token`/decrypt should catch `cryptography.fernet.InvalidToken` so a rotated key degrades gracefully instead of 500-ing the project list; (2) sync has no sanctioned path to legitimately empty a project to zero docs (the data-loss guard blocks it by design) - document or add a force flag if that scenario is real.

## Metrics

- Delivered 10/10; critic rejects: 0 (1 cheap correctness gap fixed during review: bare `/api` 404).
- Tests: backend 442 -> 484 (+42), frontend 169 -> 175 (+6). Commits: 6 on `sprint/rv0001-backlog`.
- Verification depth: functional (unit/integration suites exercising real code paths); mutation lane not run (advisory).
