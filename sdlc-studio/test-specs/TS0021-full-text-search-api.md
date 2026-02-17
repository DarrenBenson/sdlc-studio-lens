# TS0021: Full-Text Search API

> **Status:** Complete
> **Epic:** [EP0005: Search](../epics/EP0005-search.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for the full-text search API endpoint.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0021](../stories/US0021-full-text-search-api.md) | Full-Text Search API | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0021 | AC1 | Search returns matching documents | TC0228, TC0229 | Pending |
| US0021 | AC2 | Snippet includes context | TC0230 | Pending |
| US0021 | AC3 | Filter by project | TC0231 | Pending |
| US0021 | AC4 | Filter by type | TC0232 | Pending |
| US0021 | AC5 | Missing query returns 422 | TC0233 | Pending |
| US0021 | AC6 | No results returns empty list | TC0234 | Pending |

**Coverage:** 6/6 ACs covered

---

## Test Cases

### TC0228: Search returns matching documents
**Type:** Integration | **Priority:** High
- Given: Documents containing "authentication" exist
- When: GET /api/v1/search?q=authentication
- Then: 200 with items containing doc_id, type, title, project_slug, project_name, status, snippet, score

### TC0229: Results ranked by relevance
**Type:** Integration | **Priority:** High
- Given: Multiple documents match query
- Then: Results sorted by score descending

### TC0230: Snippet includes context with mark tags
**Type:** Integration | **Priority:** High
- Given: Document contains "implement authentication via API key"
- When: Search for "authentication"
- Then: Snippet contains `<mark>authentication</mark>` with surrounding context

### TC0231: Filter by project slug
**Type:** Integration | **Priority:** High
- Given: Results from multiple projects
- When: GET /api/v1/search?q=test&project=project-a
- Then: Only results from project-a returned

### TC0232: Filter by document type
**Type:** Integration | **Priority:** High
- Given: Results across multiple types
- When: GET /api/v1/search?q=test&type=story
- Then: Only story documents returned

### TC0233: Missing query returns 422
**Type:** Integration | **Priority:** High
- When: GET /api/v1/search (no q parameter)
- Then: 422 response

### TC0234: No results returns empty list
**Type:** Integration | **Priority:** High
- When: GET /api/v1/search?q=xyznonexistent
- Then: 200 with items=[], total=0

### TC0235: Pagination works
**Type:** Integration | **Priority:** Medium
- Given: 25 matching documents
- When: GET /api/v1/search?q=test&per_page=10&page=1
- Then: 10 items returned, total=25

### TC0236: Combined filters
**Type:** Integration | **Priority:** Medium
- When: GET /api/v1/search?q=test&project=project-a&type=story
- Then: Only stories from project-a matching "test"

### TC0237: Empty query string returns 422
**Type:** Integration | **Priority:** Medium
- When: GET /api/v1/search?q=
- Then: 422 response

### TC0238: Response includes query echo
**Type:** Integration | **Priority:** Medium
- When: GET /api/v1/search?q=authentication
- Then: Response body includes query="authentication"

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec |
