# PL0028: Database Schema & Project Model - Implementation Plan

> **Status:** Done
> **Story:** [US0028: Database Schema & Project Model](../stories/US0028-database-schema-github-source.md)
> **Epic:** [EP0007: GitHub Repository Sync](../epics/EP0007-github-repository-sync.md)
> **Owner:** Darren
> **Created:** 2026-02-18
> **Language:** Python / SQL

## Overview

Extend the `Project` SQLAlchemy model with columns that support GitHub as an alternative document source. The existing `sdlc_path` column becomes nullable (GitHub projects have no local path), and five new columns are added: `source_type` (defaulting to `"local"` for backward compatibility), `repo_url`, `repo_branch`, `repo_path`, and `access_token`. An Alembic migration applies these changes to existing databases without data loss.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | New columns present | `source_type`, `repo_url`, `repo_branch`, `repo_path`, `access_token` exist on the `projects` table |
| AC2 | Backward compatibility | Existing rows get `source_type="local"` and retain their `sdlc_path` value |
| AC3 | sdlc_path nullable | GitHub-source projects can have `sdlc_path=NULL` |
| AC4 | Migration reversible | `alembic downgrade` removes the new columns and restores `sdlc_path` NOT NULL |
| AC5 | Defaults applied | `repo_branch` defaults to `"main"`, `repo_path` defaults to `"sdlc-studio"` |

---

## Technical Context

### Language & Framework
- **ORM:** SQLAlchemy 2.0 async with `Mapped[]` type annotations
- **Database:** SQLite via aiosqlite
- **Migrations:** Alembic with batch mode for SQLite ALTER TABLE limitations

### Existing Patterns

The `Project` model is at `backend/src/sdlc_lens/db/models/project.py` and uses `mapped_column()` with explicit types. Alembic migrations are in `backend/alembic/versions/` with sequential numbering (`001_`, `002_`, etc.). SQLite requires `batch_alter_table` for column alterations.

### Dependencies
- None (first story in EP0007)

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** Model changes are testable by creating rows with the new columns and verifying defaults. Migration correctness is verified by running `alembic upgrade head` on an existing database and checking that existing rows are unaffected.

### Test Priority
1. Migration applies cleanly to existing database
2. Existing projects retain `source_type="local"` after migration
3. New GitHub project can be created with `sdlc_path=NULL`
4. Default values for `repo_branch` and `repo_path` are applied
5. Downgrade removes columns and restores NOT NULL on `sdlc_path`

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Add GitHub source columns to Project model | `backend/src/sdlc_lens/db/models/project.py` | - | [ ] |
| 2 | Create Alembic migration | `backend/alembic/versions/005_add_github_source_columns.py` | 1 | [ ] |
| 3 | Verify migration on existing database | manual | 2 | [ ] |
| 4 | Verify downgrade path | manual | 3 | [ ] |

---

## Implementation Phases

### Phase 1: Model Changes

**Goal:** Add new columns to the `Project` model for GitHub source support.

- [ ] Update `backend/src/sdlc_lens/db/models/project.py`:

```python
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sdlc_path: Mapped[str | None] = mapped_column(Text, nullable=True)  # was NOT NULL
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="local"
    )
    repo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    repo_branch: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default="main"
    )
    repo_path: Mapped[str] = mapped_column(
        String(500), nullable=False, server_default="sdlc-studio"
    )
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    sync_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="never_synced"
    )
    # ... remaining columns unchanged
```

**Key change:** `sdlc_path` type changes from `Mapped[str]` to `Mapped[str | None]` and `nullable=True` replaces `nullable=False`.

**Files:**
- `backend/src/sdlc_lens/db/models/project.py`

### Phase 2: Alembic Migration

**Goal:** Create migration that adds new columns and makes `sdlc_path` nullable.

- [ ] Create `backend/alembic/versions/005_add_github_source_columns.py`:

