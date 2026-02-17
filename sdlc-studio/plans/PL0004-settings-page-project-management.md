# PL0004: Settings Page - Project Management - Implementation Plan

> **Status:** Complete
> **Story:** [US0004: Settings Page - Project Management](../stories/US0004-settings-page-project-management.md)
> **Epic:** [EP0001: Project Management](../epics/EP0001-project-management.md)
> **Created:** 2026-02-17
> **Language:** TypeScript

## Overview

Implement the Settings page at /settings that provides the primary UI for project management. The page includes a form to register new projects, a list of existing projects with edit/delete/sync actions, confirmation dialogs, and sync status polling. This is the frontend counterpart to the API endpoints established in US0001-US0003.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Add project form | Form with name + path fields; project appears in list after submit |
| AC2 | Project list display | Shows all projects with name, path, sync status, last synced, document count |
| AC3 | Edit project | Click Edit, change fields, Save updates the project |
| AC4 | Delete with confirmation | Click Delete, confirm in dialog, project removed |
| AC5 | Sync button | Click Sync Now, status changes to syncing, button disabled until complete |

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
| React | /facebook/react | useState for form state, useEffect for data fetching, controlled form inputs |
| React Router | - | useNavigate() not needed (stays on same page), route at /settings |
| Tailwind CSS | - | Form inputs, buttons, cards from brand guide component library |

### Existing Patterns

Builds on US0005 patterns:
- `frontend/src/types/index.ts` - Project TypeScript interface
- `frontend/src/api/client.ts` - fetchProjects() function
- `frontend/src/components/Layout.tsx` - Layout shell (Settings page renders in Outlet)
- Brand guide component styles for buttons, inputs, cards

---

## Recommended Approach

**Strategy:** Test-After
**Rationale:** Frontend page with form interactions, optimistic UI updates, and polling behaviour. The Settings page involves complex user interactions (add, edit, delete, sync) with visual feedback. Building the UI first allows rapid iteration on the form UX and error display before writing tests. RTL tests verify form submission, list rendering, and user flow behaviour.

### Test Priority
1. Settings page renders add project form
2. Form submission creates project and updates list
3. Edit flow pre-populates form and saves changes
4. Delete confirmation dialog and removal
5. Sync button triggers sync and updates status

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Add API client functions (createProject, updateProject, deleteProject, triggerSync) | `frontend/src/api/client.ts` | PL0005 | [ ] |
| 2 | Create ProjectForm component (add/edit mode) | `frontend/src/components/ProjectForm.tsx` | 1 | [ ] |
| 3 | Create ProjectCard component (display with actions) | `frontend/src/components/ProjectCard.tsx` | 1 | [ ] |
| 4 | Create ConfirmDialog component | `frontend/src/components/ConfirmDialog.tsx` | - | [ ] |
| 5 | Create Settings page component | `frontend/src/pages/Settings.tsx` | 2, 3, 4 | [ ] |
| 6 | Add /settings route to App.tsx | `frontend/src/App.tsx` | 5 | [ ] |
| 7 | Implement sync status polling (2s interval) | `frontend/src/pages/Settings.tsx` | 5 | [ ] |
| 8 | Write Settings page tests | `frontend/src/pages/Settings.test.tsx` | 5 | [ ] |
| 9 | Write ProjectForm component tests | `frontend/src/components/ProjectForm.test.tsx` | 2 | [ ] |
| 10 | Write ProjectCard component tests | `frontend/src/components/ProjectCard.test.tsx` | 3 | [ ] |

### Parallel Execution Groups

| Group | Tasks | Prerequisite |
|-------|-------|--------------|
| API Client | 1 | PL0005 types |
| Components | 2, 3, 4 | Group: API Client |
| Page | 5, 6, 7 | Group: Components |
| Tests | 8, 9, 10 | Group: Page |

---

## Implementation Phases

### Phase 1: API Client Extensions
**Goal:** Add remaining API client functions for project CRUD and sync

- [ ] Add `createProject(data: ProjectCreate)` - POST /api/v1/projects
- [ ] Add `updateProject(slug: string, data: ProjectUpdate)` - PUT /api/v1/projects/{slug}
- [ ] Add `deleteProject(slug: string)` - DELETE /api/v1/projects/{slug}
- [ ] Add `triggerSync(slug: string)` - POST /api/v1/projects/{slug}/sync
- [ ] Add `fetchProject(slug: string)` - GET /api/v1/projects/{slug} (for polling)
- [ ] Define ProjectCreate and ProjectUpdate TypeScript interfaces

**Files:**
- `frontend/src/api/client.ts` - Additional API functions
- `frontend/src/types/index.ts` - Add request types

### Phase 2: Reusable Components
**Goal:** Build form, card, and dialog components

- [ ] Create `ProjectForm.tsx`:
  - Controlled inputs for name and sdlc_path
  - Mode: "add" (empty fields, "Add Project" button) or "edit" (pre-populated, "Save" button)
  - Client-side validation (required fields)
  - Server error display below form (path not found, duplicate slug)
  - Loading state on submit button
