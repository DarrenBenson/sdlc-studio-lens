# US0003: Trigger Sync and Track Status

> **Status:** Done
> **Epic:** [EP0001: Project Management](../epics/EP0001-project-management.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** to trigger a sync for a project and monitor its status
**So that** I know when documents are imported and can see if anything went wrong

## Context

### Persona Reference
**Darren** - Checks project status at the start of work sessions; reviews document status after running sdlc-studio commands.
[Full persona details](../personas.md#darren)

### Background
After registering a project, the developer triggers a sync to import documents. The sync runs as a background task (returns 202 immediately) while the developer can poll sync status. This story covers the sync trigger endpoint and the sync status state machine; the actual sync logic (filesystem walking, parsing) is handled in EP0002.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| Epic | Protocol | Manual sync only | User triggers via button/API, no auto-sync |
| TRD | API | POST /projects/{slug}/sync returns 202 | Background task, not blocking |
| Epic | State Machine | never_synced, syncing, synced, error | Four states with defined transitions |

---

## Acceptance Criteria

### AC1: Trigger sync returns 202 Accepted
- **Given** a registered project "homelabcmd" with sync_status "never_synced" or "synced"
- **When** I POST to `/api/v1/projects/homelabcmd/sync`
- **Then** I receive 202 with JSON `{"slug": "homelabcmd", "sync_status": "syncing", "message": "Sync started"}`

### AC2: Sync status transitions to synced on success
- **Given** a sync is running for "homelabcmd"
- **When** the sync completes successfully
- **Then** project sync_status changes to "synced" and last_synced_at is set to the current timestamp

### AC3: Sync status transitions to error on failure
- **Given** a sync is running for "homelabcmd"
- **When** the sync fails (e.g., directory no longer accessible)
- **Then** project sync_status changes to "error" and sync_error contains a descriptive message

### AC4: Concurrent sync prevention
- **Given** project "homelabcmd" has sync_status "syncing"
- **When** I POST to `/api/v1/projects/homelabcmd/sync`
- **Then** I receive 409 with error code "SYNC_IN_PROGRESS" and message "Sync already running for this project"

### AC5: Sync status queryable via project detail
- **Given** project "homelabcmd" is currently syncing
- **When** I GET `/api/v1/projects/homelabcmd`
- **Then** the response includes sync_status "syncing", allowing the frontend to poll for completion

---

## Scope

### In Scope
- POST /api/v1/projects/{slug}/sync endpoint
- Background task execution for sync
- Sync status state machine (never_synced → syncing → synced/error)
- sync_error field population on failure
- last_synced_at timestamp update on success
- Concurrent sync prevention (409 if already syncing)
- Health check endpoint: GET /api/v1/system/health

### Out of Scope
- Actual document parsing and storage (US0006-US0011, EP0002)
- Frontend sync button and progress display (US0004)
- Sync progress percentage (not tracked in v1.0; just status)

---

## Technical Notes

### API Contract

**Trigger Sync:**
```
POST /api/v1/projects/{slug}/sync → 202 | 404 | 409
```

**Health Check:**
```
GET /api/v1/system/health → 200
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

### Data Requirements
- sync_status field on projects table: TEXT NOT NULL DEFAULT 'never_synced'
- sync_error field: TEXT NULLABLE
- last_synced_at field: TIMESTAMP NULLABLE
- Background task: FastAPI BackgroundTasks or asyncio.create_task

### State Machine
```
never_synced ──► syncing ──► synced
                    │            │
                    ▼            ▼
                  error      syncing (re-sync)
```

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Sync trigger for non-existent project slug | 404 NOT_FOUND |
| Sync when project path no longer exists on filesystem | Sync starts, then transitions to "error" with message "sdlc-studio path not found" |
| Sync trigger while status is "error" (re-sync after failure) | 202 Accepted; sync_status transitions to "syncing", sync_error cleared |
| Sync trigger while status is "synced" (re-sync) | 202 Accepted; normal re-sync |
| Multiple rapid sync triggers for same project | First returns 202, subsequent return 409 until first completes |
| Backend restart during sync | sync_status stuck at "syncing"; next sync trigger should reset and proceed |
| Health check when database is unreachable | 503 with status "unhealthy" |
| Sync for project with zero documents in directory | Completes successfully with sync_status "synced", document_count 0 |
| Very long sync (>30 seconds) | No timeout; sync runs to completion |

---

## Test Scenarios

- [ ] POST /projects/{slug}/sync returns 202 for valid project
- [ ] POST /projects/{slug}/sync returns 404 for unknown slug
- [ ] POST /projects/{slug}/sync returns 409 when already syncing
- [ ] sync_status transitions from never_synced to syncing
- [ ] sync_status transitions from syncing to synced on success
- [ ] sync_status transitions from syncing to error on failure
- [ ] last_synced_at updated on successful sync
- [ ] sync_error populated on failed sync
- [ ] sync_error cleared on new sync attempt
- [ ] Re-sync from "synced" state works correctly
- [ ] Re-sync from "error" state works correctly
- [ ] GET /system/health returns 200 with status fields
- [ ] Concurrent sync requests return 409

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0001](US0001-register-new-project.md) | Schema | Projects table with sync fields | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

---

## Estimation

**Story Points:** {{TBD}}
**Complexity:** Medium

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial story creation from EP0001 |
