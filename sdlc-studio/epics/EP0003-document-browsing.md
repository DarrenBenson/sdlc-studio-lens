# EP0003: Document Browsing

> **Status:** Done
> **Owner:** Darren
> **Created:** 2026-02-17
> **Target Release:** Phase 2 (Browsing & Dashboard)
> **Story Points:** 20

## Summary

Browse, filter, sort, and view synced SDLC documents. This epic delivers the document list with type and status filtering, pagination, sorting, and a rendered markdown viewer with a frontmatter metadata sidebar. It transforms raw document data into a navigable, readable interface.

## Inherited Constraints

Constraints that flow from PRD and TRD to this Epic.

### From PRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Performance | Document list load < 500ms | Efficient queries with indexed filters |
| Performance | API response p95 < 500ms | Pagination prevents large result sets |
| Design | Dark theme with lime green accents ([Brand Guide](../brand-guide.md)) | All components follow brand guide |
| Business Logic | Read-only dashboard | No edit/create functionality in document views |

### From TRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Architecture | React SPA with client-side routing | React Router for document navigation |
| Tech Stack | react-markdown + rehype-highlight | Markdown rendering with syntax highlighting |
| API | GET /projects/{slug}/documents with query params | Type, status, sort, order, page, per_page |
| API | GET /projects/{slug}/documents/{type}/{doc_id} | Single document with full content |

> **Note:** Inherited constraints MUST propagate to child Stories. Check Story templates include these constraints.

## Business Context

### Problem Statement

After sync populates the database with parsed documents, users need to browse them. Navigating the filesystem requires knowing directory structure and filenames. A filterable, paginated document list with rendered views replaces manual file navigation.

**PRD Reference:** [§5 Feature Inventory](../prd.md#5-feature-inventory) (FR4, FR5)

### Value Proposition

Type and status filters let developers find specific artefacts in seconds. Rendered markdown with syntax highlighting provides a clean reading experience. The frontmatter sidebar surfaces metadata without scrolling through document content.

### Success Metrics

| Metric | Current State | Target | Measurement Method |
|--------|---------------|--------|-------------------|
| Time to find a specific document | Minutes (filesystem grep) | < 15 seconds (filter + click) | User observation |
| Document list response time | N/A | < 500ms | API timing |
| Markdown rendering quality | N/A | Correct for all sdlc-studio formats | Visual verification |

## Scope

### In Scope

- Document list page showing title, type badge, status badge, owner, last modified
- Type filter (epic, story, bug, plan, test-spec, prd, trd, tsd, other)
- Status filter (Draft, In Progress, Done, Blocked, Not Started, etc.)
- Combined type + status filtering
- Sort by title, type, status, or updated_at
- Sort order (ascending, descending)
- Pagination (50 per page default, configurable up to 100)
- Document view page with rendered markdown body
- Frontmatter metadata sidebar panel
- Document type badge and status badge on view page
- Syntax highlighting for code blocks
- Table rendering
- File path and sync timestamp display
- Navigation from document list to document view

### Out of Scope

- Document editing or creation (read-only)
- Document relationship navigation (epic → stories links) - P2 enhancement
- Markdown table of contents generation
- Document diff or version comparison
- Print-friendly layout

### Affected User Personas

- **SDLC Developer (Darren):** Browses documents to review project artefacts, filters to find specific stories or epics

## Acceptance Criteria (Epic Level)

- [ ] Document list displays all synced documents with type badge, status badge, and title
- [ ] Type filter narrows list to selected document type
- [ ] Status filter narrows list to selected status
- [ ] Combined filters work together (type AND status)
- [ ] Sort controls change document order by any supported field
- [ ] Pagination navigates between pages with correct total count
- [ ] Clicking a document navigates to rendered markdown view
- [ ] Markdown renders correctly with headings, lists, tables, code blocks
- [ ] Code blocks have syntax highlighting
- [ ] Frontmatter sidebar shows extracted metadata fields
- [ ] Status badge reflects correct colour per status
- [ ] API response time < 500ms for filtered document list

## Dependencies

### Blocked By

| Dependency | Type | Status | Owner | Notes |
|------------|------|--------|-------|-------|
| EP0002: Document Sync & Parsing | Epic | Draft | Darren | Need parsed documents in database |

### Blocking

| Item | Type | Impact |
|------|------|--------|
| None | - | - |

## Risks & Assumptions

### Assumptions

- react-markdown handles all sdlc-studio markdown patterns correctly
- rehype-highlight supports languages used in sdlc-studio code blocks
- 50 documents per page is a reasonable default
- Document metadata is consistent enough for filtering

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Complex markdown (nested tables, HTML) renders poorly | Medium | Medium | Test with real sdlc-studio documents; add rehype plugins as needed |
| Large document content slows rendering | Low | Low | Lazy load document content on view page |
| Filter combinations produce confusing empty states | Low | Low | Show clear "no documents match" message with filter summary |

## Technical Considerations

### Architecture Impact

- Creates document list and document view pages in React
- Establishes filter/sort/pagination query parameter pattern
- Introduces react-markdown and rehype-highlight dependencies
- Defines StatusBadge and DocumentCard reusable components

### Integration Points

- DocumentList page → GET /api/v1/projects/{slug}/documents?type=&status=&sort=&order=&page=&per_page=
- DocumentView page → GET /api/v1/projects/{slug}/documents/{type}/{doc_id}
- Sidebar → project slug for navigation context
- StatusBadge → colour mapping from status values

### Data Considerations

- Document list queries use indexed columns (doc_type, status, project_id)
- Full document content loaded only on single document view
- Pagination prevents loading all documents at once

**TRD Reference:** [§5 API Contracts](../trd.md#5-api-contracts)

## Sizing & Effort

**Story Points:** 20
**Estimated Story Count:** ~5 stories

**Complexity Factors:**

- Multiple filter/sort/pagination combinations to implement and test
- Markdown rendering configuration and plugin setup
- Responsive component design within dark theme
- Status badge colour mapping for all possible status values
- Frontmatter sidebar layout and field display

## Stakeholders

| Role | Name | Interest |
|------|------|----------|
| Product Owner | Darren | Primary user, defines requirements |
| Developer | Darren/Claude | Implementation |

## Story Breakdown

| ID | Title | Complexity | Status |
|----|-------|------------|--------|
| [US0012](../stories/US0012-document-list-api.md) | Document List API with Filtering | Medium | Done |
| [US0013](../stories/US0013-document-detail-api.md) | Document Detail API | Low | Done |
| [US0014](../stories/US0014-document-list-page.md) | Document List Page | Medium | Done |
| [US0015](../stories/US0015-document-view-page.md) | Document View Page | Medium | Done |
| [US0016](../stories/US0016-status-and-type-badge-components.md) | Status and Type Badge Components | Low | Done |

## Test Plan

**Test Spec:** To be generated via `/sdlc-studio test-spec --epic EP0003`.

## Open Questions

None.

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial epic creation from PRD |
