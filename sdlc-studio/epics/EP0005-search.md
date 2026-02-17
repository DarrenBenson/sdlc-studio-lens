# EP0005: Search

> **Status:** Done
> **Owner:** Darren
> **Created:** 2026-02-17
> **Target Release:** Phase 3 (Search & Deployment)
> **Story Points:** 12

## Summary

Full-text search across all synced documents using SQLite FTS5. This epic delivers the search API endpoint, search UI with project and type filters, result ranking by relevance, and snippet display with context. Users can find any content across all registered projects from a single search bar.

## Inherited Constraints

Constraints that flow from PRD and TRD to this Epic.

### From PRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Performance | Search response < 1 second | FTS5 query must be efficient |
| KPI | Search returns relevant results in < 1s | Ranking and snippet extraction within budget |
| Design | Dark theme with lime green accents ([Brand Guide](../brand-guide.md)) | Search results page follows brand guide |

### From TRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Tech Stack | SQLite FTS5 | Built-in full-text search, no external engine |
| API | GET /api/v1/search?q=&project=&type=&status=&page=&per_page= | Search endpoint with filters |
| Data | documents_fts virtual table (title, content) | FTS5 index already populated by EP0002 |
| Validation | 422 if `q` parameter missing | Required query parameter |

> **Note:** Inherited constraints MUST propagate to child Stories. Check Story templates include these constraints.

## Business Context

### Problem Statement

With documents spread across multiple projects and potentially hundreds of files, finding specific content requires filesystem grep or manual browsing. Developers need a fast, cross-project search that surfaces relevant documents with context.

**PRD Reference:** [§5 Feature Inventory](../prd.md#5-feature-inventory) (FR7)

### Value Proposition

Type a term into the search bar and instantly see matching documents from all projects, ranked by relevance, with snippets showing where the term appears. Filter by project or document type to narrow results.

### Success Metrics

| Metric | Current State | Target | Measurement Method |
|--------|---------------|--------|-------------------|
| Time to find content across projects | Minutes (grep across directories) | < 5 seconds (search + click) | User observation |
| Search response time | N/A | < 1 second | API timing |
| Result relevance | N/A | Top result matches intent | Manual assessment |

## Scope

### In Scope

- Search API endpoint with required query parameter
- FTS5 query execution against documents_fts virtual table
- Results ranked by FTS5 relevance score
- Search results include: doc_id, type, title, project_slug, project_name, status, snippet, score
- Snippet extraction with surrounding context
- Filter by project slug
- Filter by document type
- Filter by status
- Pagination (20 per page default, max 50)
- 422 error for missing query parameter
- Empty results list for no-match queries
- Search UI with input field in header
- Search results page with result cards
- Clicking search result navigates to document view

### Out of Scope

- Search term highlighting in rendered document view (P2)
- Search suggestions or autocomplete
- Saved searches
- Search analytics
- Fuzzy matching or typo tolerance
- Advanced query syntax (AND, OR, NOT)

### Affected User Personas

- **SDLC Developer (Darren):** Searches for specific stories, features, or technical terms across all projects

## Acceptance Criteria (Epic Level)

- [ ] Search returns results matching query term from any project
- [ ] Results ranked by FTS5 relevance score
- [ ] Each result shows document title, type, project name, status, and snippet
- [ ] Snippet includes surrounding context for the matching term
- [ ] Project filter narrows results to a single project
- [ ] Type filter narrows results to a single document type
- [ ] Combined filters work together
- [ ] Pagination works correctly with total count
- [ ] Missing query parameter returns 422 error
- [ ] No-match query returns empty results list (not an error)
- [ ] Search response time < 1 second
- [ ] Clicking a result navigates to the document view page

## Dependencies

### Blocked By

| Dependency | Type | Status | Owner | Notes |
|------------|------|--------|-------|-------|
| EP0002: Document Sync & Parsing | Epic | Draft | Darren | FTS5 index must be populated |

### Blocking

| Item | Type | Impact |
|------|------|--------|
| None | - | - |

## Risks & Assumptions

### Assumptions

- FTS5 default ranking (BM25) provides adequate relevance for technical documents
- Snippet extraction via FTS5 snippet() function is sufficient
- 20 results per page is a reasonable default for search
- UTF-8 content is handled correctly by FTS5 tokeniser

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| FTS5 tokeniser struggles with technical terms (camelCase, snake_case) | Medium | Medium | Test with representative queries; consider unicode61 tokeniser |
| Snippet extraction too slow for large documents | Low | Low | FTS5 snippet() is optimised; limit context window |
| Search result ranking poor for short queries | Low | Medium | Add title boost (weight title field higher) |

## Technical Considerations

### Architecture Impact

- Creates search API endpoint with FTS5 query execution
- Creates SearchBar component in header/navigation
- Creates SearchResults page
- FTS5 index already established by EP0002; this epic only queries it

### Integration Points

- SearchBar component → React Router navigation to /search?q=
- SearchResults page → GET /api/v1/search?q=&project=&type=
- Search result card → link to /projects/{slug}/documents/{type}/{docId}
- Backend → FTS5 MATCH query with snippet() and rank functions

### Data Considerations

- FTS5 queries use MATCH syntax
- Relevance scoring via FTS5 bm25() function
- Snippet via FTS5 snippet() function with configurable context
- Filter queries join documents_fts with documents table for project/type/status

**TRD Reference:** [§5 API Contracts](../trd.md#5-api-contracts)

## Sizing & Effort

**Story Points:** 12
**Estimated Story Count:** ~3 stories

**Complexity Factors:**

- FTS5 query syntax and ranking configuration
- Snippet extraction with context
- Cross-project result aggregation
- Filter combination with FTS5 results
- Search UI state management (query, filters, pagination)

## Stakeholders

| Role | Name | Interest |
|------|------|----------|
| Product Owner | Darren | Primary user, defines requirements |
| Developer | Darren/Claude | Implementation |

## Story Breakdown

| ID | Title | Complexity | Status |
|----|-------|------------|--------|
| [US0021](../stories/US0021-full-text-search-api.md) | Full-Text Search API | Medium | Done |
| [US0022](../stories/US0022-search-results-page.md) | Search Results Page | Medium | Done |
| [US0023](../stories/US0023-global-search-bar.md) | Global Search Bar Component | Low | Done |

## Test Plan

**Test Spec:** To be generated via `/sdlc-studio test-spec --epic EP0005`.

## Open Questions

- [x] Should FTS5 use porter stemmer or unicode61 tokeniser? - Owner: Darren
  **Resolved:** unicode61 with `tokenchars '_'`. Technical documents need exact matching over stemmed recall. Underscore as a token character keeps snake_case identifiers intact. See TRD §12 for full rationale.

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial epic creation from PRD |
