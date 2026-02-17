# TS0002: Project List and Management API

> **Status:** Draft
> **Epic:** [EP0001: Project Management](../epics/EP0001-project-management.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0002 - Project List and Management API. Covers GET (list and detail), PUT (update), and DELETE (cascade) endpoints for project management. Tests span integration level using the async test client and in-memory SQLite database established in US0001.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0002](../stories/US0002-project-list-and-management-api.md) | Project List and Management API | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0002 | AC1 | List all registered projects | TC0019, TC0020, TC0021 | Covered |
| US0002 | AC2 | Get project details by slug | TC0022, TC0023 | Covered |
| US0002 | AC3 | Update project name and path | TC0024, TC0025, TC0026, TC0027, TC0028 | Covered |
| US0002 | AC4 | Delete project with cascade | TC0029, TC0030, TC0031 | Covered |
| US0002 | AC5 | Not found for unknown slug | TC0032, TC0033, TC0034 | Covered |

**Coverage:** 5/5 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | No | Service functions are thin wrappers around SQLAlchemy queries; integration tests cover them |
| Integration | Yes | API endpoints require database and HTTP layer validation |
| E2E | No | No frontend in this story; API-only |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Python 3.12+, pytest, pytest-asyncio, httpx |
| External Services | None (SQLite in-memory for tests) |
| Test Data | Pre-seeded projects via fixtures; tmp_path for path validation |

---

## Test Cases

### TC0019: List projects returns all registered projects

**Type:** Integration | **Priority:** Critical | **Story:** US0002 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Two projects "HomelabCmd" and "SDLCLens" are registered | Both in database |
| When | GET /api/v1/projects | Request accepted |
| Then | Response is 200 with array of 2 project objects | Both projects returned |

**Assertions:**
- [ ] Status code is 200
- [ ] Response body is a JSON array with length 2
- [ ] Each object contains slug, name, sdlc_path, sync_status, last_synced_at, document_count, created_at
- [ ] Projects are ordered by created_at

---

### TC0020: List projects returns empty array when none registered

**Type:** Integration | **Priority:** High | **Story:** US0002 AC1 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | No projects are registered | Empty database |
| When | GET /api/v1/projects | Request accepted |
| Then | Response is 200 with empty array | `[]` returned |

**Assertions:**
- [ ] Status code is 200
- [ ] Response body is `[]`

---

### TC0021: List projects includes document_count field

**Type:** Integration | **Priority:** High | **Story:** US0002 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project exists with synced documents | Documents in database |
| When | GET /api/v1/projects | Request accepted |
| Then | Each project object includes document_count reflecting actual count | Computed field correct |

**Assertions:**
- [ ] Response body items contain "document_count" as integer >= 0
- [ ] document_count reflects the actual number of documents for that project

---

### TC0022: Get project by slug returns project details

**Type:** Integration | **Priority:** Critical | **Story:** US0002 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project "HomelabCmd" exists with slug "homelabcmd" | Project registered |
| When | GET /api/v1/projects/homelabcmd | Request accepted |
| Then | Response is 200 with full project object | All fields present |

**Assertions:**
- [ ] Status code is 200
- [ ] Response body "slug" equals "homelabcmd"
- [ ] Response body "name" equals "HomelabCmd"
- [ ] Response body contains sdlc_path, sync_status, last_synced_at, document_count, created_at

---

### TC0023: Get project includes stats summary

**Type:** Integration | **Priority:** Medium | **Story:** US0002 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project exists with sync_status "never_synced" | Project registered |
| When | GET /api/v1/projects/homelabcmd | Request accepted |
| Then | Response includes sync_status and document_count | Stats present |

**Assertions:**
- [ ] Response body "sync_status" is a valid status string
- [ ] Response body "document_count" is an integer

---

### TC0024: Update project name successfully

**Type:** Integration | **Priority:** Critical | **Story:** US0002 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project "HomelabCmd" exists with slug "homelabcmd" | Project registered |
| When | PUT /api/v1/projects/homelabcmd with {"name": "HomelabCmd v2"} | Update request |
| Then | Response is 200 with updated name; slug remains "homelabcmd" | Name updated, slug unchanged |

**Assertions:**
- [ ] Status code is 200
- [ ] Response body "name" equals "HomelabCmd v2"
- [ ] Response body "slug" equals "homelabcmd" (unchanged)
- [ ] Response body "updated_at" is later than "created_at"

---

### TC0025: Update project sdlc_path with path validation

**Type:** Integration | **Priority:** High | **Story:** US0002 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project exists and a new valid directory path | New path exists |
| When | PUT /api/v1/projects/homelabcmd with {"sdlc_path": "<new_valid_path>"} | Update request |
| Then | Response is 200 with updated sdlc_path | Path updated |

**Assertions:**
- [ ] Status code is 200
- [ ] Response body "sdlc_path" equals the new path
- [ ] Response body "name" is unchanged

---

### TC0026: Update with non-existent path returns 400

**Type:** Integration | **Priority:** High | **Story:** US0002 AC3 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project exists | Project registered |
| When | PUT /api/v1/projects/homelabcmd with {"sdlc_path": "/nonexistent/path"} | Invalid path |
| Then | Response is 400 with PATH_NOT_FOUND | Project unchanged |

**Assertions:**
- [ ] Status code is 400
- [ ] Response body has "error.code" equal to "PATH_NOT_FOUND"
- [ ] Subsequent GET shows original path unchanged

