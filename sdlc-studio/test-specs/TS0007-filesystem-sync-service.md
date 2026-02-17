# TS0007: Filesystem Sync Service

> **Status:** Complete
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0007 - Filesystem Sync Service. Covers the `sync_project()` async function that walks a project's sdlc-studio directory, hashes files, parses documents, and manages database records. Tests span unit (SyncResult, mocked parser) and integration (database + filesystem via tmp_path) levels.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0007](../stories/US0007-filesystem-sync-service.md) | Filesystem Sync Service | Critical |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0007 | AC1 | Add new documents | TC0097, TC0107 | Covered |
| US0007 | AC2 | Update changed documents | TC0098 | Covered |
| US0007 | AC3 | Skip unchanged documents | TC0099 | Covered |
| US0007 | AC4 | Delete removed documents | TC0100 | Covered |
| US0007 | AC5 | Sync status and timestamp | TC0101, TC0102, TC0103 | Covered |

**Coverage:** 5/5 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | Yes | SyncResult dataclass, individual operation logic |
| Integration | Yes | Database + filesystem interaction via tmp_path |
| E2E | No | No frontend; API layer tested separately in US0003 |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Python 3.12+, pytest, pytest-asyncio, aiosqlite |
| External Services | None (SQLite in-memory for tests) |
| Test Data | Filesystem tmp_path with .md files |

---

## Test Cases

### TC0097: Sync adds new documents found on filesystem

**Type:** Integration | **Priority:** Critical | **Story:** US0007 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project with 5 .md files in tmp_path, no documents in DB | Empty database |
| When | sync_project(project_id, sdlc_path, db) is called | Sync runs |
| Then | 5 documents inserted into database | All files imported |

**Assertions:**
- [ ] Database contains 5 document records for the project
- [ ] SyncResult.added equals 5
- [ ] SyncResult.updated equals 0
- [ ] SyncResult.skipped equals 0
- [ ] SyncResult.deleted equals 0

---

### TC0098: Sync updates documents with changed file hash

**Type:** Integration | **Priority:** Critical | **Story:** US0007 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A previously synced project with EP0001.md (hash "abc123") | Existing document |
| When | EP0001.md content is changed (new hash "def456") and sync runs | Content changed |
| Then | Document record updated with new content, metadata, and file_hash | Record updated |

**Assertions:**
- [ ] Document file_hash in DB equals the new hash
- [ ] Document content in DB reflects the new file content
- [ ] SyncResult.updated equals 1

---

### TC0099: Sync skips documents with unchanged file hash

**Type:** Integration | **Priority:** Critical | **Story:** US0007 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A previously synced project with EP0001.md, file unchanged | Same content |
| When | sync_project runs again | Re-sync |
| Then | Document not re-parsed, record not modified | Skipped |

**Assertions:**
- [ ] SyncResult.skipped equals number of unchanged files
- [ ] SyncResult.updated equals 0
- [ ] Document synced_at timestamp unchanged

---

### TC0100: Sync removes documents deleted from filesystem

**Type:** Integration | **Priority:** Critical | **Story:** US0007 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A previously synced project; US0099.md deleted from filesystem | File removed |
| When | sync_project runs | Deletion detected |
| Then | US0099 document record removed from database | Record deleted |

**Assertions:**
- [ ] Database no longer contains a record for US0099
- [ ] Other document records remain intact
- [ ] SyncResult.deleted equals 1

---

### TC0101: Sync updates sync_status to "synced" on success

**Type:** Integration | **Priority:** Critical | **Story:** US0007 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project with sync_status "never_synced" | Initial state |
| When | sync_project completes successfully | Sync succeeds |
| Then | Project sync_status is "synced" | Status updated |

**Assertions:**
- [ ] Project record sync_status equals "synced"

---

### TC0102: Sync updates last_synced_at timestamp

**Type:** Integration | **Priority:** High | **Story:** US0007 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project with last_synced_at as None | Never synced |
| When | sync_project completes successfully | Sync succeeds |
| Then | last_synced_at is set to a recent timestamp | Timestamp updated |

**Assertions:**
- [ ] Project last_synced_at is not None
- [ ] last_synced_at is within the last few seconds

---

### TC0103: Sync sets sync_status to "error" on failure

**Type:** Integration | **Priority:** High | **Story:** US0007 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project with an invalid sdlc_path (directory does not exist) | Bad path |
| When | sync_project is called | Sync fails |
| Then | sync_status is "error" and sync_error contains a message | Error recorded |

**Assertions:**
- [ ] Project sync_status equals "error"
- [ ] Project sync_error is not None and not empty

---

### TC0104: Sync handles empty directory (zero documents)

