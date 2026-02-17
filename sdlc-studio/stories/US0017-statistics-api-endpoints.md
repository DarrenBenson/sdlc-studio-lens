# US0017: Statistics API Endpoints

> **Status:** Done
> **Epic:** [EP0004: Dashboard & Statistics](../epics/EP0004-dashboard-and-statistics.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** API endpoints that return document counts, status breakdowns, and completion percentages
**So that** the dashboard can display project health metrics

## Context

### Persona Reference
**Darren** - Checks project status at the start of work sessions to plan next work.
[Full persona details](../personas.md#darren)

### Background
Statistics are calculated from the documents table using SQL GROUP BY queries. Two endpoints: per-project stats and aggregated stats across all projects. Completion percentage is calculated as Done stories / Total stories. No separate stats table; everything computed at query time.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Performance | Dashboard load < 2 seconds | Stats queries must respond < 100ms |
| TRD | API | GET /projects/{slug}/stats and GET /stats | Two endpoints |
| PRD | KPI | Completion = Done stories / Total stories | Specific formula |

---

## Acceptance Criteria

### AC1: Per-project statistics
- **Given** project "homelabcmd" has 152 documents: 18 epics, 120 stories (115 Done), 5 bugs, 1 prd, 1 trd, 1 tsd, 3 plans, 2 test-specs, 1 personas
- **When** I GET `/api/v1/projects/homelabcmd/stats`
- **Then** I receive 200 with: slug, name, total_documents: 152, by_type counts, by_status counts, completion_percentage: 95.8 (115/120), and last_synced_at

### AC2: Aggregated statistics
- **Given** 2 projects: "homelabcmd" (152 docs) and "sdlc-lens" (30 docs)
- **When** I GET `/api/v1/stats`
- **Then** I receive 200 with total_projects: 2, total_documents: 182, aggregate by_type, aggregate by_status, and overall completion_percentage

### AC3: Completion percentage formula
- **Given** a project with 100 stories: 80 Done, 15 In Progress, 5 Draft
- **When** stats are calculated
- **Then** completion_percentage is 80.0 (80 Done / 100 Total stories * 100)

### AC4: Zero documents handled
- **Given** a project with no synced documents
- **When** I GET stats for that project
- **Then** all counts are 0, completion_percentage is 0 (no division by zero)

### AC5: 404 for unknown project
- **Given** no project "nonexistent" exists
- **When** I GET `/api/v1/projects/nonexistent/stats`
- **Then** I receive 404 NOT_FOUND

---

## Scope

### In Scope
- GET /api/v1/projects/{slug}/stats (per-project)
- GET /api/v1/stats (aggregate)
- by_type breakdown (count per document type)
- by_status breakdown (count per status value)
- completion_percentage (Done stories / Total stories * 100)
- last_synced_at from project record
- Pydantic response models

### Out of Scope
- Historical stats or trends
- Caching (compute at query time; fast enough for <2000 docs)
- Per-epic statistics breakdown

---

## Technical Notes

### API Contracts

**Per-Project Stats (200):**
```json
{
  "slug": "homelabcmd",
  "name": "HomelabCmd",
  "total_documents": 152,
  "by_type": {"epic": 18, "story": 120, "bug": 5, "plan": 3, "test-spec": 2, "prd": 1, "trd": 1, "tsd": 1, "personas": 1},
  "by_status": {"Done": 145, "In Progress": 4, "Draft": 2, "Not Started": 1},
  "completion_percentage": 95.8,
  "last_synced_at": "2026-02-17T10:30:00Z"
}
```

**Aggregate Stats (200):**
```json
{
  "total_projects": 2,
  "total_documents": 182,
  "by_type": {"epic": 22, "story": 140, ...},
  "by_status": {"Done": 160, ...},
  "completion_percentage": 90.0,
  "projects": [
    {"slug": "homelabcmd", "name": "HomelabCmd", "total_documents": 152, "completion_percentage": 95.8, "last_synced_at": "..."}
  ]
}
```

### Data Requirements
- SQL: `SELECT doc_type, COUNT(*) FROM documents WHERE project_id = ? GROUP BY doc_type`
- SQL: `SELECT status, COUNT(*) FROM documents WHERE project_id = ? GROUP BY status`
- Completion: `SELECT COUNT(*) FILTER (WHERE status = 'Done' AND doc_type = 'story') as done, COUNT(*) FILTER (WHERE doc_type = 'story') as total FROM documents WHERE project_id = ?`

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Project with zero documents | All counts 0, completion_percentage 0.0 |
| Project with documents but no stories | completion_percentage 0.0 (no stories to complete) |
| Project with all stories Done | completion_percentage 100.0 |
| Status values with varied casing (done vs Done) | Case-sensitive grouping; document status as stored |
| Aggregate stats with zero projects | total_projects 0, total_documents 0, empty projects array |
| Very large project (2000 documents) | Query completes < 100ms |
| Null status on some documents | Grouped as null/unknown in by_status |
| Aggregate completion across projects | Weighted: total Done stories / total stories across all projects |
| Non-standard doc_type "other" | Included in by_type counts |

---

## Test Scenarios

- [ ] Per-project stats returns correct total_documents
- [ ] by_type counts match actual document types
- [ ] by_status counts match actual document statuses
- [ ] completion_percentage calculated correctly
- [ ] Zero-document project returns 0s without error
- [ ] No stories means completion_percentage 0.0
- [ ] 404 for unknown project slug
- [ ] Aggregate stats totals match sum of individual projects
- [ ] Aggregate completion is weighted average
- [ ] last_synced_at populated from project record
- [ ] projects array in aggregate includes per-project summary

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0007](US0007-filesystem-sync-service.md) | Schema | Documents table with data | Draft |
| [US0001](US0001-register-new-project.md) | Schema | Projects table | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

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