---

### TC0027: Update with only name (no sdlc_path)

**Type:** Integration | **Priority:** Medium | **Story:** US0002 AC3 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project exists with known name and path | Project registered |
| When | PUT /api/v1/projects/homelabcmd with {"name": "New Name"} | Partial update |
| Then | Response is 200; name updated, path unchanged | Partial update succeeds |

**Assertions:**
- [ ] Status code is 200
- [ ] Response body "name" equals "New Name"
- [ ] Response body "sdlc_path" equals original path

---

### TC0028: Update with empty body returns 422

**Type:** Integration | **Priority:** Medium | **Story:** US0002 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project exists | Project registered |
| When | PUT /api/v1/projects/homelabcmd with {} | Empty body |
| Then | Response is 422 VALIDATION_ERROR | At least one field required |

**Assertions:**
- [ ] Status code is 422

---

### TC0029: Delete project returns 204

**Type:** Integration | **Priority:** Critical | **Story:** US0002 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project "HomelabCmd" exists | Project registered |
| When | DELETE /api/v1/projects/homelabcmd | Delete request |
| Then | Response is 204 No Content | Project removed |

**Assertions:**
- [ ] Status code is 204
- [ ] Response body is empty
- [ ] Subsequent GET /api/v1/projects/homelabcmd returns 404

---

### TC0030: Delete cascades to documents table

**Type:** Integration | **Priority:** Critical | **Story:** US0002 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project exists with associated documents in the database | Documents linked to project |
| When | DELETE /api/v1/projects/homelabcmd | Delete request |
| Then | Both the project and all associated documents are removed | Cascade complete |

**Assertions:**
- [ ] Status code is 204
- [ ] No documents remain with the deleted project's project_id
- [ ] FTS5 entries for those documents are also removed

---

### TC0031: Delete project that is currently syncing

**Type:** Integration | **Priority:** Medium | **Story:** US0002 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project exists with sync_status "syncing" | Sync in progress |
| When | DELETE /api/v1/projects/homelabcmd | Delete request |
| Then | Response is 204; delete proceeds regardless of sync state | Delete allowed |

**Assertions:**
- [ ] Status code is 204

---

### TC0032: GET unknown slug returns 404

**Type:** Integration | **Priority:** Critical | **Story:** US0002 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | No project with slug "nonexistent" exists | No such project |
| When | GET /api/v1/projects/nonexistent | Request processed |
| Then | Response is 404 with NOT_FOUND error | Error response |

**Assertions:**
- [ ] Status code is 404
- [ ] Response body has "error.code" equal to "NOT_FOUND"
- [ ] Response body has "error.message" containing "Project not found"

---

### TC0033: PUT unknown slug returns 404

**Type:** Integration | **Priority:** High | **Story:** US0002 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | No project with slug "nonexistent" exists | No such project |
| When | PUT /api/v1/projects/nonexistent with {"name": "Test"} | Request processed |
| Then | Response is 404 with NOT_FOUND error | Error response |

**Assertions:**
- [ ] Status code is 404
- [ ] Response body has "error.code" equal to "NOT_FOUND"

---

### TC0034: DELETE unknown slug returns 404

**Type:** Integration | **Priority:** High | **Story:** US0002 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | No project with slug "nonexistent" exists | No such project |
| When | DELETE /api/v1/projects/nonexistent | Request processed |
| Then | Response is 404 with NOT_FOUND error | Error response |

**Assertions:**
- [ ] Status code is 404
- [ ] Response body has "error.code" equal to "NOT_FOUND"

---

## Fixtures

```yaml
registered_project:
  name: "HomelabCmd"
  sdlc_path: "<tmp_path>/sdlc-studio"

second_project:
  name: "SDLCLens"
  sdlc_path: "<tmp_path>/sdlc-lens"

project_with_documents:
  name: "HomelabCmd"
  sdlc_path: "<tmp_path>/sdlc-studio"
  documents:
    - doc_type: "story"
      doc_id: "US0001"
      title: "Register a New Project"
      status: "Done"
    - doc_type: "epic"
      doc_id: "EP0001"
      title: "Project Management"
      status: "In Progress"

update_name_only:
  name: "HomelabCmd v2"

update_path_only:
  sdlc_path: "<tmp_path>/sdlc-studio-new"

update_invalid_path:
  sdlc_path: "/nonexistent/path"

empty_update: {}
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0019 | List projects returns all registered | Pending | - |
| TC0020 | List projects returns empty array | Pending | - |
| TC0021 | List projects includes document_count | Pending | - |
| TC0022 | Get project by slug | Pending | - |
| TC0023 | Get project includes stats summary | Pending | - |
| TC0024 | Update project name successfully | Pending | - |
| TC0025 | Update project sdlc_path with validation | Pending | - |
| TC0026 | Update with non-existent path returns 400 | Pending | - |
| TC0027 | Update with only name | Pending | - |
| TC0028 | Update with empty body returns 422 | Pending | - |
| TC0029 | Delete project returns 204 | Pending | - |
| TC0030 | Delete cascades to documents | Pending | - |
| TC0031 | Delete project during sync | Pending | - |
| TC0032 | GET unknown slug returns 404 | Pending | - |
| TC0033 | PUT unknown slug returns 404 | Pending | - |
| TC0034 | DELETE unknown slug returns 404 | Pending | - |

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
| 2026-02-17 | Claude | Initial spec from US0002 story plan |
