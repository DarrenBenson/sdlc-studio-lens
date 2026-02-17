# TS0016: Status and Type Badge Components

> **Status:** Done
> **Epic:** [EP0003: Document Browsing](../epics/EP0003-document-browsing.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0016 - Status and Type Badge Components. Covers the StatusBadge and TypeBadge reusable React components including colour mapping, accessibility, and edge cases.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0016](../stories/US0016-status-and-type-badge-components.md) | Status and Type Badge Components | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0016 | AC1 | Status badge colour mapping | TC0136 | Covered |
| US0016 | AC2 | All status colours defined | TC0137 | Covered |
| US0016 | AC3 | Type badge display | TC0141, TC0142 | Covered |
| US0016 | AC4 | Unknown status fallback | TC0138 | Covered |
| US0016 | AC5 | Badge accessibility | TC0144 | Covered |

**Coverage:** 5/5 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | Yes | Pure presentational components with clear I/O |
| Integration | No | No API or state management |
| E2E | No | No user flows |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Vitest, React Testing Library, jsdom |
| External Services | None |
| Test Data | String status and type values |

---

## Test Cases

### TC0136: StatusBadge renders "Done" with green colour

**Type:** Unit | **Priority:** Critical | **Story:** US0016 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A StatusBadge with status="Done" | Component renders |
| When | The component mounts | Badge visible |
| Then | Badge shows "Done" text with green background class | Correct colour |

**Assertions:**
- [ ] Badge text content is "Done"
- [ ] Badge element has the green colour class

---

### TC0137: All 8 status colours render correctly

**Type:** Unit | **Priority:** Critical | **Story:** US0016 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | StatusBadge rendered for each of 8 status values | All render |
| When | Each badge mounts | Badges visible |
| Then | Each has the correct colour class | Colour mapping correct |

**Assertions:**
- [ ] Done has green class
- [ ] In Progress has blue class
- [ ] Draft has grey class
- [ ] Blocked has red class
- [ ] Not Started has grey class
- [ ] Review has amber class
- [ ] Ready has light green class
- [ ] Planned has light blue class

---

### TC0138: Unknown status shows grey fallback

**Type:** Unit | **Priority:** High | **Story:** US0016 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | StatusBadge with status="Custom Status" | Unknown value |
| When | Component renders | Badge visible |
| Then | Displays "Custom Status" with grey background | Grey fallback |

**Assertions:**
- [ ] Badge text is "Custom Status"
- [ ] Badge has grey/default colour class

---

### TC0139: Null status renders "Unknown"

**Type:** Unit | **Priority:** Medium | **Story:** US0016 AC4 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | StatusBadge with status=null or undefined | Null input |
| When | Component renders | Badge visible |
| Then | Displays "Unknown" with grey background | Graceful fallback |

**Assertions:**
- [ ] Badge text is "Unknown"
- [ ] Badge has grey colour class

---

### TC0140: Status with whitespace is trimmed

**Type:** Unit | **Priority:** Medium | **Story:** US0016 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | StatusBadge with status="  Done  " | Extra whitespace |
| When | Component renders | Badge visible |
| Then | Displays "Done" (trimmed) with correct green colour | Trimmed |

**Assertions:**
- [ ] Badge text is "Done" (no leading/trailing spaces)
- [ ] Badge has green colour class

---

### TC0141: TypeBadge renders correct labels

**Type:** Unit | **Priority:** Critical | **Story:** US0016 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | TypeBadge rendered for each of 9 types | All render |
| When | Each badge mounts | Badges visible |
| Then | Labels: Epic, Story, Bug, Plan, Test Spec, PRD, TRD, TSD, Other | Correct labels |

**Assertions:**
- [ ] "epic" renders as "Epic"
- [ ] "story" renders as "Story"
- [ ] "test-spec" renders as "Test Spec"
- [ ] "prd" renders as "PRD"
- [ ] "other" renders as "Other"

---

### TC0142: TypeBadge unknown type capitalised

**Type:** Unit | **Priority:** High | **Story:** US0016 AC3 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | TypeBadge with type="workflow" (unknown) | Unknown type |
| When | Component renders | Badge visible |
| Then | Displays "Workflow" (capitalised) | Graceful fallback |

**Assertions:**
- [ ] Badge text is "Workflow" (first letter capitalised)

---

### TC0143: TypeBadge null type renders fallback

**Type:** Unit | **Priority:** Medium | **Story:** US0016 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | TypeBadge with type=null or undefined | Null input |
| When | Component renders | Badge visible |
| Then | Displays "Unknown" | Graceful fallback |

**Assertions:**
- [ ] Badge text is "Unknown"

---

### TC0144: StatusBadge is accessible

**Type:** Unit | **Priority:** High | **Story:** US0016 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | StatusBadge with status="Done" | Badge rendered |
| When | Queried by accessible text | Found |
| Then | Status text "Done" is readable without relying on colour | Accessible |

**Assertions:**
- [ ] Badge can be found by text content "Done"
- [ ] Badge text is visible (not hidden/aria-hidden)

---

## Fixtures

```yaml
status_values:
  - { status: "Done", colour: "green" }
  - { status: "In Progress", colour: "blue" }
  - { status: "Draft", colour: "grey" }
  - { status: "Blocked", colour: "red" }
  - { status: "Not Started", colour: "grey" }
  - { status: "Review", colour: "amber" }
  - { status: "Ready", colour: "light-green" }
  - { status: "Planned", colour: "light-blue" }

type_values:
  - { type: "epic", label: "Epic" }
  - { type: "story", label: "Story" }
  - { type: "bug", label: "Bug" }
  - { type: "plan", label: "Plan" }
  - { type: "test-spec", label: "Test Spec" }
  - { type: "prd", label: "PRD" }
  - { type: "trd", label: "TRD" }
  - { type: "tsd", label: "TSD" }
  - { type: "other", label: "Other" }
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0136 | StatusBadge "Done" green | Pass | `StatusBadge.test.tsx` |
| TC0137 | All 8 status colours | Pass | `StatusBadge.test.tsx` |
| TC0138 | Unknown status grey fallback | Pass | `StatusBadge.test.tsx` |
| TC0139 | Null status "Unknown" | Pass | `StatusBadge.test.tsx` |
| TC0140 | Whitespace trimmed | Pass | `StatusBadge.test.tsx` |
| TC0141 | TypeBadge correct labels | Pass | `StatusBadge.test.tsx` |
| TC0142 | TypeBadge unknown capitalised | Pass | `StatusBadge.test.tsx` |
| TC0143 | TypeBadge null fallback | Pass | `StatusBadge.test.tsx` |
| TC0144 | StatusBadge accessibility | Pass | `StatusBadge.test.tsx` |

---

## Traceability

| Artefact | Reference |
|----------|-----------|
| PRD | [sdlc-studio/prd.md](../prd.md) |
| Epic | [EP0003](../epics/EP0003-document-browsing.md) |
| TSD | [sdlc-studio/tsd.md](../tsd.md) |

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec from US0016 story |
