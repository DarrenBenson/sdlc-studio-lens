# PL0002: Project List and Management API - Implementation Plan

> **Status:** Complete
> **Story:** [US0002: Project List and Management API](../stories/US0002-project-list-and-management-api.md)
> **Epic:** [EP0001: Project Management](../epics/EP0001-project-management.md)
> **Created:** 2026-02-17
> **Language:** Python

## Overview

Implement GET, PUT, and DELETE endpoints for project management. This story adds list, detail, update, and delete operations to the projects API established in US0001. The critical concern is cascading delete, which must remove all associated documents and FTS5 entries when a project is deleted.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | List all projects | GET /api/v1/projects returns 200 with array of project objects |
| AC2 | Get project by slug | GET /api/v1/projects/{slug} returns 200 with full project object |
| AC3 | Update project | PUT /api/v1/projects/{slug} updates name/path, slug unchanged |
| AC4 | Delete with cascade | DELETE /api/v1/projects/{slug} returns 204, removes documents and FTS5 entries |
| AC5 | Not found handling | GET/PUT/DELETE with unknown slug returns 404 NOT_FOUND |

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
| FastAPI | /fastapi/fastapi | Path parameters with type hints, Response(status_code=204), HTTPException(404) |
| SQLAlchemy | /websites/sqlalchemy_en_21 | select(), session.execute(), session.delete(), cascade="all, delete-orphan" |
| Pydantic | - | Optional fields for partial update model, model_config |

### Existing Patterns

Builds on US0001 patterns:
- `backend/src/sdlc_lens/models/project.py` - Project SQLAlchemy model
- `backend/src/sdlc_lens/schemas/project.py` - ProjectCreate, ProjectResponse schemas
- `backend/src/sdlc_lens/services/project.py` - create_project() service function
- `backend/src/sdlc_lens/api/projects.py` - POST endpoint with router
- `backend/tests/conftest.py` - async test fixtures

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** API story with 9 edge cases and clear Given/When/Then acceptance criteria. All endpoints have concrete request/response contracts. Test-first ensures the CRUD contract is validated before implementation and catches cascade delete issues early.

### Test Priority
1. GET /api/v1/projects integration tests (list, empty list)
2. GET /api/v1/projects/{slug} integration tests (found, not found)
3. PUT /api/v1/projects/{slug} integration tests (update name, update path, validation)
4. DELETE /api/v1/projects/{slug} integration tests (cascade, not found)

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Add ProjectUpdate schema (optional name, optional sdlc_path) | `backend/src/sdlc_lens/schemas/project.py` | PL0001 | [ ] |
| 2 | Add list_projects service function | `backend/src/sdlc_lens/services/project.py` | PL0001 | [ ] |
| 3 | Add get_project_by_slug service function | `backend/src/sdlc_lens/services/project.py` | PL0001 | [ ] |
| 4 | Add update_project service function with path re-validation | `backend/src/sdlc_lens/services/project.py` | 1 | [ ] |
| 5 | Add delete_project service function with cascade | `backend/src/sdlc_lens/services/project.py` | PL0001 | [ ] |
| 6 | Add GET /projects endpoint (list) | `backend/src/sdlc_lens/api/projects.py` | 2 | [ ] |
| 7 | Add GET /projects/{slug} endpoint (detail) | `backend/src/sdlc_lens/api/projects.py` | 3 | [ ] |
| 8 | Add PUT /projects/{slug} endpoint (update) | `backend/src/sdlc_lens/api/projects.py` | 4 | [ ] |
| 9 | Add DELETE /projects/{slug} endpoint (delete) | `backend/src/sdlc_lens/api/projects.py` | 5 | [ ] |
| 10 | Write GET list/detail integration tests | `backend/tests/test_project_api.py` | 6, 7 | [ ] |
| 11 | Write PUT update integration tests | `backend/tests/test_project_api.py` | 8 | [ ] |
| 12 | Write DELETE cascade integration tests | `backend/tests/test_project_api.py` | 9 | [ ] |

### Parallel Execution Groups

| Group | Tasks | Prerequisite |
|-------|-------|--------------|
| Schemas | 1 | PL0001 complete |
| Services | 2, 3, 4, 5 | Group: Schemas |
| Endpoints | 6, 7, 8, 9 | Group: Services |
| Tests | 10, 11, 12 | Group: Endpoints |

---

## Implementation Phases

