# PL0033: Relationship Data Extraction - Implementation Plan

> **Status:** Complete
> **Story:** [US0033: Relationship Data Extraction](../stories/US0033-relationship-data-extraction.md)
> **Epic:** [EP0008: Document Relationship Navigation](../epics/EP0008-document-relationship-navigation.md)
> **Created:** 2026-02-18
> **Language:** Python 3.12

## Overview

Add a `story` column to the Document model, create a utility to extract clean document IDs from markdown link values, and update the sync engine to store clean IDs in both `epic` and `story` columns. Alembic migration 006 adds the column with indexes.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | story column added | Document model has story column (String(50), nullable) |
| AC2 | Migration 006 | Alembic migration adds story column and indexes |
| AC3 | Clean ID extraction | Extracts EP0007 from `[EP0007: Title](path)` |
| AC4 | story field extracted | Documents with story frontmatter get story column populated |
| AC5 | _STANDARD_FIELDS | Includes "story" |
| AC6 | Existing docs updated | Re-sync cleans epic values and populates story |
| AC7 | Plain text preserved | Already-clean values stored unchanged |
| AC8 | Null values handled | Docs without epic/story get NULL |

---

## Technical Context

### Language & Framework
- **Primary Language:** Python 3.12
- **Framework:** FastAPI + SQLAlchemy 2.0 async
- **Test Framework:** pytest + pytest-asyncio

### Existing Patterns
- Document model in `db/models/document.py` uses `mapped_column`
- Sync engine in `services/sync_engine.py` has `_build_doc_attrs()` and `_STANDARD_FIELDS`
- Migration files in `alembic/versions/` use `op.add_column` and `op.batch_alter_table`
- Parser returns metadata dict with raw string values

---

## Recommended Approach

**Strategy:** Test-After
**Rationale:** Small, well-defined changes across 3 files + migration. Clear regex logic. Writing code first then validating with tests is efficient here.

---

## Implementation Phases

### Phase 1: Database Changes
**Goal:** Add story column and indexes

- [ ] Add `story` column to Document model
- [ ] Add `index=True` to existing `epic` column
- [ ] Create migration 006

**Files:**
- `db/models/document.py` - Add story column, add index to epic
- `alembic/versions/006_add_story_column.py` - New migration

### Phase 2: ID Extraction Utility
**Goal:** Clean markdown link values to plain IDs

- [ ] Create `extract_doc_id()` function in sync_engine.py
- [ ] Add "story" to `_STANDARD_FIELDS`
- [ ] Update `_build_doc_attrs()` to clean epic and story values

**Files:**
- `services/sync_engine.py` - Add utility, update _STANDARD_FIELDS, update _build_doc_attrs

### Phase 3: Testing & Validation
**Goal:** Verify all acceptance criteria

| AC | Verification Method | Status |
|----|---------------------|--------|
| AC1 | Check Document model has story column | Pending |
| AC2 | Run migration, check schema | Pending |
| AC3 | Unit test extract_doc_id with markdown links | Pending |
| AC4 | Integration test sync with story frontmatter | Pending |
| AC5 | Inspect _STANDARD_FIELDS | Pending |
| AC6 | Integration test re-sync cleans values | Pending |
| AC7 | Unit test extract_doc_id with plain text | Pending |
| AC8 | Integration test docs without epic/story | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | Markdown link: `[EP0007: Title](path)` | Regex extracts first group `EP0007` | Phase 2 |
| 2 | Plain text: `EP0007` | No match → return value unchanged | Phase 2 |
| 3 | Multi-line value | Extract from first part only | Phase 2 |
| 4 | Empty string | Return None | Phase 2 |
| 5 | None/missing field | Return None | Phase 2 |
| 6 | Malformed link: `[No ID](path)` | No match → return raw value | Phase 2 |
| 7 | Link without colon: `[EP0007](path)` | Regex handles (captures before `]`) | Phase 2 |
| 8 | Bug reference: `[BG0001: Title](path)` | Same regex pattern works | Phase 2 |
| 9 | Value with extra whitespace | Strip before matching | Phase 2 |

**Coverage:** 9/9 edge cases handled

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit tests written and passing
- [ ] Edge cases handled
- [ ] Code follows best practices
- [ ] No linting errors
- [ ] Existing tests still pass
