# TS0023: Global Search Bar Component

> **Status:** Complete
> **Epic:** [EP0005: Search](../epics/EP0005-search.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for the global search bar component.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0023](../stories/US0023-global-search-bar.md) | Global Search Bar Component | Medium |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0023 | AC1 | Search bar visible on all pages | TC0239 | Pending |
| US0023 | AC2 | Submit navigates to results | TC0240 | Pending |
| US0023 | AC3 | Preserves query on results page | TC0241 | Pending |
| US0023 | AC4 | Keyboard shortcut | TC0242 | Pending |
| US0023 | AC5 | Empty submit prevented | TC0243 | Pending |

**Coverage:** 5/5 ACs covered

---

## Test Cases

### TC0239: Search bar renders with placeholder
**Type:** Unit | **Priority:** High
- Given: SearchBar component rendered
- Then: Input with placeholder "Search documents..." is visible

### TC0240: Enter submits and navigates
**Type:** Unit | **Priority:** High
- Given: User types "authentication" in search bar
- When: Press Enter
- Then: Navigates to /search?q=authentication

### TC0241: Query preserved from URL
**Type:** Unit | **Priority:** High
- Given: URL is /search?q=authentication
- Then: Search bar input value is "authentication"

### TC0242: Slash key focuses search bar
**Type:** Unit | **Priority:** Medium
- Given: No input is focused
- When: Press `/` key
- Then: Search bar input receives focus

### TC0243: Empty submit does not navigate
**Type:** Unit | **Priority:** High
- Given: Search bar is empty
- When: Press Enter
- Then: No navigation occurs

### TC0244: Whitespace-only submit prevented
**Type:** Unit | **Priority:** Medium
- Given: Search bar contains only spaces
- When: Press Enter
- Then: No navigation occurs

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec |
