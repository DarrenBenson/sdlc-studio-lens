# US-01KXCB7V: Make the review index and the lint baseline tell the truth

> **Status:** Ready
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Tomas Reinholt; persona; v3
> **Triaged-by:** Darren; human; v3
> **Epic:** EP-01KXCBC9
> **Change Request:** [CR-01KXCA1Q](../change-requests/CR-01KXCA1Q-wire-ci-to-push-and-pr-and-settle.md)
> **Persona:** Tomas Reinholt (QA amigo)
> **Priority:** Medium
> **Story Points:** 1

## User Story

**As a** developer deciding whether this project is safe to release
**I want** the review index and the lint baseline to state the real position
**So that** I am not reading a release blocker that was cleared months ago, or starting a new CI green from yellow

## Background

`sdlc-studio/reviews/_index.md` still advertises **"Open Critical Issues: 3"** and *"address the High set
before any release"*. All 13 bugs are `Fixed`, including RV-0001's three High-severity findings (path
traversal, sync data-loss, error-shape). The summary is hand-maintained - `reconcile` does not own it - so
it has sat there misreporting release readiness to every subsequent reader.

Separately, RETRO-0006 recorded a pre-existing `SortField` ruff hint carried as out-of-scope. A CI gate
that is yellow on the day it is born trains everyone to ignore it (LL0009: a silent misleading signal
outranks a loud one).

## Acceptance Criteria

### AC1: The review index reports the real state

- **Given** all three of RV-0001's High-severity bugs are Fixed
- **When** `reviews/_index.md` is corrected
- **Then** the summary shows zero open critical issues and no longer names a release blocker, and the "Reviews Requiring Attention" row is resolved rather than merely deleted - it records that the findings were fixed and where
- **Verify:** shell grep -q "Open Critical Issues | 0" sdlc-studio/reviews/_index.md
- **Verified:** yes (2026-07-12)

### AC2: The lint baseline is clean, under the ruff CI actually uses

- **Given** CI must not start life yellow
- **When** `ruff check` runs over the backend **with the venv's ruff, not one from `$PATH`**
- **Then** it reports no findings. `SortField` inherited from both `str` and `Enum` (UP042) and is now a `StrEnum` - safe because the only consumer reads `sort.value`, never `str(sort)`
- **Verify:** shell cd backend && .venv/bin/ruff check src/ tests/
- **Verified:** yes (2026-07-13)

### AC3: Formatting is clean

- **Given** the CI lint job will enforce it
- **When** `ruff format --check` runs with the venv's ruff
- **Then** it passes
- **Verify:** shell cd backend && .venv/bin/ruff format --check src/ tests/
- **Verified:** yes (2026-07-13)

### AC4: Local and CI lint with the same ruff

- **Given** an unbounded `ruff>=0.8.0` let CI install 0.15.x while the developer had 0.14.x on `$PATH`, so `ruff check` was green locally and red in CI on a rule the local build did not know (UP042) - LL0011, an environment gap masquerading as a code defect
- **When** the dev dependency is bounded and `AGENTS.md` documents the venv's ruff
- **Then** a fresh install and CI resolve to the same ruff, and the lint gate means one thing
- **Verify:** shell grep -q 'ruff>=0.15.0,<0.16.0' backend/pyproject.toml && grep -q '.venv/bin/ruff check' AGENTS.md
- **Verified:** yes (2026-07-13)

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCA1Q |
