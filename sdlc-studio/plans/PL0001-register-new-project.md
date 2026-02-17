# PL0001: Register a New Project - Implementation Plan

> **Status:** Complete
> **Story:** [US0001: Register a New Project](../stories/US0001-register-new-project.md)
> **Epic:** [EP0001: Project Management](../epics/EP0001-project-management.md)
> **Created:** 2026-02-17
> **Language:** Python

## Overview

Implement the POST /api/v1/projects endpoint that registers a new sdlc-studio project. This is the first story in a greenfield project, so it also establishes the backend project structure, database infrastructure, and testing patterns that all subsequent stories will build on.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Successful registration | POST with valid name + path returns 201 with project JSON |
| AC2 | Auto-generated slug | Name "My Cool Project" produces slug "my-cool-project" |
| AC3 | Path validation | Non-existent path returns 400 PATH_NOT_FOUND |
| AC4 | Duplicate slug rejection | Same slug returns 409 CONFLICT |
| AC5 | Pydantic validation | Missing required fields returns 422 VALIDATION_ERROR |

---

## Technical Context

### Language & Framework
- **Primary Language:** Python 3.12+
- **Framework:** FastAPI >=0.115.0
- **Test Framework:** pytest >=8.0.0 with pytest-asyncio

### Relevant Best Practices
- Type hints on all public functions
- pathlib for filesystem operations
- Specific exception handling (no bare except)
- Logging module (not print)
- Ruff for linting and formatting

### Library Documentation (Context7)

| Library | Context7 ID | Key Patterns |
|---------|-------------|--------------|
| FastAPI | /fastapi/fastapi | Pydantic BaseModel for request validation, HTTPException for errors, async def endpoints, Depends() for DB session |
| SQLAlchemy | /websites/sqlalchemy_en_21 | DeclarativeBase, Mapped[type], mapped_column(), create_async_engine("sqlite+aiosqlite://"), async_sessionmaker(expire_on_commit=False) |
| Pydantic | - | BaseModel, Field(min_length, max_length), model_config |

### Existing Patterns

No existing code - greenfield project. This story establishes all foundational patterns.

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** API story with 9 edge cases and clear Given/When/Then acceptance criteria. All AC have concrete input/output values. Test-first ensures the API contract is validated before implementation.

### Test Priority
1. Slug generation unit tests (pure function, easy to test first)
2. Path validation unit tests (pure function)
3. POST /api/v1/projects integration tests (all 5 AC + edge cases)

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Create backend project structure with pyproject.toml | `backend/pyproject.toml` | - | [ ] |
| 2 | Create FastAPI application factory | `backend/src/sdlc_lens/app.py` | 1 | [ ] |
| 3 | Create Pydantic Settings config | `backend/src/sdlc_lens/config.py` | 1 | [ ] |
| 4 | Create async database engine and session | `backend/src/sdlc_lens/database.py` | 1, 3 | [ ] |
| 5 | Create SQLAlchemy Base and Project model | `backend/src/sdlc_lens/models/project.py` | 4 | [ ] |
| 6 | Create Alembic config and initial migration | `backend/alembic/` | 5 | [ ] |
| 7 | Create Pydantic request/response schemas | `backend/src/sdlc_lens/schemas/project.py` | 1 | [ ] |
| 8 | Create slug generation utility | `backend/src/sdlc_lens/utils/slug.py` | 1 | [ ] |
| 9 | Create project service (registration logic) | `backend/src/sdlc_lens/services/project.py` | 5, 7, 8 | [ ] |
| 10 | Create projects API router (POST endpoint) | `backend/src/sdlc_lens/api/projects.py` | 2, 7, 9 | [ ] |
| 11 | Create main API router and wire to app | `backend/src/sdlc_lens/api/router.py` | 10 | [ ] |
| 12 | Create test conftest with async DB fixtures | `backend/tests/conftest.py` | 4, 5 | [ ] |
| 13 | Write slug generation unit tests | `backend/tests/test_slug.py` | 8 | [ ] |
| 14 | Write POST /api/v1/projects integration tests | `backend/tests/test_project_api.py` | 10, 12 | [ ] |

### Parallel Execution Groups

| Group | Tasks | Prerequisite |
|-------|-------|--------------|
| Foundation | 1, 2, 3 | None |
| Database | 4, 5, 6 | Group: Foundation |
| API Logic | 7, 8, 9, 10, 11 | Group: Database |
| Tests | 12, 13, 14 | Group: API Logic |

---

## Implementation Phases

### Phase 1: Backend Foundation
**Goal:** Establish project structure, database, and ORM model

- [ ] Create `backend/` directory with `pyproject.toml` (uv-managed, all dependencies)
- [ ] Create `src/sdlc_lens/` package with `__init__.py`
- [ ] Create `config.py` - Pydantic Settings loading SDLC_LENS_* env vars (HOST, PORT, DATABASE_URL, LOG_LEVEL)
- [ ] Create `database.py` - create_async_engine for sqlite+aiosqlite, async_sessionmaker, get_db dependency
- [ ] Create `models/project.py` - SQLAlchemy Project model matching TRD schema (id, slug, name, sdlc_path, sync_status, sync_error, last_synced_at, created_at, updated_at)
- [ ] Create `alembic.ini` and `alembic/env.py` with async SQLAlchemy support
- [ ] Create initial migration `001_create_projects_table.py`

