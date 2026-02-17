# TS0004: Settings Page - Project Management

> **Status:** Draft
> **Epic:** [EP0001: Project Management](../epics/EP0001-project-management.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0004 - Settings Page - Project Management. Covers the Settings page component, ProjectForm (add/edit), ProjectCard (display with actions), confirmation dialog, sync polling, and error handling. Tests use Vitest + React Testing Library with mocked API responses.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0004](../stories/US0004-settings-page-project-management.md) | Settings Page - Project Management | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0004 | AC1 | Add project form | TC0056, TC0057, TC0058, TC0059 | Covered |
| US0004 | AC2 | Project list displays all projects | TC0060, TC0061 | Covered |
| US0004 | AC3 | Edit project | TC0062, TC0063 | Covered |
| US0004 | AC4 | Delete with confirmation | TC0064, TC0065, TC0066 | Covered |
| US0004 | AC5 | Sync button triggers sync | TC0067, TC0068 | Covered |

**Coverage:** 5/5 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | Yes | Component rendering, form behaviour, and user interaction testing |
| Integration | No | API integration tested via mocked fetch |
| E2E | No | Covered in later E2E spec (settings.spec.ts) |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Node 22+, Vitest, React Testing Library, react-router-dom |
| External Services | None (API responses mocked) |
| Test Data | Mock project arrays, mock API responses for CRUD operations |

---

## Test Cases

### TC0056: Settings page renders add project form

**Type:** Unit | **Priority:** Critical | **Story:** US0004 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Settings page component mounts | API returns existing projects |
| When | Page renders | Form visible |
| Then | Add project form is displayed with name and path fields and submit button | Form ready |

**Assertions:**
- [ ] Input field with label "Project Name" (or placeholder) is in the document
- [ ] Input field with label "SDLC Path" (or placeholder) is in the document
- [ ] "Add Project" button is in the document

---

### TC0057: Add project form submits successfully

**Type:** Unit | **Priority:** Critical | **Story:** US0004 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Settings page with add form | Form ready |
| When | Fill in "HomelabCmd" and "/data/projects/HomelabCmd/sdlc-studio" and click "Add Project" | Submit form |
| Then | Project appears in the list with sync_status "never_synced" and "Sync Now" button | Added to list |

**Assertions:**
- [ ] createProject API was called with correct data
- [ ] "HomelabCmd" appears in the project list
- [ ] New project shows "never_synced" status
- [ ] Form fields are cleared after successful submit

---

### TC0058: Add project shows server error for invalid path

**Type:** Unit | **Priority:** High | **Story:** US0004 AC1 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Mock API returns 400 PATH_NOT_FOUND | Server rejects |
| When | Submit add form with invalid path | Error response |
| Then | Error message displayed below form | Error visible |

**Assertions:**
- [ ] Error message containing "path" is visible
- [ ] Project is NOT added to the list

---

### TC0059: Add project shows server error for duplicate slug

**Type:** Unit | **Priority:** High | **Story:** US0004 AC1 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Mock API returns 409 CONFLICT | Duplicate slug |
| When | Submit add form with duplicate name | Error response |
| Then | Error message about duplicate is displayed | Error visible |

**Assertions:**
- [ ] Error message containing "already exists" is visible

---

### TC0060: Project list displays all registered projects

**Type:** Unit | **Priority:** Critical | **Story:** US0004 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Mock API returns 3 projects with various statuses | Projects loaded |
| When | Settings page renders | List displayed |
| Then | 3 project cards visible with name, path, status, last synced, document count | All fields shown |

**Assertions:**
- [ ] 3 project cards are rendered
- [ ] Each card shows the project name
- [ ] Each card shows sync status indicator
- [ ] Each card shows last synced timestamp (or "Never" for null)
- [ ] Each card shows document count

---

### TC0061: Empty state shown when no projects

**Type:** Unit | **Priority:** High | **Story:** US0004 AC2 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Mock API returns empty array | No projects |
| When | Settings page renders | Empty state |
| Then | Helpful message displayed | Guidance shown |

**Assertions:**
- [ ] Text "No projects registered" (or similar) is in the document

---

### TC0062: Edit button opens pre-populated form

**Type:** Unit | **Priority:** High | **Story:** US0004 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project "HomelabCmd" in the list | Card displayed |
| When | Click "Edit" button on HomelabCmd card | Edit mode activated |
| Then | Form fields pre-populated with current name and path | Values shown |

**Assertions:**
- [ ] Name input value is "HomelabCmd"
- [ ] Path input value matches current sdlc_path
- [ ] "Save" button is visible (replaces "Add Project")

---

### TC0063: Edit saves changes and updates list

**Type:** Unit | **Priority:** High | **Story:** US0004 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Edit form showing for "HomelabCmd" | In edit mode |
| When | Change name to "HomelabCmd v2" and click "Save" | Submit update |
| Then | Project name updates in the list | List refreshed |

**Assertions:**
- [ ] updateProject API was called with slug and new data
- [ ] "HomelabCmd v2" appears in the list
- [ ] Form returns to add mode

---

