# US0038: Health Check API Endpoint

> **Status:** Done
> **Raised-by:** Darren; human; v1 (inferred)
> **Epic:** [EP0009: Project Health Check](../epics/EP0009-project-health-check.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-18
> **Story Points:** 3

## User Story

**As a** SDLC Developer (Darren)
**I want** an API endpoint that returns health check results for a project
**So that** the frontend dashboard and external tools can consume structured quality analysis data

## Context

### Persona Reference
**Darren** - Accesses the API to retrieve health check results for dashboard display.
[Full persona details](../personas.md#darren)

### Background
US0037 implemented the health check rules engine as a pure function. This story exposes it via a REST API endpoint at `GET /api/v1/projects/{slug}/health-check`. The endpoint fetches all documents for the project, passes them to the rules engine, and returns the structured result as JSON via Pydantic response schemas.

---

## Inherited Constraints

> See Epic for full constraint chain. Key constraints for this story:

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Tech Stack | Pydantic v2 | Response schemas with nested models |
| TRD | Tech Stack | SQLAlchemy 2.0 async | Async document fetching |
| PRD | KPI | API response < 500ms | Full pipeline must complete within budget |

---

## Acceptance Criteria

### AC1: Endpoint registered
- **Given** the FastAPI application
- **When** I inspect the routes
- **Then** `GET /api/v1/projects/{slug}/health-check` exists on the projects router

### AC2: Successful response
- **Given** a project with synced documents
- **When** I call `GET /api/v1/projects/{slug}/health-check`
- **Then** it returns 200 with a HealthCheckResponse containing project_slug, checked_at, total_documents, findings, summary, and score

### AC3: Finding schema
- **Given** a health check with findings
- **When** the response is serialised
- **Then** each finding includes rule_id, severity, category, message, affected_documents (with doc_id, doc_type, title), and suggested_fix

### AC4: 404 for unknown project
- **Given** a non-existent project slug
- **When** I call `GET /api/v1/projects/{slug}/health-check`
- **Then** it returns 404 with the standard error format `{"error": {"code": "NOT_FOUND", ...}}`

### AC5: Empty project returns score 100
- **Given** a project with zero documents
- **When** I call the health check endpoint
- **Then** it returns score 100, empty findings, all-zero summary

---

## Scope

### In Scope
- Pydantic schemas: `HealthCheckResponse`, `HealthFindingSchema`, `AffectedDocumentSchema`
- Route handler on projects router
- Integration with `get_all_documents` and `run_health_check`
- Standard error handling for unknown projects

### Out of Scope
- Rules engine logic (US0037)
- Frontend page (US0039)
- Caching of results
- Webhook/notification on health degradation

---

## Technical Notes

### API Contract
```
GET /api/v1/projects/{slug}/health-check

Response 200:
{
  "project_slug": "my-project",
  "checked_at": "2026-02-19T10:00:00Z",
  "total_documents": 42,
  "findings": [
    {
      "rule_id": "MISSING_PRD",
      "severity": "critical",
      "category": "completeness",
      "message": "Project has no PRD document.",
      "affected_documents": [],
      "suggested_fix": "Create a PRD document..."
    }
  ],
  "summary": {"critical": 1, "high": 0, "medium": 0, "low": 0},
  "score": 85
}
```

### Schema Location
`api/schemas/health_check.py`

---

## Test Scenarios

- [x] Endpoint returns 200 with valid response schema
- [x] Response includes all expected fields
- [x] Findings array populated for projects with issues
- [x] 404 returned for unknown project slug
- [x] Empty project returns score 100

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| US0037 | Implementation | Rules engine must exist | Done |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

---

## Estimation

**Story Points:** 3
**Complexity:** Medium

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-19 | Claude | Initial story creation (retroactive, implementation complete) |
