# PL0031: API Schema Updates - Implementation Plan

> **Status:** Done
> **Story:** [US0031: API Schema Updates](../stories/US0031-api-schema-source-type.md)
> **Epic:** [EP0007: GitHub Repository Sync](../epics/EP0007-github-repository-sync.md)
> **Owner:** Darren
> **Created:** 2026-02-18
> **Language:** Python

## Overview

Update the Pydantic request/response schemas, project service, and API routes to support creating and updating projects with either a local filesystem or GitHub repository source. The `ProjectCreate` and `ProjectUpdate` schemas gain `source_type`, `repo_url`, `repo_branch`, `repo_path`, and `access_token` fields with conditional validation (local projects require `sdlc_path`; GitHub projects require `repo_url`). The `ProjectResponse` schema adds source fields and a `masked_token` computed property that displays only the last 4 characters of the access token. The project service skips filesystem path validation for GitHub-source projects.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Create local project | POST with `source_type="local"` and `sdlc_path` works as before |
| AC2 | Create GitHub project | POST with `source_type="github"` and `repo_url` creates project without path validation |
| AC3 | Conditional validation | Local without `sdlc_path` returns 422; GitHub without `repo_url` returns 422 |
| AC4 | Token masking | Response shows `masked_token: "****abcd"` (last 4 chars) or `null` |
| AC5 | Update source fields | PUT can update `repo_url`, `repo_branch`, `repo_path`, `access_token` |
| AC6 | Response includes source fields | GET returns `source_type`, `repo_url`, `repo_branch`, `repo_path`, `masked_token` |

---

## Technical Context

### Language & Framework
- **Schemas:** Pydantic v2 (`BaseModel`, `model_validator`, `Field`)
- **Service:** Async SQLAlchemy via `AsyncSession`
- **Routes:** FastAPI `APIRouter`

### Existing Patterns

**Current `ProjectCreate`** (in `backend/src/sdlc_lens/api/schemas/projects.py`):
```python
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    sdlc_path: str = Field(..., min_length=1)
```

**Current `create_project`** (in `backend/src/sdlc_lens/services/project.py`):
```python
async def create_project(session: AsyncSession, name: str, sdlc_path: str) -> Project:
    resolved = Path(sdlc_path).resolve()
    if not resolved.is_dir():
        raise PathNotFoundError
```

**Current `_project_response`** (in `backend/src/sdlc_lens/api/routes/projects.py`):
```python
return ProjectResponse(
    slug=project.slug, name=project.name, sdlc_path=project.sdlc_path,
    sync_status=project.sync_status, sync_error=project.sync_error,
    last_synced_at=project.last_synced_at, document_count=doc_count,
    created_at=project.created_at,
)
```

### Dependencies
- **PL0028:** Project model has the new columns
- **PL0030:** Sync engine accepts project object (for consistency, though not strictly required here)

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** Schema validation and API responses have clear input/output contracts. Test each validation rule (local requires path, GitHub requires URL) and verify response shape.

### Test Priority
1. Create local project (backward compatibility)
2. Create GitHub project (new path)
3. Conditional validation errors (missing sdlc_path, missing repo_url)
4. Token masking in responses
5. Update project with new fields
6. Response shape verification

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Update Pydantic schemas | `backend/src/sdlc_lens/api/schemas/projects.py` | PL0028 | [ ] |
| 2 | Update project service | `backend/src/sdlc_lens/services/project.py` | 1 | [ ] |
| 3 | Update API routes | `backend/src/sdlc_lens/api/routes/projects.py` | 1, 2 | [ ] |
| 4 | Write schema validation tests | `backend/tests/api/test_project_schemas.py` | 1 | [ ] |
| 5 | Write API integration tests | `backend/tests/api/test_projects.py` | 3 | [ ] |

---

## Implementation Phases

### Phase 1: Schema Updates

**Goal:** Add source fields with conditional validation to Pydantic schemas.

- [ ] Update `backend/src/sdlc_lens/api/schemas/projects.py`:

```python
def mask_token(token: str | None) -> str | None:
    """Mask an access token, showing only the last 4 characters."""
    if not token:
        return None
    if len(token) <= 4:
        return "****"
    return f"****{token[-4:]}"


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    source_type: str = Field(default="local")
    sdlc_path: str | None = Field(default=None, min_length=1)
    repo_url: str | None = Field(default=None, min_length=1)
    repo_branch: str = Field(default="main", min_length=1)
    repo_path: str = Field(default="sdlc-studio", min_length=1)
    access_token: str | None = Field(default=None)

    @model_validator(mode="after")
    def validate_source_fields(self) -> "ProjectCreate":
        if self.source_type == "local":
            if not self.sdlc_path:
                msg = "'sdlc_path' is required when source_type is 'local'"
                raise ValueError(msg)
        elif self.source_type == "github":
            if not self.repo_url:
                msg = "'repo_url' is required when source_type is 'github'"
                raise ValueError(msg)
        else:
            msg = f"source_type must be 'local' or 'github', got '{self.source_type}'"
            raise ValueError(msg)
        return self


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    sdlc_path: str | None = Field(None, min_length=1)
    repo_url: str | None = Field(None, min_length=1)
    repo_branch: str | None = Field(None, min_length=1)
    repo_path: str | None = Field(None, min_length=1)
    access_token: str | None = Field(None)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "ProjectUpdate":
        fields = [
            self.name, self.sdlc_path, self.repo_url,
            self.repo_branch, self.repo_path, self.access_token,
        ]
        if all(f is None for f in fields):
            msg = "At least one field must be provided"
            raise ValueError(msg)
        return self


class ProjectResponse(BaseModel):
    slug: str
    name: str
    sdlc_path: str | None = None
    source_type: str
    repo_url: str | None = None
    repo_branch: str
    repo_path: str
    masked_token: str | None = None
    sync_status: str
    sync_error: str | None = None
    last_synced_at: datetime.datetime | None
    document_count: int
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
```

