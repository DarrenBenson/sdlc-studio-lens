# CR-01KXCA1Q: Wire CI to push and PR, and settle the E2E suite

> **Status:** Complete
> **Verification depth:** functional
> **Triaged-by:** Darren; human; v3
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Tomas Reinholt; persona; v3
> **Related:** RETRO-0006 (the lesson this CR discharges)
> **Priority:** High
> **Type:** Improvement

## Summary

`.github/workflows/release.yml` is the project's **only** workflow and it triggers on `push: tags: v*`.
Backend tests, frontend tests and `tsc` therefore run for the first time **at release**. Between tags,
`main` is unverified by any machine: the suites pass because someone remembered to run them, not because
anything checked. Discovering a red suite while cutting a release is the worst possible moment to find it.

The E2E suite is worse than unverified - it is **unrunnable**. It is in no workflow, and Playwright cannot
execute on the dev box (unsupported on Ubuntu 26.04). RETRO-0006 recorded the consequence: the add-project
rewrite invalidated `settings.spec.ts` (it asserted a branch field that had moved behind the Advanced
disclosure) and **976 passing tests noticed nothing**. It was found only by a human going to look. The
retro's own lesson was blunt: *"A test suite that cannot run is not a safety net. Either wire it into CI
or stop counting it as coverage."* This CR settles that, either way.

Housekeeping in the same pass: `sdlc-studio/reviews/_index.md` still advertises "Open Critical Issues: 3"
and "address the High set before any release", but all 13 bugs are `Fixed`. That summary is hand-maintained,
`reconcile` does not own it, and it now misreports release readiness to the next reader.

## Impact

This is the safety net under every subsequent sprint, which is why it lands **first**. The incremental-sync
work (CR-01KXCAHV) rewrites the sync engine's contract - the highest-stakes code in the product, and the
place a silent regression costs a user their corpus. Doing that on top of a CI that only fires at tag time
is exactly the exposure RETRO-0006 wrote up.

**Effort:** S

## Acceptance Criteria

- [ ] **A CI workflow runs on push to `main` and on every pull request**, executing the backend suite (`PYTHONPATH=src pytest`), the frontend suite (`vitest run`), `tsc --noEmit`, and `ruff check` - the same commands `AGENTS.md` documents, so local and CI cannot diverge
- [ ] **A red suite fails the workflow.** Verified by the mutation discipline: introduce a deliberate failure, watch CI go red, revert. A gate not seen red is not a gate (LL0010)
- [ ] **The release workflow keeps its own test job.** Tagging must not depend on a PR run having happened; the tag path stays independently gated
- [ ] **The E2E suite is settled explicitly - one of two outcomes, no third:** *either* it runs in CI on a Playwright-supported runner image (`ubuntu-latest` + `playwright install --with-deps`), and `settings.spec.ts` is repaired against the post-CR-01KXB377 add-project card; *or* it is removed from the repo and struck from every coverage claim (`tsd.md`, the 43-E2E test count, the status dashboard), so nothing counts a suite that cannot run. **Wiring it into CI is preferred** - the add-project flow is precisely the surface unit tests keep missing
- [ ] **Lint is advisory-clean or explicitly waived.** The pre-existing `SortField` ruff hint noted in RETRO-0006 is either fixed or given a scoped, commented `noqa` - CI must not start life yellow
- [ ] **`reviews/_index.md` tells the truth.** The summary reflects the real state (0 open critical; RV-0001's three High bugs are Fixed), so it no longer reads as a release blocker
- [ ] Tests/verification: the CI workflow is proven by a PR that goes green, and by a deliberate red commit that fails it

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | Darren | Raised from RETRO-0006's "a test suite that cannot run is not a safety net" lesson, plus the discovery that CI fires only on `v*` tags |
