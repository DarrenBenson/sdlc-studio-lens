# US0012: Document List API with Filtering

> **Status:** Done
> **Epic:** [EP0003: Document Browsing](../epics/EP0003-document-browsing.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** to retrieve a filtered, sorted, paginated list of documents for a project
**So that** I can browse specific document types or statuses via the API

## Context

### Persona Reference
**Darren** - Browses documents to review project artefacts, filters to find specific stories or epics.
[Full persona details](../personas.md#darren)

### Background
The document list API powers the main browsing interface. It supports filtering by document type and status, sorting by multiple fields, and pagination. Results exclude full document content to keep responses lightweight; the detail endpoint (US0013) returns content.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Performance | Document list load < 500ms | Indexed queries, no full content in list |
| TRD | API | GET /projects/{slug}/documents with query params | type, status, sort, order, page, per_page |
| TRD | API | 50 per page default, 100 max | Pagination enforced |

---

## Acceptance Criteria

### AC1: List documents with default pagination
- **Given** project "homelabcmd" has 120 synced documents
- **When** I GET `/api/v1/projects/homelabcmd/documents`
- **Then** I receive 200 with `items` array (50 documents), `total: 120`, `page: 1`, `per_page: 50`, `pages: 3`

### AC2: Filter by document type
- **Given** project "homelabcmd" has 18 epics and 90 stories
- **When** I GET `/api/v1/projects/homelabcmd/documents?type=epic`
- **Then** I receive only the 18 epic documents with `total: 18`

### AC3: Filter by status
- **Given** project "homelabcmd" has 100 Done stories and 20 In Progress stories
- **When** I GET `/api/v1/projects/homelabcmd/documents?status=In+Progress`
- **Then** I receive only the 20 In Progress documents

### AC4: Sort by field and order
- **Given** documents exist with various titles
- **When** I GET `/api/v1/projects/homelabcmd/documents?sort=title&order=asc`
- **Then** results are sorted alphabetically by title in ascending order

### AC5: Combined filters
- **Given** project has stories with various statuses
- **When** I GET `/api/v1/projects/homelabcmd/documents?type=story&status=Done&sort=updated_at&order=desc`
- **Then** I receive only Done stories, sorted by most recently updated first

---

## Scope

### In Scope
- GET /api/v1/projects/{slug}/documents endpoint
- Query parameters: type, status, sort, order, page, per_page
- Pydantic response model with items, total, page, per_page, pages
- Document list items: doc_id, type, title, status, owner, priority, story_points, updated_at
- Default sort: updated_at desc
- page_size validation: min 1, max 100, default 50
- 404 for unknown project slug

### Out of Scope
- Full document content in list response (US0013 for single document)
- Search functionality (US0021, EP0005)
- Cross-project document listing

---

## Technical Notes

### API Contract

**Request:**
```
GET /api/v1/projects/{slug}/documents?type=story&status=Done&sort=title&order=asc&page=1&per_page=50
```

**Response (200):**
```json
{
  "items": [
    {
      "doc_id": "US0001",
      "type": "story",
      "title": "Register a New Project",
      "status": "Done",
      "owner": "Darren",
      "priority": "P0",
      "story_points": 5,
      "updated_at": "2026-02-17T10:30:00Z"
    }
  ],
  "total": 120,
  "page": 1,
  "per_page": 50,
  "pages": 3
}
```

### Data Requirements
- Query documents table with WHERE clauses for type, status
- ORDER BY for sort field + order direction
- LIMIT/OFFSET for pagination
- COUNT for total
- Indexed columns: doc_type, status, project_id for query performance

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Unknown project slug | 404 NOT_FOUND |
| Project with zero documents | 200 with empty items array, total: 0 |
| Invalid type filter value | Ignored; return all types (or 422 if strict validation preferred) |
| per_page exceeds 100 | Capped at 100 |
| per_page = 0 or negative | 422 VALIDATION_ERROR |
| Page number beyond total pages | 200 with empty items array |
| Sort by invalid field | 422 VALIDATION_ERROR; valid fields: title, type, status, updated_at |
| Multiple type values (type=epic&type=story) | Accept as array filter; return both types |
| Status with spaces (e.g., "In Progress") | URL-encoded: status=In+Progress or status=In%20Progress |

---

## Test Scenarios

- [ ] List documents returns paginated response
- [ ] Default pagination is 50 per page
- [ ] Type filter returns only matching type
- [ ] Status filter returns only matching status
- [ ] Combined type + status filter works
- [ ] Sort by title ascending
- [ ] Sort by updated_at descending (default)
- [ ] Pagination page 2 returns correct offset
- [ ] Total count correct with filters applied
- [ ] 404 for unknown project slug
- [ ] Empty project returns empty items
- [ ] per_page capped at 100

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0001](US0001-register-new-project.md) | Schema | Projects table | Draft |
| [US0007](US0007-filesystem-sync-service.md) | Schema | Documents table with data | Draft |

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
| 2026-02-17 | Claude | Initial story creation from EP0003 |
