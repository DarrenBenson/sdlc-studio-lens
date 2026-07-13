# US-01KXDDA0: Make auto-sync opt-in and make staleness legible in the UI

> **Status:** Done
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Elena Foss; persona; v3
> **Triaged-by:** Darren; human; v3
> **Epic:** EP-01KXDDG7
> **Change Request:** [CR-01KXCAZJ](../change-requests/CR-01KXCAZJ-commit-sha-poll-trigger-to-keep-github-projects.md)
> **Depends on:** US-01KXDD0K
> **Persona:** Elena Foss (Product amigo)
> **Priority:** Medium
> **Story Points:** 2

## User Story

**As an** operator reading a project's dashboard
**I want** to know how old the data is, and to choose whether it keeps itself current
**So that** I can tell "this project has no open bugs" apart from "this project HAD no open bugs the last time anyone synced it"

## Background

This is the half of the CR that is actually about the user. The poller makes the data fresh; this story
makes the freshness **legible** - and that matters *whether or not polling is on*.

The failure this addresses is silence, not staleness. A lens showing a confidently green health score over
a three-week-old corpus is worse than one that admits it is stale, because the operator acts on it. So the
project must say when it last synced, and whether it is keeping itself current.

Auto-sync is **opt-in, default off**: an existing project must behave exactly as it does today until the
operator asks for something different (RETRO-0006 - a change that alters an unnamed mode silently is an
incomplete change).

## Acceptance Criteria

### AC1: `auto_sync` is per-project, default OFF

- **Given** existing projects must not change behaviour on upgrade
- **When** the column is added
- **Then** it defaults to off, and every existing project keeps syncing exactly as it does today until the operator turns it on
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_poller.py -q -k auto_sync_defaults_off
- **Verified:** yes (2026-07-13)

### AC2: The API exposes and accepts it

- **Given** the UI needs to read and set it
- **When** a project is fetched or updated
- **Then** `auto_sync` and `last_synced_at` are in the response, and `auto_sync` can be toggled
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_projects.py -q -k auto_sync
- **Verified:** yes (2026-07-13)

### AC3: The UI can turn it on, and says whether it is on

- **Given** an operator on the project settings
- **When** they toggle auto-sync
- **Then** it persists, and the project surface shows whether auto-sync is active
- **Verify:** shell cd frontend && npx vitest run -t "auto-sync" 2>/dev/null | grep -q "passed" || npx vitest run src/components/ProjectForm.test.tsx
- **Verified:** yes (2026-07-13)

### AC4: Staleness is visible even with auto-sync OFF

- **Given** the honesty gap is the point of the story, and it exists whether or not polling is on
- **When** a project is displayed
- **Then** it shows when it last synced, so a stale corpus cannot masquerade as a current one
- **Verify:** manual open the dashboard for a project and confirm the last-synced time is shown, with auto-sync both on and off

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCAZJ |
