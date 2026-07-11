# US0039: Health Check Dashboard Page

> **Status:** Done
> **Raised-by:** Darren; human; v1 (inferred)
> **Epic:** [EP0009: Project Health Check](../epics/EP0009-project-health-check.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-18
> **Story Points:** 5

## User Story

**As a** SDLC Developer (Darren)
**I want** a visual dashboard showing my project's documentation health score and findings
**So that** I can quickly identify and prioritise quality issues to fix

## Context

### Persona Reference
**Darren** - Reviews project health at a glance, drills into specific findings to understand what needs fixing.
[Full persona details](../personas.md#darren)

### Background
US0037 implemented the rules engine and US0038 exposed it via API. This story adds the frontend page at `/projects/:slug/health-check` that displays the health score as a colour-coded ring, lists findings grouped by category, and provides filter/expand controls.

The page is linked from the ProjectDetail page header. Severity colours are defined as CSS custom properties in `globals.css` for consistent use across the application.

---

## Inherited Constraints

> See Epic for full constraint chain. Key constraints for this story:

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Tech Stack | React 19, TypeScript | Component with hooks for data fetching |
| TRD | Tech Stack | Tailwind CSS 4 | Styling with custom severity colour variables |
| PRD | Architecture | Read-only | Display only, no mutation actions |

---

## Acceptance Criteria

### AC1: Route registered
- **Given** the React Router configuration in App.tsx
- **When** I navigate to `/projects/:slug/health-check`
- **Then** the HealthCheck page component renders

### AC2: Score ring display
- **Given** health check results loaded from the API
- **When** the page renders
- **Then** a circular score ring displays the numeric score (0-100) with colour coding:
  - Green (80-100): healthy
  - Amber (50-79): needs attention
  - Red (0-49): critical

### AC3: Findings grouped by category
- **Given** health check findings
- **When** the page renders
- **Then** findings are grouped under headings: Completeness, Consistency, Quality, Integrity

### AC4: Finding details
- **Given** a finding in the list
- **When** it is displayed
- **Then** it shows: severity badge (colour-coded), rule ID, message, affected documents, and suggested fix

### AC5: Summary counters
- **Given** health check results
- **When** the page renders
- **Then** severity counters show counts for critical, high, medium, and low findings

### AC6: Link from ProjectDetail
- **Given** the ProjectDetail page
- **When** I look at the project header/actions area
- **Then** a "Health Check" link navigates to the health check page

### AC7: Loading and error states
- **Given** the health check page
- **When** data is loading or an error occurs
- **Then** appropriate loading spinner or error message is displayed

### AC8: Empty findings state
- **Given** a project with score 100 and no findings
- **When** the page renders
- **Then** a success message is displayed (e.g., "No issues found")

---

## Scope

### In Scope
- `HealthCheck.tsx` page component
- Score ring SVG component with colour gradient
- Findings list with category grouping
- Severity badge components using CSS custom properties
- `fetchHealthCheck()` in API client
- TypeScript types for `HealthCheckResponse`
- Route in App.tsx
- Link from ProjectDetail page
- CSS severity colour variables in globals.css

### Out of Scope
- Health check history or trends
- Filtering by severity (display all)
- Fix automation (display suggestions only)
- Health check for multiple projects at once

---

## Technical Notes

### Severity Colours (globals.css)
```css
--color-severity-critical: ...
--color-severity-high: ...
--color-severity-medium: ...
--color-severity-low: ...
```

### API Client
```typescript
export async function fetchHealthCheck(slug: string): Promise<HealthCheckResponse> {
  const res = await fetch(`/api/v1/projects/${slug}/health-check`);
  ...
}
```

### TypeScript Types
```typescript
interface HealthCheckResponse {
  project_slug: string;
  checked_at: string;
  total_documents: number;
  findings: HealthFinding[];
  summary: Record<string, number>;
  score: number;
}
```

---

## Test Scenarios

- [x] Page renders score ring with correct value
- [x] Findings grouped by category
- [x] Severity badges display with correct colours
- [x] Loading state shown while fetching
- [x] Error state shown on API failure
- [x] Empty findings shows success message
- [x] Link from ProjectDetail navigates correctly

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| US0038 | Implementation | API endpoint must exist | Done |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

---

## Estimation

**Story Points:** 5
**Complexity:** Medium

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-19 | Claude | Initial story creation (retroactive, implementation complete) |
