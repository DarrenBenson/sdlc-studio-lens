# US-01KXCBB5: Run backend, frontend, types and lint on every push and pull request

> **Status:** Done
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Tomas Reinholt; persona; v3
> **Triaged-by:** Darren; human; v3
> **Epic:** EP-01KXCBC9
> **Change Request:** [CR-01KXCA1Q](../change-requests/CR-01KXCA1Q-wire-ci-to-push-and-pr-and-settle.md)
> **Persona:** Tomas Reinholt (QA amigo)
> **Priority:** High
> **Story Points:** 2

## User Story

**As a** developer pushing to this repository
**I want** the full test suite to run on every push and pull request
**So that** a broken `main` is caught within minutes rather than at the moment I try to cut a release

## Background

`.github/workflows/release.yml` is the repository's only workflow and it triggers on `push: tags: v*`.
The suites therefore run for the first time **at release**. Between tags, `main` is verified only by
whoever remembered to run the tests locally. Finding a red suite while tagging is the most expensive
possible moment to find it - the release is already in motion.

## Acceptance Criteria

### AC1: A CI workflow exists and triggers on push to main and on pull requests

- **Given** the repository has only a tag-triggered release workflow
- **When** `.github/workflows/ci.yml` is added
- **Then** it triggers on `push` to `main` and on `pull_request`, and it is valid YAML
- **Verify:** shell python3 -c "import yaml;d=yaml.safe_load(open('.github/workflows/ci.yml'));t=d.get(True) or d.get('on');assert 'pull_request' in t and 'main' in t['push']['branches']"
- **Verified:** yes (2026-07-12)

### AC2: The workflow runs the same four checks AGENTS.md documents

- **Given** local and CI must not diverge on what "green" means
- **When** the CI workflow runs
- **Then** it executes the backend suite, the frontend suite, the type check and the linter, using the commands `AGENTS.md` specifies
- **Verify:** shell f=.github/workflows/ci.yml; grep -q pytest $f && grep -q "vitest run" $f && grep -q "tsc --noEmit" $f && grep -q "ruff check" $f
- **Verified:** yes (2026-07-12)

### AC3: A red suite fails the workflow

- **Given** a gate never seen red is not a gate (LL0010)
- **When** a deliberately failing test is pushed on a scratch branch
- **Then** the CI run fails, and the failure names the offending test
- **Verify:** manual push a scratch branch carrying a deliberately failing test, observe CI go red, delete the branch
- **Verified:** manual (2026-07-13) - PR #3: backend went red naming `test_deliberate_failure_to_prove_ci_goes_red`; frontend stayed green, so the gate fails selectively. Branch deleted.

### AC4: The release path stays independently gated

- **Given** tagging must not silently depend on a PR run having happened first
- **When** `release.yml` is left in place
- **Then** it still runs its own test job before building the image
- **Verify:** shell grep -q pytest .github/workflows/release.yml
- **Verified:** yes (2026-07-12)

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCA1Q |
