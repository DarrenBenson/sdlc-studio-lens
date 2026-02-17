# TS0019: Project Detail Statistics Page

> **Status:** Complete
> **Epic:** [EP0004: Dashboard & Statistics](../epics/EP0004-dashboard-and-statistics.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for the project detail statistics page.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0019](../stories/US0019-project-detail-statistics-page.md) | Project Detail Statistics Page | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0019 | AC1 | Project header with progress ring | TC0218, TC0219 | Pending |
| US0019 | AC2 | Document type distribution chart | TC0220 | Pending |
| US0019 | AC3 | Status breakdown chart | TC0221 | Pending |
| US0019 | AC4 | Per-type count cards | TC0222 | Pending |
| US0019 | AC5 | Navigate to documents | TC0223 | Pending |

**Coverage:** 5/5 ACs covered

---

## Test Cases

### TC0218: Project header renders name and progress ring
**Type:** Unit | **Priority:** High
- Given: Project stats for "Project Alpha" with completion_percentage=95.8
- Then: Page shows "Project Alpha" heading and ProgressRing with "95.8%"

### TC0219: Last synced timestamp displayed
**Type:** Unit | **Priority:** High
- Given: Project with last_synced_at set
- Then: Synced timestamp text displayed

### TC0220: Type distribution chart renders
**Type:** Unit | **Priority:** High
- Given: by_type has story=120, epic=18, bug=5
- Then: Recharts BarChart rendered with type data

### TC0221: Status breakdown chart renders
**Type:** Unit | **Priority:** High
- Given: by_status has Done=145, Draft=2, "In Progress"=4
- Then: Recharts BarChart rendered with status data

### TC0222: Per-type stat cards show counts
**Type:** Unit | **Priority:** High
- Given: by_type has story=120, epic=18, bug=5
- Then: StatsCards rendered with counts per type

### TC0223: Click stat card navigates to filtered documents
**Type:** Unit | **Priority:** High
- Given: Stat card for type "story"
- When: Click card
- Then: Navigates to /projects/project-alpha/documents?type=story

### TC0224: Loading state
**Type:** Unit | **Priority:** Medium
- Given: Stats still loading
- Then: Loading indicator displayed

### TC0225: Error state with retry
**Type:** Unit | **Priority:** Medium
- Given: Stats fetch fails
- Then: Error message with retry button

### TC0226: Zero-document project
**Type:** Unit | **Priority:** Medium
- Given: Project with total_documents=0, empty by_type and by_status
- Then: Page renders with empty charts, stat cards show 0

### TC0227: Not found state
**Type:** Unit | **Priority:** Medium
- Given: fetchProjectStats rejects with error
- Then: Error message displayed

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec |
