# TS0010: FTS5 Search Index Management

> **Status:** Complete
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0010 - FTS5 Search Index Management. Covers the Alembic migration creating the documents_fts virtual table and the FTS5 service functions (insert, update, delete, rebuild). Tests are integration-level since they require a real SQLite database with FTS5 support.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0010](../stories/US0010-fts5-search-index-management.md) | FTS5 Search Index Management | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0010 | AC1 | FTS5 virtual table creation | TC0118 | Covered |
| US0010 | AC2 | Index population for new documents | TC0119 | Covered |
| US0010 | AC3 | Index update for changed documents | TC0120 | Covered |
| US0010 | AC4 | Index cleanup for deleted documents | TC0121 | Covered |
| US0010 | AC5 | Searchable after sync | TC0122, TC0123, TC0126, TC0127 | Covered |

**Coverage:** 5/5 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | No | FTS5 operations require real SQLite database |
| Integration | Yes | All tests need SQLite with FTS5 extension |
| E2E | No | No frontend or API layer |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Python 3.12+, pytest, pytest-asyncio, aiosqlite, SQLite 3.40+ with FTS5 |
| External Services | None (SQLite in-memory for tests) |
| Test Data | Document records with title and content |

---

## Test Cases

### TC0118: FTS5 virtual table created by migration

**Type:** Integration | **Priority:** Critical | **Story:** US0010 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A fresh database with Alembic migrations applied | Clean database |
| When | Querying SQLite schema for documents_fts | Table lookup |
| Then | documents_fts virtual table exists with correct configuration | Table created |

**Assertions:**
- [ ] `SELECT name FROM sqlite_master WHERE name='documents_fts'` returns a row
- [ ] Table is a virtual table using fts5

---

### TC0119: New document indexed in FTS5 during sync

**Type:** Integration | **Priority:** Critical | **Story:** US0010 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A document record inserted into documents table | Document exists |
| When | fts_insert(db, doc_id, title, content) is called | FTS5 indexed |
| Then | FTS5 MATCH query for a term in the title returns the document | Searchable |

**Assertions:**
- [ ] `SELECT rowid FROM documents_fts WHERE documents_fts MATCH 'project'` returns the document rowid
- [ ] Returned rowid matches the document's id

---

### TC0120: Changed document FTS5 entry updated

**Type:** Integration | **Priority:** Critical | **Story:** US0010 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A document indexed in FTS5 with title "Old Title" | Existing entry |
| When | fts_update is called with new title "New Title" | FTS5 updated |
| Then | MATCH "New" returns the document; MATCH "Old" does not | Entry updated |

**Assertions:**
- [ ] MATCH 'New' returns the document rowid
- [ ] MATCH 'Old' returns no results (assuming "Old" only in old title)

---

### TC0121: Deleted document FTS5 entry removed

**Type:** Integration | **Priority:** Critical | **Story:** US0010 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A document indexed in FTS5 | Existing entry |
| When | fts_delete(db, doc_id, title, content) is called | FTS5 cleaned |
| Then | MATCH query no longer returns the document | Entry removed |

**Assertions:**
- [ ] MATCH query for the deleted document's terms returns no results
- [ ] Other documents still searchable

---

### TC0122: FTS5 MATCH query returns correct documents

**Type:** Integration | **Priority:** Critical | **Story:** US0010 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | 5 documents indexed: 3 contain "authentication", 2 do not | Mixed content |
| When | `SELECT rowid FROM documents_fts WHERE documents_fts MATCH 'authentication'` | Search query |
| Then | Exactly 3 results returned | Correct results |

**Assertions:**
- [ ] Result count equals 3
- [ ] All 3 returned rowids correspond to documents containing "authentication"

---

### TC0123: snake_case terms searchable as single tokens

**Type:** Integration | **Priority:** High | **Story:** US0010 AC5 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A document containing "sync_status" and "last_synced_at" | snake_case terms |
| When | MATCH 'sync_status' is queried | Search query |
| Then | Document returned (underscore preserved as part of token) | Single token match |

**Assertions:**
- [ ] MATCH 'sync_status' returns the document
- [ ] MATCH 'last_synced_at' returns the document

---

### TC0124: Empty content document indexed without error

**Type:** Integration | **Priority:** Medium | **Story:** US0010 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A document with title "Empty Doc" and content "" | Empty content |
| When | fts_insert is called | FTS5 indexed |
| Then | No error raised; document searchable by title | Handled gracefully |

**Assertions:**
- [ ] No exception raised during insert
- [ ] MATCH 'Empty' returns the document

---

### TC0125: FTS5 rebuild command works

**Type:** Integration | **Priority:** Medium | **Story:** US0010 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Documents in database and FTS5 index | Existing data |
| When | fts_rebuild(db) is called | Index rebuilt |
| Then | No error raised; search results still correct | Rebuild succeeds |

**Assertions:**
- [ ] No exception raised
- [ ] MATCH queries return same results as before rebuild

---

### TC0126: unicode61 tokeniser handles non-ASCII content

**Type:** Integration | **Priority:** Medium | **Story:** US0010 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A document containing "resume" with accented characters and "naive" with diaeresis | Non-ASCII content |
| When | Document indexed and searched | FTS5 query |
| Then | Unicode content indexed and searchable | Tokeniser works |

**Assertions:**
- [ ] Document can be found via MATCH query
- [ ] Non-ASCII characters do not cause indexing errors

---

### TC0127: FTS5 index consistent with documents table after full sync

**Type:** Integration | **Priority:** High | **Story:** US0010 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | 10 documents synced with FTS5 indexing | Full sync |
| When | Comparing FTS5 rowids with documents table ids | Consistency check |
| Then | Every document in the table has a corresponding FTS5 entry | In sync |

**Assertions:**
- [ ] Count of FTS5 entries equals count of documents
- [ ] Every document id has a matching FTS5 rowid

---

## Fixtures

```yaml
document_with_content:
  id: 1
  title: "EP0001: Project Management"
  content: "This epic covers project registration and authentication."

document_with_snake_case:
  id: 2
  title: "US0003: Trigger Sync"
  content: "Updates sync_status and last_synced_at fields."

document_empty_content:
  id: 3
  title: "Empty Doc"
  content: ""

documents_for_search:
  - id: 1
    title: "Authentication Setup"
    content: "Implements authentication flow."
  - id: 2
    title: "Database Schema"
    content: "Uses authentication tokens for access."
  - id: 3
    title: "Dashboard"
    content: "Shows authentication status."
  - id: 4
    title: "Search API"
    content: "Full-text search endpoint."
  - id: 5
    title: "Docker Config"
    content: "Container orchestration setup."
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0118 | FTS5 virtual table created by migration | Pending | - |
| TC0119 | New document indexed in FTS5 | Pending | - |
| TC0120 | Changed document FTS5 entry updated | Pending | - |
| TC0121 | Deleted document FTS5 entry removed | Pending | - |
| TC0122 | FTS5 MATCH returns correct documents | Pending | - |
| TC0123 | snake_case terms searchable | Pending | - |
| TC0124 | Empty content indexed without error | Pending | - |
| TC0125 | FTS5 rebuild command works | Pending | - |
| TC0126 | unicode61 handles non-ASCII | Pending | - |
| TC0127 | FTS5 index consistent after full sync | Pending | - |

---

## Traceability

| Artefact | Reference |
|----------|-----------|
| PRD | [sdlc-studio/prd.md](../prd.md) |
| Epic | [EP0002](../epics/EP0002-document-sync-and-parsing.md) |
| TSD | [sdlc-studio/tsd.md](../tsd.md) |

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec from US0010 story plan |
