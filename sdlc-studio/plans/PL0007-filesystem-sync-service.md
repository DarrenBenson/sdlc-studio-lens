# PL0007: Filesystem Sync Service - Implementation Plan

> **Status:** Complete
> **Story:** [US0007: Filesystem Sync Service](../stories/US0007-filesystem-sync-service.md)
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Created:** 2026-02-17
> **Language:** Python

## Overview

Implement the core sync orchestrator that walks a project's sdlc-studio directory, hashes files, invokes the parser and type inference functions, and upserts document records in the database. Handles four operations: add (new files), update (changed files), skip (unchanged files), and delete (removed files). Returns a SyncResult with counts for each operation. This is the highest-complexity story in EP0002 and integrates all other EP0002 components.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Add new documents | 5 new .md files inserted with correct fields |
| AC2 | Update changed documents | Changed file hash triggers re-parse and DB update |
| AC3 | Skip unchanged documents | Same hash skips re-parse |
| AC4 | Delete removed documents | Missing filesystem file triggers DB record deletion |
| AC5 | Sync status and timestamp | sync_status set to "synced", last_synced_at updated |

---

## Technical Context

### Language & Framework
- **Primary Language:** Python 3.12+
- **Framework:** FastAPI >=0.115.0 (for DB session dependency)
- **Test Framework:** pytest >=8.0.0 with pytest-asyncio

### Relevant Best Practices
- Type hints on all public functions
- pathlib for filesystem operations
- Specific exception handling (no bare except)
- Logging module (not print)
- Ruff for linting and formatting
- async/await for database operations

### Library Documentation (Context7)

| Library | Context7 ID | Key Patterns |
|---------|-------------|--------------|
| SQLAlchemy | /websites/sqlalchemy_en_21 | AsyncSession, select(), session.execute(), session.add() |
| pathlib | stdlib | Path.glob('**/*.md'), Path.relative_to(), Path.read_bytes() |
| hashlib | stdlib | hashlib.sha256(content).hexdigest() |

### Existing Patterns

US0001 established database patterns (async engine, session, models). US0003 created a sync endpoint stub. This story implements the actual sync logic.

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** Service layer with clear input/output contract (SyncResult), 11 edge cases, and database + filesystem interactions. Mocking the parser and type inference functions keeps tests focused on orchestration logic.

