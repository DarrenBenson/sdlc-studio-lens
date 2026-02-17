# PL0003: Trigger Sync and Track Status - Implementation Plan

> **Status:** Complete
> **Story:** [US0003: Trigger Sync and Track Status](../stories/US0003-trigger-sync-and-track-status.md)
> **Epic:** [EP0001: Project Management](../epics/EP0001-project-management.md)
> **Created:** 2026-02-17
> **Language:** Python

## Overview

Implement the sync trigger endpoint (POST /api/v1/projects/{slug}/sync) and the sync status state machine. This story establishes the sync lifecycle: the API returns 202 Accepted immediately, a background task updates sync_status through the state machine (never_synced -> syncing -> synced/error), and concurrent sync attempts are rejected with 409. Also includes the system health check endpoint.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Trigger sync returns 202 | POST /projects/{slug}/sync returns 202 with sync_status "syncing" |
| AC2 | Sync transitions to synced | On success, sync_status becomes "synced" and last_synced_at is set |
| AC3 | Sync transitions to error | On failure, sync_status becomes "error" and sync_error is populated |
| AC4 | Concurrent sync prevention | 409 SYNC_IN_PROGRESS when sync already running |
| AC5 | Status queryable via detail | GET /projects/{slug} reflects current sync_status |

---

## Technical Context

### Language & Framework
- **Primary Language:** Python 3.12+
- **Framework:** FastAPI >=0.115.0
- **Test Framework:** pytest >=8.0.0 with pytest-asyncio

### Relevant Best Practices
- Type hints on all public functions
- pathlib for filesystem operations
- Specific exception handling (no bare except)
- Logging module (not print)
- Ruff for linting and formatting

### Library Documentation (Context7)

| Library | Context7 ID | Key Patterns |
|---------|-------------|--------------|
| FastAPI | /fastapi/fastapi | BackgroundTasks parameter, Response(status_code=202), Depends() for dependency injection |
| SQLAlchemy | /websites/sqlalchemy_en_21 | session.refresh(), async session commit patterns, update() statement |
| Pydantic | - | Literal type for sync_status enum, response models |

### Existing Patterns

Builds on US0001 and US0002 patterns:
- `backend/src/sdlc_lens/models/project.py` - Project model with sync_status, sync_error, last_synced_at fields
- `backend/src/sdlc_lens/services/project.py` - get_project_by_slug() service function
- `backend/src/sdlc_lens/api/projects.py` - Projects router with CRUD endpoints

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** API story with state machine logic, 9 edge cases, and clear state transitions. The sync state machine has defined valid transitions that are straightforward to test. Background task execution requires careful mocking but the state transitions themselves are pure logic. Test-first ensures the 409 concurrent prevention and state machine are correct.

### Test Priority
1. POST /projects/{slug}/sync returns 202 (happy path)
2. Concurrent sync prevention (409)
3. State machine transitions (syncing -> synced, syncing -> error)
4. Re-sync from error/synced states
5. Health check endpoint

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Create SyncTriggerResponse schema | `backend/src/sdlc_lens/schemas/project.py` | PL0001 | [ ] |
| 2 | Create HealthResponse schema | `backend/src/sdlc_lens/schemas/system.py` | - | [ ] |
| 3 | Create sync service with trigger and state machine | `backend/src/sdlc_lens/services/sync.py` | PL0001 | [ ] |
| 4 | Add POST /projects/{slug}/sync endpoint | `backend/src/sdlc_lens/api/projects.py` | 1, 3 | [ ] |
| 5 | Create system router with health check | `backend/src/sdlc_lens/api/system.py` | 2 | [ ] |
| 6 | Register system router in main app | `backend/src/sdlc_lens/api/router.py` | 5 | [ ] |
| 7 | Write sync trigger integration tests | `backend/tests/test_sync_api.py` | 4 | [ ] |
| 8 | Write state machine transition tests | `backend/tests/test_sync_api.py` | 3 | [ ] |
| 9 | Write health check integration tests | `backend/tests/test_system_api.py` | 5 | [ ] |

### Parallel Execution Groups

| Group | Tasks | Prerequisite |
|-------|-------|--------------|
| Schemas | 1, 2 | PL0001 complete |
| Services | 3 | Group: Schemas |
| Endpoints | 4, 5, 6 | Group: Services |
| Tests | 7, 8, 9 | Group: Endpoints |

---

## Implementation Phases

### Phase 1: Sync Service & State Machine
**Goal:** Implement sync trigger logic with state machine and concurrent prevention

