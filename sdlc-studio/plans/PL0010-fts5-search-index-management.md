# PL0010: FTS5 Search Index Management - Implementation Plan

> **Status:** Complete
> **Story:** [US0010: FTS5 Search Index Management](../stories/US0010-fts5-search-index-management.md)
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Created:** 2026-02-17
> **Language:** Python

## Overview

Implement SQLite FTS5 full-text search index management for synced documents. Creates an external-content FTS5 virtual table via Alembic migration, and provides functions for inserting, updating, and deleting index entries during sync operations. Uses the unicode61 tokeniser with `tokenchars '_'` to preserve snake_case terms as single tokens.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | FTS5 table creation | Alembic migration creates documents_fts virtual table |
| AC2 | Index new documents | New document title and content inserted into FTS5 |
| AC3 | Index updated documents | Changed document FTS5 entry updated |
| AC4 | Index cleanup | Deleted document FTS5 entry removed |
| AC5 | Searchable | FTS5 MATCH query returns correct documents |

---

## Technical Context

### Language & Framework
- **Primary Language:** Python 3.12+
- **Framework:** SQLAlchemy async (raw SQL for FTS5 operations)
- **Test Framework:** pytest >=8.0.0 with pytest-asyncio

### Relevant Best Practices
- Type hints on all public functions
- Raw SQL for FTS5 operations (SQLAlchemy ORM does not support FTS5 natively)
- Alembic for schema migrations
- Ruff for linting and formatting

### Library Documentation (Context7)

| Library | Context7 ID | Key Patterns |
|---------|-------------|--------------|
| SQLAlchemy | /websites/sqlalchemy_en_21 | session.execute(text()), AsyncSession |
| SQLite FTS5 | - | External content mode, unicode61 tokeniser |

### Existing Patterns

Alembic migrations established by US0001. FTS5 operations use raw SQL via `session.execute(text(...))` since SQLAlchemy ORM does not model virtual tables.

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** SQL operations with concrete assertions: insert a document, verify MATCH returns it. Delete a document, verify MATCH does not return it. 8 edge cases with clear pass/fail criteria.

### Test Priority
1. FTS5 table creation (migration runs without error)
2. Insert + MATCH query returns document
3. Update + MATCH query returns updated content
4. Delete + MATCH query no longer returns document
5. snake_case terms searchable as single tokens
6. Edge cases (empty content, non-ASCII, rebuild)

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Create Alembic migration for documents_fts | `backend/alembic/versions/` | - | [ ] |
| 2 | Implement fts_insert function | `backend/src/sdlc_lens/services/fts.py` | 1 | [ ] |
| 3 | Implement fts_update function (delete + insert) | `backend/src/sdlc_lens/services/fts.py` | 2 | [ ] |
| 4 | Implement fts_delete function | `backend/src/sdlc_lens/services/fts.py` | 1 | [ ] |
| 5 | Implement fts_rebuild function | `backend/src/sdlc_lens/services/fts.py` | 1 | [ ] |
| 6 | Write integration tests | `backend/tests/test_fts.py` | 2, 3, 4 | [ ] |

### Parallel Execution Groups

| Group | Tasks | Prerequisite |
|-------|-------|--------------|
| Migration | 1 | None |
| FTS Functions | 2, 3, 4, 5 | Group: Migration |
| Tests | 6 | Group: FTS Functions |

---

## Implementation Phases

### Phase 1: FTS5 Migration
**Goal:** Create the documents_fts virtual table

- [ ] Create Alembic migration with raw SQL:
  ```sql
  CREATE VIRTUAL TABLE documents_fts USING fts5(
      title,
      content,
      content=documents,
      content_rowid=id,
      tokenize="unicode61 tokenchars '_'"
  );
  ```
- [ ] Downgrade drops the virtual table

**Files:**
- `backend/alembic/versions/003_create_documents_fts.py` - FTS5 migration

### Phase 2: FTS5 Service Functions
**Goal:** Implement CRUD operations for the FTS5 index

