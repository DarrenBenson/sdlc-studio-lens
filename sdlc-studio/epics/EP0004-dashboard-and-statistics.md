# EP0004: Dashboard & Statistics

> **Status:** Done
> **Owner:** Darren
> **Created:** 2026-02-17
> **Target Release:** Phase 2 (Browsing & Dashboard)
> **Story Points:** 15

## Summary

Multi-project dashboard with project cards, document counts, status breakdowns, completion percentages, and progress visualisations. This epic delivers the landing page experience: a data-dense overview of all registered projects and their SDLC health at a glance.

## Inherited Constraints

Constraints that flow from PRD and TRD to this Epic.

### From PRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Performance | Dashboard load < 2 seconds | Stats queries must be fast; consider caching |
| Design | Dark theme with lime green accents ([Brand Guide](../brand-guide.md)) | Progress rings and charts use brand guide colour system |
| Design | Space Grotesk headings, JetBrains Mono for stats | Typography locked per brand guide §4 |
| KPI | Completion = Done stories / Total stories | Specific formula for progress calculation |

### From TRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| API | GET /api/v1/projects/{slug}/stats | Per-project statistics |
| API | GET /api/v1/stats | Aggregated cross-project statistics |
| Tech Stack | Recharts (>=2.10.0) | React-native charting library |
| Data | Statistics calculated from documents table | No separate stats table; aggregate at query time |

> **Note:** Inherited constraints MUST propagate to child Stories. Check Story templates include these constraints.

## Business Context

### Problem Statement

With multiple sdlc-studio projects, developers need a consolidated view of project health without clicking into each one. Manually counting document statuses across files is error-prone and tedious.

**PRD Reference:** [§5 Feature Inventory](../prd.md#5-feature-inventory) (FR6)

### Value Proposition

A single dashboard page shows every registered project's status, document counts, and completion percentage. Progress rings and charts make it visual. The developer checks project health in seconds rather than minutes.

### Success Metrics

| Metric | Current State | Target | Measurement Method |
|--------|---------------|--------|-------------------|
| Time to assess project health | 5+ minutes per project | < 10 seconds (glance at dashboard) | User observation |
| Dashboard load time | N/A | < 2 seconds | Browser DOMContentLoaded |
| Statistics accuracy | N/A | 100% match to document data | Test assertions |

## Scope

### In Scope

- Dashboard page (landing page at `/`)
- Project cards showing: name, document count, completion %, last synced
- Per-project statistics endpoint (counts by type, counts by status, completion %)
- Aggregated statistics endpoint (totals across all projects)
- Progress ring component for story completion
- Status breakdown visualisation (bar or donut chart)
- Document type distribution visualisation
- Last-synced-at timestamp per project card
- Project detail page with expanded statistics
- Zero-project empty state with "Add Project" prompt
- Clicking project card navigates to project detail

### Out of Scope

- Recent activity feed (P2, deferred)
- Trend charts over time (no historical stats tracking in v1.0)
- Custom dashboard layouts
- Statistics export (JSON/CSV)
- Configurable dashboard widgets

### Affected User Personas

- **SDLC Developer (Darren):** Checks project health at the start of work sessions; views completion metrics to plan next work

## Acceptance Criteria (Epic Level)

- [ ] Dashboard shows a card for each registered project
- [ ] Each project card displays document count and completion percentage
- [ ] Completion percentage calculated as Done stories / Total stories
- [ ] Progress ring renders percentage correctly with emerald green fill
- [ ] Status breakdown chart shows distribution of document statuses
- [ ] Last-synced-at timestamp appears on each card
- [ ] Clicking a project card navigates to project detail page
- [ ] Project detail shows per-type document counts
- [ ] Aggregated stats across all projects display correctly
- [ ] Dashboard handles zero registered projects with helpful empty state
- [ ] Dashboard loads in < 2 seconds

## Dependencies

### Blocked By

| Dependency | Type | Status | Owner | Notes |
|------------|------|--------|-------|-------|
| EP0002: Document Sync & Parsing | Epic | Draft | Darren | Need synced document data for statistics |

### Blocking

| Item | Type | Impact |
|------|------|--------|
| None | - | - |

## Risks & Assumptions

### Assumptions

- Recharts renders correctly within dark theme styling
- Completion percentage is meaningful (projects have stories)
- Statistics queries are fast enough without denormalisation (< 100ms for 2000 docs)
- JetBrains Mono and Space Grotesk fonts load without layout shift

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Stats queries slow with many documents | Low | Medium | Add database indices; consider query-time aggregation |
| Progress ring not readable at small sizes | Low | Low | Test at various card sizes; set minimum diameter |
| Recharts bundle size too large | Medium | Low | Use tree-shaking; import only needed chart types |

## Technical Considerations

### Architecture Impact

- Creates ProgressRing and StatsCard reusable components
- Introduces Recharts dependency for charting
- Establishes the dashboard as the application landing page
- Statistics API returns pre-calculated aggregates (no N+1 queries)

### Integration Points

- Dashboard page → GET /api/v1/projects (project list with stats summary)
- Dashboard page → GET /api/v1/stats (aggregate stats)
- Project detail → GET /api/v1/projects/{slug}/stats
- ProgressRing → completion_percentage from stats response
- Recharts → by_type and by_status from stats response

### Data Considerations

- Statistics calculated via SQL GROUP BY on documents table
- No separate statistics table needed at this scale
- Completion percentage: `COUNT(status='Done' AND doc_type='story') / COUNT(doc_type='story') * 100`
- Zero-division handling when project has no stories

**TRD Reference:** [§5 API Contracts](../trd.md#5-api-contracts)

## Sizing & Effort

**Story Points:** 15
**Estimated Story Count:** ~4 stories

**Complexity Factors:**

- Recharts integration with custom dark theme styling
- Progress ring SVG component (circular arc rendering)
- Statistics aggregation queries (GROUP BY type, GROUP BY status)
- Responsive card layout within dashboard grid
- Empty state design and implementation

## Stakeholders

| Role | Name | Interest |
|------|------|----------|
| Product Owner | Darren | Primary user, defines requirements |
| Developer | Darren/Claude | Implementation |

## Story Breakdown

| ID | Title | Complexity | Status |
|----|-------|------------|--------|
| [US0017](../stories/US0017-statistics-api-endpoints.md) | Statistics API Endpoints | Medium | Done |
| [US0018](../stories/US0018-dashboard-page.md) | Multi-Project Dashboard Page | Medium | Done |
| [US0019](../stories/US0019-project-detail-statistics-page.md) | Project Detail Statistics Page | Medium | Done |
| [US0020](../stories/US0020-progress-ring-and-chart-components.md) | Progress Ring and Chart Components | Medium | Done |

## Test Plan

**Test Spec:** To be generated via `/sdlc-studio test-spec --epic EP0004`.

## Open Questions

None.

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial epic creation from PRD |
