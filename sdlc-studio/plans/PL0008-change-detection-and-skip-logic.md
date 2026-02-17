# PL0008: Change Detection and Skip Logic - Implementation Plan

> **Status:** Complete
> **Story:** [US0008: Change Detection via SHA-256 Hashing](../stories/US0008-change-detection-and-skip-logic.md)
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Created:** 2026-02-17
> **Language:** Python

## Overview

Implement SHA-256 content hashing for change detection during sync. The hash utility computes a deterministic hash from file content bytes, enabling the sync service to skip unchanged files and only re-parse documents whose content has actually changed. This ensures re-sync of 100 unchanged documents completes in under 2 seconds.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Hash computation | SHA-256 hash computed and stored for new files |
| AC2 | Skip unchanged | Same hash means file skipped, skip count incremented |
| AC3 | Detect changed | Different hash means file re-parsed and updated |
| AC4 | Re-sync performance | 100 unchanged docs re-synced in < 2 seconds |

---

## Technical Context

### Language & Framework
- **Primary Language:** Python 3.12+
- **Framework:** None (utility function)
- **Test Framework:** pytest >=8.0.0 with pytest-asyncio

### Relevant Best Practices
- Type hints on all public functions
- Standard library only (hashlib)
- Ruff for linting and formatting

### Library Documentation (Context7)

| Library | Context7 ID | Key Patterns |
|---------|-------------|--------------|
| hashlib | stdlib | hashlib.sha256(data).hexdigest() |

### Existing Patterns

Hash utility follows the same pattern as `utils/slug.py` - a small, focused utility module.

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** Pure function with deterministic output, 5 edge cases, and a performance requirement. Unit tests verify correctness; a benchmark test verifies the 2-second target.

### Test Priority
1. Hash computation for known input (deterministic)
2. Same content produces same hash (idempotent)
3. Different content produces different hash
4. Integration with sync: unchanged file skipped
5. Integration with sync: changed file detected
6. Performance: 100 docs in < 2s
7. Edge cases (empty file, BOM)

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Implement compute_file_hash function | `backend/src/sdlc_lens/utils/hashing.py` | - | [ ] |
| 2 | Write hash computation unit tests | `backend/tests/test_hashing.py` | 1 | [ ] |
| 3 | Integrate hash into sync add logic | `backend/src/sdlc_lens/services/sync.py` | 1 | [ ] |
| 4 | Integrate hash into sync skip/update logic | `backend/src/sdlc_lens/services/sync.py` | 3 | [ ] |
| 5 | Write sync integration tests for skip/update | `backend/tests/test_sync.py` | 4 | [ ] |
| 6 | Write performance benchmark test | `backend/tests/test_sync.py` | 4 | [ ] |

### Parallel Execution Groups

| Group | Tasks | Prerequisite |
|-------|-------|--------------|
| Hash Utility | 1, 2 | None |
| Sync Integration | 3, 4 | Group: Hash Utility |
| Tests | 5, 6 | Group: Sync Integration |

---

## Implementation Phases

### Phase 1: Hash Utility
**Goal:** Implement and test the hash computation function

- [ ] Create `backend/src/sdlc_lens/utils/hashing.py`
- [ ] Implement `compute_file_hash(content: bytes) -> str` using hashlib.sha256
- [ ] Hash computed from raw bytes (not decoded text)

**Files:**
- `backend/src/sdlc_lens/utils/hashing.py` - Hash utility

### Phase 2: Sync Integration
**Goal:** Wire hash comparison into sync decision logic

- [ ] In sync service: compute hash for each filesystem file
- [ ] Compare computed hash with stored file_hash from DB
- [ ] Same hash: skip (increment skip count)
- [ ] Different hash: re-parse and update (increment update count)
- [ ] New file: hash stored with insert (increment add count)

**Files:**
- `backend/src/sdlc_lens/services/sync.py` - Hash comparison in sync loop

### Phase 3: Testing
**Goal:** Verify correctness and performance

- [ ] Create `backend/tests/test_hashing.py` - Unit tests
- [ ] Test known input produces expected hash
- [ ] Test same content produces same hash
- [ ] Test different content produces different hash
- [ ] Test empty file produces valid hash
- [ ] Write performance test: create 100 tmp_path files, sync, modify none, re-sync, assert < 2s

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | Hash stored in file_hash column | `tests/test_sync.py` | Pending |
| AC2 | Unchanged file skipped | `tests/test_sync.py` | Pending |
| AC3 | Changed file re-parsed | `tests/test_sync.py` | Pending |
| AC4 | 100 unchanged docs < 2s | `tests/test_sync.py` | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | BOM added to file content | Different bytes produce different hash; re-parsed (correct) | Phase 2 |
| 2 | mtime changed but content identical | Same bytes produce same hash; skipped (correct) | Phase 2 |
| 3 | Hash collision (SHA-256) | Acceptable risk; astronomically unlikely | Phase 1 |
| 4 | Empty file (0 bytes) | Valid hash computed (e3b0c44...) | Phase 1 |
| 5 | Very large file (>1MB) | Hash computed normally; no streaming needed | Phase 1 |

**Coverage:** 5/5 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance target missed | Medium | Hash comparison is O(1) per file; parsing skipped entirely |
| Hash from raw bytes vs decoded text inconsistency | Low | Always hash raw bytes; documented in function docstring |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit tests written and passing
- [ ] Performance benchmark passing (< 2 seconds)
- [ ] Edge cases handled
- [ ] Ruff linting passes

---

## Notes

- The hash function is deliberately simple: `hashlib.sha256(content).hexdigest()`.
- Hashing raw bytes (not decoded text) ensures encoding changes (e.g. BOM addition) are detected.
- The 2-second performance target assumes local SSD storage and SQLite in-memory for tests.
