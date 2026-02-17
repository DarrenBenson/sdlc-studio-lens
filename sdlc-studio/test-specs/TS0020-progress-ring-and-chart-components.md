# TS0020: Progress Ring and Chart Components

> **Status:** Complete
> **Epic:** [EP0004: Dashboard & Statistics](../epics/EP0004-dashboard-and-statistics.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for ProgressRing, StatsCard, and chart theme components.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0020](../stories/US0020-progress-ring-and-chart-components.md) | Progress Ring and Chart Components | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0020 | AC1 | ProgressRing renders percentage | TC0200, TC0201 | Pending |
| US0020 | AC2 | Edge values 0% and 100% | TC0202, TC0203, TC0204, TC0205 | Pending |
| US0020 | AC3 | Recharts dark theme | TC0206 | Pending |
| US0020 | AC4 | StatsCard component | TC0207, TC0208 | Pending |
| US0020 | AC5 | Chart colour palette | TC0209 | Pending |

**Coverage:** 5/5 ACs covered

---

## Test Cases

### TC0200: ProgressRing renders percentage text
**Type:** Unit | **Priority:** High | **Story:** US0020
- Given: percentage=85.5
- Then: "85.5%" displayed in SVG text element

### TC0201: ProgressRing SVG arc present
**Type:** Unit | **Priority:** High | **Story:** US0020
- Given: percentage=50
- Then: SVG contains circle elements for track and progress arc

### TC0202: ProgressRing 0% shows empty ring
**Type:** Unit | **Priority:** High | **Story:** US0020
- Given: percentage=0
- Then: "0%" displayed, progress arc has zero length

### TC0203: ProgressRing 100% shows full ring
**Type:** Unit | **Priority:** High | **Story:** US0020
- Given: percentage=100
- Then: "100%" displayed, progress arc is fully filled

### TC0204: ProgressRing clamps > 100
**Type:** Unit | **Priority:** Medium | **Story:** US0020
- Given: percentage=150
- Then: Displays "100%" and full arc

### TC0205: ProgressRing clamps negative
**Type:** Unit | **Priority:** Medium | **Story:** US0020
- Given: percentage=-10
- Then: Displays "0%" and empty arc

### TC0206: Chart theme exports correct colours
**Type:** Unit | **Priority:** Medium | **Story:** US0020
- Then: CHART_THEME has background, text, grid, primary keys
- Then: STATUS_COLOURS has Done, In Progress, Draft, Blocked keys

### TC0207: StatsCard renders count and label
**Type:** Unit | **Priority:** High | **Story:** US0020
- Given: count=120, label="Stories"
- Then: "120" and "Stories" rendered

### TC0208: StatsCard click handler fires
**Type:** Unit | **Priority:** Medium | **Story:** US0020
- Given: StatsCard with onClick
- When: user clicks the card
- Then: onClick called

### TC0209: STATUS_COLOURS match brand guide
**Type:** Unit | **Priority:** Medium | **Story:** US0020
- Then: Done=#A3E635, In Progress=#3B82F6, Draft=#78909C, Blocked=#EF4444

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec |
