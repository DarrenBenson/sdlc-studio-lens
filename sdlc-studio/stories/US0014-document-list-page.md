# US0014: Document List Page

> **Status:** Done
> **Epic:** [EP0003: Document Browsing](../epics/EP0003-document-browsing.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** to browse documents with type and status filters in a list view
**So that** I can find specific artefacts quickly without navigating the filesystem

## Context

### Persona Reference
**Darren** - Filters to find specific stories or epics; prefers dark-themed developer tools.
[Full persona details](../personas.md#darren)

### Background
The document list page is the main browsing interface. It shows all documents for a project in a table/list with type badges, status badges, and metadata columns. Filter controls for type and status narrow the list, sort controls change the order, and pagination handles large result sets. Clicking a document navigates to the rendered view.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Design | Dark theme with lime green accents (Brand Guide) | All components follow brand guide |
| PRD | Performance | Document list load < 500ms | Efficient API calls, minimal re-renders |
| TRD | Architecture | React SPA with client-side routing | Route: /projects/:slug/documents |

---

## Acceptance Criteria

### AC1: Document list displays with badges
- **Given** I navigate to `/projects/homelabcmd/documents`
- **When** the page loads
- **Then** I see a list of documents with columns: title, type badge, status badge, owner, and last modified date

### AC2: Type filter narrows results
- **Given** the document list shows all types
- **When** I select "Stories" from the type filter
- **Then** only story documents are displayed and the URL updates to include `?type=story`

### AC3: Status filter narrows results
- **Given** the document list shows all statuses
- **When** I select "In Progress" from the status filter
- **Then** only In Progress documents are displayed

### AC4: Pagination controls
- **Given** a project has 120 documents showing 50 per page
- **When** I click "Next" or page 2
- **Then** the next 50 documents are displayed with correct page indicator

### AC5: Click navigates to document view
- **Given** a document "US0001: Register a New Project" is in the list
- **When** I click on it
- **Then** I navigate to `/projects/homelabcmd/documents/story/US0001`

---

## Scope

### In Scope
- Document list page component at `/projects/:slug/documents`
- Type filter dropdown/chips (epic, story, bug, plan, test-spec, prd, trd, tsd, other)
- Status filter dropdown/chips (Draft, In Progress, Done, etc.)
- Sort control (title, type, status, updated_at)
- Pagination controls (page numbers, next/prev)
- Loading state while fetching
- Empty state when no documents match filters
- URL query parameter sync (filters reflected in URL for shareability)
- DocumentCard component for list items

### Out of Scope
- Full document content display (US0015)
- Search functionality (US0022, EP0005)
- Bulk actions on documents

---

## Technical Notes

### API Integration
- GET /api/v1/projects/{slug}/documents with query parameters
- URL query params synced with React state for bookmarkable filter combinations
- Debounced filter changes to avoid excessive API calls

### Data Requirements
- React state: type filter, status filter, sort field, sort order, page number
- URL params: type, status, sort, order, page
- API response: items array, total, page, per_page, pages

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Zero documents match current filters | "No documents match your filters" message with option to clear filters |
| Project not found (invalid slug in URL) | Redirect to dashboard or show "Project not found" |
| API error during document fetch | Error message with retry button |
| Very long document title | Truncated with ellipsis in list; full title in tooltip |
| Rapid filter changes | Debounced; only latest request rendered |
| Browser back/forward with filter changes | Filters restored from URL parameters |
| Loading state | Skeleton placeholders while fetching |
| Filter produces single page | Pagination controls hidden |

---

## Test Scenarios

- [ ] Document list renders with correct columns
- [ ] Type filter updates displayed documents
- [ ] Status filter updates displayed documents
- [ ] Combined filters work together
- [ ] Sort control changes document order
- [ ] Pagination controls navigate between pages
- [ ] Click on document navigates to view page
- [ ] Empty state shown when no matches
- [ ] Loading state shown during fetch
- [ ] URL query params updated on filter change
- [ ] Filters restored from URL params on page load
- [ ] Type badges render with correct colours
- [ ] Status badges render with correct colours

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0012](US0012-document-list-api.md) | API | Document list endpoint | Draft |
| [US0016](US0016-status-and-type-badge-components.md) | Component | Badge components | Draft |
| [US0005](US0005-sidebar-project-navigation.md) | Component | Layout shell with sidebar | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| React Router | Infrastructure | Not Started |

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
