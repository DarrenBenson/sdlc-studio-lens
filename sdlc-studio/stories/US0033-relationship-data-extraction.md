# US0033: Relationship Data Extraction

> **Status:** Done
> **Epic:** [EP0008: Document Relationship Navigation](../epics/EP0008-document-relationship-navigation.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-18

## User Story

**As a** SDLC Developer (Darren)
**I want** the sync engine to extract clean document relationship IDs from frontmatter metadata
**So that** parent-child relationships between documents are stored as queryable data for navigation features

## Context

### Persona Reference
**Darren** - Maintains multiple SDLC projects and needs to understand how documents relate to each other in the hierarchy.
[Full persona details](../personas.md#darren)

### Background
SDLC documents encode their parent references in blockquote frontmatter using markdown links:
- Stories reference their epic: `> **Epic:** [EP0007: Git Repository Sync](../epics/EP0007-...md)`
- Plans/test-specs/bugs reference their story: `> **Story:** [US0028: Database Schema](../stories/US0028-...md)`

Currently the parser extracts these as raw metadata strings. The `epic` column on the Document model stores the full markdown link text (e.g., `[EP0007: Git Repository Sync](../epics/EP0007-git-repository-sync.md)`) rather than the clean ID (`EP0007`). There is no `story` column at all.

This story adds a `story` column to the Document model via Alembic migration 006, updates the sync engine to extract clean IDs from markdown link values, and re-populates existing documents on sync.

---

## Inherited Constraints

> See Epic for full constraint chain. Key constraints for this story:

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Tech Stack | SQLAlchemy 2.0 async | New column uses mapped_column |
| TRD | Infrastructure | Alembic migrations | Migration 006 for new column |
| PRD | Business Rule | Change detection via SHA-256 | Relationships refreshed only when file hash changes |
| PRD | KPI | API response < 500ms | Index on epic and story columns |

---

## Acceptance Criteria

### AC1: story column added to Document model
- **Given** the Document SQLAlchemy model
- **When** I inspect the model definition
- **Then** a `story` column of type `String(50)`, nullable, is present alongside the existing `epic` column

### AC2: Alembic migration 006 creates story column
- **Given** a database at migration 005
- **When** I run `alembic upgrade head`
- **Then** the `documents` table has a new `story` column (nullable VARCHAR(50)) with an index

### AC3: Clean ID extraction from markdown links
- **Given** a metadata value like `[EP0007: Git Repository Sync](../epics/EP0007-git-repository-sync.md)`
- **When** the sync engine processes the `epic` field
- **Then** it extracts and stores the clean ID `EP0007`

### AC4: story field extracted from frontmatter
- **Given** a document with frontmatter containing `> **Story:** [US0028: Title](../stories/US0028-...md)`
- **When** the document is synced
- **Then** the `story` column is populated with `US0028`

### AC5: _STANDARD_FIELDS includes story
- **Given** the sync engine's `_STANDARD_FIELDS` set
- **When** I inspect it
- **Then** it includes `"story"` alongside `"status"`, `"owner"`, `"priority"`, `"story_points"`, and `"epic"`

### AC6: Existing documents updated on re-sync
- **Given** existing documents with raw markdown link values in the `epic` column
- **When** a project sync runs
- **Then** the `epic` column is updated to the clean ID and `story` is populated where applicable

### AC7: Plain text values preserved
- **Given** a metadata value that is already a plain ID (e.g., `EP0007`) with no markdown link
- **When** the sync engine processes it
- **Then** the plain value is stored unchanged

### AC9: Plain text with title extracts clean ID
- **Given** a metadata value like `US0163: Container Service Status` (plain text, no markdown link)
- **When** the sync engine processes the `story` field
- **Then** it extracts and stores the clean ID `US0163`

### AC8: Null values handled
- **Given** a document type that has no `epic` or `story` in its frontmatter (e.g., a PRD or epic)
- **When** the document is synced
- **Then** the `epic` and `story` columns remain NULL

---

## Scope

### In Scope
- Add `story` column to `Document` model (`String(50)`, nullable, indexed)
- Alembic migration 006 with index on both `epic` and `story` columns
- Utility function to extract clean document ID from markdown link text
- Update `_build_doc_attrs` to clean `epic` and `story` values before storing
- Add `"story"` to `_STANDARD_FIELDS` in sync_engine.py
- Data migration: existing `epic` values cleaned on next sync (not in Alembic migration)

### Out of Scope
- API changes (US0034)
- Frontend changes (US0035, US0036)
- Cross-project relationship validation
- Relationship validation (checking referenced documents exist)
- Cleaning existing data via Alembic data migration (happens on sync)

---

## Technical Notes

### ID Extraction Regex
```python
import re

_MD_LINK_ID_RE = re.compile(r"^\[([A-Z]{2}\d{4})")
_PLAIN_ID_RE = re.compile(r"^([A-Z]{2}\d{4})\b")

def extract_doc_id(value: str | None) -> str | None:
    """Extract clean document ID from a markdown link or plain text.

    Examples:
        "[EP0007: Title](path)" -> "EP0007"
        "US0163: Container Service Status" -> "US0163"
        "EP0007" -> "EP0007"
        None -> None
    """
    if not value:
        return None
    stripped = value.strip()
    match = _MD_LINK_ID_RE.match(stripped)
    if match:
        return match.group(1)
    match = _PLAIN_ID_RE.match(stripped)
    if match:
        return match.group(1)
    return stripped
```

### Document Model Change
```python
# document.py - add after epic column
story: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
```

Also add `index=True` to the existing `epic` column.

### Sync Engine Changes
Update `_STANDARD_FIELDS`:
```python
_STANDARD_FIELDS = frozenset(
    {"status", "owner", "priority", "story_points", "epic", "story"}
)
```

Update `_build_doc_attrs` to clean values:
```python
"epic": extract_doc_id(parsed_meta.get("epic")),
"story": extract_doc_id(parsed_meta.get("story")),
```

### Migration 006
```python
# Add story column and index on both columns
op.add_column("documents", sa.Column("story", sa.String(50), nullable=True))
op.create_index("ix_documents_story", "documents", ["story"])
op.create_index("ix_documents_epic", "documents", ["epic"])
```

### Data Requirements
No Alembic data migration needed. Existing `epic` values will be cleaned on the next sync when the file hash comparison detects changes, or by clearing stored hashes to force a full re-parse. Since the extraction function handles markdown links, plain text with titles, and bare IDs, documents synced after this change will always have clean values.

**Note:** After deploying new extraction logic, existing documents with unchanged content are skipped by the hash-based change detection. To force re-parsing, clear the `file_hash` column for the project's documents, then re-sync.

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Markdown link: `[EP0007: Title](path)` | Extracts `EP0007` |
| Plain text: `EP0007` | Stores `EP0007` unchanged |
| Multi-line value (continuation) | Extracts ID from first line |
| Empty string | Stores NULL |
| None/missing field | Stores NULL |
| Plain text with title: `US0163: Container Status` | Extracts `US0163` |
| Malformed link: `[No ID](path)` | Stores raw value as fallback |
| Link with no colon: `[EP0007](path)` | Extracts `EP0007` |
| Bug reference: `[BG0001: Title](path)` | Extracts `BG0001` |
| Value with extra whitespace | Trimmed before extraction |

---

## Test Scenarios

- [ ] extract_doc_id extracts ID from markdown link with title
- [ ] extract_doc_id returns plain ID unchanged
- [ ] extract_doc_id returns None for None input
- [ ] extract_doc_id returns None for empty string
- [ ] extract_doc_id handles link without colon-title
- [ ] extract_doc_id returns raw value for non-matching format
- [ ] Document model has story column (nullable)
- [ ] Migration 006 adds story column and indexes
- [ ] _STANDARD_FIELDS includes "story"
- [ ] _build_doc_attrs cleans epic markdown link to plain ID
- [ ] _build_doc_attrs populates story from metadata
- [ ] Sync correctly stores clean epic ID for stories
- [ ] Sync correctly stores clean story ID for plans/test-specs
- [ ] Documents without epic/story have NULL values
- [ ] Re-sync updates existing documents with clean IDs

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| None | - | No story dependencies (builds on existing EP0001/EP0002 infrastructure) | - |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

---

## Estimation

**Story Points:** 3
**Complexity:** Medium

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-18 | Claude | Initial story creation from EP0008 |
| 2026-02-18 | Claude | Added AC9 for plain text ID extraction; updated regex and data notes |