```python
"""Add GitHub source columns to projects table.

Revision ID: 005
Revises: 004
Create Date: 2026-02-18
"""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("source_type", sa.String(20), nullable=False, server_default="local"),
    )
    op.add_column(
        "projects",
        sa.Column("repo_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("repo_branch", sa.String(255), nullable=False, server_default="main"),
    )
    op.add_column(
        "projects",
        sa.Column("repo_path", sa.String(500), nullable=False, server_default="sdlc-studio"),
    )
    op.add_column(
        "projects",
        sa.Column("access_token", sa.Text(), nullable=True),
    )
    # Make sdlc_path nullable (SQLite requires batch mode)
    with op.batch_alter_table("projects") as batch_op:
        batch_op.alter_column("sdlc_path", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    # Restore sdlc_path NOT NULL (existing GitHub rows would need manual fix)
    with op.batch_alter_table("projects") as batch_op:
        batch_op.alter_column(
            "sdlc_path", existing_type=sa.Text(), nullable=False, server_default=""
        )
    op.drop_column("projects", "access_token")
    op.drop_column("projects", "repo_path")
    op.drop_column("projects", "repo_branch")
    op.drop_column("projects", "repo_url")
    op.drop_column("projects", "source_type")
```

**Design decisions:**
- **`server_default="local"`** on `source_type` ensures all existing rows are automatically classified as local sources.
- **`batch_alter_table`** is required for SQLite, which does not support `ALTER COLUMN` directly.
- **Downgrade** sets a server_default of `""` on `sdlc_path` as a safety net, since any GitHub-source rows would have NULL. In practice, GitHub rows should be deleted before downgrading.

**Files:**
- `backend/alembic/versions/005_add_github_source_columns.py`

### Phase 3: Testing and Validation

**Goal:** Verify migration applies cleanly and backward compatibility is maintained.

- [ ] Run `alembic upgrade head` on existing database with projects
- [ ] Verify existing projects have `source_type="local"` and `sdlc_path` intact
- [ ] Create a new project row with `source_type="github"`, `repo_url` set, `sdlc_path=NULL`
- [ ] Verify `repo_branch` defaults to `"main"` and `repo_path` defaults to `"sdlc-studio"`
- [ ] Run `alembic downgrade -1` and verify columns are removed
- [ ] Run backend tests: `cd backend && PYTHONPATH=src python -m pytest`

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | Query `pragma_table_info('projects')` after migration | migration file | Pending |
| AC2 | `SELECT source_type FROM projects` returns `"local"` for all existing rows | migration `server_default` | Pending |
| AC3 | `INSERT` with `sdlc_path=NULL` succeeds | model change | Pending |
| AC4 | `alembic downgrade -1` removes columns | downgrade function | Pending |
| AC5 | `SELECT repo_branch, repo_path` returns defaults for new rows | `server_default` values | Pending |

---

## Edge Case Handling

| # | Edge Case | Handling Strategy | Phase |
|---|-----------|-------------------|-------|
| 1 | Existing database with projects (upgrade) | `server_default="local"` populates `source_type` automatically | Phase 2 |
| 2 | Downgrade with GitHub-source rows | `server_default=""` on `sdlc_path` prevents NOT NULL violation; data note in migration docstring | Phase 2 |
| 3 | Empty access_token vs NULL | Both treated as "no token"; API layer normalises empty string to NULL | Phase 1 |
| 4 | SQLite ALTER TABLE limitations | `batch_alter_table` used for column nullability change | Phase 2 |

**Coverage:** 4/4 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| SQLite batch mode recreates table | Medium | Tested in isolation; batch mode is the standard Alembic pattern for SQLite |
| Existing tests assume sdlc_path is NOT NULL | Medium | Update test fixtures to provide sdlc_path for local projects; new tests for GitHub projects |
| access_token stored in plaintext | Low | Documented as a known limitation; token masking in API layer (PL0031) |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Migration applies and downgrades cleanly
- [ ] Existing backend tests still pass
- [ ] Project model has all new columns with correct types and defaults
- [ ] Ruff linting passes

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-18 | Darren | Initial plan created |
