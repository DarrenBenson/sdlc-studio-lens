# US0013: Document Detail API

> **Status:** Done
> **Epic:** [EP0003: Document Browsing](../epics/EP0003-document-browsing.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** to retrieve a single document with its full content and metadata
**So that** I can view it rendered in the dashboard

## Context

### Persona Reference
**Darren** - Views rendered documents in a clean interface without opening a text editor.
[Full persona details](../personas.md#darren)

### Background
The document detail endpoint returns the full document including raw markdown content, extracted frontmatter metadata, and sync information. The frontend uses this to render the markdown viewer with a metadata sidebar.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Performance | API response p95 < 500ms | Single document retrieval must be fast |
| TRD | API | GET /projects/{slug}/documents/{type}/{doc_id} | Type + doc_id in URL path |
| TRD | Data | Content stored in SQLite | No filesystem read at view time |

---

## Acceptance Criteria

### AC1: Retrieve document with full content
- **Given** document US0001 exists for project "homelabcmd"
- **When** I GET `/api/v1/projects/homelabcmd/documents/story/US0001`
- **Then** I receive 200 with doc_id, type, title, status, owner, priority, story_points, epic, metadata (JSON), content (full markdown), file_path, file_hash, and synced_at

### AC2: 404 for unknown document
- **Given** no document with type "story" and doc_id "US9999" exists for project "homelabcmd"
- **When** I GET `/api/v1/projects/homelabcmd/documents/story/US9999`
- **Then** I receive 404 with error code "NOT_FOUND"

### AC3: 404 for unknown project
- **Given** no project with slug "nonexistent" exists
- **When** I GET `/api/v1/projects/nonexistent/documents/story/US0001`
- **Then** I receive 404 with error code "NOT_FOUND"

### AC4: Metadata includes additional frontmatter
- **Given** a document with frontmatter fields beyond the standard set (e.g., "Sprint: Sprint 3")
- **When** I retrieve the document
- **Then** the metadata JSON field includes `{"sprint": "Sprint 3"}`

---

## Scope

### In Scope
- GET /api/v1/projects/{slug}/documents/{type}/{doc_id} endpoint
- Full Pydantic response model with all fields
- Raw markdown content returned for frontend rendering
- metadata JSON field with non-standard frontmatter
- file_path and file_hash for audit/debug
- synced_at timestamp

### Out of Scope
- Server-side markdown rendering (frontend handles this)
- Document relationship resolution (linked epics/stories)
- Document edit/update (read-only)

---

## Technical Notes

### API Contract

**Response (200):**
```json
{
  "doc_id": "US0001",
  "type": "story",
  "title": "Register a New Project",
  "status": "Done",
  "owner": "Darren",
  "priority": "P0",
  "story_points": 5,
  "epic": "EP0001",
  "metadata": {"sprint": "Sprint 1", "created": "2026-02-17"},
  "content": "# US0001: Register a New Project\n\n> **Status:** Done\n...",
  "file_path": "stories/US0001-register-new-project.md",
  "file_hash": "a1b2c3d4e5f6...",
  "synced_at": "2026-02-17T10:30:00Z"
}
```

### Data Requirements
- Query: SELECT * FROM documents WHERE project_id = ? AND doc_type = ? AND doc_id = ?
- Lookup by project slug requires JOIN with projects table (or subquery)

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Document type mismatch (EP0001 at path /story/EP0001) | 404 NOT_FOUND; type in URL must match doc_type |
| Document with null optional fields (no owner, no priority) | Fields returned as null in JSON |
| Document with very large content (>500KB) | Returned normally; no size limit |
| Document with empty content | content field returns empty string |
| Concurrent read during sync | Returns current DB state (may be stale) |
| doc_id with special characters | URL-encoded; matched exactly |
| Singleton documents (prd, trd, tsd) | Retrieved at /documents/prd/prd |
| metadata field is empty (no extra frontmatter) | Returns empty object `{}` |

---

## Test Scenarios

- [ ] GET document returns full content and metadata
- [ ] GET document returns all standard fields
- [ ] metadata JSON contains non-standard frontmatter
- [ ] 404 for unknown doc_id
- [ ] 404 for unknown project slug
- [ ] 404 for type mismatch
- [ ] Null fields returned correctly (owner, priority)
- [ ] file_path and file_hash present in response
- [ ] synced_at timestamp present
- [ ] Singleton documents (prd) retrievable

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0012](US0012-document-list-api.md) | API | Shares project lookup logic | Draft |
| [US0007](US0007-filesystem-sync-service.md) | Schema | Documents table populated | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

---

## Estimation

**Story Points:** {{TBD}}
**Complexity:** Low

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial story creation from EP0003 |
