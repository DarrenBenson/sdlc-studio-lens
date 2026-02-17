# PL0012: Document List API with Filtering - Implementation Plan

> **Status:** Done
> **Story:** [US0012: Document List API with Filtering](../stories/US0012-document-list-api.md)
> **Epic:** [EP0003: Document Browsing](../epics/EP0003-document-browsing.md)
> **Created:** 2026-02-17
> **Language:** Python (FastAPI)

## Overview

Add a paginated, filterable document list endpoint at `GET /api/v1/projects/{slug}/documents`. Supports filtering by document type and status, sorting by multiple fields, and cursor-based pagination with total count.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Default pagination | Returns 50 items per page with total, page, per_page, pages |
| AC2 | Type filter | `?type=epic` returns only epics |
| AC3 | Status filter | `?status=In+Progress` returns only matching status |
| AC4 | Sort by field and order | `?sort=title&order=asc` sorts correctly |
| AC5 | Combined filters | Multiple filters work together |

---

## Technical Context

### Language & Framework
- **Primary Language:** Python 3.13
- **Framework:** FastAPI + SQLAlchemy async
- **Test Framework:** pytest + httpx AsyncClient

### Existing Patterns
- Project routes in `api/routes/projects.py` using `APIRouter`
- Pydantic schemas in `api/schemas/projects.py`
- Service functions in `services/project.py` with custom exceptions
- Error responses: `{"error": {"code": "...", "message": "..."}}`

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** Clear API contract with defined query parameters, response shape, and edge cases. Perfect for test-first.

### Test Priority
1. Default pagination returns correct structure
2. Type and status filters narrow results
3. Sorting works correctly
4. Edge cases (404, empty, invalid params)

---

## Implementation Phases

### Phase 1: Pydantic Schemas
**Goal:** Define request/response models for document list

- [ ] Create `DocumentListItem` schema (doc_id, type, title, status, owner, priority, story_points, updated_at)
- [ ] Create `PaginatedDocuments` schema (items, total, page, per_page, pages)

**Files:** `backend/src/sdlc_lens/api/schemas/documents.py`

### Phase 2: Service Layer
**Goal:** Query function with filtering, sorting, pagination

- [ ] Create `list_documents()` service function
- [ ] Support type, status filters via WHERE clauses
- [ ] Support sort field + order direction
- [ ] Implement LIMIT/OFFSET pagination with COUNT

**Files:** `backend/src/sdlc_lens/services/documents.py`

### Phase 3: Route Handler
**Goal:** Wire up GET endpoint with query parameters

- [ ] Add `GET /projects/{slug}/documents` route
- [ ] Parse query params: type, status, sort, order, page, per_page
- [ ] Validate sort field against allowlist
- [ ] Cap per_page at 100, default 50
- [ ] 404 for unknown project slug

**Files:** `backend/src/sdlc_lens/api/routes/projects.py`

### Phase 4: Testing & Validation
**Goal:** Verify all acceptance criteria

| AC | Verification Method | Status |
|----|---------------------|--------|
| AC1 | Test default pagination structure | Pending |
| AC2 | Test type filter | Pending |
| AC3 | Test status filter | Pending |
| AC4 | Test sorting | Pending |
| AC5 | Test combined filters | Pending |

---

## Edge Case Handling

| # | Edge Case | Handling Strategy | Phase |
|---|-----------|-------------------|-------|
| 1 | Unknown project slug | 404 NOT_FOUND | Phase 3 |
| 2 | Zero documents | 200 with empty items, total: 0 | Phase 2 |
| 3 | per_page > 100 | Cap at 100 | Phase 3 |
| 4 | per_page <= 0 | 422 VALIDATION_ERROR | Phase 3 |
| 5 | Page beyond total | 200 with empty items | Phase 2 |
| 6 | Invalid sort field | 422 VALIDATION_ERROR | Phase 3 |
| 7 | Status with spaces | URL-encoded, works naturally | Phase 3 |

**Coverage:** 7/7 edge cases handled

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit/integration tests written and passing
- [ ] Edge cases handled
- [ ] Code follows existing patterns
- [ ] No linting errors
