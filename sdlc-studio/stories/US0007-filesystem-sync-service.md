# US0007: Filesystem Sync Service

> **Status:** Done
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** sync to walk the sdlc-studio directory, parse documents, and persist them to the database
**So that** the dashboard has up-to-date, searchable document data

## Context

### Persona Reference
**Darren** - Triggers sync after running sdlc-studio commands to refresh dashboard data.
[Full persona details](../personas.md#darren)

### Background
The sync service is the core data pipeline: it walks the filesystem, computes file hashes, invokes the parser, and upserts document records. It handles four behaviours: add (new files), update (changed files), skip (unchanged files), and delete (removed files). This story covers the orchestration; the parser is US0006 and the FTS5 indexing is US0010.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Architecture | Read-only filesystem access | Never write to project directories |
| PRD | Business Logic | Hard delete on sync | Files missing from filesystem are deleted from DB |
| Epic | Performance | Sync 100 docs < 10s | Efficient I/O and batch DB writes |
| TRD | Tech Stack | Python pathlib + hashlib | Filesystem walking and SHA-256 hashing |

---

## Acceptance Criteria

### AC1: Add new documents
- **Given** a project with sdlc-studio directory containing 5 new .md files not in the database
- **When** sync runs for the project
- **Then** all 5 documents are parsed and inserted into the documents table with correct doc_type, doc_id, title, metadata, content, file_path, and file_hash

### AC2: Update changed documents
- **Given** a document EP0001.md exists in the database with hash "abc123"
- **When** the file content has changed (new hash "def456") and sync runs
- **Then** the document record is updated with new content, metadata, and file_hash

### AC3: Skip unchanged documents
- **Given** a document EP0001.md exists in the database with hash "abc123"
- **When** the file content has not changed (same hash "abc123") and sync runs
- **Then** the document record is not modified and the file is not re-parsed

### AC4: Delete removed documents
- **Given** document US0099.md exists in the database but the file has been deleted from the filesystem
- **When** sync runs for the project
- **Then** the document record is removed from the database

### AC5: Sync updates project status and timestamp
- **Given** a project with sync_status "never_synced"
- **When** sync completes successfully
- **Then** sync_status is "synced" and last_synced_at is set to the current timestamp

---

## Scope

### In Scope
- Recursive walk of sdlc-studio directory for `*.md` files
- SHA-256 hash computation for each file
- Compare file hash with database record to determine add/update/skip
- Invoke parser (US0006) for new and changed files
- Upsert document records in SQLite
- Delete document records for removed files
- Update project sync_status and last_synced_at
- Log warnings for unreadable files (continue sync)
- Handle empty sdlc-studio directories (complete with zero documents)

### Out of Scope
- Parser implementation (US0006)
- Document type inference (US0011)
- FTS5 index management (US0010)
- Sync trigger API endpoint (US0003)
- Change detection as a separate story (US0008) - integrated here
- Deletion detection as a separate story (US0009) - integrated here

---

## Technical Notes

### API Contract (Internal)
```python
async def sync_project(project_id: int, sdlc_path: str, db: AsyncSession) -> SyncResult:
    """Sync all documents from a project's sdlc-studio directory.

    Returns:
        SyncResult with counts: added, updated, skipped, deleted, errors.
    """
```

### Data Requirements
- Documents table: project_id, doc_type, doc_id, title, status, owner, priority, story_points, epic, metadata (JSON), content, file_path, file_hash, synced_at
- Unique constraint: (project_id, doc_type, doc_id)
- Upsert on unique constraint match (update if exists, insert if not)
- Batch operations for efficiency (commit after all files processed)

### Sync Algorithm
```
1. Set project sync_status = "syncing"
2. Walk sdlc_path recursively for *.md files
3. Build dict of filesystem files: {relative_path: sha256_hash}
4. Load existing documents for project from DB: {relative_path: file_hash}
5. For each filesystem file:
   a. If not in DB → parse and INSERT (add)
   b. If in DB with different hash → parse and UPDATE (update)
   c. If in DB with same hash → SKIP
6. For each DB record not in filesystem → DELETE (delete)
7. Update FTS5 index (delegate to US0010)
8. Set project sync_status = "synced", last_synced_at = now()
9. On error: set sync_status = "error", sync_error = message
```

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Unreadable file (permission denied) | Log warning with filename, skip file, continue sync |
| Empty sdlc-studio directory (no .md files) | Complete successfully with 0 added, 0 updated, 0 deleted |
| Binary file with .md extension | Attempt to read as UTF-8; if decode fails, log warning and skip |
| Extremely large file (>1MB) | Parse normally; no size limit enforced in v1.0 |
| Subdirectory with no .md files | Walk continues into deeper directories; no error |
| File added and deleted between syncs | Not seen; filesystem state at sync time is truth |
| UTF-8 BOM in file content | Strip BOM before parsing |
| Symlinked .md file | Follow symlink, read target content |
| Same doc_id in different subdirectories | file_path differentiates; unique constraint includes path |
| Database error during upsert | Rollback transaction, set sync_status to "error" |
| Thousands of files (stress case) | Process sequentially; no parallelism needed for 100-2000 docs |

---

## Test Scenarios

- [ ] Sync adds new documents found on filesystem
- [ ] Sync updates documents with changed file hash
- [ ] Sync skips documents with unchanged file hash
- [ ] Sync removes documents deleted from filesystem
- [ ] Sync updates sync_status to "synced" on success
- [ ] Sync updates last_synced_at timestamp
- [ ] Sync sets sync_status to "error" on failure
- [ ] Sync handles empty directory (zero documents)
- [ ] Sync handles unreadable files (skip and continue)
- [ ] Sync correctly computes SHA-256 hash
- [ ] Sync populates all document fields from parser output
- [ ] Sync handles re-sync (mix of add, update, skip, delete)
- [ ] SyncResult contains correct counts for each operation

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0001](US0001-register-new-project.md) | Schema | Projects table | Draft |
| [US0006](US0006-blockquote-frontmatter-parser.md) | Service | Parser function | Draft |
| [US0011](US0011-document-type-and-id-inference.md) | Service | Type/ID inference function | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Documents table Alembic migration | Infrastructure | Not Started |

---

## Estimation

**Story Points:** {{TBD}}
**Complexity:** High

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial story creation from EP0002 |
