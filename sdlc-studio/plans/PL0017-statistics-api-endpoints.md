# PL0017: Statistics API Endpoints - Implementation Plan

> **Status:** Complete
> **Story:** [US0017: Statistics API Endpoints](../stories/US0017-statistics-api-endpoints.md)
> **Epic:** [EP0004: Dashboard & Statistics](../epics/EP0004-dashboard-and-statistics.md)
> **Created:** 2026-02-17
> **Language:** Python

## Overview

Add two statistics endpoints: per-project stats (GET /projects/{slug}/stats) and aggregate stats (GET /stats). Both compute counts from the documents table using GROUP BY queries. Completion percentage = Done stories / Total stories * 100.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Per-project statistics | Returns slug, name, total_documents, by_type, by_status, completion_percentage, last_synced_at |
| AC2 | Aggregated statistics | Returns total_projects, total_documents, aggregate by_type/by_status, overall completion_percentage, projects array |
| AC3 | Completion formula | Done stories / Total stories * 100 |
| AC4 | Zero documents | All counts 0, completion_percentage 0.0 |
| AC5 | 404 for unknown project | Returns 404 NOT_FOUND |

---

## Technical Context

### Language & Framework
- **Primary Language:** Python 3.12
- **Framework:** FastAPI + SQLAlchemy async
- **Test Framework:** pytest + pytest-asyncio + httpx

### Existing Patterns
- Routes in `api/routes/projects.py` with `DbDep` annotation
- Service functions in `services/documents.py` with `AsyncSession` param
- Pydantic schemas in `api/schemas/` directory
- `get_project_by_slug()` + `ProjectNotFoundError` for 404 handling

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** Pure query logic with clear inputs/outputs. AC are specific with exact numbers.

### Test Priority
1. Per-project stats with seeded documents (AC1)
2. Completion percentage edge cases (AC3, AC4)
3. Aggregate stats across multiple projects (AC2)

---

## Implementation Phases

### Phase 1: Schemas
- [ ] Create `api/schemas/stats.py` with ProjectStats, ProjectSummary, AggregateStats

### Phase 2: Service Layer
- [ ] Create `services/stats.py` with `get_project_stats()` and `get_aggregate_stats()`
- [ ] SQL GROUP BY queries for by_type and by_status
- [ ] Completion percentage calculation with zero-division guard

### Phase 3: Routes
- [ ] Add GET `/{slug}/stats` to `api/routes/projects.py`
- [ ] Add GET `/stats` to a new `api/routes/stats.py` (or on projects router)
- [ ] 404 handling for unknown project slug

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | Zero documents | Return all counts 0, completion 0.0 | Phase 2 |
| 2 | No stories | completion_percentage 0.0 (guard against division by zero) | Phase 2 |
| 3 | All stories Done | completion_percentage 100.0 | Phase 2 |
| 4 | Case-sensitive status | GROUP BY uses values as stored | Phase 2 |
| 5 | Zero projects (aggregate) | Return totals 0, empty projects array | Phase 2 |
| 6 | Large project (2000 docs) | Indexed columns, single query | Phase 2 |
| 7 | Null status on documents | Grouped under null key in by_status | Phase 2 |
| 8 | Weighted aggregate completion | Total Done stories / Total stories across all projects | Phase 2 |
| 9 | Non-standard doc_type "other" | Included in by_type counts | Phase 2 |

**Coverage:** 9/9 edge cases handled

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit tests written and passing
- [ ] Edge cases handled
- [ ] Code follows best practices
- [ ] No linting errors
