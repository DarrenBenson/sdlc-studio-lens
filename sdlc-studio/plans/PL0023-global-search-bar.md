# PL0023: Global Search Bar Component - Implementation Plan

> **Status:** Complete
> **Story:** [US0023: Global Search Bar Component](../stories/US0023-global-search-bar.md)
> **Epic:** [EP0005: Search](../epics/EP0005-search.md)
> **Created:** 2026-02-17
> **Language:** TypeScript

## Overview

Create a SearchBar component in the Layout header. Typing a query and pressing Enter navigates to /search?q=... Keyboard shortcut `/` focuses the input. Reads query from URL on search results page.

## Recommended Approach

**Strategy:** TDD

## Implementation Phases

### Phase 1: SearchBar Component
- [ ] Create `components/SearchBar.tsx`
- [ ] Text input with search icon and placeholder
- [ ] Enter key navigates to /search?q=...
- [ ] Empty submit prevented
- [ ] Reads `q` from URL search params to sync value
- [ ] `/` keyboard shortcut focuses input (when no other input focused)

### Phase 2: Layout Integration
- [ ] Add SearchBar to Layout.tsx header

## Edge Case Handling

| # | Edge Case | Handling Strategy | Phase |
|---|-----------|-------------------|-------|
| 1 | Empty submit | Prevent navigation | Phase 1 |
| 2 | Whitespace-only | Trim and treat as empty | Phase 1 |
| 3 | Special characters | URL-encoded by navigate | Phase 1 |
| 4 | `/` in text input | Don't steal focus | Phase 1 |
| 5 | Query preserved on results page | Read from useSearchParams | Phase 1 |

**Coverage:** 5/5

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit tests written and passing
- [ ] Edge cases handled
