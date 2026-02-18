# TS0028: Database Schema & Project Model

> **Status:** Done
> **Story:** [US0028: Database Schema & Project Model](../stories/US0028-database-schema-github-source.md)
> **Epic:** [EP0007: Git Repository Sync](../epics/EP0007-git-repository-sync.md)
> **Owner:** Darren
> **Created:** 2026-02-18
> **Last Updated:** 2026-02-18

## Overview

Test specification for US0028 - Database Schema & Project Model. Covers Alembic migration 005 that adds five new columns to the Project table (`source_type`, `repo_url`, `repo_branch`, `repo_path`, `access_token`), makes `sdlc_path` nullable, and ensures backward compatibility with existing local-only projects. Tests verify migration application on fresh and existing databases, default value behaviour, and model-level column acceptance for the new GitHub source fields.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0028](../stories/US0028-database-schema-github-source.md) | Database Schema & Project Model | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0028 | AC1 | New columns on Project model | TC0290, TC0291 | Pending |
| US0028 | AC2 | sdlc_path nullable | TC0291 | Pending |
| US0028 | AC3 | Alembic migration 005 | TC0287, TC0288 | Pending |
| US0028 | AC4 | Backward compatibility | TC0289, TC0292 | Pending |

**Coverage:** 4/5 ACs covered (AC5 downgrade tested manually)

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | Yes | Model default values and column acceptance |
| Integration | Yes | Alembic migration on real SQLite database |
| E2E | No | Schema changes validated by integration tests |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Python 3.12, pytest, aiosqlite, Alembic |
| External Services | None |
| Test Data | Seed projects via SQLAlchemy ORM for migration tests |

---

## Test Cases

| ID | Description | Type | Priority |
|----|-------------|------|----------|
| TC0287 | Migration 005 applies to fresh database | Integration | P0 |
| TC0288 | Migration 005 applies to existing database with projects | Integration | P0 |
| TC0289 | Existing projects get source_type="local" default after migration | Integration | P0 |
| TC0290 | Project model accepts github source_type fields | Unit | P0 |
| TC0291 | sdlc_path is nullable for github projects | Unit | P0 |
| TC0292 | source_type defaults to "local" when not specified | Unit | P0 |
| TC0293 | repo_branch defaults to "main" when not specified | Unit | P1 |

---

### TC0287: Migration 005 applies to fresh database

**Type:** Integration | **Priority:** P0 | **Story:** US0028 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A fresh SQLite database with no tables | Empty database |
| When | Run `alembic upgrade head` to apply all migrations including 005 | All migrations execute |
| Then | The `projects` table contains the five new columns with correct types and defaults | Schema updated |

**Assertions:**
- [ ] `alembic upgrade head` exit code is 0
- [ ] `source_type` column exists with type `VARCHAR(20)` and server default `"local"`
- [ ] `repo_url` column exists with type `TEXT` and is nullable
- [ ] `repo_branch` column exists with type `VARCHAR(100)` and server default `"main"`
- [ ] `repo_path` column exists with type `VARCHAR(500)` and server default `"sdlc-studio"`
- [ ] `access_token` column exists with type `TEXT` and is nullable
- [ ] `sdlc_path` column is nullable

---

### TC0288: Migration 005 applies to existing database with projects

**Type:** Integration | **Priority:** P0 | **Story:** US0028 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A database at migration 004 containing at least two local projects with `sdlc_path` set | Existing data |
| When | Run `alembic upgrade head` to apply migration 005 | Migration executes |
| Then | The migration completes without error and existing project rows are preserved | Data intact |

**Assertions:**
- [ ] Migration exit code is 0
- [ ] Row count in `projects` table is unchanged
- [ ] Existing project `name` and `sdlc_path` values are preserved
- [ ] No data loss or corruption in existing columns

---

### TC0289: Existing projects get source_type="local" default after migration