**Files:**
- `backend/pyproject.toml` - Project metadata and dependencies
- `backend/src/sdlc_lens/__init__.py` - Package init
- `backend/src/sdlc_lens/config.py` - Settings
- `backend/src/sdlc_lens/database.py` - Engine and session
- `backend/src/sdlc_lens/models/__init__.py` - Models package
- `backend/src/sdlc_lens/models/project.py` - Project model
- `backend/alembic.ini` - Alembic config
- `backend/alembic/env.py` - Alembic environment
- `backend/alembic/versions/001_create_projects_table.py` - Initial migration

### Phase 2: API Layer
**Goal:** Implement POST /api/v1/projects with validation and error handling

- [ ] Create `schemas/project.py` - ProjectCreate (name: str, sdlc_path: str with validators), ProjectResponse, ErrorResponse
- [ ] Create `utils/slug.py` - generate_slug() function (lowercase, replace spaces/underscores, strip special chars, collapse hyphens)
- [ ] Create `services/project.py` - create_project() with path validation (Path.resolve().is_dir()), slug generation, duplicate checking, DB insert
- [ ] Create `api/projects.py` - POST route returning 201, handling 400/409/422
- [ ] Create `api/router.py` - Include projects router under /api/v1
- [ ] Create `app.py` - FastAPI factory with lifespan, include router, error response configuration

**Files:**
- `backend/src/sdlc_lens/schemas/__init__.py`
- `backend/src/sdlc_lens/schemas/project.py` - Request/response models
- `backend/src/sdlc_lens/utils/__init__.py`
- `backend/src/sdlc_lens/utils/slug.py` - Slug generation
- `backend/src/sdlc_lens/services/__init__.py`
- `backend/src/sdlc_lens/services/project.py` - Business logic
- `backend/src/sdlc_lens/api/__init__.py`
- `backend/src/sdlc_lens/api/projects.py` - POST endpoint
- `backend/src/sdlc_lens/api/router.py` - API router
- `backend/src/sdlc_lens/app.py` - Application factory

### Phase 3: Testing & Validation
**Goal:** Verify all acceptance criteria

- [ ] Create `tests/conftest.py` - async test engine (in-memory SQLite), test session, async test client (httpx.AsyncClient)
- [ ] Create `tests/test_slug.py` - Unit tests for slug generation (spaces, special chars, unicode, empty result, consecutive hyphens)
- [ ] Create `tests/test_project_api.py` - Integration tests covering all 5 AC and 9 edge cases

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | POST with valid data returns 201 with all fields | `tests/test_project_api.py` | Pending |
| AC2 | Slug generated from name correctly | `tests/test_slug.py` + `tests/test_project_api.py` | Pending |
| AC3 | Non-existent path returns 400 | `tests/test_project_api.py` | Pending |
| AC4 | Duplicate slug returns 409 | `tests/test_project_api.py` | Pending |
| AC5 | Missing fields returns 422 | `tests/test_project_api.py` | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | Path exists but is a file, not a directory | Check Path.resolve().is_dir() returns False; return 400 PATH_NOT_FOUND | Phase 2 |
| 2 | Name with only special characters ("!!!") | Validate slug not empty after sanitisation; return 422 if empty | Phase 2 |
| 3 | Very long name (>200 characters) | Pydantic Field(max_length=200) on name | Phase 2 |
| 4 | Path with trailing slash vs without | Path() normalises trailing slashes automatically | Phase 2 |
| 5 | Name with unicode characters | Slug generation strips non-ASCII via regex [a-z0-9-] | Phase 2 |
| 6 | Empty name string | Pydantic Field(min_length=1) on name | Phase 2 |
| 7 | Empty sdlc_path string | Pydantic Field(min_length=1) on sdlc_path | Phase 2 |
| 8 | Path with symlinks | Path.resolve() resolves symlinks before is_dir() check | Phase 2 |
| 9 | Concurrent registration with same slug | Database UNIQUE constraint on slug column; catch IntegrityError, return 409 | Phase 2 |

**Coverage:** 9/9 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Alembic async setup complexity | Medium | Use synchronous fallback in env.py with run_sync |
| Path validation behaves differently in Docker vs local | Medium | Tests use tmp_path fixture; document Docker volume mapping |
| SQLite async locking with aiosqlite | Low | Single-writer pattern; WAL mode in production |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Edge cases handled
- [ ] Code follows Python best practices (type hints, pathlib, specific exceptions)
- [ ] Ruff linting passes
- [ ] API returns correct error format: `{"error": {"code": "...", "message": "..."}}`

---

## Notes

- This is the first story - establishes all backend patterns. Extra setup time expected.
- The document_count field in the response is always 0 for a new project (no sync has run).
- sync_status defaults to "never_synced" and is not settable via the API.
- The projects table also needs sync_error and updated_at columns per TRD, even though they are not exposed in the create response.
