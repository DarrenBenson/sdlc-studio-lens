# US0004: Settings Page - Project Management

> **Status:** Done
> **Epic:** [EP0001: Project Management](../epics/EP0001-project-management.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** a settings page where I can add, edit, and remove projects
**So that** I can manage project registrations through the dashboard UI

## Context

### Persona Reference
**Darren** - Comfortable with CLI tools but wants visual oversight; prefers dark-themed developer tools.
[Full persona details](../personas.md#darren)

### Background
The settings page is the primary UI for project management. It provides a form to register new projects, a list of existing projects with edit and delete actions, and a sync button per project. This is the frontend counterpart to the project API endpoints (US0001-US0003).

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Design | Dark theme with lime green accents (Brand Guide) | All form controls and buttons follow brand guide |
| TRD | Architecture | React SPA with client-side routing | Route: /settings |
| TRD | Tech Stack | React 19, TypeScript, Tailwind CSS | Component implementation |
| PRD | Architecture | Read-only filesystem access | UI never writes to project directories |

---

## Acceptance Criteria

### AC1: Add project form
- **Given** I am on the Settings page at `/settings`
- **When** I fill in "Project Name" as "HomelabCmd" and "SDLC Path" as "/data/projects/HomelabCmd/sdlc-studio" and click "Add Project"
- **Then** the project appears in the project list below with sync_status "never_synced" and a "Sync Now" button

### AC2: Project list displays all registered projects
- **Given** 3 projects are registered
- **When** I navigate to `/settings`
- **Then** I see a list of 3 project cards showing name, path, sync status, last synced timestamp, and document count

### AC3: Edit project
- **Given** project "HomelabCmd" is in the list
- **When** I click "Edit", change the name to "HomelabCmd v2", and click "Save"
- **Then** the project name updates in the list and a success notification appears

### AC4: Delete project with confirmation
- **Given** project "HomelabCmd" is in the list
- **When** I click "Delete" and confirm in the confirmation dialog
- **Then** the project is removed from the list

### AC5: Sync button triggers sync
- **Given** project "HomelabCmd" is in the list with sync_status "synced"
- **When** I click the "Sync Now" button
- **Then** the sync_status indicator changes to "syncing" and the button becomes disabled until sync completes

---

## Scope

### In Scope
- Settings page component at `/settings` route
- Add project form (name + path fields, submit button)
- Project list with edit/delete/sync actions
- Form validation (client-side: required fields, path format)
- Server error display (path not found, duplicate slug)
- Sync button with status indicator
- Confirmation dialog for delete
- Success/error notifications
- Empty state when no projects registered

### Out of Scope
- Sidebar navigation (US0005)
- Project import/export
- Bulk operations
- Sync progress percentage display

---

## Technical Notes

### API Integration
- POST /api/v1/projects (add)
- GET /api/v1/projects (list)
- PUT /api/v1/projects/{slug} (edit)
- DELETE /api/v1/projects/{slug} (delete)
- POST /api/v1/projects/{slug}/sync (sync trigger)
- Poll GET /api/v1/projects/{slug} for sync status updates

### Data Requirements
- React state for project list, form inputs, loading states
- Optimistic UI update on delete (remove from list before server confirms)
- Polling interval for sync status: 2 seconds while syncing

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Add project with invalid path | Error message below form: "Path does not exist on the server filesystem" |
| Add project with duplicate name | Error message: "A project with this name already exists" |
| Delete project during active sync | Confirmation warns "This project is currently syncing. Delete anyway?" |
| Network error during add/edit/delete | Error notification: "Failed to save. Check your connection." |
| Very long project name in list | Name truncated with ellipsis; full name in tooltip |
| Sync button clicked rapidly | Button disabled immediately on first click; prevents double-trigger |
| Zero projects state | Show helpful message: "No projects registered. Add your first project above." |
| Edit form pre-populated with current values | Form fields filled with current name and path on edit click |

---

## Test Scenarios

- [ ] Settings page renders add project form
- [ ] Add project form submits successfully and project appears in list
- [ ] Add project shows server validation errors (path not found)
- [ ] Add project shows server validation errors (duplicate slug)
- [ ] Project list displays all registered projects
- [ ] Edit button opens edit form pre-populated with current values
- [ ] Edit saves changes and updates list
- [ ] Delete button shows confirmation dialog
- [ ] Delete confirmation removes project from list
- [ ] Delete cancel keeps project in list
- [ ] Sync button triggers sync and shows syncing state
- [ ] Sync completion updates status indicator
- [ ] Empty state shown when no projects exist

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0001](US0001-register-new-project.md) | API | POST /api/v1/projects endpoint | Draft |
| [US0002](US0002-project-list-and-management-api.md) | API | GET/PUT/DELETE /api/v1/projects | Draft |
| [US0003](US0003-trigger-sync-and-track-status.md) | API | POST /api/v1/projects/{slug}/sync | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| React Router setup | Infrastructure | Not Started |
| Tailwind CSS configuration | Infrastructure | Not Started |

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
| 2026-02-17 | Claude | Initial story creation from EP0001 |