### Test Priority
1. SyncResult dataclass and counts
2. Add new documents (AC1)
3. Skip unchanged documents (AC3)
4. Update changed documents (AC2)
5. Delete removed documents (AC4)
6. Sync status updates (AC5)
7. Error handling (unreadable files, DB errors)
8. Mixed operations (add + update + skip + delete in one sync)

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Define SyncResult dataclass | `backend/src/sdlc_lens/services/sync.py` | - | [ ] |
| 2 | Create Document SQLAlchemy model | `backend/src/sdlc_lens/models/document.py` | - | [ ] |
| 3 | Create Alembic migration for documents table | `backend/alembic/versions/` | 2 | [ ] |
| 4 | Implement filesystem walk (pathlib glob **/*.md) | `backend/src/sdlc_lens/services/sync.py` | 1 | [ ] |
| 5 | Implement hash computation utility | `backend/src/sdlc_lens/utils/hashing.py` | - | [ ] |
| 6 | Implement add logic (new file, parse + insert) | `backend/src/sdlc_lens/services/sync.py` | 2, 4, 5 | [ ] |
| 7 | Implement skip logic (same hash, no-op) | `backend/src/sdlc_lens/services/sync.py` | 5, 6 | [ ] |
| 8 | Implement update logic (different hash, re-parse + update) | `backend/src/sdlc_lens/services/sync.py` | 6 | [ ] |
| 9 | Implement delete logic (missing file, delete record) | `backend/src/sdlc_lens/services/sync.py` | 6 | [ ] |
| 10 | Implement FTS5 index calls (delegate to US0010) | `backend/src/sdlc_lens/services/sync.py` | 6, 9 | [ ] |
| 11 | Implement sync status management | `backend/src/sdlc_lens/services/sync.py` | 6 | [ ] |
| 12 | Implement error handling and rollback | `backend/src/sdlc_lens/services/sync.py` | 11 | [ ] |
| 13 | Write unit and integration tests | `backend/tests/test_sync.py` | 6-12 | [ ] |

### Parallel Execution Groups

| Group | Tasks | Prerequisite |
|-------|-------|--------------|
| Foundation | 1, 2, 3, 5 | None |
| Core Sync | 4, 6, 7, 8, 9 | Group: Foundation |
| Integration | 10, 11, 12 | Group: Core Sync |
| Tests | 13 | Group: Integration |

---

## Implementation Phases

### Phase 1: Data Model & Utilities
**Goal:** Document model, migration, and hash utility

- [ ] Create `backend/src/sdlc_lens/models/document.py` - Document model with columns: project_id, doc_type, doc_id, title, status, owner, priority, story_points, epic, metadata (JSON), content, file_path, file_hash, synced_at
- [ ] Create Alembic migration for documents table with unique constraint (project_id, file_path)
- [ ] Create `backend/src/sdlc_lens/utils/hashing.py` - compute_file_hash(content: bytes) -> str
- [ ] Define `SyncResult` dataclass in `services/sync.py`

**Files:**
- `backend/src/sdlc_lens/models/document.py` - Document ORM model
- `backend/alembic/versions/002_create_documents_table.py` - Migration
- `backend/src/sdlc_lens/utils/hashing.py` - Hash utility
- `backend/src/sdlc_lens/services/sync.py` - SyncResult definition

### Phase 2: Sync Orchestration
**Goal:** Implement the 9-step sync algorithm

- [ ] Implement `sync_project(project_id, sdlc_path, db)` function
- [ ] Step 1: Set project sync_status = "syncing"
- [ ] Step 2: Walk sdlc_path with Path.glob('**/*.md'), skip _index.md
- [ ] Step 3: Build filesystem dict {relative_path: sha256_hash}
- [ ] Step 4: Load existing documents from DB for project
- [ ] Step 5a: New files - call parser + inference, INSERT document
- [ ] Step 5b: Changed files - call parser, UPDATE document
- [ ] Step 5c: Unchanged files - SKIP
- [ ] Step 6: DB records not in filesystem - DELETE
- [ ] Step 7: Update FTS5 index (call fts module functions)
- [ ] Step 8: Set sync_status = "synced", last_synced_at = now()
- [ ] Step 9: On error - set sync_status = "error", sync_error = message
- [ ] Handle unreadable files: log warning, skip, continue
- [ ] Handle UTF-8 decode failure: log warning, skip
- [ ] Strip UTF-8 BOM before parsing

**Files:**
- `backend/src/sdlc_lens/services/sync.py` - Full sync implementation

### Phase 3: Testing
**Goal:** Integration tests covering all AC and edge cases

- [ ] Create `backend/tests/test_sync.py`
- [ ] Create filesystem fixtures using tmp_path
- [ ] Mock parser and inference functions for isolated orchestration tests
- [ ] Test add, update, skip, delete operations individually
- [ ] Test mixed operations in a single sync
- [ ] Test sync status transitions
- [ ] Test error handling scenarios

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | Sync adds 5 new docs with correct fields | `tests/test_sync.py` | Pending |
| AC2 | Changed hash triggers re-parse and update | `tests/test_sync.py` | Pending |
| AC3 | Same hash skips re-parse | `tests/test_sync.py` | Pending |
| AC4 | Missing file triggers DB deletion | `tests/test_sync.py` | Pending |
| AC5 | sync_status and last_synced_at updated | `tests/test_sync.py` | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | Unreadable file (permission denied) | Catch PermissionError, log warning, increment errors, continue | Phase 2 |
| 2 | Empty sdlc-studio directory | Return SyncResult(0, 0, 0, 0, 0) with sync_status "synced" | Phase 2 |
| 3 | Binary file with .md extension | Catch UnicodeDecodeError on UTF-8 decode, skip file | Phase 2 |
| 4 | Extremely large file (>1MB) | No size limit; parse normally | Phase 2 |
| 5 | Subdirectory with no .md files | Walk continues; no error | Phase 2 |
| 6 | File added and deleted between syncs | Not seen; filesystem state at sync time is truth | Phase 2 |
| 7 | UTF-8 BOM in file content | Strip BOM (\ufeff) before parsing | Phase 2 |
| 8 | Symlinked .md file | pathlib follows symlinks by default | Phase 2 |
| 9 | Same doc_id in different subdirectories | file_path differentiates; unique constraint on (project_id, file_path) | Phase 2 |
| 10 | Database error during upsert | Rollback transaction, set sync_status "error" | Phase 2 |
| 11 | Thousands of files | Sequential processing; no parallelism needed | Phase 2 |

**Coverage:** 11/11 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Sync takes too long for large projects | Medium | Hash-based skip keeps re-sync fast; only new/changed files parsed |
| Transaction too large for bulk upsert | Low | SQLite handles thousands of rows in a single transaction |
| Parser or inference function raises unexpectedly | Medium | Wrap per-file processing in try/except; log and continue |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit and integration tests written and passing
- [ ] Edge cases handled
- [ ] Code follows Python best practices (type hints, pathlib, async/await)
- [ ] Ruff linting passes
- [ ] sync_project is importable and callable from the API layer

---

## Notes

- This story integrates US0006 (parser), US0011 (inference), US0008 (hashing), US0009 (deletion), and US0010 (FTS5).
- The sync service should be designed to allow parser and inference functions to be imported, keeping the orchestration logic testable.
- The Document model will be shared across multiple stories and should be complete from the start (all columns from TRD).
- The sync endpoint stub from US0003 will call sync_project and return the SyncResult.
