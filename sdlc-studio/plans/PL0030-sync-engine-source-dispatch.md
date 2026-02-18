# PL0030: Sync Engine Source Dispatch - Implementation Plan

> **Status:** Done
> **Story:** [US0030: Sync Engine Source Dispatch](../stories/US0030-sync-engine-source-dispatch.md)
> **Epic:** [EP0007: GitHub Repository Sync](../epics/EP0007-github-repository-sync.md)
> **Owner:** Darren
> **Created:** 2026-02-18
> **Language:** Python

## Overview

Refactor the sync engine to support both local filesystem and GitHub repository sources. The current `sync_project` function is tightly coupled to local filesystem walking. This plan extracts the file-collection step into a separate function (`collect_local_files`) and adds a parallel `collect_github_files` wrapper. A dispatch block at the top of `sync_project` selects the appropriate collector based on the project's `source_type`. Steps 2 through 6 (DB comparison, parsing, upsert, deletion, FTS rebuild) remain unchanged since they all operate on the same `dict[str, tuple[str, bytes]]` structure regardless of source.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Local sync unchanged | Existing local-source projects sync identically to before the refactor |
| AC2 | GitHub dispatch | Projects with `source_type="github"` call `fetch_github_files` instead of walking the filesystem |
| AC3 | Signature change | `sync_project` accepts a `Project` object (or project_id + session) and reads source_type from the model |
| AC4 | Error propagation | GitHub source errors (404, 401, 403) are caught and stored in `sync_error` |
| AC5 | run_sync_task updated | The background sync task passes the project object to the refactored `sync_project` |

---

## Technical Context

### Language & Framework
- **Module:** `backend/src/sdlc_lens/services/sync_engine.py`
- **Caller:** `backend/src/sdlc_lens/services/sync.py` (`run_sync_task`)
- **New dependency:** `backend/src/sdlc_lens/services/github_source.py` (PL0029)

### Existing Patterns

The current `sync_project` function (lines 118-264 in `sync_engine.py`) takes `project_id: int`, `sdlc_path: str`, and `session: AsyncSession`. The file-collection logic is at lines 156-175:

```python
fs_files: dict[str, tuple[str, bytes]] = {}
for md_file in sorted(_walk_md_files(root)):
    rel_path = str(md_file.relative_to(root))
    filename = md_file.name
    inference = infer_type_and_id(filename, rel_path)
    if inference is None:
        continue
    try:
        raw = md_file.read_bytes()
    except (PermissionError, OSError) as exc:
        logger.warning("Cannot read %s: %s", md_file, exc)
        result.errors += 1
        continue
    file_hash = compute_hash(raw)
    fs_files[rel_path] = (file_hash, raw)
```

The `run_sync_task` function in `sync.py` (line 59) currently calls:
```python
sync_result = await sync_project(project.id, project.sdlc_path, session)
```

### Dependencies
- **PL0028:** Project model has `source_type`, `repo_url`, `repo_branch`, `repo_path`, `access_token`
- **PL0029:** `github_source.fetch_github_files` function exists

---

## Recommended Approach

**Strategy:** TDD (Refactor)
**Rationale:** This is a structural refactor of an existing function with comprehensive test coverage. Existing tests must continue passing after the refactor. New tests verify dispatch logic for the GitHub path.

### Test Priority
1. Existing sync tests pass without changes (local source path)
2. `collect_local_files` extracted function produces identical output
3. GitHub-source project dispatches to `fetch_github_files`
4. GitHub source errors are stored in `sync_error`
5. `run_sync_task` passes project object correctly

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Extract `collect_local_files` function | `backend/src/sdlc_lens/services/sync_engine.py` | - | [ ] |
| 2 | Add `collect_github_files` wrapper | `backend/src/sdlc_lens/services/sync_engine.py` | PL0029 | [ ] |
| 3 | Add dispatch logic to `sync_project` | `backend/src/sdlc_lens/services/sync_engine.py` | 1, 2 | [ ] |
| 4 | Update `run_sync_task` caller | `backend/src/sdlc_lens/services/sync.py` | 3 | [ ] |
| 5 | Update existing sync tests | `backend/tests/services/test_sync_engine.py` | 3 | [ ] |
| 6 | Write new dispatch tests | `backend/tests/services/test_sync_engine.py` | 3 | [ ] |

