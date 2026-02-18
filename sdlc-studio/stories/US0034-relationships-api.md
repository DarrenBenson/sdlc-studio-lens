# US0034: Relationships API

> **Status:** Done
> **Epic:** [EP0008: Document Relationship Navigation](../epics/EP0008-document-relationship-navigation.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-18

## User Story

**As a** SDLC Developer (Darren)
**I want** an API endpoint that returns a document's parent chain and child documents
**So that** the frontend can render navigation breadcrumbs and related document panels

## Context

### Persona Reference
**Darren** - Navigates between related documents and needs structured relationship data to build navigation UI.
[Full persona details](../personas.md#darren)

### Background
With US0033 storing clean `epic` and `story` IDs on each document, the backend can now resolve document relationships. Given any document, the API needs to:

1. **Parent chain** - Walk up the hierarchy to build a breadcrumb path (e.g., Story → Epic for a plan)
2. **Children** - Query for documents whose `epic` or `story` column matches this document's ID

The hierarchy is: PRD/TRD/TSD (top-level) → Epics → Stories → Plans/Test Specs/Bugs.

The existing document detail endpoint (`GET /projects/{slug}/documents/{type}/{docId}`) returns the `epic` and `story` fields but doesn't resolve them to actual document records. A new endpoint returns the full relationship context.

---

## Inherited Constraints

> See Epic for full constraint chain. Key constraints for this story:

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | KPI | API response < 500ms | Use indexed column lookups, not full table scans |
| TRD | Tech Stack | Pydantic v2 | Response schemas use BaseModel |
| TRD | Architecture | Read-only access | Relationships are inferred, not stored as a separate table |

---

## Acceptance Criteria

### AC1: Related documents endpoint exists
- **Given** a synced project with documents
- **When** I call `GET /api/v1/projects/{slug}/documents/{type}/{docId}/related`
- **Then** the API returns HTTP 200 with the document's parent chain and children

### AC2: Parent chain is correct
- **Given** a plan document with `story=US0028` and the story has `epic=EP0007`
- **When** I request the plan's related documents
- **Then** the `parents` array contains the story (US0028) and the epic (EP0007) in order from nearest to furthest ancestor

### AC3: Children are correct
- **Given** an epic EP0007 with three child stories
- **When** I request the epic's related documents
- **Then** the `children` array contains all three stories, each with doc_id, type, title, and status

### AC4: Leaf documents have no children
- **Given** a plan document (leaf node in the hierarchy)
- **When** I request its related documents
- **Then** the `children` array is empty

### AC5: Top-level documents have no parents
- **Given** a PRD or epic document
- **When** I request its related documents
- **Then** the `parents` array is empty (epics are top-level under the PRD umbrella, but the PRD isn't a direct column reference)

### AC6: Document not found returns 404
- **Given** a non-existent document type/ID combination
- **When** I request its related documents
- **Then** the API returns HTTP 404 with the standard error format

### AC7: DocumentDetail response includes story field
- **Given** a document with a `story` value
- **When** I call `GET /projects/{slug}/documents/{type}/{docId}`
- **Then** the response includes the `story` field

### AC8: Document list includes epic and story fields
- **Given** documents with `epic` and `story` values
- **When** I call `GET /projects/{slug}/documents`
- **Then** each item in the response includes `epic` and `story` fields

---

## Scope

### In Scope
- New endpoint: `GET /projects/{slug}/documents/{type}/{docId}/related`
- Pydantic response schema for related documents
- Parent chain resolution (walk up via `story` → `epic` columns)
- Children query (find documents where `epic` or `story` matches this doc's ID)
- Add `story` field to `DocumentDetail` schema
- Add `epic` and `story` fields to `DocumentListItem` schema
- 404 handling for missing document

### Out of Scope
- Creating or editing relationships (read-only)
- Cross-project relationships
- Relationship validation (dangling references)
- Caching of relationship data
- Grandchildren (only direct children returned; tree built client-side)

---

## Technical Notes

### Response Schema
```python
class RelatedDocumentItem(BaseModel):
    doc_id: str
    type: str
    title: str
    status: str | None

class DocumentRelationships(BaseModel):
    doc_id: str
    type: str
    title: str
    parents: list[RelatedDocumentItem]   # nearest ancestor first
    children: list[RelatedDocumentItem]  # sorted by type then doc_id
```

### Parent Chain Resolution
```python
async def get_parent_chain(session, project_id, doc) -> list[RelatedDocumentItem]:
    """Walk up the hierarchy using epic/story columns."""
    parents = []

    # If doc has a story reference, find the story
    if doc.story:
        story_doc = await find_doc_by_id(session, project_id, doc.story)
        if story_doc:
            parents.append(story_doc)
            # Story's epic is the grandparent
            if story_doc.epic:
                epic_doc = await find_doc_by_id(session, project_id, story_doc.epic)
                if epic_doc:
                    parents.append(epic_doc)
    elif doc.epic:
        # Doc directly references an epic (it's a story)
        epic_doc = await find_doc_by_id(session, project_id, doc.epic)
        if epic_doc:
            parents.append(epic_doc)

    return parents
```

### Children Query
```python
async def get_children(session, project_id, doc) -> list[RelatedDocumentItem]:
    """Find documents that reference this doc as their parent."""
    if doc.doc_type == "epic":
        # Children are stories with epic == this doc's doc_id
        query = select(Document).where(
            Document.project_id == project_id,
            Document.epic == doc.doc_id,
        )
    elif doc.doc_type == "story":
        # Children are plans/test-specs/bugs with story == this doc's doc_id
        query = select(Document).where(
            Document.project_id == project_id,
            Document.story == doc.doc_id,
        )
    else:
        return []

    result = await session.execute(query)
    return [to_related_item(d) for d in result.scalars().all()]
```

### API Contracts

**Request:** `GET /api/v1/projects/{slug}/documents/{type}/{docId}/related`

**Response (200):**
```json
{
  "doc_id": "PL0028",
  "type": "plan",
  "title": "Database Schema for GitHub Source",
  "parents": [
    {"doc_id": "US0028", "type": "story", "title": "Database Schema", "status": "Done"},
    {"doc_id": "EP0007", "type": "epic", "title": "Git Repository Sync", "status": "Done"}
  ],
  "children": []
}
```

**Response (404):**
```json
{"error": {"code": "NOT_FOUND", "message": "Document not found: plan/PL9999"}}
```

### Data Requirements
Depends on US0033 having populated clean `epic` and `story` column values.

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Document has `story` but story doc doesn't exist in DB | Parent chain omits the missing parent; no error |
| Document has `epic` but epic doc doesn't exist in DB | Parent chain omits the missing parent; no error |
| Epic with no child stories | `children` array is empty |
| Story with no child plans/specs/bugs | `children` array is empty |
| PRD/TRD/TSD document | `parents` and `children` both empty |
| Bug document with story reference | Parent chain includes the story and its epic |
| Project has no synced documents | 404 for the document itself |
| Circular reference (should not occur) | Depth limit of 3 levels prevents infinite loops |

---

## Test Scenarios

- [ ] GET /related returns 200 with correct parents and children
- [ ] Story's parents include its epic
- [ ] Plan's parents include its story and grandparent epic
- [ ] Epic's children include its stories
- [ ] Story's children include its plans, test-specs, and bugs
- [ ] Leaf document (plan) has empty children
- [ ] Top-level document (epic) has empty parents
- [ ] Missing parent reference returns partial chain (no error)
- [ ] Non-existent document returns 404
- [ ] Non-existent project returns 404
- [ ] DocumentDetail response includes story field
- [ ] DocumentListItem response includes epic and story fields
- [ ] Children sorted by type then doc_id

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0033](US0033-relationship-data-extraction.md) | Data | Clean epic/story columns populated on documents | Not Started |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

---

## Estimation

**Story Points:** 5
**Complexity:** Medium

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-18 | Claude | Initial story creation from EP0008 |
