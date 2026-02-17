# US0020: Progress Ring and Chart Components

> **Status:** Done
> **Epic:** [EP0004: Dashboard & Statistics](../epics/EP0004-dashboard-and-statistics.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** reusable progress ring and chart components styled to the brand guide
**So that** statistics visualisations are consistent across the dashboard

## Context

### Persona Reference
**Darren** - Expects clean, data-dense visualisations in a dark theme.
[Full persona details](../personas.md#darren)

### Background
The progress ring is a custom SVG component showing a circular arc representing completion percentage. Chart components wrap Recharts with brand guide theming (dark backgrounds, lime green accents). These are reusable across the dashboard page, project detail page, and potentially other views.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Design | Brand Guide colour system and chart theming | All chart colours from brand guide |
| TRD | Tech Stack | Recharts (>=2.10.0) | Chart library |
| PRD | Design | JetBrains Mono for stat numbers | Font for percentage display |

---

## Acceptance Criteria

### AC1: Progress ring renders percentage
- **Given** a completion value of 85.5%
- **When** the ProgressRing renders
- **Then** a circular SVG arc is filled to 85.5% with lime green (#A3E635) on a dark track (#1C2520), with "85.5%" displayed in the centre using JetBrains Mono

### AC2: Progress ring handles edge values
- **Given** completion values of 0% and 100%
- **When** the ProgressRing renders
- **Then** 0% shows an empty ring (track only) and 100% shows a full ring

### AC3: Recharts dark theme
- **Given** a Recharts BarChart component
- **When** rendered within the application
- **Then** it uses dark background colours, lime green for primary data, and brand guide text colours for labels and axes

### AC4: StatsCard component
- **Given** a stat label "Stories" and count 120
- **When** StatsCard renders
- **Then** it displays "120" in JetBrains Mono bold and "Stories" as a label, on a dark surface (#111916) card

### AC5: Chart colour palette
- **Given** a multi-series chart (e.g., status breakdown)
- **When** rendered
- **Then** series use brand guide status colours: Done=#A3E635, In Progress=#3B82F6, Draft=#78909C, Blocked=#EF4444

---

## Scope

### In Scope
- ProgressRing SVG component (configurable size, percentage)
- StatsCard component (count + label)
- Recharts theme configuration (dark mode colours)
- Recharts wrapper components for BarChart and PieChart
- Brand guide colour constants/tokens as TypeScript module

### Out of Scope
- Complex chart interactions (zoom, pan)
- Animated transitions (keep simple for v1.0)
- Chart export or download

---

## Technical Notes

### ProgressRing SVG
```
- Circle radius: configurable (default 40px)
- Stroke width: 8px
- Track colour: #1C2520 (bg-elevated)
- Fill colour: #A3E635 (accent-primary)
- Text: percentage in centre, JetBrains Mono 700
- SVG viewBox: calculated from radius + stroke
```

### Recharts Theme
```typescript
const CHART_THEME = {
  background: '#111916',
  text: '#B0BEC5',
  grid: '#1C2520',
  primary: '#A3E635',
  series: ['#A3E635', '#3B82F6', '#F59E0B', '#EF4444', '#78909C'],
};
```

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Percentage > 100 | Clamped to 100% display |
| Percentage < 0 | Clamped to 0% display |
| NaN percentage | Display "- -" or 0% |
| Very small ProgressRing (24px) | Text scales down or hidden; arc still visible |
| Chart with zero data points | Empty chart with "No data" message |
| Chart with single data point | Single bar/segment displayed |
| Recharts import fails | Fallback to text-based display |

---

## Test Scenarios

- [ ] ProgressRing renders correct arc for 50%
- [ ] ProgressRing renders correct arc for 0%
- [ ] ProgressRing renders correct arc for 100%
- [ ] ProgressRing displays percentage text in centre
- [ ] ProgressRing uses brand guide colours
- [ ] StatsCard displays count and label
- [ ] StatsCard uses JetBrains Mono for numbers
- [ ] Chart theme applies dark colours
- [ ] Chart series use status colour palette

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| None | - | Standalone UI components | - |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Recharts (>=2.10.0) | Package | Not Installed |
| JetBrains Mono font | Asset | Not Configured |
| Space Grotesk font | Asset | Not Configured |

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
| 2026-02-17 | Claude | Initial story creation from EP0004 |
