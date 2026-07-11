# CR-01KX8BYH: Remove the N+1 query pattern in the aggregate stats endpoint

> **Status:** Complete
> **Triaged-by:** Darren; human; v3
> **Priority:** Medium
> **Type:** Improvement
> **Date:** 2026-07-11
> **Created-by:** sdlc-studio file
> **Raised-by:** Priya Nair; persona; v3

## Summary

stats.py:112 loops per project calling `get_project_stats`, which issues ~3 GROUP BY queries each -> 3*N queries for GET /api/v1/stats, the dashboard's primary endpoint. The same function also reconstructs done-story counts from a rounded percentage (line 125), a lossy round-trip - fold into this fix.

## Acceptance Criteria

- [ ] Aggregate stats are computed with a bounded number of grouped queries across all projects (GROUP BY `project_id`, ...), not O(N) per-project round-trips
- [ ] Done/total story counts are summed from true integer counts, not reconstructed from a rounded `completion_percentage`

## Impact

GET /api/v1/stats is the dashboard's primary endpoint; its query count grows linearly with the number of projects (~3 grouped queries per project). Cheap at today's scale, but an avoidable full-table-scan multiplier on the hottest read path as the dataset grows.

**Effort:** M

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Raised |
