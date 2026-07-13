# EP-01KXCBC9: CI safety net: run the tests on every change, and stop counting a suite that cannot run

> **Status:** Done
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Tomas Reinholt; persona; v3
> **Triaged-by:** Darren; human; v3
> **Change Request:** [CR-01KXCA1Q](../change-requests/CR-01KXCA1Q-wire-ci-to-push-and-pr-and-settle.md)
> **Priority:** High

## Summary

Puts a working safety net under the repository before the incremental-sync work (CR-01KXCAHV) rewrites
the sync engine's contract.

Two gaps, both recorded by RETRO-0006 and both currently invisible:

1. **CI fires only on `v*` tags.** `release.yml` is the only workflow. Backend tests, frontend tests and
   `tsc` therefore run for the first time *at release*. Between tags, `main` is verified by memory.
2. **The E2E suite executes nowhere.** It is in no workflow and Playwright cannot run on the dev box.
   `settings.spec.ts` was hand-repaired after the add-project rewrite and has still never been run - a
   repair nobody has executed is a hypothesis, not a fix.

The epic's principle, taken straight from the retro: **a test suite that cannot run is not a safety net.**
Either it runs, or it stops being counted.

## Story Breakdown

- [x] [US-01KXCBB5: Run backend, frontend, types and lint on every push and pull request](../stories/US-01KXCBB5-run-backend-frontend-types-and-lint-on-every.md)
- [x] [US-01KXCBHJ: Settle the E2E suite: run it in CI so its repairs are proven, not assumed](../stories/US-01KXCBHJ-settle-the-e2e-suite-run-it-in-ci.md)
- [x] [US-01KXCB7V: Make the review index and the lint baseline tell the truth](../stories/US-01KXCB7V-make-the-review-index-and-the-lint-baseline.md)

## Acceptance Criteria

- [ ] Backend, frontend, type-check and lint run on every push to `main` and every pull request
- [ ] Each gate has been **seen red** - proven able to fail, not merely observed passing (LL0010)
- [ ] The E2E suite either runs in CI or is removed from the repo and struck from every coverage claim. It is not left unrun and counted
- [ ] The release path keeps its own independent test gate
- [ ] The review index and the lint baseline state the real position, so CI does not start life yellow

## Risks

- **Playwright in CI is unproven here.** The suite has never executed, so the E2E job may surface real failures on first run. That is the point of the story, but it means the story's cost is not knowable up front. CR-01KXCA1Q's escape hatch (delete it, strike the coverage claim) bounds the downside.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCA1Q; three stories |
