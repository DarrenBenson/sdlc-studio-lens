# RETRO-0006: Add-project overhaul sprint: browse every connection, plus three review fixes

> **Date:** 2026-07-12
> **Batch:** CR-01KXB377, BG-01KXB3QF
> **Goal:** Rebuild the add-project card around the operator's intent - pick a repository - and derive the rest.
> **Delivered:** 2 / 2   **Blocked:** 0

## Delivered

- **CR-01KXB377** - Add-project card overhaul. `GET /api/v1/connections/repos` aggregates repos across every
  stored connection with **no credential in the request**, de-duplicated by `full_name` (first connection
  wins, and that connection binds the created project). The UI no longer asks which connection to browse
  with; selecting a repo derives the name, URL, branch (the repo's real `default_branch`) and connection;
  branch and sdlc path moved behind an Advanced disclosure. Manual URL, a one-off raw token, and local-path
  sources remain as fallbacks.
- **BG-01KXB3QF** - Org-listing failure no longer aborts the browse. `list_repositories_detailed` returns
  repos plus degradation reasons; org enumeration and per-org listing failures are partial results, and only
  a failure of the primary `GET /user/repos` is fatal. This bit exactly the operator following least-privilege
  advice: a fine-grained PAT is scoped to one owner and is commonly barred from `/user/orgs`.

## Blocked / deferred

- None.

## What went well

- The locked-contract-plus-parallel-agents pattern held for a second sprint: backend and frontend halves were
  built concurrently against a spec neither owned, and integrated first time.
- The adversarial review again found what the tests could not: three real defects, two HIGH, none of which any
  of 976 passing tests noticed. Its tautology hunt (mutating the code to prove the new tests go red) confirmed
  the key assertions were honest.

## What was hard / what stalled

- **The spec forgot a mode.** CR-01KXB377 was written entirely about *adding* a project and never said what
  happens to **edit** when the connection picker is deleted. The agent faithfully removed the control, taking
  with it the only way to change a project's credential - so replacing a revoked PAT submitted `{}` silently.
  The feature was specified as a flow, but the component serves two modes, and the unnamed one broke.
- **A green suite hid a broken E2E.** The card rewrite invalidated `settings.spec.ts`, which asserted the
  branch field was visible in the default GitHub flow. Nothing caught it: the agents were told not to touch
  E2E, the unit suites do not cover it, **and CI does not run the E2E suite at all**. It was found only by
  going to look. Playwright also cannot execute in this environment (unsupported on Ubuntu 26.04), so the
  spec could only be verified by static reading against the component's testids plus a live check of the one
  endpoint it newly depends on.

## Lessons

- **When a shared component serves several modes, a CR that names only one mode is an incomplete spec.**
  Enumerate the modes (add / edit / local / GitHub) and say what each does, or the unnamed one silently loses
  behaviour. Both HIGH findings this sprint were mode-blindness: a stale binding carried between selections,
  and an edit path whose control had been deleted from under it.
  <!-- promote the durable, cross-project ones: lessons add --global -->
- **A test suite that cannot run is not a safety net.** The E2E suite is not in CI and cannot run on the dev
  box, so it silently rotted the moment the UI changed. Either wire it into CI or stop counting it as coverage.
- **Derive, do not store, a value that is a function of a selection.** The stale-`connection_id` bug existed
  only because the credential was mirrored into independent state; deriving it from the current selection at
  submit time made the whole bug class unrepresentable. Prefer that over remembering to clear it.
- **A cap must speak.** Silent truncation - 200 repos returned, `degraded: []`, an entire connection missing -
  reads to the operator as "that is all your repos". Any bound that drops data must name what it dropped.

## Metrics

- Units: 2/2 delivered. Backend tests 720 -> 735 (+15). Frontend 234 -> 248 (+14). No migration (no schema
  change). tsc + eslint clean; ruff clean bar the pre-existing `SortField` hint (out of scope). Gate: PASS.
  Critic: 3 findings (2 high, 1 medium), all confirmed real and all fixed; 0 rejected.