---

## Implementation Phases

### Phase 1: Extract Local File Collection

**Goal:** Move the filesystem walk and file-reading logic into a standalone function without changing behaviour.

- [ ] Create `collect_local_files` in `sync_engine.py`:

```python
def collect_local_files(
    root: Path,
) -> tuple[dict[str, tuple[str, bytes]], int]:
    """Walk a local directory and collect Markdown files.

    Args:
        root: Absolute path to the sdlc-studio directory.

    Returns:
        Tuple of (files_dict, error_count) where files_dict maps
        rel_path to (sha256_hash, raw_bytes).
    """
    fs_files: dict[str, tuple[str, bytes]] = {}
    errors = 0

    for md_file in sorted(_walk_md_files(root)):
        rel_path = str(md_file.relative_to(root))
        filename = md_file.name

        inference = infer_type_and_id(filename, rel_path)
        if inference is None:
            continue

        try:
            raw = md_file.read_bytes()
        except (PermissionError, OSError) as exc:
            logger.warning("Cannot read %s: %s", md_file, exc)
            errors += 1
            continue

        file_hash = compute_hash(raw)
        fs_files[rel_path] = (file_hash, raw)

    return fs_files, errors
```

- [ ] Replace inline code in `sync_project` with call to `collect_local_files`

**Files:**
- `backend/src/sdlc_lens/services/sync_engine.py`

### Phase 2: Add GitHub Collection Wrapper

**Goal:** Create an async wrapper that calls the GitHub source module.

- [ ] Create `collect_github_files` in `sync_engine.py`:

```python
async def collect_github_files(
    project: Project,
) -> tuple[dict[str, tuple[str, bytes]], int]:
    """Fetch Markdown files from a GitHub repository.

    Args:
        project: Project instance with repo_url, repo_branch,
                 repo_path, and access_token fields.

    Returns:
        Tuple of (files_dict, error_count) where files_dict maps
        rel_path to (sha256_hash, raw_bytes).

    Raises:
        GitHubSourceError: On API errors (propagated to caller).
    """
    from sdlc_lens.services.github_source import fetch_github_files

    fs_files = await fetch_github_files(
        repo_url=project.repo_url,
        branch=project.repo_branch,
        repo_path=project.repo_path,
        access_token=project.access_token,
    )
    return fs_files, 0
```

**Files:**
- `backend/src/sdlc_lens/services/sync_engine.py`

### Phase 3: Dispatch Logic in sync_project

**Goal:** Route to the correct file collector based on `source_type`.

- [ ] Refactor `sync_project` signature and add dispatch:

```python
async def sync_project(
    project_id: int,
    session: AsyncSession,
    *,
    sdlc_path: str | None = None,
    source_type: str = "local",
    project: Project | None = None,
) -> SyncResult:
    """Sync documents from a project's document source.

    Dispatches to local filesystem or GitHub API based on source_type.
    """
    result = SyncResult()

    # Fetch project if not provided
    if project is None:
        project = await session.get(Project, project_id)
        if project is None:
            return result

    source = project.source_type or "local"

    # Set project to syncing
    project.sync_status = "syncing"
    await session.flush()

    try:
        # Dispatch: collect files from appropriate source
        if source == "github":
            fs_files, collect_errors = await collect_github_files(project)
        else:
            root = Path(project.sdlc_path)
            if not root.is_dir():
                project.sync_status = "error"
                project.sync_error = f"Path not found: {project.sdlc_path}"
                await session.commit()
                return result
            fs_files, collect_errors = collect_local_files(root)

        result.errors = collect_errors

        # Steps 2-6: DB comparison, parse, upsert, delete, FTS
        # (unchanged from current implementation)
        ...
```

