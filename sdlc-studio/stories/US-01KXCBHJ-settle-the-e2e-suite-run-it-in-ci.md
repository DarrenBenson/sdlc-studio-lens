# US-01KXCBHJ: Settle the E2E suite: run it in CI so its repairs are proven, not assumed

> **Status:** Ready
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Epic:** EP-01KXCBC9
> **Change Request:** [CR-01KXCA1Q](../change-requests/CR-01KXCA1Q-wire-ci-to-push-and-pr-and-settle.md)
> **Persona:** Tomas Reinholt (QA amigo)
> **Priority:** High
> **Story Points:** 3

## User Story

**As a** developer changing the add-project flow
**I want** the E2E suite to actually execute somewhere
**So that** a UI change that invalidates a spec is caught by a machine rather than by someone going to look

## Background

The E2E suite is in no workflow, and Playwright cannot run on the dev box (unsupported on Ubuntu 26.04).
So it executes **nowhere**. RETRO-0006 recorded the cost: the add-project rewrite invalidated
`settings.spec.ts` and 976 passing tests noticed nothing.

The subtlety this story exists for: `settings.spec.ts` was subsequently **repaired by hand** - it now
references CR-01KXB377 and asserts the branch and sdlc-path fields sit behind the Advanced disclosure,
and all six testids it expects do exist in `ProjectForm`. But it was repaired by *reading*, and it has
**never been executed**. A hand-verified spec is a hypothesis. Until it runs, we do not know whether the
suite passes - we only know it type-checks against the DOM we believe we wrote.

CR-01KXCA1Q permits two outcomes: run it in CI, or delete it and strike it from every coverage claim.
This story takes the first. If the suite proves unfixable in CI within the story's budget, fall back to
the second - what is not permitted is leaving it in the repo, unrun, counted as coverage.

## Acceptance Criteria

### AC1: The E2E suite runs in CI on a Playwright-capable runner

- **Given** Playwright cannot execute on the dev box
- **When** the CI workflow runs
- **Then** an E2E job installs browsers (`playwright install --with-deps`) and runs the suite on `ubuntu-latest`
- **Verify:** shell f=.github/workflows/ci.yml; grep -q "playwright install" $f && grep -q "ubuntu-latest" $f
- **Verified:** yes (2026-07-12)

### AC2: The suite actually passes - the hand-repair is confirmed

- **Given** `settings.spec.ts` was repaired statically and never executed
- **When** the E2E job runs against the built app
- **Then** all eight specs pass, including `settings.spec.ts`'s Advanced-disclosure assertions; any spec that fails is repaired against the real DOM, not the assumed one
- **Verify:** manual observe the CI E2E job green on the sprint PR; the run is the first execution this suite has ever had

### AC3: E2E failure fails the build

- **Given** a suite that runs but cannot fail is not a gate (LL0010)
- **When** a spec is deliberately broken on a scratch branch
- **Then** the E2E job fails and the workflow fails with it
- **Verify:** manual break one assertion on a scratch branch, observe CI go red, delete the branch

### AC4: The coverage claim matches reality

- **Given** the project has been counting 43 E2E tests it never ran
- **When** the suite is wired in (or, on fallback, removed)
- **Then** `tsd.md` and the test-count claims state what is actually executed and where
- **Verify:** manual confirm the E2E count in tsd.md matches the specs the CI job runs

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCA1Q; retitled once it emerged the spec was already hand-repaired, so the gap is execution, not repair |
