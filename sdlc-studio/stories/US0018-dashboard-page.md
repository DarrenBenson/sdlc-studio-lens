# US0018: Multi-Project Dashboard Page

> **Status:** Done
> **Epic:** [EP0004: Dashboard & Statistics](../epics/EP0004-dashboard-and-statistics.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** a dashboard showing project cards with health metrics
**So that** I can assess the status of all projects at a glance

## Context

### Persona Reference
**Darren** - Checks project health at the start of work sessions.
[Full persona details](../personas.md#darren)

### Background
The dashboard is the application landing page (route `/`). It displays a card for each registered project showing document count, completion percentage via a progress ring, status breakdown, and last sync timestamp. Clicking a card navigates to the project detail page.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Performance | Dashboard load < 2 seconds | Single API call for all project data |
| PRD | Design | Dark theme, Space Grotesk headings, JetBrains Mono for stats | Typography per brand guide |
| TRD | Tech Stack | Recharts for charts | Chart library chosen |

---

## Acceptance Criteria

### AC1: Project cards display
- **Given** 2 projects are registered and synced
- **When** I navigate to `/`
- **Then** I see 2 project cards, each showing: project name, document count, completion percentage, and last synced timestamp

### AC2: Progress ring on cards
- **Given** project "homelabcmd" has 95.8% completion
- **When** the dashboard renders
- **Then** the project card shows a circular progress ring filled to 95.8% in lime green (#A3E635)

### AC3: Click navigates to project detail
- **Given** a project card for "HomelabCmd"
- **When** I click on it
- **Then** I navigate to `/projects/homelabcmd`

### AC4: Zero projects empty state
- **Given** no projects are registered
- **When** I navigate to `/`
- **Then** I see a helpful message: "No projects registered" with a link to Settings to add one

### AC5: Aggregate statistics header
- **Given** 3 projects with a total of 300 documents
- **When** the dashboard loads
- **Then** a summary section shows total projects (3), total documents (300), and overall completion percentage

---

## Scope

### In Scope
- Dashboard page component at `/` route
- Project card grid layout
- ProgressRing component on each card (US0020)
- Document count and completion percentage display
- Last synced timestamp per card
- Aggregate stats summary section
- Zero-project empty state
- Click navigation to project detail
- Loading skeleton while data fetches

### Out of Scope
- Recent activity feed (deferred to v2.0)
- Trend charts over time
- Custom card layouts
- Statistics export

---

## Technical Notes

### API Integration
- GET /api/v1/stats (aggregate stats with per-project summaries)
- Single API call powers the entire dashboard

### Data Requirements
- Aggregate stats response includes projects array with per-project summaries
- ProgressRing takes completion_percentage as prop
- Card grid: CSS Grid or Flexbox, responsive layout

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Zero projects | Empty state with "Add Project" link to /settings |
| Project never synced | Card shows "Never synced" instead of timestamp; document count 0 |
| Project with sync error | Card shows error indicator (red dot or text) |
| API error loading stats | Error message with retry button |
| Single project | One card, no aggregate needed (still displayed) |
| Ten projects | Cards wrap into multiple rows in grid layout |
| Loading state | Skeleton cards while data loads |

---

## Test Scenarios

- [ ] Dashboard renders project cards for each registered project
- [ ] Project card shows name, document count, completion %
- [ ] Progress ring renders at correct percentage
- [ ] Last synced timestamp displayed on cards
- [ ] Clicking card navigates to project detail
- [ ] Empty state shown when no projects
- [ ] Aggregate stats section shows totals
- [ ] Loading skeleton displayed during fetch
- [ ] Error state displayed on API failure
- [ ] Never-synced project shows appropriate state

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0017](US0017-statistics-api-endpoints.md) | API | Stats endpoints | Draft |
| [US0020](US0020-progress-ring-and-chart-components.md) | Component | ProgressRing | Draft |
| [US0005](US0005-sidebar-project-navigation.md) | Component | Layout shell | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

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
