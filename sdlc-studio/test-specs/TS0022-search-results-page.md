# TS0022: Search Results Page

> **Status:** Complete
> **Epic:** [EP0005: Search](../epics/EP0005-search.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for the search results page.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0022](../stories/US0022-search-results-page.md) | Search Results Page | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0022 | AC1 | Search results display | TC0245, TC0246 | Pending |
| US0022 | AC2 | Click navigates to document | TC0247 | Pending |
| US0022 | AC3 | Project filter | TC0248 | Pending |
| US0022 | AC4 | No results state | TC0249 | Pending |
| US0022 | AC5 | Search term preserved | TC0250 | Pending |

**Coverage:** 5/5 ACs covered

---

## Test Cases

### TC0245: Renders result cards
**Type:** Unit | **Priority:** High
- Given: Search returns 3 results
- Then: 3 result cards with titles visible

### TC0246: Result card shows type badge, project, snippet
**Type:** Unit | **Priority:** High
- Given: Result with type=story, project_name="HomelabCmd", snippet with mark
- Then: Card shows type badge, project name, snippet

### TC0247: Click result navigates to document
**Type:** Unit | **Priority:** High
- Given: Result for doc_id=US0045, type=story, project_slug=homelabcmd
- When: Click result card
- Then: Navigates to /projects/homelabcmd/documents/story/US0045

### TC0248: Project filter updates results
**Type:** Unit | **Priority:** High
- Given: Results from multiple projects
- When: Select project filter
- Then: URL updates with project parameter, results re-fetched

### TC0249: No results shows empty state
**Type:** Unit | **Priority:** High
- Given: Search returns 0 results
- Then: "No results found" message displayed

### TC0250: Search query shown in heading
**Type:** Unit | **Priority:** High
- Given: Search for "authentication"
- Then: Page shows query context (e.g., results count)

### TC0251: Loading state
**Type:** Unit | **Priority:** Medium
- Given: Search still loading
- Then: Loading indicator displayed

### TC0252: Error state with retry
**Type:** Unit | **Priority:** Medium
- Given: Search API fails
- Then: Error message with retry button

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec |
