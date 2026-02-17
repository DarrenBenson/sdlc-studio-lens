# TS0017: Statistics API Endpoints

> **Status:** Complete
> **Epic:** [EP0004: Dashboard & Statistics](../epics/EP0004-dashboard-and-statistics.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for statistics API endpoints: per-project stats and aggregate stats.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0017](../stories/US0017-statistics-api-endpoints.md) | Statistics API Endpoints | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0017 | AC1 | Per-project statistics | TC0187, TC0188, TC0189, TC0190, TC0191 | Pending |
| US0017 | AC2 | Aggregated statistics | TC0192, TC0193, TC0194 | Pending |
| US0017 | AC3 | Completion formula | TC0195, TC0196, TC0197 | Pending |
| US0017 | AC4 | Zero documents | TC0198 | Pending |
| US0017 | AC5 | 404 for unknown project | TC0199 | Pending |

**Coverage:** 5/5 ACs covered

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Python 3.12, pytest, httpx |
| External Services | None (in-memory SQLite) |
| Test Data | Seeded projects + documents via fixtures |

---

## Test Cases

### TC0187: Per-project stats returns total document count

**Type:** Integration | **Priority:** High | **Story:** US0017

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with 10 seeded documents | Documents in DB |
| When | GET /api/v1/projects/{slug}/stats | 200 response |
| Then | total_documents equals 10 | Correct count |

### TC0188: Per-project by_type counts

**Type:** Integration | **Priority:** High | **Story:** US0017

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with 3 stories, 2 epics, 1 prd | Documents seeded |
| When | GET /api/v1/projects/{slug}/stats | 200 response |
| Then | by_type = {"story": 3, "epic": 2, "prd": 1} | Correct type breakdown |

### TC0189: Per-project by_status counts

**Type:** Integration | **Priority:** High | **Story:** US0017

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with 5 Done, 3 Draft, 2 In Progress docs | Documents seeded |
| When | GET stats | 200 response |
| Then | by_status = {"Done": 5, "Draft": 3, "In Progress": 2} | Correct status breakdown |

### TC0190: Per-project includes slug, name, last_synced_at

**Type:** Integration | **Priority:** Medium | **Story:** US0017

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project "Test Project" with slug "test-project" | Synced project |
| When | GET stats | 200 response |
| Then | Response includes slug, name, last_synced_at | All fields present |

### TC0191: Null status grouped in by_status

**Type:** Integration | **Priority:** Medium | **Story:** US0017

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with documents having null status | Seeded |
| When | GET stats | 200 response |
| Then | by_status includes null key with count | Null handled |

### TC0192: Aggregate stats total_projects and total_documents

**Type:** Integration | **Priority:** High | **Story:** US0017

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | 2 projects: A (5 docs), B (3 docs) | Seeded |
| When | GET /api/v1/stats | 200 response |
| Then | total_projects=2, total_documents=8 | Correct totals |

### TC0193: Aggregate by_type sums across projects

**Type:** Integration | **Priority:** High | **Story:** US0017

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project A (2 stories, 1 epic), Project B (3 stories) | Seeded |
| When | GET /api/v1/stats | 200 response |
| Then | by_type.story=5, by_type.epic=1 | Aggregated correctly |

### TC0194: Aggregate projects array includes per-project summaries

**Type:** Integration | **Priority:** High | **Story:** US0017

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | 2 projects | Seeded |
| When | GET /api/v1/stats | 200 response |
| Then | projects array has 2 entries with slug, name, total_documents, completion_percentage | Summaries present |

### TC0195: Completion percentage calculated correctly

**Type:** Integration | **Priority:** High | **Story:** US0017

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with 4 stories: 3 Done, 1 Draft | Seeded |
| When | GET stats | 200 response |
| Then | completion_percentage = 75.0 | Correct formula |

### TC0196: No stories means completion 0.0

**Type:** Integration | **Priority:** High | **Story:** US0017

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with 5 epics, 0 stories | Seeded |
| When | GET stats | 200 response |
| Then | completion_percentage = 0.0 | No division by zero |

### TC0197: All stories Done means 100.0

**Type:** Integration | **Priority:** Medium | **Story:** US0017

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with 5 stories, all status "Done" | Seeded |
| When | GET stats | 200 response |
| Then | completion_percentage = 100.0 | Full completion |

### TC0198: Zero-document project returns zeroes

**Type:** Integration | **Priority:** High | **Story:** US0017

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project with no documents | Empty project |
| When | GET stats | 200 response |
| Then | total_documents=0, by_type={}, by_status={}, completion_percentage=0.0 | All zeroes |

### TC0199: 404 for unknown project slug

**Type:** Integration | **Priority:** High | **Story:** US0017

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | No project "nonexistent" | - |
| When | GET /api/v1/projects/nonexistent/stats | Response |
| Then | 404 status code | Not found |

---

## Fixtures

```yaml
project_a:
  name: "Project Alpha"
  slug: "project-alpha"
  sdlc_path: "/tmp/alpha"

project_b:
  name: "Project Beta"
  slug: "project-beta"
  sdlc_path: "/tmp/beta"

documents_a:
  - doc_type: story, status: Done, count: 3
  - doc_type: story, status: Draft, count: 1
  - doc_type: epic, status: Done, count: 2
  - doc_type: prd, status: null, count: 1
  - doc_type: trd, status: null, count: 1
  - doc_type: plan, status: Done, count: 2

documents_b:
  - doc_type: story, status: Done, count: 2
  - doc_type: story, status: "In Progress", count: 1
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0187 | Per-project total document count | Pending | - |
| TC0188 | Per-project by_type counts | Pending | - |
| TC0189 | Per-project by_status counts | Pending | - |
| TC0190 | Per-project slug, name, last_synced_at | Pending | - |
| TC0191 | Null status in by_status | Pending | - |
| TC0192 | Aggregate total_projects and total_documents | Pending | - |
| TC0193 | Aggregate by_type sums | Pending | - |
| TC0194 | Aggregate projects array | Pending | - |
| TC0195 | Completion percentage formula | Pending | - |
| TC0196 | No stories completion 0.0 | Pending | - |
| TC0197 | All stories Done 100.0 | Pending | - |
| TC0198 | Zero-document project zeroes | Pending | - |
| TC0199 | 404 unknown project | Pending | - |

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec |
