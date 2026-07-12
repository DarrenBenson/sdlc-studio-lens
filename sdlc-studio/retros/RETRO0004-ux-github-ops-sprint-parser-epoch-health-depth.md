# RETRO-0004: UX + GitHub + ops sprint (parser-epoch, health depth, prettify, repo selector)

> **Date:** 2026-07-12
> **Batch:** BG-01KXARHJ, CR-01KXARM8, CR-01KXASF9, CR-01KXAS75
> **Goal:** Close the 0.2.0 prod-verification gaps and advance the GitHub-integration and readability themes.
> **Delivered:** 4 / 4   **Blocked:** 0

## Delivered

- **BG-01KXARHJ** - Parser-epoch reparse. A `PARSER_EPOCH` module constant plus a per-document
  `parser_epoch` column (migration 010, `server_default "0"`); the sync skip-vs-reparse guard now
  reparses a byte-unchanged doc when `hash matches AND (parser_epoch or 0) < PARSER_EPOCH`,
  generalising and subsuming the old ref_id-null self-heal. Fixes the two stale `homelabcmd` statuses
  seen on prod. Heals once, then stamps the current epoch so it is not reparsed again.
- **CR-01KXARM8** - Health readiness depth + single-source version. `GET /system/health` now reports
  `migration_ok` (Alembic revision == head, resolved dynamically via ScriptDirectory), `fts_ok`
  (`documents_fts` present), and a `ready` boolean gated on all three; every check is wrapped so a DB
  fault yields `ready:false`, never a 500. The backend version derives from a single
  `importlib.metadata` source (`version.py`), removing four hardcoded literals.
- **CR-01KXASF9** - Prettify the read-only DocumentView. Installed `@tailwindcss/typography`, added a
  dark-tuned `.prose-lens` with a bounded reading measure, a structured metadata card, clickable
  id-reference links (reusing the id resolver), and horizontal scroll for wide tables/code. Purely
  presentational; source content untouched.
- **CR-01KXAS75** - GitHub repo selector. Lists ALL repos a token can see (user + orgs + org repos,
  de-duped, paginated, rate-limit aware), flags - never filters - those already carrying an
  `sdlc-studio/` workspace via a lazy per-row Contents check, and lets ProjectForm browse/search and
  click-to-fill. Token travels in the request body, stored encrypted on the created project as before.

## Blocked / deferred

- None. RFC-01KXARHK (incremental GitHub sync) stays Draft by design - it is the design record whose
  CRs come later; not in this sprint's scope.

## What went well

- Two-wave parallel TDD held: Wave 1 (three units over disjoint file surfaces) and Wave 2 (repo
  selector, built on the committed Wave 1) each integrated green with no cross-wave conflicts.
- The closing adversarial review (QA seat, refute framing) found no critical/high/medium defects and
  cleared the risk paths it probed (parser-epoch idempotency, health gating, token handling,
  pagination termination, id-link XSS).

## What was hard / what stalled

- The transition script's `--root` takes the **project root**, not the `sdlc-studio/` dir - its
  `ARTIFACT_TYPES` rel paths already carry the `sdlc-studio/` prefix, so pointing `--root` at the
  workspace made every id resolve to "artifact not found". Cost one wrong batch before tracing
  `find_by_id` -> `iter_artifact_files`.
- The version single-source surfaced real drift: the editable install's metadata was pinned at 0.1.0
  while pyproject read 0.2.1. The tautological version test (asserting the endpoint against the same
  `get_version()` source) hid it; pinning the test to the pyproject value exposed it, and a
  `uv pip install -e .` refresh reconciled the metadata.

## Lessons

- **A "single-source" assertion must compare against the *upstream* source, not the same accessor the
  code uses** - else it is a tautology that passes through drift. Pin version tests to pyproject.
  <!-- promote the durable, cross-project ones: lessons add --global -->
- **`transition.py --root` = project root** (the type rel paths include `sdlc-studio/`). Recurring
  foot-gun when driving the skill scripts against a consuming project from outside.
- **Editable-install metadata goes stale on version bumps** - `importlib.metadata.version` reflects the
  last `pip/uv install`, not the current pyproject; refresh the install after a bump, or the local
  `/health` mislabels the version (prod is safe: the Docker build does a fresh install per tag).
- **Classify a GitHub 403 by its headers, not just the status** - primary limit (`x-ratelimit-remaining:
  0`) and secondary/abuse limit (`Retry-After`) are both rate limits; only a bare 403 is access-denied.

## Metrics

- Units: 4/4 delivered. Backend tests 654 -> 670 (+16 net; +17 repo-selector, +1 secondary-limit, plus
  parser-epoch/health additions). Frontend 212 -> 216. tsc + eslint clean; ruff clean bar the
  pre-existing `SortField` StrEnum hint (out of scope). Gate: PASS. Critic rejects: 0 (2 LOW
  observations fixed in the close, 1 documented as a non-blocking fragility).
