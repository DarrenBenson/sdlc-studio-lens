# EP0008: Document Relationship Navigation

> **Status:** Done
> **Owner:** Darren
> **Created:** 2026-02-18
> **Target Release:** Phase 5 (Navigation)
> **Story Points:** 16

## Summary

Add hierarchical navigation between SDLC documents. Documents in sdlc-studio follow a tree structure (PRD → Epics → Stories → Plans/Test Specs/Bugs) with parent references encoded in frontmatter markdown links. This epic extracts those relationships into queryable data, exposes them via API, and adds frontend breadcrumbs, related document panels, and a tree view so users can navigate up and down the document hierarchy from any level.

## Inherited Constraints

Constraints that flow from PRD and TRD to this Epic.

### From PRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Architecture | Read-only access to document sources | Relationships inferred from parsed metadata, not written back |
| Business Rule | Manual sync only | Relationship data refreshed on sync, not real-time |
| Business Rule | Change detection via SHA-256 | Relationship data updated only when file content changes |
| KPI | API response < 500ms | Relationship queries must be efficient (indexed columns) |

### From TRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Tech Stack | SQLAlchemy 2.0 async | New column uses mapped_column with async session |
| Tech Stack | Pydantic v2 | Response schemas extended with relationship fields |
| Infrastructure | Alembic migrations | Migration 006 for new `story` column |
| Architecture | Single container | No new dependencies needed |

> **Note:** Inherited constraints MUST propagate to child Stories. Check Story templates include these constraints.

## Business Context

### Problem Statement

SDLC Studio Lens displays documents as a flat list within each project. Users cannot see the hierarchical relationships between documents - for example, which stories belong to an epic, or which plans and test specs relate to a story. Navigating the document tree requires manually reading frontmatter references and searching for related documents.

