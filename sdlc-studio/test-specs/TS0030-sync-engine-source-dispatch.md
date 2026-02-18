# TS0030: Sync Engine Source Dispatch

> **Status:** Done
> **Story:** [US0030: Sync Engine Source Dispatch](../stories/US0030-sync-engine-source-dispatch.md)
> **Epic:** [EP0007: Git Repository Sync](../epics/EP0007-git-repository-sync.md)
> **Owner:** Darren
> **Created:** 2026-02-18
> **Last Updated:** 2026-02-18

## Overview

Test specification for US0030 - Sync Engine Source Dispatch. Covers the refactoring of the sync engine to dispatch file collection to either `collect_local_files()` or `collect_github_files()` based on the project's `source_type`. Tests verify that the extracted local file collector produces identical output to the previous inline code, that the dispatch function routes correctly for both source types, that the sync pipeline (hash comparison, parsing, upsert, delete) remains unchanged for local projects, and that GitHub source errors are handled gracefully with appropriate status updates.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0030](../stories/US0030-sync-engine-source-dispatch.md) | Sync Engine Source Dispatch | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0030 | AC1 | Local file collection extracted | TC0308 | Pending |
| US0030 | AC2 | GitHub file collection integrated | TC0310 | Pending |
| US0030 | AC3 | Source dispatch function | TC0309, TC0310 | Pending |
| US0030 | AC4 | sync_project accepts pre-built files dict | TC0316 | Pending |
| US0030 | AC5 | Local sync behaviour unchanged | TC0311 | Pending |
| US0030 | AC6 | run_sync_task updated | TC0314 | Pending |
| US0030 | AC7 | Unknown source_type handled | TC0312 | Pending |

**Coverage:** 7/7 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | Yes | Extracted functions and dispatch logic |
| Integration | Yes | End-to-end sync pipeline with database |
| E2E | No | Covered by integration tests |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Python 3.12, pytest, pytest-asyncio, aiosqlite |
| External Services | None (GitHub API mocked) |
| Test Data | Local fixture directories with .md files; mocked GitHub responses |

---

## Test Cases

| ID | Description | Type | Priority |
|----|-------------|------|----------|
| TC0308 | collect_local_files returns same dict as old inline code | Unit | P0 |
| TC0309 | sync_project with local source_type calls collect_local_files | Integration | P0 |
| TC0310 | sync_project with github source_type calls collect_github_files | Integration | P0 |
| TC0311 | sync_project add/update/skip/delete behaviour unchanged for local (regression) | Integration | P0 |
| TC0312 | sync_project handles github source error gracefully | Integration | P0 |
| TC0313 | sync_project sets error status on github fetch failure | Integration | P0 |
| TC0314 | run_sync_task passes project to sync_project | Unit | P1 |
| TC0315 | collect_local_files raises on missing path | Unit | P1 |
| TC0316 | sync_project works with pre-built files dict from any source | Unit | P0 |

---

### TC0308: collect_local_files returns same dict as old inline code

**Type:** Unit | **Priority:** P0 | **Story:** US0030 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A temporary directory containing `.md` files with known content | Test directory |
| When | I call `collect_local_files()` with the directory path | Function executes |
| Then | The returned dict maps relative file paths to `(sha256_hex, content_bytes)` tuples matching the file contents | Correct output |

**Assertions:**
- [ ] Return type is `dict[str, tuple[str, bytes]]`
- [ ] Each key is a relative path from the sdlc_path root
- [ ] Each value's bytes match the file content read from disk
- [ ] Each value's hash matches `hashlib.sha256(content).hexdigest()`
- [ ] Non-`.md` files are excluded
- [ ] Directories in `_EXCLUDED_DIRS` are skipped

---

### TC0309: sync_project with local source_type calls collect_local_files

**Type:** Integration | **Priority:** P0 | **Story:** US0030 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project with `source_type="local"` and a valid `sdlc_path` | Local project |
| When | The sync dispatch executes for this project | Dispatch runs |
| Then | `collect_local_files()` is called with the project's `sdlc_path` | Correct dispatch |

**Assertions:**
- [ ] `collect_local_files` is invoked (verified via mock or spy)
- [ ] `collect_github_files` is not invoked
- [ ] The `sdlc_path` argument matches the project's configured path

---

### TC0310: sync_project with github source_type calls collect_github_files

**Type:** Integration | **Priority:** P0 | **Story:** US0030 AC2, AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project with `source_type="github"`, `repo_url`, `repo_branch`, `repo_path`, and `access_token` set | GitHub project |
| When | The sync dispatch executes for this project | Dispatch runs |
| Then | `collect_github_files()` is called with the project's GitHub fields | Correct dispatch |

**Assertions:**
- [ ] `collect_github_files` is invoked (verified via mock or spy)
- [ ] `collect_local_files` is not invoked
- [ ] Arguments include `repo_url`, `repo_branch`, `repo_path`, and `access_token` from the project

---

### TC0311: sync_project add/update/skip/delete behaviour unchanged for local (regression)