**Design decisions:**
- **`sdlc_path` becomes optional** in `ProjectCreate` (was required). Conditional validation ensures it is present for local sources.
- **`mask_token` helper** is a module-level function, not a Pydantic computed field, so the route layer can call it explicitly when building the response.
- **`ProjectUpdate`** does not validate source_type consistency; the service layer handles that since it knows the project's current source_type.
- **`source_type` not updatable** via `ProjectUpdate`; changing source type requires delete and recreate (avoids complex migration of in-flight sync state).

**Files:**
- `backend/src/sdlc_lens/api/schemas/projects.py`

### Phase 2: Service Updates

**Goal:** Update `create_project` and `update_project` to accept and handle the new fields.

- [ ] Update `backend/src/sdlc_lens/services/project.py`:

```python
async def create_project(
    session: AsyncSession,
    name: str,
    sdlc_path: str | None = None,
    *,
    source_type: str = "local",
    repo_url: str | None = None,
    repo_branch: str = "main",
    repo_path: str = "sdlc-studio",
    access_token: str | None = None,
) -> Project:
    """Register a new project.

    For local source: validates sdlc_path exists on filesystem.
    For github source: skips path validation, stores repo details.
    """
    slug = generate_slug(name)
    if not slug:
        raise EmptySlugError

    # Path validation only for local sources
    resolved_path: str | None = None
    if source_type == "local":
        if not sdlc_path:
            raise PathNotFoundError("sdlc_path is required for local projects")
        resolved = Path(sdlc_path).resolve()
        if not resolved.is_dir():
            raise PathNotFoundError
        resolved_path = str(resolved)

    # Check for existing slug
    existing = await session.execute(select(Project).where(Project.slug == slug))
    if existing.scalar_one_or_none() is not None:
        raise SlugConflictError

    project = Project(
        slug=slug,
        name=name,
        sdlc_path=resolved_path,
        source_type=source_type,
        repo_url=repo_url,
        repo_branch=repo_branch,
        repo_path=repo_path,
        access_token=access_token,
    )
    session.add(project)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise SlugConflictError from exc

    await session.refresh(project)
    return project


async def update_project(
    session: AsyncSession,
    slug: str,
    name: str | None = None,
    sdlc_path: str | None = None,
    *,
    repo_url: str | None = None,
    repo_branch: str | None = None,
    repo_path: str | None = None,
    access_token: str | None = None,
) -> Project:
    """Update a project's fields.

    Path validation only applies to local-source projects.
    """
    project = await get_project_by_slug(session, slug)

    if sdlc_path is not None and project.source_type == "local":
        resolved = Path(sdlc_path).resolve()
        if not resolved.is_dir():
            raise PathNotFoundError
        project.sdlc_path = str(resolved)

    if name is not None:
        project.name = name
    if repo_url is not None:
        project.repo_url = repo_url
    if repo_branch is not None:
        project.repo_branch = repo_branch
    if repo_path is not None:
        project.repo_path = repo_path
    if access_token is not None:
        project.access_token = access_token

    await session.commit()
    await session.refresh(project)
    return project
```

**Files:**
- `backend/src/sdlc_lens/services/project.py`

### Phase 3: Route Updates

**Goal:** Wire the new schema fields through the API routes.

- [ ] Update `backend/src/sdlc_lens/api/routes/projects.py`:

