# TS0003: Trigger Sync and Track Status

> **Status:** Draft
> **Epic:** [EP0001: Project Management](../epics/EP0001-project-management.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0003 - Trigger Sync and Track Status. Covers the POST /api/v1/projects/{slug}/sync endpoint, sync status state machine transitions, concurrent sync prevention, and the GET /api/v1/system/health endpoint. Tests span unit (state machine logic) and integration (API endpoint) levels.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0003](../stories/US0003-trigger-sync-and-track-status.md) | Trigger Sync and Track Status | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0003 | AC1 | Trigger sync returns 202 | TC0035, TC0036 | Covered |
| US0003 | AC2 | Sync transitions to synced on success | TC0037, TC0038 | Covered |
| US0003 | AC3 | Sync transitions to error on failure | TC0039, TC0040 | Covered |
| US0003 | AC4 | Concurrent sync prevention | TC0041, TC0042 | Covered |
| US0003 | AC5 | Sync status queryable via project detail | TC0043 | Covered |

**Coverage:** 5/5 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | Yes | State machine transition logic is testable in isolation |
| Integration | Yes | API endpoint requires database and background task validation |
| E2E | No | No frontend in this story; API-only |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Python 3.12+, pytest, pytest-asyncio, httpx |
| External Services | None (SQLite in-memory for tests) |
| Test Data | Pre-seeded project via fixtures; tmp_path for path validation |

---

## Test Cases

### TC0035: Sync trigger returns 202 for valid project

**Type:** Integration | **Priority:** Critical | **Story:** US0003 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project "homelabcmd" exists with sync_status "never_synced" | Project registered |
| When | POST /api/v1/projects/homelabcmd/sync | Request accepted |
| Then | Response is 202 with JSON body | Sync started |

**Assertions:**
- [ ] Status code is 202
- [ ] Response body "slug" equals "homelabcmd"
- [ ] Response body "sync_status" equals "syncing"
- [ ] Response body "message" equals "Sync started"

---

### TC0036: Sync trigger for non-existent project returns 404

**Type:** Integration | **Priority:** Critical | **Story:** US0003 AC1 (error path)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | No project with slug "nonexistent" exists | No such project |
| When | POST /api/v1/projects/nonexistent/sync | Request processed |
| Then | Response is 404 with NOT_FOUND error | Error response |

**Assertions:**
- [ ] Status code is 404
- [ ] Response body has "error.code" equal to "NOT_FOUND"

---

### TC0037: Sync status transitions to synced on success

**Type:** Integration | **Priority:** Critical | **Story:** US0003 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A sync is triggered and completes successfully | Background task finishes |
| When | GET /api/v1/projects/homelabcmd after sync completes | Check status |
| Then | sync_status is "synced" and last_synced_at is set | Status updated |

**Assertions:**
- [ ] Response body "sync_status" equals "synced"
- [ ] Response body "last_synced_at" is a valid ISO 8601 timestamp
- [ ] Response body "last_synced_at" is not null

---

### TC0038: last_synced_at updated on successful sync

**Type:** Integration | **Priority:** High | **Story:** US0003 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project with a previous last_synced_at value | Previously synced |
| When | A new sync completes successfully | Re-sync complete |
| Then | last_synced_at is updated to the new timestamp | Timestamp refreshed |

**Assertions:**
- [ ] New last_synced_at is later than previous last_synced_at

---

### TC0039: Sync status transitions to error on failure

**Type:** Integration | **Priority:** Critical | **Story:** US0003 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project whose sdlc_path no longer exists on filesystem | Path removed |
| When | Sync is triggered and background task runs | Task encounters error |
| Then | sync_status is "error" and sync_error is populated | Error captured |

**Assertions:**
- [ ] Response body "sync_status" equals "error"
- [ ] Response body "sync_error" is a non-empty string
- [ ] Response body "sync_error" contains descriptive message about the failure

---

### TC0040: sync_error cleared on new sync attempt

**Type:** Integration | **Priority:** High | **Story:** US0003 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project with sync_status "error" and sync_error populated | Previous failure |
| When | POST /api/v1/projects/homelabcmd/sync (re-sync) | New sync triggered |
| Then | sync_status changes to "syncing" and sync_error is cleared | Error reset |

**Assertions:**
- [ ] Status code is 202
- [ ] Subsequent GET shows sync_error is null while syncing

---

### TC0041: Concurrent sync returns 409

**Type:** Integration | **Priority:** Critical | **Story:** US0003 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project "homelabcmd" has sync_status "syncing" | Sync in progress |
| When | POST /api/v1/projects/homelabcmd/sync | Second sync attempt |
| Then | Response is 409 with SYNC_IN_PROGRESS error | Concurrent rejected |

