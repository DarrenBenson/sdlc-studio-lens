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

### AC2: The lint baseline is clean

- **Given** CI must not start life yellow
- **When** `ruff check` runs over the backend
- **Then** it reports no findings - the `SortField` hint is either fixed or given a scoped, commented `noqa` explaining why it stands
- **Verify:** shell cd backend && ruff check src/ tests/
- **Verified:** yes (2026-07-12)

### AC3: Formatting is clean

- **Given** the CI lint job will enforce it
- **When** `ruff format --check` runs
- **Then** it passes
- **Verify:** shell cd backend && ruff format --check src/ tests/
- **Verified:** yes (2026-07-12)

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCA1Q |
