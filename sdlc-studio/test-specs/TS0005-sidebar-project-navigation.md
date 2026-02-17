# TS0005: Sidebar Project Navigation

> **Status:** Draft
> **Epic:** [EP0001: Project Management](../epics/EP0001-project-management.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0005 - Sidebar Project Navigation. Covers the Sidebar component rendering, sync status colour indicators, navigation behaviour, active project highlighting, and empty/error states. Tests use Vitest + React Testing Library with mocked API responses.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0005](../stories/US0005-sidebar-project-navigation.md) | Sidebar Project Navigation | Medium |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0005 | AC1 | Sidebar displays project list | TC0048, TC0049 | Covered |
| US0005 | AC2 | Sync status indicators | TC0050 | Covered |
| US0005 | AC3 | Click navigates to project documents | TC0051 | Covered |
| US0005 | AC4 | Active project highlighted | TC0052 | Covered |
| US0005 | AC5 | Settings link | TC0053 | Covered |

**Coverage:** 5/5 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | Yes | Component rendering and conditional logic |
| Integration | No | API integration tested via mocked fetch |
| E2E | No | Sidebar behaviour covered in later E2E specs |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Node 22+, Vitest, React Testing Library, react-router-dom |
| External Services | None (API responses mocked) |
| Test Data | Mock project arrays with various sync statuses |

---

## Test Cases

### TC0048: Sidebar renders project list from API data

**Type:** Unit | **Priority:** Critical | **Story:** US0005 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Mock API returns 3 projects | fetchProjects mocked |
| When | Sidebar component renders | Component mounted |
| Then | All 3 project names are visible in the sidebar | Names displayed |

**Assertions:**
- [ ] "HomelabCmd" text is in the document
- [ ] "SDLCLens" text is in the document
- [ ] "PersonalBlog" text is in the document
- [ ] Projects appear in a vertical list

---

### TC0049: Sidebar shows empty state when no projects

**Type:** Unit | **Priority:** High | **Story:** US0005 AC1 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Mock API returns empty array | No projects |
| When | Sidebar component renders | Component mounted |
| Then | "No projects" message is displayed with link to Settings | Empty state shown |

**Assertions:**
- [ ] Text "No projects" (or similar) is in the document
- [ ] A link to "/settings" is present

---

### TC0050: Sync status indicators show correct colours

**Type:** Unit | **Priority:** Critical | **Story:** US0005 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Projects with statuses: "synced", "syncing", "never_synced", "error" | Mixed statuses |
| When | Sidebar component renders | Status dots rendered |
| Then | Each project has the correct colour indicator | Colours match brand guide |

**Assertions:**
- [ ] Synced project has lime green indicator (class or style containing #A3E635)
- [ ] Syncing project has blue indicator (class or style containing #3B82F6)
- [ ] Never synced project has grey indicator (class or style containing #78909C)
- [ ] Error project has red indicator (class or style containing #EF4444)

---

### TC0051: Clicking project navigates to document list

**Type:** Unit | **Priority:** Critical | **Story:** US0005 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Sidebar renders with project "HomelabCmd" (slug: "homelabcmd") | Project in list |
| When | User clicks on "HomelabCmd" | Click event |
| Then | Navigation to /projects/homelabcmd/documents occurs | Route changed |

**Assertions:**
- [ ] Project link href is "/projects/homelabcmd/documents"
- [ ] Link is a valid anchor or NavLink element

---

### TC0052: Active project is highlighted

**Type:** Unit | **Priority:** High | **Story:** US0005 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Current route is /projects/homelabcmd/documents | Viewing HomelabCmd |
| When | Sidebar renders | Component mounted |
| Then | "HomelabCmd" has active/highlighted styling | Accent colour applied |

**Assertions:**
- [ ] The active project element has a distinct class or style (lime green accent)
- [ ] Non-active projects do not have the active styling

---

### TC0053: Settings link navigates to /settings

**Type:** Unit | **Priority:** High | **Story:** US0005 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Sidebar component renders | Component mounted |
| When | Looking at the bottom of the sidebar | Settings area |
| Then | "Settings" link is present and points to /settings | Link correct |

**Assertions:**
- [ ] Text "Settings" is in the document
- [ ] Settings link href is "/settings"

---

### TC0054: Application title displays at top of sidebar

**Type:** Unit | **Priority:** Medium | **Story:** US0005 (implied)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Sidebar component renders | Component mounted |
| When | Looking at the top of the sidebar | Header area |
| Then | Application title "Studio Lens" is displayed | Brand name shown |

**Assertions:**
- [ ] Text "Studio Lens" is in the document

---

### TC0055: Sidebar handles API error gracefully

**Type:** Unit | **Priority:** Medium | **Story:** US0005 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Mock API fetch rejects with network error | API failure |
| When | Sidebar component renders | Error caught |
| Then | Error message displayed with retry option | Graceful degradation |

**Assertions:**
- [ ] Text "Failed to load projects" (or similar) is in the document
- [ ] A retry button is present

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
    sync_status: "syncing"
    last_synced_at: null
    document_count: 0
    created_at: "2026-02-17T09:30:00Z"
  - slug: "personalblog"
    name: "PersonalBlog"
    sdlc_path: "/data/projects/PersonalBlog/sdlc-studio"
    sync_status: "never_synced"
    last_synced_at: null
    document_count: 0
    created_at: "2026-02-17T10:00:00Z"

mixed_status_projects:
  - slug: "proj-synced"
    name: "Synced Project"
    sync_status: "synced"
  - slug: "proj-syncing"
    name: "Syncing Project"
    sync_status: "syncing"
  - slug: "proj-never"
    name: "Never Synced"
    sync_status: "never_synced"
  - slug: "proj-error"
    name: "Error Project"
    sync_status: "error"

empty_projects: []
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0048 | Sidebar renders project list | Pending | - |
| TC0049 | Sidebar shows empty state | Pending | - |
| TC0050 | Sync status indicators colours | Pending | - |
| TC0051 | Click navigates to documents | Pending | - |
| TC0052 | Active project highlighted | Pending | - |
| TC0053 | Settings link to /settings | Pending | - |
| TC0054 | Application title at top | Pending | - |
| TC0055 | API error handled gracefully | Pending | - |

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
| 2026-02-17 | Claude | Initial spec from US0005 story plan |
