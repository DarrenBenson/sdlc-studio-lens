# PL0022: Search Results Page - Implementation Plan

> **Status:** Complete
> **Story:** [US0022: Search Results Page](../stories/US0022-search-results-page.md)
> **Epic:** [EP0005: Search](../epics/EP0005-search.md)
> **Created:** 2026-02-17
> **Language:** TypeScript

## Overview

Create the search results page at `/search?q=...` displaying result cards with title, type/status badges, project name, and highlighted snippets. Filter controls for project and type. Clicking a result navigates to the document view.

## Recommended Approach

**Strategy:** TDD

## Implementation Phases

### Phase 1: Types and API Client
- [ ] Add SearchResult and SearchResponse interfaces to types/index.ts
- [ ] Add fetchSearchResults() to api/client.ts

### Phase 2: SearchResults Page Component
- [ ] Create `pages/SearchResults.tsx`
- [ ] Read `q`, `project`, `type` from URL search params
- [ ] Fetch results via fetchSearchResults()
- [ ] Render result cards with title, type badge, project name, status badge, snippet
- [ ] Snippet rendered with dangerouslySetInnerHTML for `<mark>` tags
- [ ] Click result navigates to /projects/{slug}/documents/{type}/{docId}
- [ ] Empty state for no results
- [ ] Loading and error states

### Phase 3: Route Update
- [ ] Add `/search` route to App.tsx

## Edge Case Handling

| # | Edge Case | Handling Strategy | Phase |
|---|-----------|-------------------|-------|
| 1 | No results | "No results found" message | Phase 2 |
| 2 | API error | Error message with retry | Phase 2 |
| 3 | Loading state | Loading text | Phase 2 |
| 4 | Long snippet | Truncated by API (32 tokens) | Phase 2 |
| 5 | Special chars in query | URL-decoded for display | Phase 2 |

**Coverage:** 5/5

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit tests written and passing
- [ ] Edge cases handled
