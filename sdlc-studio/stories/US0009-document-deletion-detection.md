# US0009: Document Deletion Detection

> **Status:** Done
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** files removed from the filesystem to be deleted from the database during sync
**So that** the dashboard reflects reality and does not show stale documents

## Context

### Persona Reference
**Darren** - Expects the dashboard to accurately reflect the filesystem state after sync.
[Full persona details](../personas.md#darren)

### Background
When sdlc-studio documents are deleted or moved, the sync service must detect their absence and remove corresponding database records. This is a "hard delete" - removed files are permanently deleted from the database, not soft-deleted. The filesystem is the source of truth.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Business Logic | Hard delete on sync | No soft-delete; records permanently removed |
| Epic | Data | FTS5 index must be cleaned | Deleted docs removed from search index |

---

## Acceptance Criteria

### AC1: Detect and delete removed files
- **Given** documents US0001.md, US0002.md, and US0003.md exist in the database for project "homelabcmd"
- **When** US0002.md is deleted from the filesystem and sync runs
- **Then** the US0002 record is deleted from the documents table; US0001 and US0003 remain

### AC2: Delete associated FTS5 entries
- **Given** a document being deleted has an entry in the documents_fts index
- **When** the document record is deleted
- **Then** the corresponding FTS5 entry is also removed

### AC3: Handle bulk deletion
- **Given** a project had 50 documents and the entire stories/ subdirectory is removed (20 files)
- **When** sync runs
- **Then** all 20 story documents are deleted from the database; remaining 30 documents unchanged

### AC4: No deletion without sync
- **Given** a file is deleted from the filesystem
- **When** no sync is triggered
- **Then** the document remains in the database (deletion only occurs during sync)

---

## Scope

### In Scope
- Compare database document records against filesystem to find deletions
- Delete document records not found on filesystem
- Delete associated FTS5 index entries
- Report deletion count in sync results

### Out of Scope
- Soft-delete or archive functionality
- Undo deletion
- Notification of deleted documents

---

## Technical Notes

### Detection Algorithm
```
1. Build set of relative file paths from filesystem walk
2. Query all document file_paths for this project from database
3. For each DB path not in filesystem set → DELETE
```

### Data Requirements
- Query: SELECT file_path FROM documents WHERE project_id = ?
- Delete by: (project_id, file_path) or document id
- FTS5 cleanup: DELETE FROM documents_fts WHERE rowid = ?

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| All files deleted from sdlc-studio directory | All documents deleted; project remains with 0 documents |
| File moved to different subdirectory | Old path deleted, new path added (different file_path = different record) |
| File renamed (e.g., US0001.md to US0001-old.md) | Old record deleted, new record added |
| Deletion fails mid-batch (DB error) | Transaction rollback; sync_status set to "error" |
| Project directory itself is deleted | Sync fails at walk stage; sync_status "error", no deletions |

---

## Test Scenarios

- [ ] Sync detects and removes deleted files from database
- [ ] FTS5 entries removed for deleted documents
- [ ] Bulk deletion handles multiple missing files
- [ ] Remaining documents unaffected by deletion
- [ ] Deletion count reported correctly in sync results
- [ ] File moved to new directory detected as delete + add
- [ ] All files deleted results in zero documents for project
- [ ] No deletion occurs without running sync

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0007](US0007-filesystem-sync-service.md) | Service | Sync orchestration | Draft |
| [US0010](US0010-fts5-search-index-management.md) | Service | FTS5 cleanup function | Draft |

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
