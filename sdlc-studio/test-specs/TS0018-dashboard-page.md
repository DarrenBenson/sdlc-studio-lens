# TS0018: Dashboard Page

> **Status:** Complete
> **Epic:** [EP0004: Dashboard & Statistics](../epics/EP0004-dashboard-and-statistics.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for the multi-project dashboard page.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0018](../stories/US0018-dashboard-page.md) | Multi-Project Dashboard Page | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0018 | AC1 | Project cards display | TC0210, TC0211 | Pending |
| US0018 | AC2 | Progress ring on cards | TC0212 | Pending |
| US0018 | AC3 | Click navigates to detail | TC0213 | Pending |
| US0018 | AC4 | Zero projects empty state | TC0214 | Pending |
| US0018 | AC5 | Aggregate stats header | TC0215 | Pending |

**Coverage:** 5/5 ACs covered

---

## Test Cases

### TC0210: Dashboard renders project cards
**Type:** Unit | **Priority:** High
- Given: 2 projects in aggregate stats
- Then: 2 project cards rendered with names

### TC0211: Project card shows document count and completion
**Type:** Unit | **Priority:** High
- Given: Project with total_documents=152, completion_percentage=95.8
- Then: Card shows "152" documents and "95.8%" completion

### TC0212: Progress ring on cards
**Type:** Unit | **Priority:** High
- Given: Project with completion_percentage=75.0
- Then: ProgressRing rendered with percentage text "75%"

### TC0213: Click card navigates to project detail
**Type:** Unit | **Priority:** High
- Given: Project card for "project-alpha"
- When: Click card
- Then: Navigates to /projects/project-alpha

### TC0214: Empty state when no projects
**Type:** Unit | **Priority:** High
- Given: Aggregate stats with 0 projects
- Then: "No projects registered" message with Settings link

### TC0215: Aggregate stats header
**Type:** Unit | **Priority:** High
- Given: total_projects=2, total_documents=182, completion_percentage=90.0
- Then: Header shows "2 Projects", "182 Documents", "90%"

### TC0216: Loading state
**Type:** Unit | **Priority:** Medium
- Given: Stats still loading
- Then: Loading indicator displayed

### TC0217: Error state with retry
**Type:** Unit | **Priority:** Medium
- Given: Stats fetch fails
- Then: Error message with retry button

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec |
