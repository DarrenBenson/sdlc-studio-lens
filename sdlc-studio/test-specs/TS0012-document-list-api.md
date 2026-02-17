# TS0012: Document List API with Filtering

> **Status:** Done
> **Epic:** [EP0003: Document Browsing](../epics/EP0003-document-browsing.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0012 - Document List API with Filtering. Covers the paginated document list endpoint including filtering, sorting, pagination, and error handling.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0012](../stories/US0012-document-list-api.md) | Document List API with Filtering | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0012 | AC1 | Default pagination | TC0145, TC0146 | Covered |
| US0012 | AC2 | Type filter | TC0147 | Covered |
| US0012 | AC3 | Status filter | TC0148 | Covered |
| US0012 | AC4 | Sort by field and order | TC0150, TC0151 | Covered |
| US0012 | AC5 | Combined filters | TC0149 | Covered |

**Coverage:** 5/5 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | No | Logic is thin service + route wiring |
| Integration | Yes | API endpoint with DB queries |
| E2E | No | Covered by frontend tests later |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | pytest, httpx, aiosqlite |
| External Services | None (in-memory SQLite) |
| Test Data | Seed documents via direct DB insert |

---

## Test Cases

### TC0145: List documents returns paginated response

**Type:** Integration | **Priority:** Critical | **Story:** US0012 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with 3 synced documents | Documents exist |
| When | GET /api/v1/projects/{slug}/documents | 200 response |
| Then | Response has items array, total, page, per_page, pages | Correct structure |

**Assertions:**
- [ ] Status code is 200
- [ ] Response has `items` array
- [ ] Response has `total`, `page`, `per_page`, `pages` fields
- [ ] `total` equals 3
- [ ] `page` equals 1
- [ ] `per_page` equals 50

---

### TC0146: Default per_page is 50 and pages calculated correctly

**Type:** Integration | **Priority:** High | **Story:** US0012 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with documents | Documents exist |
| When | GET without per_page param | Default applied |
| Then | per_page is 50, pages calculated from total | Correct pagination |

---

### TC0147: Type filter returns only matching type

**Type:** Integration | **Priority:** Critical | **Story:** US0012 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with epics and stories | Mixed types |
| When | GET ?type=epic | Filtered request |
| Then | Only epic documents returned, total reflects filter | Correct filtering |

---

### TC0148: Status filter returns only matching status

**Type:** Integration | **Priority:** Critical | **Story:** US0012 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with Done and Draft documents | Mixed statuses |
| When | GET ?status=Done | Filtered request |
| Then | Only Done documents returned | Correct filtering |

---

### TC0149: Combined type + status filter

**Type:** Integration | **Priority:** High | **Story:** US0012 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with stories (Done and Draft) and epics | Mixed |
| When | GET ?type=story&status=Done | Combined filter |
| Then | Only Done stories returned | Both filters applied |

---

### TC0150: Sort by title ascending

**Type:** Integration | **Priority:** High | **Story:** US0012 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Documents with titles A, B, C | Unsorted |
| When | GET ?sort=title&order=asc | Sort request |
| Then | Items ordered A, B, C | Ascending sort |

---

### TC0151: Default sort is synced_at descending

**Type:** Integration | **Priority:** Medium | **Story:** US0012 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Documents synced at different times | Multiple docs |
| When | GET without sort params | Default sort |
| Then | Most recently synced first | Descending by synced_at |

---

### TC0152: Pagination page 2 returns correct offset

**Type:** Integration | **Priority:** High | **Story:** US0012 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with 5 documents | Multiple docs |
| When | GET ?per_page=2&page=2 | Page 2 request |
| Then | Items 3-4 returned, page=2, total=5 | Correct offset |

---

### TC0153: Total count correct with filters applied

**Type:** Integration | **Priority:** Medium | **Story:** US0012 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | 5 stories and 3 epics | 8 total docs |
| When | GET ?type=story | Filtered request |
| Then | total=5, items has 5 items | Filtered count |

---

### TC0154: 404 for unknown project slug

**Type:** Integration | **Priority:** Critical | **Story:** US0012 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | No project with slug "nonexistent" | No project |
| When | GET /api/v1/projects/nonexistent/documents | Request |
| Then | 404 with error code NOT_FOUND | Error response |

---

### TC0155: Empty project returns empty items

**Type:** Integration | **Priority:** Medium | **Story:** US0012 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with zero documents | Empty project |
| When | GET /api/v1/projects/{slug}/documents | Request |
| Then | 200 with items=[], total=0 | Empty response |

---

### TC0156: per_page capped at 100

**Type:** Integration | **Priority:** Medium | **Story:** US0012 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with documents | Documents exist |
| When | GET ?per_page=200 | Over limit |
| Then | per_page capped at 100 in response | Capped |

---

### TC0157: per_page zero or negative returns 422

**Type:** Integration | **Priority:** Medium | **Story:** US0012 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Any project | Exists |
| When | GET ?per_page=0 | Invalid value |
| Then | 422 validation error | Rejected |

---

### TC0158: Invalid sort field returns 422

**Type:** Integration | **Priority:** Medium | **Story:** US0012 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Any project | Exists |
| When | GET ?sort=invalid_field | Bad sort |
| Then | 422 validation error | Rejected |

---

## Fixtures

```yaml
seed_documents:
  - project: "testproject"
    documents:
      - doc_type: "epic", doc_id: "EP0001-test", title: "Alpha Epic", status: "Done"
      - doc_type: "epic", doc_id: "EP0002-test", title: "Beta Epic", status: "Draft"
      - doc_type: "story", doc_id: "US0001-test", title: "Charlie Story", status: "Done"
      - doc_type: "story", doc_id: "US0002-test", title: "Delta Story", status: "Draft"
      - doc_type: "story", doc_id: "US0003-test", title: "Echo Story", status: "Done"
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0145 | Paginated response structure | Pass | `test_api_documents.py` |
| TC0146 | Default per_page 50 | Pass | `test_api_documents.py` |
| TC0147 | Type filter | Pass | `test_api_documents.py` |
| TC0148 | Status filter | Pass | `test_api_documents.py` |
| TC0149 | Combined filters | Pass | `test_api_documents.py` |
| TC0150 | Sort title ascending | Pass | `test_api_documents.py` |
| TC0151 | Default sort synced_at desc | Pass | `test_api_documents.py` |
| TC0152 | Pagination page 2 | Pass | `test_api_documents.py` |
| TC0153 | Total count with filters | Pass | `test_api_documents.py` |
| TC0154 | 404 unknown slug | Pass | `test_api_documents.py` |
| TC0155 | Empty project | Pass | `test_api_documents.py` |
| TC0156 | per_page capped at 100 | Pass | `test_api_documents.py` |
| TC0157 | per_page zero/negative 422 | Pass | `test_api_documents.py` |
| TC0158 | Invalid sort field 422 | Pass | `test_api_documents.py` |

---

## Traceability

| Artefact | Reference |
|----------|-----------|
| PRD | [sdlc-studio/prd.md](../prd.md) |
| Epic | [EP0003](../epics/EP0003-document-browsing.md) |
| TSD | [sdlc-studio/tsd.md](../tsd.md) |

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec from US0012 story |