- [ ] Create `ProjectCard.tsx`:
  - Display project name, sdlc_path, sync_status badge, last_synced_at, document_count
  - Action buttons: Edit, Delete, Sync Now
  - Sync Now button disabled and shows spinner when sync_status is "syncing"
  - Long project names truncated with ellipsis
- [ ] Create `ConfirmDialog.tsx`:
  - Modal overlay with message, Confirm and Cancel buttons
  - Warning variant for delete-during-sync scenario

**Files:**
- `frontend/src/components/ProjectForm.tsx` - Add/edit form
- `frontend/src/components/ProjectCard.tsx` - Project display card
- `frontend/src/components/ConfirmDialog.tsx` - Confirmation modal

### Phase 3: Settings Page
**Goal:** Assemble components into the Settings page with full CRUD workflow

- [ ] Create `Settings.tsx` page component:
  - Fetch project list on mount
  - Render ProjectForm in "add" mode at top
  - Render list of ProjectCard components below
  - Handle add: call createProject(), append to list on success
  - Handle edit: switch card to edit mode, call updateProject(), update list on success
  - Handle delete: show ConfirmDialog, call deleteProject(), remove from list on success (optimistic)
  - Handle sync: call triggerSync(), update card status to "syncing"
  - Poll GET /projects/{slug} every 2 seconds for projects with sync_status "syncing"
  - Stop polling when status changes to "synced" or "error"
  - Success/error notifications (simple inline messages)
  - Empty state: "No projects registered. Add your first project above."
- [ ] Add /settings route in App.tsx

**Files:**
- `frontend/src/pages/Settings.tsx` - Settings page
- `frontend/src/App.tsx` - Add route

### Phase 4: Testing
**Goal:** Verify user interactions and component behaviour

- [ ] Write `Settings.test.tsx`:
  - Renders add project form
  - Form submission creates project and updates list
  - Server validation errors displayed (path not found, duplicate)
  - Project list shows all projects
  - Edit button opens edit form pre-populated
  - Edit saves and updates list
  - Delete shows confirmation dialog
  - Delete confirmation removes project
  - Delete cancel keeps project
  - Sync button triggers sync
  - Empty state shown when no projects
- [ ] Write `ProjectForm.test.tsx`:
  - Renders name and path inputs
  - Submit calls onSubmit with form data
  - Displays server error messages
  - Disabled during loading state
- [ ] Write `ProjectCard.test.tsx`:
  - Renders project details
  - Edit button calls onEdit
  - Delete button calls onDelete
  - Sync button calls onSync
  - Sync button disabled when syncing

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | Form submits and project appears in list | `Settings.test.tsx` | Pending |
| AC2 | Project cards show all fields | `ProjectCard.test.tsx` | Pending |
| AC3 | Edit flow updates project | `Settings.test.tsx` | Pending |
| AC4 | Delete with confirmation dialog | `Settings.test.tsx` | Pending |
| AC5 | Sync button triggers and disables | `Settings.test.tsx`, `ProjectCard.test.tsx` | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | Add project with invalid path | Display server error below form: "Path does not exist on the server filesystem" | Phase 2 |
| 2 | Add project with duplicate name | Display server error: "A project with this name already exists" | Phase 2 |
| 3 | Delete project during active sync | Confirmation warns: "This project is currently syncing. Delete anyway?" | Phase 3 |
| 4 | Network error during add/edit/delete | Error notification: "Failed to save. Check your connection." | Phase 3 |
| 5 | Very long project name in list | CSS text-overflow: ellipsis; full name in title tooltip | Phase 2 |
| 6 | Sync button clicked rapidly | Button disabled immediately on first click; prevents double-trigger | Phase 2 |
| 7 | Zero projects state | Show message: "No projects registered. Add your first project above." | Phase 3 |
| 8 | Edit form pre-populated with current values | Form fields filled on edit click; cancel reverts | Phase 2 |

**Coverage:** 8/8 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Polling creates excessive API requests | Low | Only poll for projects with sync_status "syncing"; clear interval on unmount |
| Optimistic delete fails on server | Medium | Revert list state on error; show error notification |
| Form state management complexity with add/edit modes | Medium | Use separate state variables for editing project slug; clear on cancel |
| Race condition between sync poll and user actions | Low | Debounce state updates; check component mounted before setState |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Component tests written and passing
- [ ] Form validation works (client-side and server error display)
- [ ] Delete confirmation dialog functional
- [ ] Sync polling works and stops on completion
- [ ] Empty state and error states implemented
- [ ] Styles match brand guide (dark theme, lime accents)
- [ ] ESLint passes

---

## Notes

- This page depends on all three API stories: US0001 (POST), US0002 (GET/PUT/DELETE), US0003 (POST sync).
- The Settings page is a full CRUD form - the most interactive component in EP0001.
- Polling interval of 2 seconds is a balance between responsiveness and API load.
- Optimistic UI on delete: remove from list immediately, restore on server error.
- The ProjectForm component is reused in both "add" and "edit" modes to avoid duplication.
