# US0022: Search Results Page

> **Status:** Done
> **Epic:** [EP0005: Search](../epics/EP0005-search.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** a search results page showing matching documents with snippets
**So that** I can evaluate results and navigate to the right document

## Context

### Persona Reference
**Darren** - Searches for content across projects; needs to quickly evaluate which result is most relevant.
[Full persona details](../personas.md#darren)

### Background
The search results page displays results from the search API with document title, type badge, project name, status badge, and a snippet showing where the search term appears. Filter controls for project and type narrow results. Clicking a result navigates to the document view.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Design | Dark theme with lime green accents (Brand Guide) | All components follow brand guide |
| TRD | Architecture | React SPA | Route: /search |

---

## Acceptance Criteria

### AC1: Search results display
- **Given** a search for "authentication" returns 12 results
- **When** the search results page renders
- **Then** I see result cards showing: document title, type badge, project name, status badge, and snippet with highlighted matching term

### AC2: Click navigates to document
- **Given** a search result for "US0045: API Key Authentication" in project "homelabcmd"
- **When** I click the result card
- **Then** I navigate to `/projects/homelabcmd/documents/story/US0045`

### AC3: Project filter
- **Given** search results from multiple projects
- **When** I select "HomelabCmd" from the project filter
- **Then** only results from "homelabcmd" are shown; the URL updates to include `&project=homelabcmd`

### AC4: No results state
- **Given** a search for "xyznonexistent" returns 0 results
- **When** the page renders
- **Then** I see "No results found for 'xyznonexistent'" message

### AC5: Search term preserved
- **Given** I searched for "authentication"
- **When** the results page loads
- **Then** the search bar shows "authentication" and results reflect that query

---

## Scope

### In Scope
- Search results page at `/search?q=...`
- Result cards with title, type badge, project name, status badge, snippet
- Snippet with highlighted matching terms (using `<mark>` tags from API)
- Project filter dropdown
- Type filter dropdown
- Pagination for results
- Empty state for no results
- Search query reflected in search bar
- Loading state while searching

### Out of Scope
- Search autocomplete
- Saved searches
- Search history

---

## Technical Notes

### API Integration
- GET /api/v1/search?q=...&project=...&type=...&page=...
- URL query params synced with React state

### Data Requirements
- Parse snippet HTML (contains `<mark>` tags) safely for rendering
- Use dangerouslySetInnerHTML or sanitised HTML rendering for snippets

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| No results for query | "No results found" message with suggestion to adjust query |
| API error during search | Error message with retry button |
| Very long snippet | Truncated with ellipsis |
| Query with special characters | URL-encoded; displayed as-is in search bar |
| Rapid typing in search bar | Debounced search (300ms) to avoid excessive API calls |
| Loading state | Skeleton result cards while searching |
| Many results (>100) | Pagination controls show; only 20 per page |

---

## Test Scenarios

- [ ] Search results page renders result cards
- [ ] Each result shows title, type badge, project name, snippet
- [ ] Clicking result navigates to document view
- [ ] Project filter narrows results
- [ ] Type filter narrows results
- [ ] No results shows empty state message
- [ ] Search term displayed in search bar
- [ ] Pagination controls work for multi-page results
- [ ] Loading state shown during search
- [ ] Highlighted terms visible in snippets

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0021](US0021-full-text-search-api.md) | API | Search endpoint | Draft |
| [US0016](US0016-status-and-type-badge-components.md) | Component | Badge components | Draft |
| [US0023](US0023-global-search-bar.md) | Component | Search bar | Draft |

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
| 2026-02-17 | Claude | Initial story creation from EP0005 |
