# PL0021: Full-Text Search API - Implementation Plan

> **Status:** Complete
> **Story:** [US0021: Full-Text Search API](../stories/US0021-full-text-search-api.md)
> **Epic:** [EP0005: Search](../epics/EP0005-search.md)
> **Created:** 2026-02-17
> **Language:** Python

## Overview

Create GET /api/v1/search endpoint querying FTS5 index with filters, pagination, BM25 ranking, and snippet extraction. The FTS5 virtual table already exists from EP0002.

## Recommended Approach

**Strategy:** TDD

## Implementation Phases

### Phase 1: Search Service
- [ ] Create `services/search.py` with `search_documents()` function
- [ ] FTS5 MATCH query with BM25 ranking
- [ ] snippet() extraction with `<mark>` tags
- [ ] Filter by project slug, doc_type, status
- [ ] Pagination (page, per_page with defaults)
- [ ] Total count query

### Phase 2: Search Schema and Route
- [ ] Create `api/schemas/search.py` with SearchResult and SearchResponse models
- [ ] Create `api/routes/search.py` with GET /search endpoint
- [ ] Query parameter validation (q required, per_page max 50)
- [ ] Register search_router in main.py

## Edge Case Handling

| # | Edge Case | Handling Strategy | Phase |
|---|-----------|-------------------|-------|
| 1 | Empty query string | 422 VALIDATION_ERROR | Phase 2 |
| 2 | FTS5 special syntax | Wrap in double quotes for literal search | Phase 1 |
| 3 | Very long query (>500 chars) | 422 VALIDATION_ERROR | Phase 2 |
| 4 | No results | Return 200 with empty items, total=0 | Phase 1 |
| 5 | Non-existent project filter | Empty results (not 404) | Phase 1 |
| 6 | snake_case terms | Handled by unicode61 tokenchars | Phase 1 |
| 7 | Thousands of results | Pagination limits response | Phase 1 |

**Coverage:** 7/7

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit tests written and passing
- [ ] Edge cases handled