### Phase 1: Schema & Service Layer
**Goal:** Add update schema and all CRUD service functions

- [ ] Add `ProjectUpdate` Pydantic model with optional `name` and `sdlc_path` fields (both Optional[str])
- [ ] Add `list_projects()` - SELECT all projects ordered by created_at
- [ ] Add `get_project_by_slug()` - SELECT by slug, return None if not found
- [ ] Add `update_project()` - fetch by slug, validate new path if changed, update fields, refresh updated_at
- [ ] Add `delete_project()` - fetch by slug, delete with cascade (documents + FTS5 entries)

**Files:**
- `backend/src/sdlc_lens/schemas/project.py` - Add ProjectUpdate
- `backend/src/sdlc_lens/services/project.py` - Add CRUD functions

### Phase 2: API Endpoints
**Goal:** Wire service functions to HTTP endpoints

- [ ] Add `GET /api/v1/projects` - returns list[ProjectResponse]
- [ ] Add `GET /api/v1/projects/{slug}` - returns ProjectResponse or 404
- [ ] Add `PUT /api/v1/projects/{slug}` - accepts ProjectUpdate, returns ProjectResponse or 404/400
- [ ] Add `DELETE /api/v1/projects/{slug}` - returns 204 or 404
- [ ] Ensure consistent error response format: `{"error": {"code": "...", "message": "..."}}`

**Files:**
- `backend/src/sdlc_lens/api/projects.py` - Add GET, PUT, DELETE routes

### Phase 3: Testing
**Goal:** Verify all acceptance criteria and edge cases

- [ ] Write tests for GET /projects (empty list, populated list, field verification)
- [ ] Write tests for GET /projects/{slug} (found, not found)
- [ ] Write tests for PUT /projects/{slug} (update name, update path, both, invalid path, empty body, not found)
- [ ] Write tests for DELETE /projects/{slug} (success, cascade verification, not found)

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | GET /projects returns correct list | `tests/test_project_api.py` | Pending |
| AC2 | GET /projects/{slug} returns project details | `tests/test_project_api.py` | Pending |
| AC3 | PUT /projects/{slug} updates fields, slug unchanged | `tests/test_project_api.py` | Pending |
| AC4 | DELETE cascades to documents and FTS5 | `tests/test_project_api.py` | Pending |
| AC5 | Unknown slug returns 404 for all methods | `tests/test_project_api.py` | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | List projects with zero registered | Return 200 with empty array `[]` | Phase 2 |
| 2 | Update with non-existent new path | Path.resolve().is_dir() check; return 400 PATH_NOT_FOUND | Phase 1 |
| 3 | Update with only name (no sdlc_path) | Optional fields; only update provided fields | Phase 1 |
| 4 | Update with only sdlc_path (no name) | Optional fields; only update provided fields | Phase 1 |
| 5 | Delete project that is currently syncing | Proceed with delete; orphaned sync is acceptable | Phase 1 |
| 6 | PUT with empty body | Pydantic validation; return 422 VALIDATION_ERROR | Phase 2 |
| 7 | Slug with special characters in URL | FastAPI path parameter; 404 if no match | Phase 2 |
| 8 | GET project includes document_count | Count documents with matching project_id | Phase 1 |
| 9 | Concurrent delete requests for same project | First succeeds 204, second returns 404 | Phase 1 |

**Coverage:** 9/9 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| FTS5 entries not cleaned up on cascade delete | Medium | Use SQLAlchemy cascade or explicit DELETE FROM documents_fts WHERE rowid IN (...) |
| Partial update model allows empty body | Low | Add at least-one-field validator on ProjectUpdate |
| Document count query performance | Low | Simple COUNT(*) with index on project_id; acceptable for <1000 docs |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Edge cases handled
- [ ] Code follows Python best practices (type hints, pathlib, specific exceptions)
- [ ] Ruff linting passes
- [ ] API returns correct error format: `{"error": {"code": "...", "message": "..."}}`
- [ ] Cascading delete verified (documents + FTS5 entries removed)

---

## Notes

- Slug is immutable - PUT never changes the slug even if name changes.
- document_count is a computed field from COUNT(*) on documents table, not stored on the project row.
- The documents table and FTS5 virtual table are created in EP0002 migrations but the cascade delete relationship is defined here via SQLAlchemy relationship configuration.
- updated_at must be refreshed on every PUT operation.
