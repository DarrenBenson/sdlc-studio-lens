# EP0002: Document Sync & Parsing

> **Status:** Done
> **Owner:** Darren
> **Created:** 2026-02-17
> **Target Release:** Phase 1 (Foundation)
> **Story Points:** 24

## Summary

Walk sdlc-studio project directories, parse blockquote-style frontmatter from markdown documents, detect changes via SHA-256 hashing, and persist parsed documents to SQLite with FTS5 indexing. This epic delivers the core data pipeline that all browsing, statistics, and search features depend on.

## Inherited Constraints

Constraints that flow from PRD and TRD to this Epic.

### From PRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Performance | Sync 100 documents in < 10 seconds | Parser and DB writes must be efficient |
| Architecture | Read-only filesystem access | Never write to project sdlc-studio directories |
| Business Logic | Manual sync only | Sync runs on user trigger, not automatically |
| Business Logic | Hard delete on sync | Files removed from filesystem are deleted from DB |

### From TRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Architecture | SQLite + FTS5 | FTS5 virtual table for search indexing |
| Tech Stack | Python 3.12+ (pathlib, hashlib) | Filesystem walking and hashing |
| Data Model | Documents table with 15 fields | Must populate all fields from parsed content |
| Parser | Blockquote frontmatter (`> **Key:** Value`) | Custom regex-based parser |

> **Note:** Inherited constraints MUST propagate to child Stories. Check Story templates include these constraints.

## Business Context

### Problem Statement

sdlc-studio documents contain structured metadata in blockquote frontmatter format, but this metadata is trapped in markdown files. To display documents with filtering, statistics, and search, the system must extract and index this data.