**Type:** Integration | **Priority:** P0 | **Story:** US0030 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A local project with existing synced documents in the database and a fixture directory where one file is new, one is modified, one is unchanged, and one has been removed | Mixed changes |
| When | I run a sync for the local project | Sync executes |
| Then | The new file is added, the modified file is updated, the unchanged file is skipped, and the removed file is deleted from the database | Behaviour preserved |

**Assertions:**
- [ ] New document record created for the added file
- [ ] Existing document record updated (new hash, new content) for the modified file
- [ ] Unchanged document record has the same hash as before
- [ ] Removed document record is deleted from the database
- [ ] FTS index is rebuilt after the sync

---

### TC0312: sync_project handles github source error gracefully

**Type:** Integration | **Priority:** P0 | **Story:** US0030 AC7

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project with `source_type="github"` and a mocked `collect_github_files` that raises `GitHubRepoNotFoundError` | Error scenario |
| When | The sync dispatch executes for this project | Sync attempts |
| Then | The error is caught and the sync completes without crashing the application | Graceful handling |

**Assertions:**
- [ ] No unhandled exception propagates to the caller
- [ ] The error is logged with sufficient detail for debugging
- [ ] Existing documents for the project are not deleted or modified

---

### TC0313: sync_project sets error status on github fetch failure

**Type:** Integration | **Priority:** P0 | **Story:** US0030 AC7

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project with `source_type="github"` and a mocked `collect_github_files` that raises `GitHubSourceError` | Error scenario |
| When | The sync dispatch executes and fails | Sync fails |
| Then | The project's sync status is set to an error state with a descriptive message | Status updated |

**Assertions:**
- [ ] Project sync status reflects the failure
- [ ] Error message stored includes the reason (e.g., "Repository not found")
- [ ] Subsequent syncs can still be triggered (not permanently stuck)

---

### TC0314: run_sync_task passes project to sync_project

**Type:** Unit | **Priority:** P1 | **Story:** US0030 AC6

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project record in the database with `source_type` and relevant fields set | Project exists |
| When | `run_sync_task` is called with the project's ID | Task runs |
| Then | The project object (with `source_type`, `repo_url`, etc.) is passed to the sync dispatch layer | Fields forwarded |

**Assertions:**
- [ ] `sync_project` (or equivalent) receives the full project object
- [ ] The project's `source_type` is accessible in the dispatch logic
- [ ] For GitHub projects, `repo_url`, `repo_branch`, `repo_path`, `access_token` are all available

---

### TC0315: collect_local_files raises on missing path

**Type:** Unit | **Priority:** P1 | **Story:** US0030 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A path that does not exist on the filesystem | Missing directory |
| When | I call `collect_local_files()` with this path | Function executes |
| Then | An appropriate error is raised indicating the path does not exist | Error raised |

**Assertions:**
- [ ] `FileNotFoundError` or equivalent is raised
- [ ] Error message includes the missing path
- [ ] No partial results are returned

---

### TC0316: sync_project works with pre-built files dict from any source

**Type:** Unit | **Priority:** P0 | **Story:** US0030 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A manually constructed `dict[str, tuple[str, bytes]]` with known file paths and content | Pre-built dict |
| When | I call the sync pipeline with this dict (bypassing the collection step) | Pipeline executes |
| Then | The sync correctly processes the dict: adds new documents, updates changed ones, deletes missing ones | Source-agnostic |

**Assertions:**
- [ ] Documents are created in the database matching the dict entries
- [ ] Hash comparison works correctly against the provided SHA-256 values
- [ ] Parsing extracts frontmatter and content from the provided bytes
- [ ] The pipeline does not depend on source_type for processing

---

## Test Data Requirements

| Data Item | Description | Used By |
|-----------|-------------|---------|
| Local fixture directory | Temporary directory with 3-4 `.md` files and one non-`.md` file | TC0308, TC0309, TC0311 |
| Modified fixture directory | Same as above but with one file changed, one added, one removed | TC0311 |
| Pre-built files dict | Manually constructed dict with 2-3 entries | TC0316 |
| GitHub project fixture | Project record with `source_type="github"` and GitHub fields | TC0310, TC0312, TC0313 |
| Mocked collect_github_files | Mock returning a valid files dict or raising errors | TC0310, TC0312, TC0313 |

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0308 | collect_local_files returns same dict as old inline code | Pending | - |
| TC0309 | sync_project with local source_type calls collect_local_files | Pending | - |
| TC0310 | sync_project with github source_type calls collect_github_files | Pending | - |
| TC0311 | sync_project add/update/skip/delete behaviour unchanged for local | Pending | - |
| TC0312 | sync_project handles github source error gracefully | Pending | - |
| TC0313 | sync_project sets error status on github fetch failure | Pending | - |
| TC0314 | run_sync_task passes project to sync_project | Pending | - |
| TC0315 | collect_local_files raises on missing path | Pending | - |
| TC0316 | sync_project works with pre-built files dict from any source | Pending | - |

---

## Traceability

| Artefact | Reference |
|----------|-----------|
| PRD | [sdlc-studio/prd.md](../prd.md) |
| Epic | [EP0007](../epics/EP0007-git-repository-sync.md) |

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-18 | Claude | Initial spec |
