# US0030: Sync Engine Source Dispatch

> **Status:** Done
> **Epic:** [EP0007: Git Repository Sync](../epics/EP0007-git-repository-sync.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-18

## User Story

**As a** SDLC Developer (Darren)
**I want** the sync engine to dispatch file collection to either the local filesystem or the GitHub API based on project source type
**So that** syncing works identically regardless of where the SDLC documents are stored

## Context

### Persona Reference
**Darren** - Runs sync operations against both local and remote projects and expects the same outcome.
[Full persona details](../personas.md#darren)

### Background
The current sync engine (`sync_engine.py`) walks a local filesystem directory to collect Markdown files, then compares hashes against the database, parses changed files, and upserts/deletes as needed. To support GitHub sources, the file collection step must be extracted into a pluggable dispatch layer. A new `collect_files()` function checks the project's `source_type` and calls either `collect_local_files()` (the existing filesystem walker, extracted into its own function) or `collect_github_files()` (which delegates to the GitHub source module from US0029). The rest of the sync pipeline (hash comparison, parsing, upsert, delete, FTS rebuild) remains unchanged because both collectors produce the same `dict[str, tuple[str, bytes]]` output format.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Architecture | Sync engine is the single entry point for document ingestion | Dispatch happens within sync_engine |
| TRD | Tech Stack | Python 3.12 async | Both collectors must be async |
| PRD | KPI | Sync completes within reasonable time | No unnecessary refactoring of hot paths |

---

## Acceptance Criteria

### AC1: Local file collection extracted
- **Given** the existing filesystem walking logic in `sync_engine.py`
- **When** I inspect the refactored code
- **Then** it is extracted into an `async def collect_local_files(sdlc_path: str) -> dict[str, tuple[str, bytes]]` function

### AC2: GitHub file collection integrated
- **Given** the GitHub source module from US0029
- **When** a project has `source_type="github"`
- **Then** `collect_github_files()` is called with the project's `repo_url`, `repo_branch`, `repo_path`, and `access_token`

### AC3: Source dispatch function
- **Given** a project with a known `source_type`
- **When** `collect_files()` is called
- **Then** it dispatches to `collect_local_files()` for "local" or `collect_github_files()` for "github"

### AC4: sync_project accepts pre-built files dict
- **Given** the refactored `sync_project()` function
- **When** called with a files dict
- **Then** it performs hash comparison, parsing, upsert, delete, and FTS rebuild using the provided dict (steps 2-6 unchanged)

### AC5: Local sync behaviour unchanged
- **Given** an existing local project
- **When** I trigger a sync
- **Then** the behaviour is identical to before the refactor (same files collected, same parse results, same database state)

### AC6: run_sync_task updated
- **Given** the `sync.py` background task
- **When** it triggers a sync for a GitHub project
- **Then** it passes the project's `source_type` and relevant fields to the dispatch layer

### AC7: Unknown source_type handled
- **Given** a project with an unrecognised `source_type`
- **When** `collect_files()` is called
- **Then** it raises a descriptive error

---

## Scope

### In Scope
- Extract filesystem walking into `collect_local_files()`
- Create `collect_files()` dispatcher function
- Integrate `collect_github_files()` from US0029
- Refactor `sync_project()` to accept a pre-built files dict
- Update `sync.py` `run_sync_task` to pass source_type and fields
- Error handling for unknown source_type

### Out of Scope
- Changes to hash comparison, parsing, upsert, or delete logic
- FTS rebuild changes
- New sync scheduling or frequency changes
- Retry logic for failed GitHub fetches
- Caching of GitHub API results between syncs

---

## Technical Notes

### Refactored Flow
```
run_sync_task(project_id)
  |
  v
collect_files(project)
  |-- source_type == "local"  --> collect_local_files(sdlc_path)
  |-- source_type == "github" --> collect_github_files(repo_url, branch, repo_path, token)
  |
  v
files: dict[str, tuple[str, bytes]]
  |
  v
sync_project(session, project, files)
  |-- compare hashes with DB
  |-- parse changed/new files
  |-- upsert documents
  |-- delete removed documents
  |-- rebuild FTS index
```

### Key Design Decision
The dispatch happens **before** `sync_project()` is called, keeping the sync pipeline itself source-agnostic. This avoids adding conditional logic inside the core sync loop.

### collect_local_files Extraction
The existing code that walks the filesystem, reads file content, and computes SHA-256 hashes is moved verbatim into `collect_local_files()`. The function signature matches the GitHub collector exactly.

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| source_type is "local" with valid sdlc_path | Existing behaviour preserved |
| source_type is "github" with valid repo_url | GitHub collector called; files returned |
| source_type is "github" but repo_url is NULL | Error raised before API call |
| source_type is unrecognised (e.g. "gitlab") | ValueError raised with descriptive message |
| GitHub collector raises GitHubSourceError | Error propagated to sync task; project sync status set to failed |
| Local path does not exist | Existing error handling preserved (sync fails gracefully) |
| Both collectors return empty dict | Sync deletes all existing documents for the project |
| GitHub fetch succeeds but no .md files found | Empty dict returned; existing documents deleted |

---

## Test Scenarios

- [ ] collect_local_files returns same output as previous inline code
- [ ] collect_files dispatches to collect_local_files for source_type="local"
- [ ] collect_files dispatches to collect_github_files for source_type="github"
- [ ] collect_files raises ValueError for unknown source_type
- [ ] sync_project works correctly with pre-built files dict
- [ ] Local sync end-to-end behaviour unchanged (regression test)
- [ ] GitHub sync end-to-end with mocked GitHub source
- [ ] run_sync_task passes correct fields for GitHub project
- [ ] run_sync_task passes correct fields for local project
- [ ] Error from GitHub collector propagated correctly

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0028](US0028-database-schema-github-source.md) | Schema | Project model with source_type field | Not Started |
| [US0029](US0029-github-api-source-module.md) | Code | collect_github_files() function | Not Started |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

---

## Estimation

**Story Points:** {{TBD}}
**Complexity:** Medium

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-18 | Claude | Initial story creation from EP0007 |
