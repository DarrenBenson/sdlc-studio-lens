# US0005: Sidebar Project Navigation

> **Status:** Done
> **Epic:** [EP0001: Project Management](../epics/EP0001-project-management.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** a sidebar showing all registered projects with sync status indicators
**So that** I can navigate between projects and see their status at a glance

## Context

### Persona Reference
**Darren** - Checks project status at the start of work sessions; navigates between multiple projects.
[Full persona details](../personas.md#darren)

### Background
The sidebar is the persistent navigation element visible on every page. It lists registered projects with sync status indicators (green dot for synced, amber for syncing, grey for never synced, red for error). Clicking a project navigates to its document list. The sidebar also contains a link to Settings.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Design | Dark theme with lime green accents (Brand Guide) | Sidebar uses bg-surface (#111916) background |
| TRD | Architecture | React SPA layout shell | Sidebar is part of Layout.tsx component |
| PRD | Performance | Dashboard load < 2 seconds | Sidebar data must load quickly |

---

## Acceptance Criteria

### AC1: Sidebar displays project list
- **Given** 3 projects are registered
- **When** I load any page in the dashboard
- **Then** the sidebar shows all 3 project names in a vertical list

### AC2: Sync status indicators
- **Given** projects with different sync statuses: "synced", "syncing", "error", "never_synced"
- **When** I view the sidebar
- **Then** each project shows a coloured dot: lime green (#A3E635) for synced, blue (#3B82F6) for syncing, grey (#78909C) for never_synced, red (#EF4444) for error

### AC3: Click navigates to project documents
- **Given** project "HomelabCmd" is in the sidebar
- **When** I click "HomelabCmd"
- **Then** I navigate to `/projects/homelabcmd/documents`

### AC4: Active project highlighted
- **Given** I am viewing documents for "HomelabCmd"
- **When** I look at the sidebar
- **Then** "HomelabCmd" is highlighted with the accent colour (lime green) to indicate it is the active project

### AC5: Settings link
- **Given** I am on any page
- **When** I look at the bottom of the sidebar
- **Then** I see a "Settings" link that navigates to `/settings`

---

## Scope

### In Scope
- Sidebar component within Layout.tsx shell
- Project list loaded from GET /api/v1/projects
- Sync status colour indicators
- Active project highlighting based on current route
- Navigation links to project documents
- Settings link
- Application title/logo area at top of sidebar
- Responsive sidebar (collapsible on narrow viewports)

### Out of Scope
- Search bar in sidebar (search is in the header, US0023)
- Project management actions (US0004)
- Document type sub-navigation within a project

---

## Technical Notes

### API Integration
- GET /api/v1/projects on initial load and after sync events
- Sidebar re-fetches project list when sync completes (via state update)

### Data Requirements
- Project list: slug, name, sync_status
- React Router useParams() or useLocation() to determine active project
- Layout.tsx wraps all routes with sidebar

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Zero projects registered | Sidebar shows "No projects" message with link to Settings |
| Project list fails to load (API error) | Sidebar shows "Failed to load projects" with retry button |
| Very long project name | Truncated with ellipsis; full name in tooltip on hover |
| Sync status changes while viewing | Sidebar indicator updates when project data refreshes |
| Many projects (10+) | Scrollable sidebar list with fixed header and footer |

---

## Test Scenarios

- [ ] Sidebar renders project list from API data
- [ ] Each project shows correct sync status colour
- [ ] Clicking project navigates to document list
- [ ] Active project is highlighted
- [ ] Settings link navigates to /settings
- [ ] Empty state shows "No projects" message
- [ ] Application title displays at top of sidebar
- [ ] Sidebar visible on all pages (layout wrapping)

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0002](US0002-project-list-and-management-api.md) | API | GET /api/v1/projects endpoint | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| React Router setup | Infrastructure | Not Started |
| Layout.tsx shell component | Infrastructure | Not Started |

---

## Estimation

**Story Points:** {{TBD}}
**Complexity:** Low

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial story creation from EP0001 |
