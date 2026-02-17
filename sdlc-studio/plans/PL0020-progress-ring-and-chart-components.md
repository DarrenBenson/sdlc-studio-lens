# PL0020: Progress Ring and Chart Components - Implementation Plan

> **Status:** Complete
> **Story:** [US0020: Progress Ring and Chart Components](../stories/US0020-progress-ring-and-chart-components.md)
> **Epic:** [EP0004: Dashboard & Statistics](../epics/EP0004-dashboard-and-statistics.md)
> **Created:** 2026-02-17
> **Language:** TypeScript

## Overview

Create reusable ProgressRing (SVG), StatsCard, and Recharts-themed chart wrapper components styled to the brand guide. These components are consumed by US0018 (Dashboard) and US0019 (Project Detail).

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | ProgressRing renders percentage | SVG circular arc with lime green fill and percentage text |
| AC2 | Edge values (0%, 100%) | Empty ring for 0, full ring for 100 |
| AC3 | Recharts dark theme | Dark background, lime green primary, brand text colours |
| AC4 | StatsCard component | Count in JetBrains Mono + label on dark surface |
| AC5 | Chart colour palette | Status colours: Done=#A3E635, In Progress=#3B82F6, Draft=#78909C, Blocked=#EF4444 |

## Recommended Approach

**Strategy:** TDD
**Rationale:** Pure UI components with clear visual contracts. Easy to test SVG attributes and rendered text.

## Implementation Phases

### Phase 1: ProgressRing SVG Component
- [ ] Create `components/ProgressRing.tsx`
- [ ] SVG circle with track + arc for percentage
- [ ] Percentage text in centre
- [ ] Props: percentage, size (default 80), strokeWidth (default 8)
- [ ] Clamp percentage to 0-100

### Phase 2: StatsCard Component
- [ ] Create `components/StatsCard.tsx`
- [ ] Display count (large, mono font) and label
- [ ] Optional onClick for navigation

### Phase 3: Chart Theme Constants
- [ ] Create `lib/chartTheme.ts` with brand guide colour constants
- [ ] Export CHART_THEME and STATUS_COLOURS

## Edge Case Handling

| # | Edge Case | Handling Strategy | Phase |
|---|-----------|-------------------|-------|
| 1 | Percentage > 100 | Clamp to 100 | Phase 1 |
| 2 | Percentage < 0 | Clamp to 0 | Phase 1 |
| 3 | NaN percentage | Treat as 0 | Phase 1 |
| 4 | Very small ring (24px) | Scale text; hide if too small | Phase 1 |
| 5 | Zero data points in chart | Handled by consuming pages | Phase 3 |
| 6 | Single data point | Works naturally | Phase 3 |
| 7 | Recharts import failure | Consuming pages handle fallback | Phase 3 |

**Coverage:** 7/7 edge cases handled

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit tests written and passing
- [ ] Edge cases handled
- [ ] Components use brand guide tokens
