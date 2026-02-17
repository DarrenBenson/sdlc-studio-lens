# US0016: Status and Type Badge Components

> **Status:** Done
> **Epic:** [EP0003: Document Browsing](../epics/EP0003-document-browsing.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** consistent, colour-coded status and type badges
**So that** I can scan document lists and identify states at a glance

## Context

### Persona Reference
**Darren** - Prefers data-dense, scannable interfaces with visual status indicators.
[Full persona details](../personas.md#darren)

### Background
Status badges and type badges are reusable components used across the document list, document view, dashboard cards, and search results. They follow the brand guide colour system for consistency. Status badges colour-code document states (Done=green, In Progress=blue, etc.) and type badges identify document categories (Epic, Story, Bug, etc.).

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Design | Brand Guide colour tokens | Status and type colours from brand guide |
| TRD | UI | StatusBadge and DocumentCard components | Component names defined in TRD |

---

## Acceptance Criteria

### AC1: Status badge colour mapping
- **Given** a status value "Done"
- **When** the StatusBadge renders
- **Then** it displays "Done" with lime green (#A3E635) background

### AC2: All status colours defined
- **Given** status values: Done, In Progress, Draft, Blocked, Not Started, Review, Ready, Planned
- **When** each StatusBadge renders
- **Then** colours are: Done=#A3E635, In Progress=#3B82F6, Draft=#78909C, Blocked=#EF4444, Not Started=#78909C, Review=#F59E0B, Ready=#A3E635/dimmed, Planned=#3B82F6/dimmed

### AC3: Type badge display
- **Given** a document type "epic"
- **When** the TypeBadge renders
- **Then** it displays "Epic" with appropriate styling differentiating it from status badges

### AC4: Unknown status fallback
- **Given** an unexpected status value "Custom Status"
- **When** the StatusBadge renders
- **Then** it displays the text with a neutral grey (#78909C) background

### AC5: Badge accessibility
- **Given** a StatusBadge with colour indicator
- **When** viewed by a screen reader
- **Then** the status text is readable (colour is not the only indicator)

---

## Scope

### In Scope
- StatusBadge component (status text + colour background)
- TypeBadge component (document type label)
- Colour mapping from brand guide tokens
- Accessible text labels (not colour-only)
- Consistent sizing and typography (JetBrains Mono for badges)

### Out of Scope
- Custom badge colours per project
- Badge animations
- Badge click interactions

---

## Technical Notes

### Status Colour Map
```typescript
const STATUS_COLOURS: Record<string, string> = {
  'Done': '#A3E635',
  'In Progress': '#3B82F6',
  'Draft': '#78909C',
  'Blocked': '#EF4444',
  'Not Started': '#78909C',
  'Review': '#F59E0B',
  'Ready': '#86EFAC',
  'Planned': '#93C5FD',
};
```

### Type Labels
```typescript
const TYPE_LABELS: Record<string, string> = {
  'epic': 'Epic',
  'story': 'Story',
  'bug': 'Bug',
  'plan': 'Plan',
  'test-spec': 'Test Spec',
  'prd': 'PRD',
  'trd': 'TRD',
  'tsd': 'TSD',
  'other': 'Other',
};
```

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Unknown status value | Neutral grey badge with text displayed |
| Unknown type value | Display raw type value capitalised |
| Null or undefined status | Render empty or "Unknown" badge |
| Very long status text | Badge expands to fit; no truncation |
| Status with extra whitespace | Trimmed before rendering |

---

## Test Scenarios

- [ ] StatusBadge renders "Done" with correct green colour
- [ ] StatusBadge renders "In Progress" with correct blue colour
- [ ] StatusBadge renders "Blocked" with correct red colour
- [ ] StatusBadge renders "Draft" with correct grey colour
- [ ] StatusBadge handles unknown status with grey fallback
- [ ] TypeBadge renders correct label for each type
- [ ] TypeBadge handles unknown type gracefully
- [ ] Badges are accessible (text readable by screen reader)

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| None | - | Standalone UI components | - |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Tailwind CSS configuration with brand colours | Infrastructure | Not Started |

---

## Estimation

**Story Points:** {{TBD}}
**Complexity:** Low

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial story creation from EP0003 |
