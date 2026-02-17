# PL0019: Project Detail Statistics Page - Implementation Plan

> **Status:** Complete
> **Story:** [US0019: Project Detail Statistics Page](../stories/US0019-project-detail-statistics-page.md)
> **Epic:** [EP0004: Dashboard & Statistics](../epics/EP0004-dashboard-and-statistics.md)
> **Created:** 2026-02-17
> **Language:** TypeScript

## Overview

Create the project detail page at `/projects/:slug` with large progress ring, Recharts charts for type distribution and status breakdown, per-type StatsCards with navigation to filtered document list. Uses fetchProjectStats() from US0017, ProgressRing/StatsCard from US0020, and CHART_THEME/STATUS_COLOURS from chartTheme.

## Recommended Approach

**Strategy:** TDD

## Implementation Phases

### Phase 1: Tests (RED)
- [ ] Create `test/pages/ProjectDetail.test.tsx`
- [ ] TC0218-TC0227: 10 test cases covering all 5 ACs + edge cases

### Phase 2: Project Detail Page Component (GREEN)
- [ ] Create `pages/ProjectDetail.tsx`
- [ ] Fetch project stats via fetchProjectStats(slug) using useParams()
- [ ] Render project header with name, large ProgressRing (size=120), last synced
- [ ] Render type distribution bar chart (Recharts BarChart)
- [ ] Render status breakdown bar chart (Recharts BarChart with STATUS_COLOURS)
- [ ] Render per-type StatsCards with onClick navigation to /projects/:slug/documents?type=X
- [ ] Loading and error states
- [ ] 404 state for unknown slug

### Phase 3: Route Update
- [ ] Add `/projects/:slug` route to App.tsx before documents route

## Edge Case Handling

| # | Edge Case | Handling Strategy | Phase |
|---|-----------|-------------------|-------|
| 1 | Project not found | Show "Project not found" with link back to dashboard | Phase 2 |
| 2 | Zero documents | Empty charts, stat cards show 0 | Phase 2 |
| 3 | Single document type | Chart shows single bar | Phase 2 |
| 4 | API error | Error message with retry button | Phase 2 |
| 5 | Loading state | Loading text | Phase 2 |

**Coverage:** 5/5

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit tests written and passing
- [ ] Edge cases handled
