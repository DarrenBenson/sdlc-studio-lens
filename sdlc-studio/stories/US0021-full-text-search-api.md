# US0021: Full-Text Search API

> **Status:** Done
> **Epic:** [EP0005: Search](../epics/EP0005-search.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** to search across all documents using FTS5 and filter results by project and type
**So that** I can find content regardless of which project it lives in

## Context

### Persona Reference
**Darren** - Searches for specific stories, features, or technical terms across all projects.
[Full persona details](../personas.md#darren)

### Background
The search API uses SQLite FTS5 to query across all synced documents. Results are ranked by BM25 relevance, include context snippets around matching terms, and can be filtered by project, document type, and status. The FTS5 index is populated by EP0002 sync.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Performance | Search response < 1 second | FTS5 query + pagination within budget |
| TRD | API | GET /api/v1/search?q=&project=&type=&status=&page=&per_page= | Query parameters defined |
| TRD | Data | documents_fts with unicode61 tokeniser | FTS5 MATCH syntax |
| TRD | Validation | 422 if q parameter missing | Required parameter |

---

## Acceptance Criteria

### AC1: Search returns matching documents
- **Given** documents containing the word "authentication" exist across projects
- **When** I GET `/api/v1/search?q=authentication`
- **Then** I receive 200 with items containing doc_id, type, title, project_slug, project_name, status, snippet, and score; sorted by relevance

### AC2: Snippet includes context
- **Given** a document contains "implement authentication via API key header"
- **When** searching for "authentication"
- **Then** the snippet field contains surrounding context with the matching term marked: "...implement <mark>authentication</mark> via API key header..."

### AC3: Filter by project
- **Given** "authentication" appears in both "homelabcmd" and "sdlc-lens" projects
- **When** I GET `/api/v1/search?q=authentication&project=homelabcmd`
- **Then** only results from "homelabcmd" are returned

### AC4: Filter by type
- **Given** "authentication" appears in stories and epics
- **When** I GET `/api/v1/search?q=authentication&type=story`
- **Then** only story documents are returned

### AC5: Missing query returns 422
- **Given** no `q` parameter in the request
- **When** I GET `/api/v1/search`
- **Then** I receive 422 with error code "VALIDATION_ERROR"

### AC6: No results returns empty list
- **Given** no documents contain "xyznonexistent"
- **When** I GET `/api/v1/search?q=xyznonexistent`
- **Then** I receive 200 with items: [], total: 0

---

## Scope

### In Scope
- GET /api/v1/search endpoint
- FTS5 MATCH query execution
- BM25 relevance ranking
- Snippet extraction via FTS5 snippet() function
- Filter by project slug, document type, status
- Pagination (20 per page default, max 50)
- 422 for missing query parameter
- Pydantic response model

### Out of Scope
- Search suggestions or autocomplete
- Fuzzy matching or typo tolerance
- Advanced query syntax (AND, OR, NOT)
- Search analytics or logging
- Highlighting in document view

---

## Technical Notes

### API Contract

**Request:**
```
GET /api/v1/search?q=authentication&project=homelabcmd&type=story&page=1&per_page=20
```

**Response (200):**
```json
{
  "items": [
    {
      "doc_id": "US0045",
      "type": "story",
      "title": "API Key Authentication",
      "project_slug": "homelabcmd",
      "project_name": "HomelabCmd",
      "status": "Done",
      "snippet": "...implement <mark>authentication</mark> via API key header...",
      "score": 0.95
    }
  ],
  "total": 12,
  "page": 1,
  "per_page": 20,
  "query": "authentication"
}
```

### FTS5 Query
```sql
SELECT d.id, d.doc_id, d.doc_type, d.title, d.status,
       p.slug, p.name,
       snippet(documents_fts, 1, '<mark>', '</mark>', '...', 32) as snippet,
       rank
FROM documents_fts
JOIN documents d ON d.id = documents_fts.rowid
JOIN projects p ON p.id = d.project_id
WHERE documents_fts MATCH ?
  AND (? IS NULL OR p.slug = ?)
  AND (? IS NULL OR d.doc_type = ?)
  AND (? IS NULL OR d.status = ?)
ORDER BY rank
LIMIT ? OFFSET ?
```

### Data Requirements
- FTS5 MATCH uses query term directly (simple search)
- BM25 ranking via FTS5 rank column
- snippet() function extracts context (32 tokens around match)
- COUNT query for total results (separate from paginated query)

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Empty query string (q=) | 422 VALIDATION_ERROR |
| Query with FTS5 special syntax (AND, OR) | Passed to FTS5; may fail - wrap in quotes for literal search |
| Query with asterisk wildcard (auth*) | FTS5 prefix search supported; returns matches |
| Very long query string (>500 chars) | 422 VALIDATION_ERROR; max query length enforced |
| Multiple words in query | FTS5 implicit AND between terms |
| Query matching thousands of documents | Pagination limits response; total count returned |
| Project filter for non-existent project | Empty results (not 404; filter simply matches nothing) |
| Snippet extraction for very short document | Shorter snippet returned; no padding |
| Search with unicode characters | unicode61 tokeniser handles correctly |
| snake_case search terms (sync_status) | Matched as single token due to tokenchars '_' |

---

## Test Scenarios

- [ ] Search returns matching documents for query term
- [ ] Results ranked by relevance (highest score first)
- [ ] Snippet contains matching term with context
- [ ] Filter by project narrows results
- [ ] Filter by type narrows results
- [ ] Filter by status narrows results
- [ ] Combined filters work together
- [ ] Pagination returns correct page
- [ ] Total count correct with filters
- [ ] Missing q parameter returns 422
- [ ] Empty results returns 200 with empty items
- [ ] snake_case terms searchable as single tokens
- [ ] Response includes query echo

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0010](US0010-fts5-search-index-management.md) | Schema | FTS5 index populated | Draft |
| [US0001](US0001-register-new-project.md) | Schema | Projects table | Draft |

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