**PRD Reference:** [§5 Feature Inventory](../prd.md#5-feature-inventory) (FR10)

### Value Proposition

Document relationship navigation lets users traverse the SDLC document tree from any level. Clicking an epic shows its child stories; clicking a story shows its parent epic and child plans, test specs, and bugs. Breadcrumbs show the full path from PRD to current document. A tree view provides an at-a-glance project structure.

### Success Metrics

| Metric | Current State | Target | Measurement Method |
|--------|---------------|--------|-------------------|
| Navigation clicks to reach related doc | 3-5 (search/filter) | 1 (direct link) | User flow analysis |
| Document hierarchy visibility | None | Full tree view | Feature test |
| Relationship data accuracy | N/A | 100% (matches frontmatter) | Automated tests |
| Existing test regression | 451 tests pass | 451 tests still pass | Test suite |

## Scope

### In Scope

- Extract clean document IDs from frontmatter markdown links (e.g., "EP0007" from `[EP0007: Title](path)`)
- Add `story` column to Document model; Alembic migration 006
- Store clean parent IDs in `epic` and `story` columns (not raw markdown links)
- New API endpoint returning parent chain and child documents for any document
- Frontend breadcrumb component showing hierarchy path on DocumentView
- Frontend related documents panel showing parent and children on DocumentView
- Frontend document tree view page showing expandable project hierarchy
- Re-parse existing documents on sync to populate clean relationship data

### Out of Scope

- Cross-project relationships (documents only link within the same project)
- Editing or creating relationships (read-only, inferred from frontmatter)
- Graphical relationship visualisation (node graph, force-directed layout)
- Custom relationship types beyond the standard hierarchy
- Relationship validation (e.g., checking that referenced documents exist)

### Affected User Personas

- **SDLC Developer (Darren):** Navigates between related documents, reviews project structure

## Acceptance Criteria (Epic Level)

- [ ] From any story, user can navigate to its parent epic in one click
- [ ] From any story, user can see its child plans, test specs, and bugs
- [ ] From any epic, user can see its child stories
- [ ] From any plan or test spec, user can navigate to its parent story and grandparent epic
- [ ] Breadcrumbs show the full hierarchy path (Project → Epic → Story → Document)
- [ ] A tree view shows the complete document hierarchy for a project
- [ ] Relationship data is extracted from frontmatter markdown links during sync
- [ ] All existing tests pass without modification
- [ ] New tests cover relationship extraction, API, and frontend components

## Dependencies

### Blocked By

| Dependency | Type | Status | Owner | Notes |
|------------|------|--------|-------|-------|
| EP0001: Project Management | Epic | Done | Darren | Project and document models |
| EP0002: Document Sync & Parsing | Epic | Done | Darren | Parser and sync engine |
| EP0003: Document Browsing | Epic | Done | Darren | DocumentView page to enhance |

### Blocking

| Item | Type | Impact |
|------|------|--------|
| None | - | Enhancement epic, no downstream blockers |

## Risks & Assumptions

### Assumptions

- All sdlc-studio documents use the standard frontmatter format with markdown links for references
- Parent references use `> **Epic:** [ID: Title](path)` and `> **Story:** [ID: Title](path)` patterns
- Document IDs can be reliably extracted from the `[ID: Title]` portion of markdown links
- The document hierarchy is strictly: PRD → Epics → Stories → Plans/Test Specs/Bugs
- PRD, TRD, and TSD are singleton top-level documents (one per project)

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Inconsistent frontmatter link formats | Low | Medium | Regex handles common variations; fallback to raw text |
| Circular references in metadata | Low | Low | Tree traversal has depth limit; parent chain is linear |
| Large projects slow down tree rendering | Low | Medium | Lazy-load children; limit initial expansion depth |
| Missing references (dangling links) | Medium | Low | Show "unknown" for unresolved references; don't break UI |

## Technical Considerations

### Architecture Impact

- Document model gains 1 new column (`story`)
- Existing `epic` column repurposed to store clean IDs (was storing raw markdown link text)
- New relationship extraction utility in parser or sync engine
- New API endpoint for relationship queries
- Frontend DocumentView enhanced with breadcrumbs and related docs panel
- New frontend tree view page/component

### Integration Points

- Existing parser (frontmatter extraction)
- Existing sync engine (document attribute building)
- DocumentView page (enhanced with navigation)
- Document API (new relationship endpoint)
- React Router (new tree view route)

### Data Considerations

- Migration 006 adds `story` column (nullable VARCHAR)
- Existing `epic` values need cleaning (strip markdown link syntax to just ID)
- Data migration within 006: parse existing `epic` values to extract clean IDs
- `story` column populated on next sync (or via data migration for existing docs)
- Index on `epic` and `story` columns for efficient child queries

### Document Hierarchy Model

```
PRD (type: prd)          - Top level, no parent
├── TRD (type: trd)      - Top level, no parent
├── TSD (type: tsd)      - Top level, no parent
└── Epics (type: epic)   - Parent: none (top-level under PRD umbrella)
    └── Stories (type: story)      - Parent: epic (via `epic` column)
        ├── Plans (type: plan)     - Parent: story (via `story` column)
        ├── Test Specs (type: test-spec) - Parent: story (via `story` column)
        └── Bugs (type: bug)       - Parent: story (via `story` column)
```

**TRD Reference:** [§6 Data Architecture](../trd.md#6-data-architecture)

## Sizing & Effort

**Story Points:** 16
**Estimated Story Count:** 4 stories

**Complexity Factors:**

- Regex parsing of markdown link references with edge cases
- Data migration to clean existing `epic` column values
- Recursive parent chain building for breadcrumbs
- Frontend tree component with expand/collapse state
- Efficient child document queries (indexed lookups)

## Stakeholders

| Role | Name | Interest |
|------|------|----------|
| Product Owner | Darren | Primary user, defines requirements |
| Developer | Darren/Claude | Implementation |

## Story Breakdown

| ID | Title | Complexity | Status |
|----|-------|------------|--------|
| [US0033](../stories/US0033-relationship-data-extraction.md) | Relationship Data Extraction | Medium | Done |
| [US0034](../stories/US0034-relationships-api.md) | Relationships API | Medium | Done |
| [US0035](../stories/US0035-document-view-navigation.md) | Document View Navigation | Medium | Done |
| [US0036](../stories/US0036-document-tree-view.md) | Document Tree View | Medium | Done |

## Test Plan

**Test Specs:** [TS0033](../test-specs/TS0033-relationship-data-extraction.md), [TS0034](../test-specs/TS0034-relationships-api.md), [TS0035](../test-specs/TS0035-document-view-navigation.md), [TS0036](../test-specs/TS0036-document-tree-view.md) (all Complete).

## Open Questions

None.

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-18 | Claude | Initial epic creation from PRD FR10 |
