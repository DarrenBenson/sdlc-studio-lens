# US0028: Database Schema & Project Model

> **Status:** Done
> **Epic:** [EP0007: Git Repository Sync](../epics/EP0007-git-repository-sync.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-18

## User Story

**As a** SDLC Developer (Darren)
**I want** the Project model to support GitHub repository source fields alongside the existing local path
**So that** projects can be configured to sync from either a local directory or a remote GitHub repository

## Context

### Persona Reference
**Darren** - Manages multiple SDLC projects, some local and some hosted on GitHub.
[Full persona details](../personas.md#darren)

### Background
The current Project model assumes all projects sync from a local filesystem path via `sdlc_path`. To support GitHub repository sync, the model needs additional columns: `source_type` to distinguish local from GitHub sources, `repo_url` for the repository address, `repo_branch` for the target branch, `repo_path` for the subdirectory within the repository, and `access_token` for private repository authentication. The `sdlc_path` column must become nullable since GitHub-sourced projects do not require a local path. An Alembic migration (005) handles the schema change with `server_default="local"` so existing rows remain valid.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Database | SQLite via aiosqlite | Migration must be SQLite-compatible |
| TRD | ORM | SQLAlchemy 2.0 async | New columns defined as mapped_column |
| TRD | Migrations | Alembic for schema changes | New migration 005 required |
| PRD | Architecture | Backward compatibility with existing data | server_default ensures existing rows valid |

---

## Acceptance Criteria

### AC1: New columns on Project model
- **Given** the updated Project model in `models/project.py`
- **When** I inspect the model definition
- **Then** the following columns exist: `source_type` (String, default "local"), `repo_url` (Text, nullable), `repo_branch` (String, default "main"), `repo_path` (String, default "sdlc-studio"), `access_token` (Text, nullable)

### AC2: sdlc_path nullable
- **Given** the updated Project model
- **When** a project has `source_type="github"`
- **Then** `sdlc_path` can be NULL without violating any constraint

### AC3: Alembic migration 005
- **Given** a database at migration 004
- **When** I run `alembic upgrade head`
- **Then** the migration adds the five new columns with correct types and defaults, and alters `sdlc_path` to be nullable

### AC4: Backward compatibility
- **Given** an existing database with local-only projects
- **When** the migration runs
- **Then** all existing rows have `source_type="local"` via server_default and all other new columns are NULL

### AC5: Downgrade support
- **Given** the database at migration 005
- **When** I run `alembic downgrade -1`
- **Then** the new columns are removed and `sdlc_path` is restored to non-nullable

---

## Scope

### In Scope
- Add five new columns to the Project model
- Make `sdlc_path` nullable
- Alembic migration 005 (upgrade and downgrade)
- server_default="local" for `source_type`

### Out of Scope
- API schema changes (US0031)
- GitHub API integration (US0029)
- Frontend changes (US0032)
- Encryption of access_token at rest

---

## Technical Notes

### Column Definitions
```python
source_type: Mapped[str] = mapped_column(String(20), server_default="local")
repo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
repo_branch: Mapped[str] = mapped_column(String(100), server_default="main")
repo_path: Mapped[str] = mapped_column(String(500), server_default="sdlc-studio")
access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
```

### Migration Notes
- SQLite `ALTER TABLE` supports `ADD COLUMN` but not `ALTER COLUMN`. Making `sdlc_path` nullable may require batch mode in Alembic (`render_as_batch=True`).
- `server_default` ensures the database engine sets the default, not just the ORM.

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Existing project with sdlc_path set | Unchanged; source_type defaults to "local" |
| New GitHub project without sdlc_path | Valid; sdlc_path is NULL |
| New local project without sdlc_path | Should fail validation at API layer (US0031) |
| Migration on empty database | Creates columns with no rows to migrate |
| Downgrade after GitHub projects created | GitHub projects lose new columns; sdlc_path becomes non-nullable (may fail if NULL values exist) |
| access_token stored as plaintext | Acceptable for MVP; encryption is out of scope |

---

## Test Scenarios

- [ ] Migration 005 runs successfully on existing database
- [ ] Existing projects have source_type="local" after migration
- [ ] New columns have correct types and defaults
- [ ] sdlc_path accepts NULL values after migration
- [ ] Downgrade removes new columns
- [ ] Project model can be created with source_type="github" and repo_url set
- [ ] Project model can be created with source_type="local" and sdlc_path set
- [ ] Default values applied when columns not explicitly set

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| All EP0001-EP0006 stories | Code | Existing Project model and migration 004 | Done |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Alembic | Library | Available |
| SQLAlchemy 2.0 | Library | Available |

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