**Assertions:**
- [ ] Status code is 409
- [ ] Response body has "error.code" equal to "SYNC_IN_PROGRESS"
- [ ] Response body has "error.message" containing "Sync already running"

---

### TC0042: Multiple rapid sync triggers

**Type:** Integration | **Priority:** Medium | **Story:** US0003 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project "homelabcmd" with sync_status "never_synced" | Ready to sync |
| When | Two POST /sync requests sent in rapid succession | Race condition |
| Then | First returns 202, second returns 409 | Only one sync runs |

**Assertions:**
- [ ] First response status code is 202
- [ ] Second response status code is 409

---

### TC0043: Sync status queryable via project detail

**Type:** Integration | **Priority:** High | **Story:** US0003 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project "homelabcmd" is currently syncing | sync_status is "syncing" |
| When | GET /api/v1/projects/homelabcmd | Poll for status |
| Then | Response includes sync_status "syncing" | Status visible |

**Assertions:**
- [ ] Response body "sync_status" equals "syncing"

---

### TC0044: Re-sync from synced state

**Type:** Integration | **Priority:** High | **Story:** US0003 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with sync_status "synced" | Previously synced |
| When | POST /api/v1/projects/homelabcmd/sync | Re-sync request |
| Then | Response is 202; sync proceeds normally | Re-sync allowed |

**Assertions:**
- [ ] Status code is 202
- [ ] Response body "sync_status" equals "syncing"

---

### TC0045: Re-sync from error state

**Type:** Integration | **Priority:** High | **Story:** US0003 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with sync_status "error" | Previous failure |
| When | POST /api/v1/projects/homelabcmd/sync | Retry sync |
| Then | Response is 202; sync_error cleared | Recovery allowed |

**Assertions:**
- [ ] Status code is 202
- [ ] Response body "sync_status" equals "syncing"

---

### TC0046: Health check returns 200

**Type:** Integration | **Priority:** High | **Story:** US0003 AC (health endpoint)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Application is running with database connected | Healthy state |
| When | GET /api/v1/system/health | Health check request |
| Then | Response is 200 with status fields | Healthy response |

**Assertions:**
- [ ] Status code is 200
- [ ] Response body "status" equals "healthy"
- [ ] Response body "database" equals "connected"
- [ ] Response body "version" is a non-empty string

---

### TC0047: Sync with zero documents in directory

**Type:** Integration | **Priority:** Medium | **Story:** US0003 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project path exists but contains no .md files | Empty directory |
| When | Sync is triggered and completes | Background task finishes |
| Then | sync_status is "synced" with document_count 0 | Success with no docs |

**Assertions:**
- [ ] sync_status equals "synced"
- [ ] document_count equals 0

---

## Fixtures

```yaml
project_never_synced:
  name: "HomelabCmd"
  sdlc_path: "<tmp_path>/sdlc-studio"
  sync_status: "never_synced"
  sync_error: null

project_syncing:
  name: "HomelabCmd"
  sdlc_path: "<tmp_path>/sdlc-studio"
  sync_status: "syncing"
  sync_error: null

project_synced:
  name: "HomelabCmd"
  sdlc_path: "<tmp_path>/sdlc-studio"
  sync_status: "synced"
  last_synced_at: "2026-02-17T10:00:00Z"

project_error:
  name: "HomelabCmd"
  sdlc_path: "<tmp_path>/sdlc-studio"
  sync_status: "error"
  sync_error: "sdlc-studio path not found"

project_missing_path:
  name: "HomelabCmd"
  sdlc_path: "<tmp_path>/nonexistent"
  sync_status: "never_synced"

empty_sdlc_directory:
  path: "<tmp_path>/sdlc-studio"
  files: []
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0035 | Sync trigger returns 202 | Pending | - |
| TC0036 | Sync trigger for non-existent project | Pending | - |
| TC0037 | Sync transitions to synced on success | Pending | - |
| TC0038 | last_synced_at updated on successful sync | Pending | - |
| TC0039 | Sync transitions to error on failure | Pending | - |
| TC0040 | sync_error cleared on new sync attempt | Pending | - |
| TC0041 | Concurrent sync returns 409 | Pending | - |
| TC0042 | Multiple rapid sync triggers | Pending | - |
| TC0043 | Sync status queryable via project detail | Pending | - |
| TC0044 | Re-sync from synced state | Pending | - |
| TC0045 | Re-sync from error state | Pending | - |
| TC0046 | Health check returns 200 | Pending | - |
| TC0047 | Sync with zero documents in directory | Pending | - |

---

## Traceability

| Artefact | Reference |
|----------|-----------|
| PRD | [sdlc-studio/prd.md](../prd.md) |
| Epic | [EP0001](../epics/EP0001-project-management.md) |
| TSD | [sdlc-studio/tsd.md](../tsd.md) |

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec from US0003 story plan |