**PRD Reference:** [§5 Feature Inventory](../prd.md#5-feature-inventory)

### Value Proposition

Automatic extraction of document metadata enables filtering by type, status, and owner. Change detection means re-sync is fast (only processes modified files). FTS5 indexing enables sub-second full-text search across all documents.

### Success Metrics

| Metric | Current State | Target | Measurement Method |
|--------|---------------|--------|-------------------|
| Documents parsed per project | 0 | 10-200 | Database count after sync |
| Sync time (100 docs) | N/A | < 10 seconds | API timing |
| Re-sync time (no changes) | N/A | < 2 seconds | API timing (hash skip) |
| Metadata extraction accuracy | N/A | 100% for standard fields | Test fixtures |

## Scope

### In Scope

- Recursive directory walking for `*.md` files within sdlc-studio path
- Blockquote frontmatter parser: `> **Key:** Value` extraction
- Multi-line blockquote value handling
- Title extraction from first `#` heading
- Document ID extraction from filename pattern (EP0001, US0045, prd, etc.)
- Document type inference from filename and directory structure
- Standard field extraction: status, owner, priority, story_points, epic
- Additional metadata stored as JSON
- SHA-256 hash computation for change detection
- Skip unchanged files on re-sync (hash match)
- Detect and delete documents removed from filesystem
- Upsert document records in SQLite
- FTS5 index population (title + content)
- FTS5 index update on document change
- FTS5 index cleanup on document deletion
- Sync status state transitions (syncing → synced/error)
- Last-synced-at timestamp update
- Unreadable file handling (log warning, continue)
- Empty directory handling (complete with zero documents)

### Out of Scope

- Project registration and management (EP0001)
- Document browsing UI (EP0003)
- Statistics aggregation queries (EP0004)
- Search API endpoint (EP0005)
- YAML frontmatter parsing (sdlc-studio uses blockquote format)
- Binary file handling (only *.md)
- Symlink resolution

### Affected User Personas

- **SDLC Developer (Darren):** Sync populates the dashboard with all project documents

## Acceptance Criteria (Epic Level)

- [ ] Parser extracts all standard frontmatter fields from every sdlc-studio document type
- [ ] Parser handles multi-line blockquote values correctly
- [ ] Parser returns empty metadata for documents with no frontmatter
- [ ] Parser skips malformed lines and continues with valid ones
- [ ] Document type correctly inferred from filename (EP*, US*, BG*, PL*, TS*, prd, trd, tsd)
- [ ] SHA-256 hash computed for each file; unchanged files skipped on re-sync
- [ ] Deleted files (in DB but not on filesystem) removed during sync
- [ ] FTS5 index populated for new documents, updated for changed, cleaned for deleted
- [ ] Sync completes within 10 seconds for 100 documents
- [ ] Unreadable files logged as warnings without stopping sync
- [ ] Empty sdlc-studio directory results in zero documents synced (not an error)

## Dependencies

### Blocked By

| Dependency | Type | Status | Owner | Notes |
|------------|------|--------|-------|-------|
| EP0001: Project Management | Epic | Draft | Darren | Need registered projects with paths |

### Blocking

| Item | Type | Impact |
|------|------|--------|
| EP0003: Document Browsing | Epic | Cannot browse without parsed documents |
| EP0004: Dashboard & Statistics | Epic | Cannot calculate stats without document data |
| EP0005: Search | Epic | Cannot search without FTS5 index |

## Risks & Assumptions

### Assumptions

- All sdlc-studio documents use blockquote frontmatter format (`> **Key:** Value`)
- Filename patterns are consistent (EP0001.md, US0045.md, prd.md, etc.)
- Document encoding is UTF-8
- File sizes are reasonable (< 1MB per document)
- sdlc-studio directory structure follows convention (epics/, stories/, bugs/, plans/, test-specs/)

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Frontmatter format varies between doc types | Medium | Medium | Test with fixture files from real sdlc-studio output |
| Large files slow down sync | Low | Medium | Stream file reading; set reasonable size limit |
| FTS5 index grows too large | Low | Low | Acceptable for 100-2000 documents |
| Nested blockquotes confuse parser | Medium | Low | Parser stops at first non-blockquote line |

## Technical Considerations

### Architecture Impact

- Creates the documents table and FTS5 virtual table
- Establishes the sync service pattern (called from API route)
- Defines the parser module (pure function, easily testable)
- Sets up the document data pipeline: filesystem → parser → database → FTS5

### Integration Points

- Sync service → pathlib (filesystem walking)
- Sync service → parser (frontmatter extraction)
- Sync service → SQLAlchemy (document upsert)
- Sync service → SQLite FTS5 (index maintenance)
- API route → sync service (POST /api/v1/projects/{slug}/sync)

### Data Considerations

- Documents table: moderate volume (10-200 per project, 100-2000 total)
- Content stored in DB to avoid filesystem reads at view time
- FTS5 content table uses external content mode (content=documents)
- Unique constraint: (project_id, doc_type, doc_id)

**TRD Reference:** [§6 Data Architecture](../trd.md#6-data-architecture)

## Sizing & Effort

**Story Points:** 24
**Estimated Story Count:** ~6 stories

**Complexity Factors:**

- Regex-based parser with edge cases (multi-line values, malformed input)
- Four sync behaviours to implement and test (add, update, skip, delete)
- FTS5 integration with external content table
- Change detection algorithm (SHA-256 comparison)
- Error handling and resilience (unreadable files, encoding issues)

## Stakeholders

| Role | Name | Interest |
|------|------|----------|
| Product Owner | Darren | Primary user, defines requirements |
| Developer | Darren/Claude | Implementation |

## Story Breakdown

| ID | Title | Complexity | Status |
|----|-------|------------|--------|
| [US0006](../stories/US0006-blockquote-frontmatter-parser.md) | Blockquote Frontmatter Parser | Medium | Draft |
| [US0007](../stories/US0007-filesystem-sync-service.md) | Filesystem Sync Service | High | Draft |
| [US0008](../stories/US0008-change-detection-and-skip-logic.md) | Change Detection via SHA-256 Hashing | Low | Draft |
| [US0009](../stories/US0009-document-deletion-detection.md) | Document Deletion Detection | Low | Draft |
| [US0010](../stories/US0010-fts5-search-index-management.md) | FTS5 Search Index Management | Medium | Draft |
| [US0011](../stories/US0011-document-type-and-id-inference.md) | Document Type and ID Inference | Low | Draft |

## Test Plan

**Test Spec:** To be generated via `/sdlc-studio test-spec --epic EP0002`.

## Open Questions

None.

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial epic creation from PRD |
