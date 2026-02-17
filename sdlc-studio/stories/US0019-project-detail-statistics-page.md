# US0019: Project Detail Statistics Page

> **Status:** Done
> **Epic:** [EP0004: Dashboard & Statistics](../epics/EP0004-dashboard-and-statistics.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** a project detail page with type and status charts and a progress ring
**So that** I can see a detailed breakdown of a single project's health

## Context

### Persona Reference
**Darren** - Clicks into a specific project to understand its detailed status breakdown.
[Full persona details](../personas.md#darren)

### Background
The project detail page expands on the dashboard card. It shows a larger progress ring, a document type distribution chart (bar or donut), a status breakdown chart, and per-type document counts. It provides the detailed view before diving into the document list.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Design | Brand Guide colour system | Charts use brand guide chart tokens |
| TRD | Tech Stack | Recharts (>=2.10.0) | Chart components |
| TRD | API | GET /projects/{slug}/stats | Data source |

---

## Acceptance Criteria

### AC1: Project header with progress ring
- **Given** I navigate to `/projects/homelabcmd`
- **When** the page loads
- **Then** I see the project name, a large progress ring showing completion percentage, and last synced timestamp

### AC2: Document type distribution chart
- **Given** project stats include by_type: {epic: 18, story: 120, bug: 5, ...}
- **When** the page renders
- **Then** a bar or donut chart shows the document type distribution with correct proportions

### AC3: Status breakdown chart
- **Given** project stats include by_status: {Done: 145, In Progress: 4, Draft: 2, ...}
- **When** the page renders
- **Then** a chart shows the status distribution using brand guide status colours

### AC4: Per-type count cards
- **Given** project has 18 epics, 120 stories, 5 bugs
- **When** I view the detail page
- **Then** individual stat cards show counts per type (e.g., "18 Epics", "120 Stories", "5 Bugs")

### AC5: Navigate to documents
- **Given** I am on the project detail page
- **When** I click a type count card (e.g., "120 Stories")
- **Then** I navigate to `/projects/homelabcmd/documents?type=story`

---

## Scope

### In Scope
- Project detail page at `/projects/:slug`
- Large progress ring with percentage
- Document type distribution chart (Recharts)
- Status breakdown chart (Recharts)
- Stat cards for per-type counts
- Last synced timestamp display
- Navigation to filtered document list from stat cards
- Sync button on detail page

### Out of Scope
- Historical trend charts
- Per-epic breakdown within a project
- Custom date range filtering

---

## Technical Notes

### API Integration
- GET /api/v1/projects/{slug}/stats

### Data Requirements
- Recharts BarChart or PieChart for type distribution
- Recharts BarChart for status breakdown
- Custom Recharts theme matching brand guide dark colours
- StatsCard component with count + label + click handler

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Project not found | 404 page or redirect to dashboard |
| Project with zero documents | Charts show empty state; stat cards show 0 |
| Project with only one document type | Chart shows single bar/segment |
| Recharts fails to render | Fallback to text-based stats display |
| Loading state | Skeleton placeholders for charts and cards |

---

## Test Scenarios

- [ ] Project detail page renders with correct project name
- [ ] Progress ring shows correct completion percentage
- [ ] Type distribution chart renders with data
- [ ] Status breakdown chart renders with correct colours
- [ ] Stat cards show per-type counts
- [ ] Clicking stat card navigates to filtered document list
- [ ] Last synced timestamp displayed
- [ ] 404 for unknown project slug
- [ ] Zero-document project shows empty charts
- [ ] Loading state renders skeleton

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0017](US0017-statistics-api-endpoints.md) | API | Per-project stats endpoint | Draft |
| [US0020](US0020-progress-ring-and-chart-components.md) | Component | ProgressRing and chart theme | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Recharts (>=2.10.0) | Package | Not Installed |

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
| 2026-02-17 | Claude | Initial story creation from EP0004 |
