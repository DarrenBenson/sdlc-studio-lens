# PL0005: Sidebar Project Navigation - Implementation Plan

> **Status:** Complete
> **Story:** [US0005: Sidebar Project Navigation](../stories/US0005-sidebar-project-navigation.md)
> **Epic:** [EP0001: Project Management](../epics/EP0001-project-management.md)
> **Created:** 2026-02-17
> **Language:** TypeScript

## Overview

Implement the persistent sidebar component that displays all registered projects with sync status colour indicators. The sidebar is part of the Layout.tsx shell and is visible on every page. It fetches the project list from the API, highlights the active project based on the current route, and provides navigation to project documents and the Settings page.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Project list display | Sidebar shows all registered projects in a vertical list |
| AC2 | Sync status indicators | Coloured dots: lime (#A3E635) synced, blue (#3B82F6) syncing, grey (#78909C) never_synced, red (#EF4444) error |
| AC3 | Click navigates to documents | Clicking project navigates to /projects/{slug}/documents |
| AC4 | Active project highlighted | Current project highlighted with accent colour |
| AC5 | Settings link | Settings link at bottom navigates to /settings |

---

## Technical Context

### Language & Framework
- **Primary Language:** TypeScript 5.0+
- **Framework:** React 19, Vite 6.0+, Tailwind CSS 4.0+
- **Test Framework:** Vitest + React Testing Library

### Relevant Best Practices
- Functional components with hooks
- TypeScript strict mode
- Tailwind utility classes (no raw CSS)
- Component co-location (test file next to component)

### Library Documentation (Context7)

| Library | Context7 ID | Key Patterns |
|---------|-------------|--------------|
| React | /facebook/react | useEffect for data fetching, useState for project list, conditional rendering |
| React Router | - | useLocation() for active route detection, useParams(), Link component, NavLink |
| Tailwind CSS | - | Utility-first classes, dark theme tokens from brand guide |

### Existing Patterns

This is one of the first frontend components. Establishes patterns for:
- API data fetching via fetch()
- Layout shell with sidebar + main content area
- React Router integration for navigation
- Brand guide colour token usage in Tailwind

---

## Recommended Approach

**Strategy:** Test-After
**Rationale:** Frontend component story with visual rendering concerns. The sidebar is a presentational component with React Router integration. Testing after implementation allows iterating on the visual design and layout before locking down test assertions. RTL tests verify rendering and navigation behaviour.

### Test Priority
1. Sidebar renders project list from mock API data
2. Sync status colour indicators render correctly
3. Active project highlighting based on route
4. Navigation links produce correct URLs
5. Empty state rendering

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Create TypeScript types for Project | `frontend/src/types/index.ts` | - | [ ] |
| 2 | Create API client fetchProjects function | `frontend/src/api/client.ts` | 1 | [ ] |
| 3 | Create Sidebar component | `frontend/src/components/Sidebar.tsx` | 1, 2 | [ ] |
| 4 | Create Layout shell component | `frontend/src/components/Layout.tsx` | 3 | [ ] |
| 5 | Configure React Router with Layout wrapper | `frontend/src/App.tsx` | 4 | [ ] |
| 6 | Add sidebar styles using Tailwind tokens | `frontend/src/components/Sidebar.tsx` | 3 | [ ] |
| 7 | Write Sidebar component tests | `frontend/src/components/Sidebar.test.tsx` | 3 | [ ] |
| 8 | Write Layout component tests | `frontend/src/components/Layout.test.tsx` | 4 | [ ] |

### Parallel Execution Groups

| Group | Tasks | Prerequisite |
|-------|-------|--------------|
| Foundation | 1, 2 | None |
| Components | 3, 4, 5, 6 | Group: Foundation |
| Tests | 7, 8 | Group: Components |

---

## Implementation Phases

### Phase 1: Foundation
**Goal:** Establish TypeScript types and API client

- [ ] Create `types/index.ts` with Project interface (slug, name, sdlc_path, sync_status, last_synced_at, document_count, created_at)
- [ ] Create `api/client.ts` with `fetchProjects()` - GET /api/v1/projects, returns Promise<Project[]>
- [ ] Define SyncStatus type: "never_synced" | "syncing" | "synced" | "error"

**Files:**
- `frontend/src/types/index.ts` - TypeScript interfaces
- `frontend/src/api/client.ts` - API client functions

### Phase 2: Components
**Goal:** Build sidebar and layout shell

- [ ] Create `Sidebar.tsx`:
  - Fetch project list on mount via useEffect + fetchProjects()
  - Render application title "Studio Lens" at top with accent colour
  - Render vertical list of project names
  - Each project has coloured status dot (6px circle) using brand guide status colours
  - Use NavLink from React Router; active project gets lime green highlight
  - Settings link at bottom with gear icon
  - Empty state: "No projects" message with link to Settings
  - Error state: "Failed to load projects" with retry button
  - Scrollable list for 10+ projects
- [ ] Create `Layout.tsx`:
  - CSS Grid: 240px sidebar + 1fr main content
  - Sidebar component on left
  - Outlet (React Router) for main content on right
  - Full viewport height

**Files:**
- `frontend/src/components/Sidebar.tsx` - Sidebar component
- `frontend/src/components/Layout.tsx` - Layout shell

### Phase 3: Routing & Integration
**Goal:** Wire layout to React Router

- [ ] Update `App.tsx` with React Router BrowserRouter
- [ ] Add Layout as parent route wrapping all child routes
- [ ] Configure routes: /, /projects/:slug/documents, /settings
- [ ] Verify sidebar appears on all pages

**Files:**
- `frontend/src/App.tsx` - Router configuration

### Phase 4: Testing
**Goal:** Verify component behaviour

- [ ] Write `Sidebar.test.tsx`:
  - Renders project list from mock data
  - Each project shows correct status colour class
  - Clicking project navigates to /projects/{slug}/documents
  - Active project has highlight styling
  - Settings link present and navigates to /settings
  - Empty state renders when no projects
  - Error state renders on API failure
- [ ] Write `Layout.test.tsx`:
  - Renders sidebar and main content area
  - Sidebar visible alongside content

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | Sidebar renders all projects | `Sidebar.test.tsx` | Pending |
| AC2 | Status dots use correct colours | `Sidebar.test.tsx` | Pending |
| AC3 | Click navigates to document list | `Sidebar.test.tsx` | Pending |
| AC4 | Active project highlighted | `Sidebar.test.tsx` | Pending |
| AC5 | Settings link at bottom | `Sidebar.test.tsx` | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | Zero projects registered | Show "No projects" message with link to Settings page | Phase 2 |
| 2 | Project list fails to load (API error) | Show "Failed to load projects" with retry button | Phase 2 |
| 3 | Very long project name | Truncate with CSS text-overflow: ellipsis; full name in title tooltip | Phase 2 |
| 4 | Sync status changes while viewing | Sidebar re-fetches when project data refreshes (state lifted to Layout) | Phase 2 |
| 5 | Many projects (10+) | overflow-y: auto on project list section; fixed header and footer | Phase 2 |

**Coverage:** 5/5 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| React Router version API changes | Medium | Pin react-router-dom version; check Context7 for current patterns |
| Tailwind class names not matching brand guide tokens | Low | Define custom theme in tailwind.config.ts matching brand guide exactly |
| Sidebar layout breaks on narrow viewports | Low | Add responsive breakpoint to collapse sidebar; out of scope for v1.0 but structure supports it |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Component tests written and passing
- [ ] Sidebar renders on all pages via Layout shell
- [ ] Sync status colours match brand guide exactly
- [ ] Active project highlighting works with React Router
- [ ] Empty state and error state implemented
- [ ] Ruff/ESLint passes

---

## Notes

- The sidebar data-fetches from GET /api/v1/projects (US0002). The API must be implemented first.
- Sync status colour values come from the brand guide: synced=#A3E635, syncing=#3B82F6, never_synced=#78909C, error=#EF4444.
- The Layout.tsx component is the shell for the entire application. All routes render inside it.
- Lucide Icons used for Settings (settings icon) and project items (folder-open icon).