- [ ] Create `backend/src/sdlc_lens/services/fts.py`
- [ ] `fts_insert(db, doc_id, title, content)` - INSERT into documents_fts
- [ ] `fts_update(db, doc_id, old_title, old_content, new_title, new_content)` - DELETE old + INSERT new
- [ ] `fts_delete(db, doc_id, title, content)` - DELETE from documents_fts
- [ ] `fts_rebuild(db)` - `INSERT INTO documents_fts(documents_fts) VALUES('rebuild')`
- [ ] All operations use `session.execute(text(...))` with bound parameters

**FTS5 SQL patterns:**
```sql
-- Insert
INSERT INTO documents_fts(rowid, title, content) VALUES (:rowid, :title, :content);

-- Update (delete old, insert new)
INSERT INTO documents_fts(documents_fts, rowid, title, content)
    VALUES('delete', :rowid, :old_title, :old_content);
INSERT INTO documents_fts(rowid, title, content) VALUES (:rowid, :new_title, :new_content);

-- Delete
INSERT INTO documents_fts(documents_fts, rowid, title, content)
    VALUES('delete', :rowid, :title, :content);

-- Rebuild
INSERT INTO documents_fts(documents_fts) VALUES('rebuild');
```

**Files:**
- `backend/src/sdlc_lens/services/fts.py` - FTS5 service

### Phase 3: Testing
**Goal:** Verify FTS5 operations and searchability

- [ ] Create `backend/tests/test_fts.py`
- [ ] Test migration creates virtual table
- [ ] Test insert makes document searchable via MATCH
- [ ] Test update changes searchable content
- [ ] Test delete removes document from search results
- [ ] Test snake_case terms searchable (e.g. "sync_status")
- [ ] Test empty content indexed without error
- [ ] Test rebuild command works

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | Migration runs; table exists | `tests/test_fts.py` | Pending |
| AC2 | Insert + MATCH returns document | `tests/test_fts.py` | Pending |
| AC3 | Update + MATCH returns new content | `tests/test_fts.py` | Pending |
| AC4 | Delete + MATCH returns nothing | `tests/test_fts.py` | Pending |
| AC5 | MATCH query returns correct results | `tests/test_fts.py` | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | FTS5 index out of sync | fts_rebuild() function available for manual recovery | Phase 2 |
| 2 | Document with empty content | Insert with empty string; title still searchable | Phase 2 |
| 3 | Very large content (>100KB) | FTS5 handles large content natively | Phase 2 |
| 4 | Special characters (markdown syntax) | FTS5 tokeniser handles; no special escaping needed | Phase 2 |
| 5 | snake_case terms | tokenchars '_' preserves underscores; "sync_status" is one token | Phase 1 |
| 6 | Unicode content | unicode61 tokeniser handles non-ASCII | Phase 1 |
| 7 | FTS5 insert fails | Log warning; document in table but not searchable | Phase 2 |
| 8 | Concurrent writes | SQLite serialises writes; no corruption risk | Phase 2 |

**Coverage:** 8/8 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| FTS5 not available in SQLite build | High | Require SQLite 3.40+; check at startup |
| External content mode complexity | Medium | Explicit insert/delete/update functions; no triggers |
| aiosqlite FTS5 compatibility | Low | FTS5 operations are standard SQL; aiosqlite handles |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Alembic migration creates FTS5 table
- [ ] Integration tests written and passing
- [ ] Edge cases handled
- [ ] Ruff linting passes
- [ ] FTS5 functions importable from sdlc_lens.services.fts

---

## Notes

- External content mode means FTS5 does not store a copy of the content - it references the documents table. This saves storage but requires explicit maintenance.
- The DELETE syntax for external content FTS5 requires passing the old values: `INSERT INTO documents_fts(documents_fts, rowid, title, content) VALUES('delete', ?, ?, ?)`.
- The fts module functions take the SQLAlchemy AsyncSession and document data as parameters.
