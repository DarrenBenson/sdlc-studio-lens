# TS0008: Change Detection and Skip Logic

> **Status:** Complete
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0008 - Change Detection via SHA-256 Hashing. Covers the `compute_file_hash()` utility function and its integration with the sync service skip/update logic. Tests span unit (hash computation) and integration (sync with database) levels, including a performance benchmark.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0008](../stories/US0008-change-detection-and-skip-logic.md) | Change Detection via SHA-256 Hashing | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0008 | AC1 | Hash computed and stored for new files | TC0110, TC0115 | Covered |
| US0008 | AC2 | Same hash skips file | TC0111, TC0113 | Covered |
| US0008 | AC3 | Different hash triggers re-parse | TC0112, TC0114 | Covered |
| US0008 | AC4 | 100 unchanged docs re-synced in < 2s | TC0116 | Covered |

**Coverage:** 4/4 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | Yes | Hash computation is a pure function |
| Integration | Yes | Skip/update logic requires database and filesystem |
| Performance | Yes | AC4 requires benchmark under 2 seconds |
| E2E | No | No frontend or API layer |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Python 3.12+, pytest, pytest-asyncio, aiosqlite |
| External Services | None (SQLite in-memory for tests) |
| Test Data | Inline byte strings and tmp_path files |

---

## Test Cases

### TC0110: SHA-256 hash computed correctly for known input

**Type:** Unit | **Priority:** Critical | **Story:** US0008 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Known content bytes b"# Test\n\nBody text" | Deterministic input |
| When | compute_file_hash(content) is called | Hash computed |
| Then | Result matches pre-computed SHA-256 hex digest | Correct hash |

**Assertions:**
- [ ] Result equals hashlib.sha256(b"# Test\n\nBody text").hexdigest()
- [ ] Result is a 64-character lowercase hex string

---

### TC0111: Same content produces same hash across calls

**Type:** Unit | **Priority:** High | **Story:** US0008 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Same content bytes | Identical input |
| When | compute_file_hash called twice with identical bytes | Two hashes |
| Then | Both results are identical | Deterministic |

**Assertions:**
- [ ] compute_file_hash(data) == compute_file_hash(data)

---

### TC0112: Different content produces different hashes

**Type:** Unit | **Priority:** High | **Story:** US0008 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Two different content byte strings | Different input |
| When | compute_file_hash called for each | Two hashes |
| Then | Results differ | Unique hashes |

**Assertions:**
- [ ] compute_file_hash(b"content A") != compute_file_hash(b"content B")

---

### TC0113: Unchanged file skipped during re-sync

**Type:** Integration | **Priority:** Critical | **Story:** US0008 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A synced project with 3 documents, no files changed | Same content |
| When | sync_project runs again | Re-sync |
| Then | All 3 files skipped (not re-parsed) | Efficient re-sync |

**Assertions:**
- [ ] SyncResult.skipped equals 3
- [ ] SyncResult.updated equals 0
- [ ] SyncResult.added equals 0

---

### TC0114: Changed file detected and re-parsed

**Type:** Integration | **Priority:** Critical | **Story:** US0008 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A synced project; one file's content modified | Changed content |
| When | sync_project runs again | Re-sync |
| Then | Changed file re-parsed and updated in database | Change detected |

**Assertions:**
- [ ] SyncResult.updated equals 1
- [ ] Updated document's file_hash matches the new content hash
- [ ] Updated document's content reflects new file content

---

### TC0115: file_hash stored correctly in database

**Type:** Integration | **Priority:** High | **Story:** US0008 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A new file synced to database | First sync |
| When | Querying the document record | Record exists |
| Then | file_hash is a 64-character hex string matching the file content | Hash stored |

**Assertions:**
- [ ] Document file_hash is not None
- [ ] len(file_hash) equals 64
- [ ] file_hash matches compute_file_hash(file_content_bytes)

---

### TC0116: Re-sync of 100 unchanged documents in < 2 seconds

**Type:** Performance | **Priority:** High | **Story:** US0008 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project with 100 .md files, all previously synced | Large project |
| When | sync_project runs with no file changes | Re-sync |
| Then | Sync completes in less than 2 seconds | Performance met |

**Assertions:**
- [ ] Elapsed time < 2.0 seconds
- [ ] SyncResult.skipped equals 100
- [ ] SyncResult.added equals 0
- [ ] SyncResult.updated equals 0

---

### TC0117: Empty file produces valid hash

**Type:** Unit | **Priority:** Medium | **Story:** US0008 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Empty content (0 bytes) | Edge case |
| When | compute_file_hash(b"") is called | Hash computed |
| Then | Returns the known SHA-256 of empty string | Valid hash |

**Assertions:**
- [ ] Result equals "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

---

## Fixtures

```yaml
known_content:
  bytes: b"# Test\n\nBody text"
  expected_hash: "<sha256 hex digest>"

empty_content:
  bytes: b""
  expected_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

project_100_files:
  sdlc_path: "<tmp_path>/sdlc-studio-perf"
  files: 100 generated .md files with unique content
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0110 | SHA-256 hash computed correctly | Pending | - |
| TC0111 | Same content same hash | Pending | - |
| TC0112 | Different content different hashes | Pending | - |
| TC0113 | Unchanged file skipped during re-sync | Pending | - |
| TC0114 | Changed file detected and re-parsed | Pending | - |
| TC0115 | file_hash stored correctly in database | Pending | - |
| TC0116 | Re-sync of 100 unchanged docs < 2s | Pending | - |
| TC0117 | Empty file produces valid hash | Pending | - |

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
| 2026-02-17 | Claude | Initial spec from US0008 story plan |
