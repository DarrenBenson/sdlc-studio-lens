# PL0034: Relationships API - Implementation Plan

> **Status:** Complete
> **Story:** [US0034: Relationships API](../stories/US0034-relationships-api.md)
> **Epic:** [EP0008: Document Relationship Navigation](../epics/EP0008-document-relationship-navigation.md)
> **Created:** 2026-02-18
> **Language:** Python 3.12

## Overview

Add a `/related` endpoint that returns a document's parent chain and children. Update existing document list and detail endpoints to include `epic` and `story` fields. Service layer resolves relationships by walking the `epic`/`story` columns.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Related endpoint exists | GET /projects/{slug}/documents/{type}/{docId}/related returns 200 |
| AC2 | Parent chain correct | Parents ordered nearest-first (story, then epic) |
| AC3 | Children correct | Epic returns its stories; story returns its plans/test-specs/bugs |
| AC4 | Leaf docs no children | Plans/test-specs have empty children array |
| AC5 | Top-level no parents | Epics/PRD have empty parents array |
| AC6 | 404 for missing doc | Standard error format |
| AC7 | DocumentDetail story field | Detail response includes story field |
| AC8 | List includes epic/story | List items include epic and story fields |

---

## Technical Context

### Language & Framework
- **Primary Language:** Python 3.12
- **Framework:** FastAPI + SQLAlchemy 2.0 async
- **Test Framework:** pytest + pytest-asyncio

### Existing Patterns
- Document service in `services/documents.py` with `get_document()` and `list_documents()`
- Route handlers in `api/routes/projects.py` build Pydantic models from Document ORM objects
- Schemas in `api/schemas/documents.py` use `BaseModel` with `from_attributes`

---

## Recommended Approach

**Strategy:** Test-After
**Rationale:** Clear endpoint contract defined in story. Service functions are straightforward DB queries. Writing code then validating with tests is efficient.

---

## Implementation Phases

### Phase 1: Pydantic Schemas
**Goal:** Add response schemas and update existing schemas

- [x] Add `epic` and `story` fields to `DocumentListItem`
- [x] Add `story` field to `DocumentDetail`
- [x] Add `RelatedDocumentItem` schema
- [x] Add `DocumentRelationships` schema
- [x] Remove unused imports (`json`, `Field`, `field_validator`)

**Files:**
- `api/schemas/documents.py`

### Phase 2: Service Layer
**Goal:** Add relationship resolution functions

- [x] Add `_extract_doc_prefix()` to get clean prefix from doc_id
- [x] Add `_find_doc_by_clean_id()` to find doc by clean ID prefix
- [x] Add `_get_parent_chain()` to walk up hierarchy
- [x] Add `_get_children()` to find direct children
- [x] Add `get_related_documents()` as public entry point
- [x] Epic children filtered with `story IS NULL` for direct children only

**Files:**
- `services/documents.py`

### Phase 3: Route Handlers
**Goal:** Wire up endpoint and fix existing handlers

- [x] Update `list_project_documents` to pass `epic`/`story` to `DocumentListItem`
- [x] Update `get_document_detail` to pass `story` to `DocumentDetail`
- [x] Add `get_document_related` endpoint at `/{slug}/documents/{doc_type}/{doc_id}/related`
- [x] Ensure `/related` route registered BEFORE `{doc_id:path}` catch-all

**Files:**
- `api/routes/projects.py`

### Phase 4: Testing
**Goal:** Verify all acceptance criteria

- [x] 18 integration tests (TC0358-TC0371)
- [x] Full hierarchy fixture: epic -> stories -> plans/test-specs
- [x] All 361 backend tests pass (343 existing + 18 new)

**Files:**
- `tests/test_api_relationships.py`

---

## Edge Case Handling

| # | Edge Case | Handling Strategy | Phase |
|---|-----------|-------------------|-------|
| 1 | Story references missing epic | Parent chain omits missing parent | Phase 2 |
| 2 | Plan references missing story | Parent chain empty, no error | Phase 2 |
| 3 | Epic with no child stories | Empty children array | Phase 2 |
| 4 | PRD/TRD/TSD document | Both arrays empty | Phase 2 |
| 5 | Epic children include grandchildren | Filter with `story IS NULL` | Phase 2 |
| 6 | Non-standard doc_id without prefix | `_extract_doc_prefix` returns None, empty children | Phase 2 |

**Coverage:** 6/6 edge cases handled

---

## Definition of Done

- [x] All acceptance criteria implemented
- [x] Integration tests written and passing
- [x] Edge cases handled
- [x] No new linting errors
- [x] Existing tests still pass (361 total)