**Type:** Integration | **Priority:** Medium | **Story:** US0007 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project pointing to an empty directory (no .md files) | Empty directory |
| When | sync_project runs | Sync completes |
| Then | SyncResult shows all zeros, sync_status is "synced" | Handled gracefully |

**Assertions:**
- [ ] SyncResult.added equals 0
- [ ] SyncResult.deleted equals 0
- [ ] Project sync_status equals "synced"

---

### TC0105: Sync handles unreadable files (skip and continue)

**Type:** Integration | **Priority:** Medium | **Story:** US0007 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A directory with 3 .md files, one with restricted permissions | Unreadable file |
| When | sync_project runs | Sync continues |
| Then | 2 documents added, 1 error logged, sync completes | Partial sync |

**Assertions:**
- [ ] SyncResult.added equals 2
- [ ] SyncResult.errors equals 1
- [ ] Project sync_status equals "synced" (partial success)

---

### TC0106: Sync correctly computes SHA-256 hash

**Type:** Unit | **Priority:** High | **Story:** US0007 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A file with known content "# Test\n\nBody" | Known input |
| When | Hash is computed during sync | Hash calculated |
| Then | Stored file_hash matches expected SHA-256 hex digest | Correct hash |

**Assertions:**
- [ ] file_hash equals hashlib.sha256(b"# Test\n\nBody").hexdigest()

---

### TC0107: Sync populates all document fields from parser output

**Type:** Integration | **Priority:** High | **Story:** US0007 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A .md file with frontmatter: status, owner, priority, story_points, epic | Full metadata |
| When | sync_project runs | Document created |
| Then | All fields populated: doc_type, doc_id, title, status, owner, priority, story_points, epic, content, file_path, file_hash | Complete record |

**Assertions:**
- [ ] doc_type is set (from inference)
- [ ] doc_id is set (from inference)
- [ ] title is set (from parser)
- [ ] status, owner, priority are set (from parser metadata)
- [ ] content is set (body from parser)
- [ ] file_path is the relative path
- [ ] file_hash is a 64-character hex string

---

### TC0108: Sync handles re-sync with mixed operations

**Type:** Integration | **Priority:** High | **Story:** US0007 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A synced project; 1 file added, 1 file changed, 1 file deleted, 2 unchanged | Mixed state |
| When | sync_project runs again | Re-sync |
| Then | SyncResult: added=1, updated=1, deleted=1, skipped=2 | Correct counts |

**Assertions:**
- [ ] SyncResult.added equals 1
- [ ] SyncResult.updated equals 1
- [ ] SyncResult.deleted equals 1
- [ ] SyncResult.skipped equals 2

---

### TC0109: SyncResult contains correct counts for each operation

**Type:** Unit | **Priority:** Medium | **Story:** US0007 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A SyncResult dataclass | Data structure |
| When | Inspecting fields | All fields present |
| Then | Fields: added, updated, skipped, deleted, errors are all integers | Correct types |

**Assertions:**
- [ ] SyncResult has fields: added, updated, skipped, deleted, errors
- [ ] All fields default to 0
- [ ] All fields are integers

---

## Fixtures

```yaml
project_with_files:
  sdlc_path: "<tmp_path>/sdlc-studio"
  files:
    - "epics/EP0001-project-management.md"
    - "stories/US0001-register-new-project.md"
    - "stories/US0002-project-list.md"
    - "prd.md"
    - "trd.md"

project_with_changed_file:
  # Initial sync with original content, then change EP0001 content

project_with_deleted_file:
  # Initial sync with US0099.md, then delete it from filesystem

project_empty:
  sdlc_path: "<tmp_path>/sdlc-studio-empty"
  files: []

project_with_unreadable_file:
  # 3 files, one with chmod 000
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0097 | Sync adds new documents | Pending | - |
| TC0098 | Sync updates changed documents | Pending | - |
| TC0099 | Sync skips unchanged documents | Pending | - |
| TC0100 | Sync removes deleted documents | Pending | - |
| TC0101 | Sync updates sync_status to "synced" | Pending | - |
| TC0102 | Sync updates last_synced_at timestamp | Pending | - |
| TC0103 | Sync sets sync_status to "error" on failure | Pending | - |
| TC0104 | Sync handles empty directory | Pending | - |
| TC0105 | Sync handles unreadable files | Pending | - |
| TC0106 | Sync correctly computes SHA-256 hash | Pending | - |
| TC0107 | Sync populates all document fields | Pending | - |
| TC0108 | Sync handles re-sync with mixed operations | Pending | - |
| TC0109 | SyncResult contains correct counts | Pending | - |

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
| 2026-02-17 | Claude | Initial spec from US0007 story plan |
