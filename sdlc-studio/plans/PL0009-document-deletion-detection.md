# PL0009: Document Deletion Detection - Implementation Plan

> **Status:** Complete
> **Story:** [US0009: Document Deletion Detection](../stories/US0009-document-deletion-detection.md)
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Created:** 2026-02-17
> **Language:** Python

## Overview

Implement deletion detection within the sync service: compare filesystem paths against database records and hard-delete any database records whose files no longer exist. Also removes corresponding FTS5 index entries. This runs as step 6 of the sync algorithm, after all adds/updates/skips are processed.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Detect and delete | Missing filesystem file triggers DB record removal; others intact |
| AC2 | FTS5 cleanup | Deleted document's FTS5 entry also removed |
| AC3 | Bulk deletion | 20 deleted files result in all 20 DB records removed |
| AC4 | No deletion without sync | DB unchanged until sync runs |

---

## Technical Context

### Language & Framework
- **Primary Language:** Python 3.12+
- **Framework:** SQLAlchemy async
- **Test Framework:** pytest >=8.0.0 with pytest-asyncio

### Relevant Best Practices
- Type hints on all public functions
- Set operations for path comparison (O(n) not O(n*m))
- Ruff for linting and formatting

### Library Documentation (Context7)

| Library | Context7 ID | Key Patterns |
|---------|-------------|--------------|
| SQLAlchemy | /websites/sqlalchemy_en_21 | session.execute(select()), session.delete(), bulk operations |

### Existing Patterns

Deletion logic is part of the sync service (US0007). FTS5 cleanup uses functions from the FTS module (US0010).

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** Clear algorithm with set comparison, 5 edge cases, and testable DB assertions. Tests verify correct records deleted and correct records retained.

### Test Priority
1. Single file deletion detected
2. Remaining documents unaffected
3. FTS5 entry removed for deleted document
4. Bulk deletion (multiple files)
5. No deletion without sync trigger
6. Edge cases (all files deleted, file moved, DB error)

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Implement deletion detection in sync service | `backend/src/sdlc_lens/services/sync.py` | US0007 | [ ] |
| 2 | Integrate FTS5 cleanup for deleted documents | `backend/src/sdlc_lens/services/sync.py` | US0010 | [ ] |
| 3 | Write deletion detection integration tests | `backend/tests/test_sync.py` | 1, 2 | [ ] |

### Parallel Execution Groups

| Group | Tasks | Prerequisite |
|-------|-------|--------------|
| Deletion Logic | 1, 2 | US0007 sync service, US0010 FTS module |
| Tests | 3 | Group: Deletion Logic |

---

## Implementation Phases

### Phase 1: Deletion Detection Logic
**Goal:** Detect and remove orphaned database records

- [ ] Build set of relative file paths from filesystem walk result
- [ ] Query all document file_paths for project from database
- [ ] Compute orphaned paths: db_paths - filesystem_paths
- [ ] For each orphaned path: DELETE document record
- [ ] For each deleted document: call fts_delete to remove FTS5 entry
- [ ] Increment SyncResult.deleted counter for each deletion

**Files:**
- `backend/src/sdlc_lens/services/sync.py` - Deletion logic within sync_project

### Phase 2: Testing
**Goal:** Verify deletion behaviour

- [ ] Test single file deletion (US0002.md removed, US0001 and US0003 intact)
- [ ] Test FTS5 entry removed for deleted document
- [ ] Test bulk deletion (20 files from stories/ removed)
- [ ] Test all files deleted results in project with 0 documents
- [ ] Test file moved (old path deleted, new path added)
- [ ] Test no deletion without sync trigger

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | Delete US0002, verify US0001/US0003 intact | `tests/test_sync.py` | Pending |
| AC2 | Verify FTS5 MATCH no longer returns deleted doc | `tests/test_sync.py` | Pending |
| AC3 | Delete 20 docs, verify all removed | `tests/test_sync.py` | Pending |
| AC4 | No sync triggers no DB change | `tests/test_sync.py` | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | All files deleted from directory | All documents deleted; project record remains with 0 docs | Phase 1 |
| 2 | File moved to different subdirectory | Old path deleted + new path added (handled by add + delete) | Phase 1 |
| 3 | File renamed | Old record deleted + new record added | Phase 1 |
| 4 | DB error mid-batch | Transaction rollback; sync_status set to "error" | Phase 1 |
| 5 | Project directory itself deleted | Sync fails at walk stage; sync_status "error", no deletions | Phase 1 |

**Coverage:** 5/5 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Accidental bulk deletion (filesystem temporarily unavailable) | High | Sync fails at walk stage if directory does not exist; no deletions occur |
| FTS5 cleanup failure leaves stale index entries | Low | fts_rebuild() available for manual recovery |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Integration tests written and passing
- [ ] Edge cases handled
- [ ] FTS5 entries cleaned for all deletions
- [ ] Ruff linting passes

---

## Notes

- Deletion logic is part of the sync_project function in sync.py, not a separate module.
- The set comparison approach (db_paths - filesystem_paths) is O(n) and handles thousands of documents efficiently.
- Hard delete means no undo - the filesystem is the authoritative source.