**Key changes:**
- `sync_project` reads `source_type` from the `Project` model rather than requiring separate parameters.
- Path validation only runs for local sources.
- GitHub errors are caught in the outer try/except block and stored in `sync_error`.

**Files:**
- `backend/src/sdlc_lens/services/sync_engine.py`

### Phase 4: Update run_sync_task

**Goal:** Pass the project object to the refactored sync_project.

- [ ] Update `backend/src/sdlc_lens/services/sync.py`:

```python
async def run_sync_task(slug: str, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Background task that performs the sync."""
    async with session_factory() as session:
        result = await session.execute(select(Project).where(Project.slug == slug))
        project = result.scalar_one_or_none()
        if project is None:
            logger.warning("Project '%s' deleted during sync", slug)
            return

        sync_result = await sync_project(
            project.id, session, project=project
        )
        logger.info(
            "Sync completed for '%s': added=%d updated=%d skipped=%d deleted=%d errors=%d",
            slug,
            sync_result.added,
            sync_result.updated,
            sync_result.skipped,
            sync_result.deleted,
            sync_result.errors,
        )
```

**Files:**
- `backend/src/sdlc_lens/services/sync.py`

### Phase 5: Testing and Validation

**Goal:** Verify backward compatibility and new dispatch logic.

- [ ] Run existing backend tests: `cd backend && PYTHONPATH=src python -m pytest`
- [ ] Verify all existing sync tests pass without modification (local source path)
- [ ] Write new tests for dispatch logic:

| # | Test | Description |
|---|------|-------------|
| 1 | `test_collect_local_files_returns_dict` | Verify extracted function matches previous inline output |
| 2 | `test_sync_project_local_dispatch` | Local project calls `collect_local_files` |
| 3 | `test_sync_project_github_dispatch` | GitHub project calls `fetch_github_files` (mocked) |
| 4 | `test_sync_project_github_error_stored` | `GitHubSourceError` sets `sync_status="error"` and `sync_error` |
| 5 | `test_sync_project_github_auth_error` | `AuthenticationError` stored in `sync_error` |
| 6 | `test_run_sync_task_passes_project` | `run_sync_task` passes project to `sync_project` |

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | Existing sync tests pass unchanged | `test_sync_engine.py` | Pending |
| AC2 | `test_sync_project_github_dispatch` verifies dispatch | `test_sync_engine.py` | Pending |
| AC3 | `sync_project` signature accepts project object | `sync_engine.py` | Pending |
| AC4 | `test_sync_project_github_error_stored` | `test_sync_engine.py` | Pending |
| AC5 | `test_run_sync_task_passes_project` | `test_sync.py` | Pending |

---

## Edge Case Handling

| # | Edge Case | Handling Strategy | Phase |
|---|-----------|-------------------|-------|
| 1 | Project with source_type=NULL (old row before migration) | Default to `"local"` via `project.source_type or "local"` | Phase 3 |
| 2 | GitHub project with no repo_url | `parse_github_url` raises `ValueError`; caught by outer try/except, stored in `sync_error` | Phase 3 |
| 3 | GitHub rate limit during sync | `RateLimitError` propagates, caught in try/except, stored in `sync_error` | Phase 3 |
| 4 | Local project with invalid sdlc_path | Existing path validation logic unchanged | Phase 3 |
| 5 | Network timeout during GitHub fetch | httpx `TimeoutException` caught by generic exception handler | Phase 3 |

**Coverage:** 5/5 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Refactor breaks existing sync behaviour | High | Existing tests provide safety net; extract function first, then dispatch |
| Circular import between sync_engine and github_source | Low | Use lazy import (`from ... import` inside function body) |
| sync_project signature change breaks callers | Medium | Keep backward-compatible parameters; only `run_sync_task` calls `sync_project` directly |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Existing sync tests pass unchanged
- [ ] New dispatch tests written and passing
- [ ] `collect_local_files` extracted as standalone function
- [ ] `collect_github_files` wrapper delegates to github_source module
- [ ] `run_sync_task` updated to pass project object
- [ ] Ruff linting passes

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-18 | Darren | Initial plan created |
