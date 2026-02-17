# US0010: FTS5 Search Index Management

> **Status:** Done
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** synced documents indexed for full-text search
**So that** I can find content across all projects quickly

## Context

### Persona Reference
**Darren** - Searches for specific stories, features, or technical terms across projects.
[Full persona details](../personas.md#darren)

### Background
SQLite FTS5 provides full-text search capability. The documents_fts virtual table indexes document titles and content, enabling sub-second search across all synced documents. This story covers FTS5 table creation, index population during sync (add/update), and index cleanup (delete). The actual search API query is handled in EP0005.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Data | FTS5 virtual table: documents_fts(title, content) | External content mode linked to documents table |
| TRD | Data | unicode61 tokeniser with tokenchars '_' | Technical terms and snake_case preserved |
| Epic | Performance | Search < 1s | FTS5 index must be correctly populated |

---

## Acceptance Criteria

### AC1: FTS5 virtual table creation
- **Given** the database is initialised via Alembic migration
- **When** the migration runs
- **Then** a documents_fts virtual table exists with columns title and content, using external content mode linked to the documents table, with unicode61 tokeniser and tokenchars '_'

### AC2: Index population for new documents
- **Given** a new document "EP0001: Project Management" is added during sync
- **When** the document is inserted into the documents table
- **Then** its title and content are also inserted into documents_fts

### AC3: Index update for changed documents
- **Given** document EP0001 content changes during re-sync
- **When** the document is updated in the documents table
- **Then** the documents_fts entry is also updated with new title and content

### AC4: Index cleanup for deleted documents
- **Given** document US0099 is deleted from the documents table during sync
- **When** the deletion is processed
- **Then** the corresponding documents_fts entry is also removed

### AC5: Searchable after sync
- **Given** 50 documents have been synced with FTS5 indexing
- **When** I query `SELECT * FROM documents_fts WHERE documents_fts MATCH 'authentication'`
- **Then** documents containing "authentication" in title or content are returned

---

## Scope

### In Scope
- Alembic migration to create documents_fts virtual table
- FTS5 INSERT trigger/function for new documents
- FTS5 UPDATE function for changed documents
- FTS5 DELETE function for removed documents
- unicode61 tokeniser with tokenchars '_' configuration
- External content mode (content=documents, content_rowid=id)

### Out of Scope
- Search API endpoint (US0021, EP0005)
- Search UI (US0022-US0023, EP0005)
- FTS5 ranking or snippet functions (US0021)

---

## Technical Notes

### FTS5 DDL
```sql
CREATE VIRTUAL TABLE documents_fts USING fts5(
    title,
    content,
    content=documents,
    content_rowid=id,
    tokenize="unicode61 tokenchars '_'"
);
```

### Index Maintenance (External Content Mode)
With external content mode, FTS5 does not store content - it references the documents table. Index maintenance requires explicit triggers or manual operations:

```sql
-- Insert into FTS5
INSERT INTO documents_fts(rowid, title, content) VALUES (?, ?, ?);

-- Update in FTS5 (delete old, insert new)
INSERT INTO documents_fts(documents_fts, rowid, title, content) VALUES('delete', ?, ?, ?);
INSERT INTO documents_fts(rowid, title, content) VALUES (?, ?, ?);

-- Delete from FTS5
INSERT INTO documents_fts(documents_fts, rowid, title, content) VALUES('delete', ?, ?, ?);
```

### Data Requirements
- FTS5 rowid matches documents.id
- Content synced during sync service operations
- No separate FTS5 rebuild needed if sync maintains the index

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| FTS5 index out of sync with documents table | Provide rebuild command: `INSERT INTO documents_fts(documents_fts) VALUES('rebuild')` |
| Document with empty content | Indexed with empty content; title still searchable |
| Document with very large content (>100KB) | Indexed normally; FTS5 handles large content |
| Special characters in content (markdown syntax) | Indexed as-is; FTS5 tokeniser handles |
| snake_case terms (sync_status, last_synced_at) | Treated as single tokens due to tokenchars '_' |
| Unicode content (non-ASCII characters) | unicode61 tokeniser handles correctly |
| FTS5 insert fails (DB error) | Sync continues; document in table but not searchable |
| Concurrent FTS5 writes | SQLite serialises writes; no corruption risk |

---

## Test Scenarios

- [ ] FTS5 virtual table created by migration
- [ ] New document indexed in FTS5 during sync
- [ ] Changed document FTS5 entry updated
- [ ] Deleted document FTS5 entry removed
- [ ] FTS5 MATCH query returns correct documents
- [ ] snake_case terms searchable as single tokens
- [ ] Empty content document indexed without error
- [ ] FTS5 rebuild command works
- [ ] unicode61 tokeniser handles non-ASCII content
- [ ] FTS5 index consistent with documents table after full sync

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0007](US0007-filesystem-sync-service.md) | Service | Sync orchestration calls FTS5 functions | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| SQLite compiled with FTS5 extension | Infrastructure | Available in standard SQLite 3.40+ |

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
| 2026-02-17 | Claude | Initial story creation from EP0002 |
