# RETRO-0007: Incremental sync sprint: CI that gates, and three critics that found what green could not

> **Date:** 2026-07-13
> **Batch:** CR-01KXCA1Q, CR-01KXCAHV (CR-01KXCAZJ deferred)
> **Goal:** Put a real safety net under the repo, then make a GitHub re-sync fetch only what changed.
> **Delivered:** 2 / 3   **Blocked:** 0 (one deliberately deferred)

## Delivered

- **CR-01KXCA1Q - CI that actually gates.** CI fired *only* on `v*` tags, so backend, frontend and `tsc`
  ran for the first time **at release**; between tags `main` was verified by whoever remembered to run the
  suites. Added `ci.yml` (backend / frontend / e2e) on every push to `main` and every PR, **saw each gate
  go red on a scratch branch**, and turned on branch protection so a red PR is no longer mergeable. The
  E2E suite - which ran *nowhere*, and could not run on the dev box - now runs in CI, and passed on the
  first execution it has ever had.
- **CR-01KXCAHV - incremental GitHub sync.** A re-sync used to download the whole tarball every time. Now
  one Trees call yields every path's git blob SHA, we diff it, and fetch only the blobs that moved. The
  tarball remains the cold start, the backfill, the repair path and the escape hatch (first sync, NULL
  `blob_sha`, stale `parser_epoch`, truncated tree, over the 200-blob cap, or a transient API failure) -
  and every fallback **says which path ran and why**.

## Blocked / deferred

- **CR-01KXCAZJ (commit-SHA poll trigger)** - deliberately deferred, not blocked. The sprint had already
  absorbed three critic rounds and two data-loss-class bugs; the poll is a clean, separable next step now
  that the re-sync it depends on is O(change).

## What went well

- **The adversarial critic was, without exaggeration, the most valuable thing in the sprint.** It ran three
  times and found a **confirmed High-severity bug every single time**, each one invisible to a fully green
  suite:
  1. `blob_sha` was never backfilled for a byte-unchanged file, so every pre-existing install would have
     kept NULLs for ever, taken the tarball for ever, and **incremental sync would never have engaged for a
     single real user**. The feature would have shipped inert.
  2. An unreadable local file was **dropped from the manifest**, and the deletion loop reads absence as
     "deleted upstream" - so a `chmod 000` **destroyed the document** while the file sat intact on disk, and
     the sync reported `synced`. Pre-existing on `main` (BG-01KXCG98), nothing to do with this sprint.
  3. `_index.md` is never a document, so it was never in `existing_docs`, so it was classified "changed" on
     **every sync, for ever**. This repo has ten. The headline claim - a no-op sync costs zero blob
     requests - was **false on every real repo**.
- **The structural fix beat the defensive one, repeatedly.** Rather than teaching the empty-source guard and
  the deletion loop about incremental sync, the manifest was kept *complete* and only the content made
  optional. Both call sites then needed **no change at all** and cannot misfire. The bug class became
  unrepresentable instead of merely tested-against.
- **Mutation testing earned its place.** Fifteen mutants, all killed - including four that a previous
  version of the tests let survive.

## What was hard / what stalled

- **I stated an invariant and it was already false.** "The manifest is complete - every live path is a key"
  went into a docstring as holding *by construction*. It did not hold: the local walker had been dropping
  unreadable files for months. The critic went looking **precisely because the claim was stated so
  confidently**. Asserting an invariant is not establishing one.
- **My own tests were repeatedly the weak point, not the code.** In three separate places a test passed for
  the wrong reason: a fixture with no `_index.md`; a `needs_blob_sha_backfill` clause that silently hollowed
  out BG-01KXARHJ's stale-epoch test (deleting the clause under test left 755 green); and a directory fixture
  not named `*.md`, which let the `type != "blob"` filter be deleted with the suite still green.
- **The critic was also wrong once, and it mattered.** It recommended catching `GitHubSourceError` and
  falling back to the tarball. Applied blanket, that falls back **on a rate limit** - issuing another request
  when the quota is already spent, making the throttling worse. A failing test caught it. An adversarial
  reviewer is a source of hypotheses, not verdicts.

## Lessons

- **An AC that enumerates the paths it checks silently exempts the path it forgot.** "Every *added or
  updated* document gets a `blob_sha`" was fully satisfiable while the feature was broken end to end, because
  a *skipped* document is neither. State the invariant, not the paths.
  <!-- promote the durable, cross-project ones: lessons add --global -->
- **A mocked boundary tests the code on your side of it.** It says nothing about whether you read the other
  side's payload correctly. 148 lines of network code sat at 0% coverage behind an `AsyncMock`, and deleting
  the sole defence against mass deletion kept the whole suite green.
- **A guard that only catches the total case is not a guard.** The empty-source guard fires on a 100% empty
  manifest and *feels* like protection. Every partial failure - the far likelier one - sailed straight past
  it. When writing a defence, ask what the 1% version of the same failure does.
- **When two code paths produce the same artefact, they must agree on what it MEANS.** The tarball and the
  Trees manifests disagreed about `_index.md` and about symlinks, and a path that is live under one and
  absent under the other gets added by one sync and deleted by the next, for ever.
- **A test suite that cannot run is not a safety net** (carried from RETRO-0006, now discharged). It ran
  nowhere; it now runs in CI and has been seen red.

## Metrics

- Units: 2/2 attempted delivered, 1 deferred. Backend tests 735 -> 785 (+50). Migrations 012, 013 (verified
  up **and** down against a populated DB). ruff + tsc + eslint clean; CI green on backend, frontend and e2e.
- **Critic: 3 rounds, 14 findings, 2 HIGH + 2 HIGH + 2 HIGH confirmed. 0 rejected as false.** Two of them
  were data-loss-class. One (BG-01KXCG98) was a live bug in the deployed v0.5.0.
- Mutation: 15 mutants, 15 killed (1 recorded as a provable equivalent).
- Toolchain parity fixed twice: ruff was 0.14 locally vs 0.15 in CI (a green local lint, a red CI); the venv
  was Python 3.14 while CI and production are 3.12. Both are now pinned and documented as a hard rule.