- [ ] Create `SyncTriggerResponse` schema (slug, sync_status, message)
- [ ] Create `HealthResponse` schema (status, database, version)
- [ ] Create `services/sync.py` with:
  - `trigger_sync()` - check current status, reject if "syncing" (409), set to "syncing", clear sync_error, launch background task
  - `_run_sync()` - background task stub that sets sync_status to "synced" and updates last_synced_at (actual document parsing is EP0002)
  - `_handle_sync_error()` - set sync_status to "error", populate sync_error message

**Files:**
- `backend/src/sdlc_lens/schemas/project.py` - Add SyncTriggerResponse
- `backend/src/sdlc_lens/schemas/system.py` - HealthResponse (new file)
- `backend/src/sdlc_lens/services/sync.py` - Sync service (new file)

### Phase 2: API Endpoints
**Goal:** Wire sync trigger and health check to HTTP routes

- [ ] Add `POST /api/v1/projects/{slug}/sync` endpoint - validates project exists (404), checks sync_status (409 if syncing), triggers background task, returns 202
- [ ] Create `api/system.py` with `GET /api/v1/system/health` - checks DB connectivity, returns 200 with status fields
- [ ] Register system router in `api/router.py`

**Files:**
- `backend/src/sdlc_lens/api/projects.py` - Add sync endpoint
- `backend/src/sdlc_lens/api/system.py` - Health check (new file)
- `backend/src/sdlc_lens/api/router.py` - Register system router

### Phase 3: Testing
**Goal:** Verify all acceptance criteria and state machine transitions

- [ ] Write sync trigger tests (202 response, fields present)
- [ ] Write concurrent prevention tests (409 when already syncing)
- [ ] Write state transition tests (never_synced->syncing, syncing->synced, syncing->error)
- [ ] Write re-sync tests (from "synced" and "error" states)
- [ ] Write health check tests (200 with status fields)

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | POST /projects/{slug}/sync returns 202 | `tests/test_sync_api.py` | Pending |
| AC2 | sync_status transitions to "synced", last_synced_at set | `tests/test_sync_api.py` | Pending |
| AC3 | sync_status transitions to "error", sync_error populated | `tests/test_sync_api.py` | Pending |
| AC4 | POST while syncing returns 409 SYNC_IN_PROGRESS | `tests/test_sync_api.py` | Pending |
| AC5 | GET /projects/{slug} reflects current sync_status | `tests/test_sync_api.py` | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | Sync trigger for non-existent project | get_project_by_slug() returns None; raise 404 NOT_FOUND | Phase 2 |
| 2 | Project path no longer exists on filesystem | Background task catches OSError; transitions to "error" with descriptive message | Phase 1 |
| 3 | Re-sync after failure (error state) | Allow trigger from "error" state; clear sync_error, set to "syncing" | Phase 1 |
| 4 | Re-sync from synced state | Allow trigger from "synced" state; normal re-sync flow | Phase 1 |
| 5 | Multiple rapid sync triggers | First returns 202, subsequent return 409 until first completes | Phase 1 |
| 6 | Backend restart during sync | sync_status stuck at "syncing"; next trigger should detect stale state and allow reset | Phase 1 |
| 7 | Health check when DB unreachable | Catch connection error; return 503 with status "unhealthy" | Phase 2 |
| 8 | Sync with zero documents in directory | Complete successfully; sync_status "synced", document_count remains 0 | Phase 1 |
| 9 | Very long sync (>30 seconds) | No timeout; sync runs to completion | Phase 1 |

**Coverage:** 9/9 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Background task loses DB session after request completes | High | Create new session in background task; do not reuse request session |
| Stale "syncing" status after server restart | Medium | Add startup check or allow trigger to reset stale syncing state after timeout |
| Race condition between status check and update | Low | Use database-level optimistic locking or atomic update with WHERE clause |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Edge cases handled
- [ ] Code follows Python best practices (type hints, pathlib, specific exceptions)
- [ ] Ruff linting passes
- [ ] API returns correct error format: `{"error": {"code": "...", "message": "..."}}`
- [ ] State machine transitions verified (all valid paths tested)
- [ ] Health check endpoint functional

---

## Notes

- The actual document parsing logic (filesystem walking, blockquote parsing, FTS5 indexing) is handled in EP0002 stories (US0006-US0011). This story's background task is a stub that validates the path exists and sets the appropriate status.
- The sync service must create its own database session for the background task, as the request session is closed after the 202 response.
- sync_error should be cleared when a new sync is triggered (not just on success).
- The health check is a simple endpoint that verifies database connectivity by executing a lightweight query (SELECT 1).
