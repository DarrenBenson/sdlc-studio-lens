# TS0009: Document Deletion Detection

> **Status:** Complete
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0009 - Document Deletion Detection. Covers the deletion detection logic within the sync service that compares filesystem paths against database records and removes orphaned records. Tests are integration-level since they require database and filesystem interaction.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0009](../stories/US0009-document-deletion-detection.md) | Document Deletion Detection | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0009 | AC1 | Detect and delete removed files | TC0128, TC0131 | Covered |
| US0009 | AC2 | Delete associated FTS5 entries | TC0129 | Covered |
| US0009 | AC3 | Handle bulk deletion | TC0130 | Covered |
| US0009 | AC4 | No deletion without sync | TC0135 | Covered |

**Coverage:** 4/4 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | No | Deletion logic is tightly coupled to database operations |
| Integration | Yes | Requires database + filesystem interaction |
| E2E | No | No frontend or API layer |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Python 3.12+, pytest, pytest-asyncio, aiosqlite |
| External Services | None (SQLite in-memory for tests) |
| Test Data | Filesystem tmp_path with .md files and pre-populated database |

---

## Test Cases

### TC0128: Sync detects and removes deleted files from database

**Type:** Integration | **Priority:** Critical | **Story:** US0009 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Documents US0001, US0002, US0003 synced; US0002.md deleted from filesystem | One file missing |
| When | sync_project runs | Deletion detected |
| Then | US0002 record removed from database; US0001 and US0003 remain | Selective deletion |

**Assertions:**
- [ ] Database does not contain a record with file_path matching US0002
- [ ] Database contains records for US0001 and US0003
- [ ] SyncResult.deleted equals 1

---

### TC0129: FTS5 entries removed for deleted documents

**Type:** Integration | **Priority:** Critical | **Story:** US0009 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A document indexed in FTS5, then deleted from filesystem | FTS5 entry exists |
| When | sync_project runs (triggers deletion) | FTS5 cleaned |
| Then | FTS5 MATCH query no longer returns the deleted document | Index cleaned |

**Assertions:**
- [ ] MATCH query for the deleted document's terms returns no results
- [ ] Other indexed documents still searchable

---

### TC0130: Bulk deletion handles multiple missing files

**Type:** Integration | **Priority:** High | **Story:** US0009 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project with 50 documents; 20 files in stories/ deleted from filesystem | Bulk deletion |
| When | sync_project runs | Mass deletion detected |
| Then | All 20 story documents removed; 30 remaining documents intact | Bulk handled |

**Assertions:**
- [ ] SyncResult.deleted equals 20
- [ ] Database document count for project equals 30
- [ ] Non-story documents unaffected

---

### TC0131: Remaining documents unaffected by deletion

**Type:** Integration | **Priority:** High | **Story:** US0009 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | 5 documents synced; 2 files deleted from filesystem | Partial deletion |
| When | sync_project runs | Sync completes |
| Then | 3 remaining documents have unchanged content, metadata, and file_hash | No side effects |

**Assertions:**
- [ ] Remaining document content matches original
- [ ] Remaining document file_hash unchanged
- [ ] Remaining document metadata unchanged

---

### TC0132: Deletion count reported correctly in sync results

**Type:** Integration | **Priority:** Medium | **Story:** US0009 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | 3 files deleted from filesystem since last sync | Known deletions |
| When | sync_project runs | Sync completes |
| Then | SyncResult.deleted equals 3 | Correct count |

**Assertions:**
- [ ] SyncResult.deleted equals 3

---

### TC0133: File moved to new directory detected as delete + add

**Type:** Integration | **Priority:** Medium | **Story:** US0009 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | US0001.md moved from stories/ to archive/stories/ | File moved |
| When | sync_project runs | Move detected |
| Then | Old path record deleted, new path record added | Delete + add |

**Assertions:**
- [ ] No document with old file_path "stories/US0001..." in database
- [ ] Document exists with new file_path "archive/stories/US0001..."
- [ ] SyncResult.deleted >= 1
- [ ] SyncResult.added >= 1

---

### TC0134: All files deleted results in zero documents for project

**Type:** Integration | **Priority:** Medium | **Story:** US0009 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project with 10 documents; all .md files deleted from filesystem | Empty directory |
| When | sync_project runs | All deleted |
| Then | Project has 0 documents in database; project record still exists | Clean state |

**Assertions:**
- [ ] Document count for project equals 0
- [ ] Project record still exists in projects table
- [ ] SyncResult.deleted equals 10
- [ ] Project sync_status equals "synced"

---

### TC0135: No deletion occurs without running sync

**Type:** Integration | **Priority:** Medium | **Story:** US0009 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A synced project with 5 documents; 2 files then deleted from filesystem | Files removed |
| When | No sync is triggered (just query the database) | No sync |
| Then | All 5 document records still exist in database | DB unchanged |

**Assertions:**
- [ ] Database document count equals 5 (unchanged)
- [ ] All 5 original records present

---

## Fixtures

```yaml
project_with_three_docs:
  files:
    - "stories/US0001-register-new-project.md"
    - "stories/US0002-project-list.md"
    - "stories/US0003-trigger-sync.md"

project_with_fifty_docs:
  files: 20 story files + 10 epic files + 10 plan files + 5 test-spec files + 5 root docs

project_moved_file:
  # US0001.md moved from stories/ to archive/stories/
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0128 | Sync detects and removes deleted files | Pending | - |
| TC0129 | FTS5 entries removed for deleted docs | Pending | - |
| TC0130 | Bulk deletion handles multiple files | Pending | - |
| TC0131 | Remaining documents unaffected | Pending | - |
| TC0132 | Deletion count reported correctly | Pending | - |
| TC0133 | File moved detected as delete + add | Pending | - |
| TC0134 | All files deleted gives zero documents | Pending | - |
| TC0135 | No deletion without running sync | Pending | - |

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
| 2026-02-17 | Claude | Initial spec from US0009 story plan |