**Type:** Integration | **Priority:** P0 | **Story:** US0028 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A database at migration 004 containing existing local projects | Pre-migration data |
| When | Migration 005 runs and I query the existing project rows | Check defaults applied |
| Then | Every existing row has `source_type="local"`, `repo_url=NULL`, `repo_branch="main"`, `repo_path="sdlc-studio"`, `access_token=NULL` | Defaults populated |

**Assertions:**
- [ ] All existing rows have `source_type` equal to `"local"`
- [ ] All existing rows have `repo_url` equal to `NULL`
- [ ] All existing rows have `repo_branch` equal to `"main"`
- [ ] All existing rows have `repo_path` equal to `"sdlc-studio"`
- [ ] All existing rows have `access_token` equal to `NULL`

---

### TC0290: Project model accepts github source_type fields

**Type:** Unit | **Priority:** P0 | **Story:** US0028 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The updated Project SQLAlchemy model | Model available |
| When | I create a Project instance with `source_type="github"`, `repo_url="https://github.com/owner/repo"`, `repo_branch="develop"`, `repo_path="docs"`, `access_token="ghp_xxxx1234"` | Instance created |
| Then | All fields are stored correctly on the model instance | Fields accepted |

**Assertions:**
- [ ] `project.source_type` equals `"github"`
- [ ] `project.repo_url` equals `"https://github.com/owner/repo"`
- [ ] `project.repo_branch` equals `"develop"`
- [ ] `project.repo_path` equals `"docs"`
- [ ] `project.access_token` equals `"ghp_xxxx1234"`

---

### TC0291: sdlc_path is nullable for github projects

**Type:** Unit | **Priority:** P0 | **Story:** US0028 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The updated Project model with `sdlc_path` made nullable | Model available |
| When | I create a Project instance with `source_type="github"` and `sdlc_path=None` | Instance created |
| Then | The instance is valid and `sdlc_path` is `None` without raising an error | Nullable accepted |

**Assertions:**
- [ ] `project.sdlc_path` is `None`
- [ ] Persisting to database succeeds (no NOT NULL constraint violation)
- [ ] Querying the row back returns `sdlc_path` as `None`

---

### TC0292: source_type defaults to "local" when not specified

**Type:** Unit | **Priority:** P0 | **Story:** US0028 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The Project model with `server_default="local"` on `source_type` | Model available |
| When | I create a Project instance without explicitly setting `source_type` and persist it | Instance created |
| Then | The stored row has `source_type="local"` | Default applied |

**Assertions:**
- [ ] After flush/commit, the database row has `source_type` equal to `"local"`
- [ ] Reading the instance back from the database confirms the default value

---

### TC0293: repo_branch defaults to "main" when not specified

**Type:** Unit | **Priority:** P1 | **Story:** US0028 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The Project model with `server_default="main"` on `repo_branch` | Model available |
| When | I create a Project instance without explicitly setting `repo_branch` and persist it | Instance created |
| Then | The stored row has `repo_branch="main"` | Default applied |

**Assertions:**
- [ ] After flush/commit, the database row has `repo_branch` equal to `"main"`
- [ ] Reading the instance back from the database confirms the default value

---

## Test Data Requirements

| Data Item | Description | Used By |
|-----------|-------------|---------|
| Local project fixture | Project with `name`, `slug`, `sdlc_path` set (pre-migration) | TC0288, TC0289 |
| GitHub project fixture | Project with `source_type="github"`, `repo_url`, `repo_branch`, `repo_path`, `access_token` | TC0290, TC0291 |
| Empty database | Fresh SQLite file with no tables | TC0287 |
| Migration-004 database | Database with all migrations up to 004 applied | TC0288, TC0289 |

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0287 | Migration 005 applies to fresh database | Pending | - |
| TC0288 | Migration 005 applies to existing database with projects | Pending | - |
| TC0289 | Existing projects get source_type="local" default after migration | Pending | - |
| TC0290 | Project model accepts github source_type fields | Pending | - |
| TC0291 | sdlc_path is nullable for github projects | Pending | - |
| TC0292 | source_type defaults to "local" when not specified | Pending | - |
| TC0293 | repo_branch defaults to "main" when not specified | Pending | - |

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