### TC0064: Delete button shows confirmation dialog

**Type:** Unit | **Priority:** Critical | **Story:** US0004 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project "HomelabCmd" in the list | Card displayed |
| When | Click "Delete" button | Dialog triggered |
| Then | Confirmation dialog appears asking to confirm deletion | Dialog visible |

**Assertions:**
- [ ] Dialog contains text about deleting "HomelabCmd"
- [ ] "Confirm" button is in the dialog
- [ ] "Cancel" button is in the dialog

---

### TC0065: Delete confirmation removes project from list

**Type:** Unit | **Priority:** Critical | **Story:** US0004 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Confirmation dialog is showing for "HomelabCmd" | Dialog open |
| When | Click "Confirm" | Deletion confirmed |
| Then | Project is removed from the list | List updated |

**Assertions:**
- [ ] deleteProject API was called with correct slug
- [ ] "HomelabCmd" is no longer in the document
- [ ] Dialog is closed

---

### TC0066: Delete cancel keeps project in list

**Type:** Unit | **Priority:** Medium | **Story:** US0004 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Confirmation dialog is showing for "HomelabCmd" | Dialog open |
| When | Click "Cancel" | Deletion cancelled |
| Then | Project remains in the list | No change |

**Assertions:**
- [ ] deleteProject API was NOT called
- [ ] "HomelabCmd" is still in the document
- [ ] Dialog is closed

---

### TC0067: Sync button triggers sync and shows syncing state

**Type:** Unit | **Priority:** Critical | **Story:** US0004 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project "HomelabCmd" with sync_status "synced" | Ready to sync |
| When | Click "Sync Now" button | Sync triggered |
| Then | Status indicator changes to "syncing" and button becomes disabled | Visual feedback |

**Assertions:**
- [ ] triggerSync API was called with correct slug
- [ ] Sync status indicator shows syncing state (blue)
- [ ] Sync button is disabled

---

### TC0068: Sync completion updates status indicator

**Type:** Unit | **Priority:** High | **Story:** US0004 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project is syncing (poll in progress) | Polling active |
| When | Poll returns sync_status "synced" | Sync complete |
| Then | Status indicator updates to "synced" and button re-enables | Polling stops |

**Assertions:**
- [ ] Status indicator shows synced state (green)
- [ ] Sync button is re-enabled
- [ ] Polling has stopped (no more API calls)

---

## Fixtures

```yaml
three_projects:
  - slug: "homelabcmd"
    name: "HomelabCmd"
    sdlc_path: "/data/projects/HomelabCmd/sdlc-studio"
    sync_status: "synced"
    last_synced_at: "2026-02-17T10:00:00Z"
    document_count: 152
    created_at: "2026-02-17T09:00:00Z"
  - slug: "sdlclens"
    name: "SDLCLens"
    sdlc_path: "/data/projects/SDLCLens/sdlc-studio"
    sync_status: "never_synced"
    last_synced_at: null
    document_count: 0
    created_at: "2026-02-17T09:30:00Z"
  - slug: "personalblog"
    name: "PersonalBlog"
    sdlc_path: "/data/projects/PersonalBlog/sdlc-studio"
    sync_status: "error"
    last_synced_at: null
    document_count: 0
    created_at: "2026-02-17T10:00:00Z"

new_project_response:
  slug: "homelabcmd"
  name: "HomelabCmd"
  sdlc_path: "/data/projects/HomelabCmd/sdlc-studio"
  sync_status: "never_synced"
  last_synced_at: null
  document_count: 0
  created_at: "2026-02-17T11:00:00Z"

path_not_found_error:
  error:
    code: "PATH_NOT_FOUND"
    message: "Project sdlc-studio path does not exist on filesystem"

conflict_error:
  error:
    code: "CONFLICT"
    message: "Project slug already exists"

sync_trigger_response:
  slug: "homelabcmd"
  sync_status: "syncing"
  message: "Sync started"

empty_projects: []
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0056 | Settings page renders add form | Pending | - |
| TC0057 | Add project form submits successfully | Pending | - |
| TC0058 | Add project shows invalid path error | Pending | - |
| TC0059 | Add project shows duplicate slug error | Pending | - |
| TC0060 | Project list displays all projects | Pending | - |
| TC0061 | Empty state shown | Pending | - |
| TC0062 | Edit opens pre-populated form | Pending | - |
| TC0063 | Edit saves changes | Pending | - |
| TC0064 | Delete shows confirmation dialog | Pending | - |
| TC0065 | Delete confirmation removes project | Pending | - |
| TC0066 | Delete cancel keeps project | Pending | - |
| TC0067 | Sync button triggers sync | Pending | - |
| TC0068 | Sync completion updates status | Pending | - |

---

## Traceability

| Artefact | Reference |
|----------|-----------|
| PRD | [sdlc-studio/prd.md](../prd.md) |
| Epic | [EP0001](../epics/EP0001-project-management.md) |
| TSD | [sdlc-studio/tsd.md](../tsd.md) |
| Brand Guide | [sdlc-studio/brand-guide.md](../brand-guide.md) |

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec from US0004 story plan |
