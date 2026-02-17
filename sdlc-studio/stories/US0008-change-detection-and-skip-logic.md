# US0008: Change Detection via SHA-256 Hashing

> **Status:** Done
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** unchanged files to be skipped during re-sync
**So that** repeated syncs are fast and only process what has actually changed

## Context

### Persona Reference
**Darren** - Triggers sync frequently after running sdlc-studio commands.
[Full persona details](../personas.md#darren)

### Background
When re-syncing a project, most documents will not have changed. By computing a SHA-256 hash of each file's content and comparing it with the stored hash, the sync service can skip unchanged files entirely. This makes re-sync O(n) hash comparisons rather than O(n) full parses.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| Epic | Performance | Re-sync (no changes) < 2s | Hash comparison must be fast |
| TRD | Tech Stack | Python hashlib for SHA-256 | Standard library, no external deps |
| TRD | Data Model | file_hash TEXT NOT NULL on documents table | Hash stored per document |

---

## Acceptance Criteria

### AC1: Hash computation for new files
- **Given** a new .md file with content "# Test\n\nBody text"
- **When** the sync service processes this file
- **Then** it computes the SHA-256 hash of the file content and stores it in the file_hash column

### AC2: Skip unchanged files
- **Given** a document in the database with file_hash "a1b2c3..." and the filesystem file produces the same hash
- **When** sync runs
- **Then** the document is skipped (not re-parsed, not updated) and the skip count increments

### AC3: Detect changed files
- **Given** a document in the database with file_hash "a1b2c3..." and the filesystem file now produces hash "d4e5f6..."
- **When** sync runs
- **Then** the document is re-parsed and updated with new content, metadata, and file_hash

### AC4: Re-sync performance
- **Given** a project with 100 synced documents and no changes
- **When** sync runs
- **Then** sync completes in < 2 seconds (hash comparisons only, no parsing)

---

## Scope

### In Scope
- SHA-256 hash computation from file content bytes
- Hash comparison between filesystem and database
- Skip logic that avoids re-parsing unchanged files
- file_hash column storage on document records

### Out of Scope
- Full sync orchestration (US0007)
- Parser logic (US0006)
- Using file modification time instead of content hash (hash is authoritative)

---

## Technical Notes

### Hash Algorithm
```python
import hashlib

def compute_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
```

### Data Requirements
- file_hash: TEXT NOT NULL on documents table
- Hash computed from raw file bytes (not decoded text) for consistency
- Hash comparison: simple string equality check

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| File content identical but encoding differs (BOM added) | Different hash; file re-parsed (correct behaviour) |
| File touched (mtime changed) but content identical | Same hash; file skipped (hash-based, not mtime-based) |
| Hash collision (astronomically unlikely) | File skipped incorrectly; acceptable risk for SHA-256 |
| Empty file (0 bytes) | Valid hash computed; parsed as empty document |
| Very large file (>1MB) | Hash computed normally; no streaming needed at this scale |

---

## Test Scenarios

- [ ] SHA-256 hash computed correctly for known input
- [ ] Same content produces same hash across calls
- [ ] Different content produces different hashes
- [ ] Unchanged file skipped during re-sync
- [ ] Changed file detected and re-parsed
- [ ] file_hash stored correctly in database
- [ ] Re-sync of 100 unchanged documents completes in < 2 seconds
- [ ] Empty file produces valid hash

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0007](US0007-filesystem-sync-service.md) | Service | Sync orchestration calls hash logic | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

---

## Estimation

**Story Points:** {{TBD}}
**Complexity:** Low

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial story creation from EP0002 |