```python
from sdlc_lens.api.schemas.projects import mask_token

async def _project_response(db: AsyncSession, project) -> ProjectResponse:
    """Build a ProjectResponse with computed fields."""
    doc_count = await get_document_count(db, project.id)
    return ProjectResponse(
        slug=project.slug,
        name=project.name,
        sdlc_path=project.sdlc_path,
        source_type=project.source_type,
        repo_url=project.repo_url,
        repo_branch=project.repo_branch,
        repo_path=project.repo_path,
        masked_token=mask_token(project.access_token),
        sync_status=project.sync_status,
        sync_error=project.sync_error,
        last_synced_at=project.last_synced_at,
        document_count=doc_count,
        created_at=project.created_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProjectResponse)
async def register_project(body: ProjectCreate, db: DbDep) -> ProjectResponse | JSONResponse:
    """Register a new sdlc-studio project."""
    try:
        project = await create_project(
            db,
            body.name,
            body.sdlc_path,
            source_type=body.source_type,
            repo_url=body.repo_url,
            repo_branch=body.repo_branch,
            repo_path=body.repo_path,
            access_token=body.access_token,
        )
    except PathNotFoundError as exc:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "PATH_NOT_FOUND", "message": exc.message}},
        )
    except SlugConflictError as exc:
        return JSONResponse(
            status_code=409,
            content={"error": {"code": "CONFLICT", "message": exc.message}},
        )
    except EmptySlugError as exc:
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "VALIDATION_ERROR", "message": exc.message}},
        )
    return await _project_response(db, project)


@router.put("/{slug}", response_model=ProjectResponse)
async def update_project_endpoint(
    slug: str, body: ProjectUpdate, db: DbDep
) -> ProjectResponse | JSONResponse:
    """Update a project's fields."""
    try:
        project = await update_project(
            db,
            slug,
            name=body.name,
            sdlc_path=body.sdlc_path,
            repo_url=body.repo_url,
            repo_branch=body.repo_branch,
            repo_path=body.repo_path,
            access_token=body.access_token,
        )
    except ProjectNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": exc.message}},
        )
    except PathNotFoundError as exc:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "PATH_NOT_FOUND", "message": exc.message}},
        )
    return await _project_response(db, project)
```

**Files:**
- `backend/src/sdlc_lens/api/routes/projects.py`

### Phase 4: Testing and Validation

**Goal:** Verify all API paths for both source types.

- [ ] Schema validation tests:

| # | Test | Description |
|---|------|-------------|
| 1 | `test_create_local_requires_sdlc_path` | `source_type="local"` without `sdlc_path` raises validation error |
| 2 | `test_create_github_requires_repo_url` | `source_type="github"` without `repo_url` raises validation error |
| 3 | `test_create_local_valid` | `source_type="local"` with `sdlc_path` passes validation |
| 4 | `test_create_github_valid` | `source_type="github"` with `repo_url` passes validation |
| 5 | `test_create_invalid_source_type` | `source_type="svn"` raises validation error |
| 6 | `test_mask_token_full` | `"ghp_abc123xyz9"` returns `"****yz9"` (last 4) |
| 7 | `test_mask_token_short` | `"ab"` returns `"****"` |
| 8 | `test_mask_token_none` | `None` returns `None` |

- [ ] API integration tests:

| # | Test | Description |
|---|------|-------------|
| 1 | `test_post_local_project` | POST with `source_type="local"` returns 201 |
| 2 | `test_post_github_project` | POST with `source_type="github"` returns 201, no path validation |
| 3 | `test_post_github_missing_url` | POST with `source_type="github"` and no `repo_url` returns 422 |
| 4 | `test_get_project_includes_source_fields` | GET returns `source_type`, `repo_url`, `masked_token` |
| 5 | `test_put_update_repo_url` | PUT updates `repo_url` for GitHub project |
| 6 | `test_response_token_masked` | Response `masked_token` shows `"****{last4}"` |
| 7 | `test_response_token_null` | No token returns `masked_token: null` |

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | `test_post_local_project` | `test_projects.py` | Pending |
| AC2 | `test_post_github_project` | `test_projects.py` | Pending |
| AC3 | Schema validation tests | `test_project_schemas.py` | Pending |
| AC4 | `test_response_token_masked`, `_null` | `test_projects.py` | Pending |
| AC5 | `test_put_update_repo_url` | `test_projects.py` | Pending |
| AC6 | `test_get_project_includes_source_fields` | `test_projects.py` | Pending |

---

## Edge Case Handling

| # | Edge Case | Handling Strategy | Phase |
|---|-----------|-------------------|-------|
| 1 | Local project POST without sdlc_path (backward compat) | Pydantic validator rejects with 422 (same as before since sdlc_path was always required for local) | Phase 1 |
| 2 | GitHub project POST with sdlc_path provided | Ignored; `sdlc_path` stored as None for GitHub projects | Phase 2 |
| 3 | Token with fewer than 4 characters | `mask_token` returns `"****"` (fully masked) | Phase 1 |
| 4 | Empty string access_token | Treated same as None (no auth header); normalised to None in service | Phase 2 |
| 5 | Update sdlc_path on GitHub project | Path validation skipped; field update ignored for GitHub source | Phase 2 |
| 6 | Existing API clients sending old schema | Default `source_type="local"` means old POST bodies work unchanged | Phase 1 |

**Coverage:** 6/6 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing API clients | High | Default `source_type="local"` preserves backward compatibility; `sdlc_path` only conditionally required |
| Token exposed in logs or error messages | Medium | `mask_token` in response; avoid logging token values |
| ProjectUpdate allows invalid field combinations | Low | Service layer validates against project's current `source_type` |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Schema validation tests written and passing
- [ ] API integration tests written and passing
- [ ] Backward compatibility with existing local projects verified
- [ ] Token masking works for all cases (full, short, None)
- [ ] Ruff linting passes

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-18 | Darren | Initial plan created |
