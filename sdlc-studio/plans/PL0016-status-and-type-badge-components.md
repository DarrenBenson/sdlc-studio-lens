# PL0016: Status and Type Badge Components - Implementation Plan

> **Status:** Done
> **Story:** [US0016: Status and Type Badge Components](../stories/US0016-status-and-type-badge-components.md)
> **Epic:** [EP0003: Document Browsing](../epics/EP0003-document-browsing.md)
> **Created:** 2026-02-17
> **Language:** TypeScript (React)

## Overview

Create reusable StatusBadge and TypeBadge React components with colour-coded indicators following the brand guide. These are pure presentational components with no API dependencies - ideal for TDD.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Status badge colour mapping | Done renders lime green (#A3E635) |
| AC2 | All status colours defined | 8 statuses with correct colours |
| AC3 | Type badge display | Type label with distinct styling |
| AC4 | Unknown status fallback | Grey fallback for unknown values |
| AC5 | Badge accessibility | Text readable by screen readers |

---

## Technical Context

### Language & Framework
- **Primary Language:** TypeScript
- **Framework:** React 19 + Tailwind CSS 4
- **Test Framework:** Vitest + React Testing Library

### Existing Patterns
- Existing badge pattern in `ProjectCard.tsx` with `STATUS_COLOURS` Record lookup
- Tailwind CSS theme tokens in `globals.css` for status colours
- Brand guide colour tokens already defined

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** Pure presentational components with clear input/output. Colour mapping is a lookup table - perfect for test-first.

### Test Priority
1. StatusBadge renders correct colour per status value
2. TypeBadge renders correct labels per type
3. Edge cases (unknown, null, whitespace)

---

## Implementation Phases

### Phase 1: StatusBadge Component
**Goal:** Colour-coded status badge with all 8 statuses + fallback

- [ ] Add status colour CSS variables to globals.css
- [ ] Create StatusBadge component with colour mapping
- [ ] Handle unknown status fallback to grey
- [ ] Handle null/undefined status
- [ ] Trim whitespace from status text

**Files:** `frontend/src/components/StatusBadge.tsx`, `frontend/src/styles/globals.css`

### Phase 2: TypeBadge Component
**Goal:** Document type label badge with distinct styling

- [ ] Create TypeBadge component with type label mapping
- [ ] Handle unknown type (capitalise raw value)
- [ ] Distinct visual style from StatusBadge

**Files:** `frontend/src/components/TypeBadge.tsx`

### Phase 3: Testing & Validation
**Goal:** Verify all acceptance criteria

| AC | Verification Method | Status |
|----|---------------------|--------|
| AC1 | Test StatusBadge "Done" has green class | Pending |
| AC2 | Parametrised test for all 8 statuses | Pending |
| AC3 | Test TypeBadge renders correct labels | Pending |
| AC4 | Test unknown status gets grey fallback | Pending |
| AC5 | Test badge has visible text (not colour-only) | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | Unknown status value | Grey fallback via default case | Phase 1 |
| 2 | Unknown type value | Capitalise raw value | Phase 2 |
| 3 | Null or undefined status | Render "Unknown" with grey | Phase 1 |
| 4 | Very long status text | Badge expands naturally (no max-width) | Phase 1 |
| 5 | Status with extra whitespace | trim() before lookup and display | Phase 1 |

**Coverage:** 5/5 edge cases handled

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit tests written and passing
- [ ] Edge cases handled
- [ ] Code follows TypeScript best practices
- [ ] No linting errors
