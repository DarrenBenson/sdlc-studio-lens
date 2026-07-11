# EP0009: Project Health Check

> **Status:** Done
> **Raised-by:** Darren; human; v1 (inferred)
> **Owner:** Darren
> **Created:** 2026-02-18
> **Target Release:** Phase 6 (Quality)
> **Story Points:** 13

## Summary

Add a project health check feature that analyses a project's SDLC documents for completeness, consistency, quality, and integrity issues. A pure-function rules engine evaluates 17 rules across 4 categories, producing structured findings with severity ratings and suggested fixes. Results are exposed via API and rendered as an interactive dashboard with a colour-coded score ring.

## Inherited Constraints

Constraints that flow from PRD and TRD to this Epic.

### From PRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Architecture | Read-only access to document sources | Health check is read-only analysis, no mutations |
| Business Rule | Manual sync only | Health check analyses current synced state |
| KPI | API response < 500ms | Rules engine must complete within budget |

### From TRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Tech Stack | SQLAlchemy 2.0 async | Fetch all documents via async session |
| Tech Stack | Pydantic v2 | Response schemas for health check results |
| Architecture | Single container | No new dependencies needed |
| Decision | ADR-006 | Pure function rules engine, no DB writes |

> **Note:** Inherited constraints MUST propagate to child Stories. Check Story templates include these constraints.

## Business Context

### Problem Statement

SDLC Studio Lens displays documents and statistics but provides no automated quality analysis. Users cannot easily identify missing documents (e.g., stories without plans), inconsistent references (e.g., orphaned parent links), or quality gaps (e.g., documents without status or owner). Manual review of document relationships across a large project is error-prone and time-consuming.

**PRD Reference:** [SS5 Feature Inventory](../prd.md#5-feature-inventory) (FR11)

### Value Proposition

The health check feature provides an automated, at-a-glance quality assessment of a project's SDLC documentation. It identifies specific issues with actionable fix suggestions, helping maintain documentation hygiene as projects grow.

### Success Metrics

| Metric | Current State | Target | Measurement Method |
|--------|---------------|--------|-------------------|
| Documentation quality visibility | None | Score + findings dashboard | Feature test |
| Issue detection rules | 0 | 17 rules, 4 categories | Unit tests |
| Time to identify quality gaps | Manual review | < 2 seconds | API response time |
| Existing test regression | 530 tests pass | 530 tests still pass | Test suite |

## Scope

### In Scope

- Pure-function rules engine with 17 rules across 4 categories
- Categories: completeness (5 rules), consistency (6 rules), quality (4 rules), integrity (3 rules)
- Severity levels: critical, high, medium, low with weighted scoring
- Score formula: `100 - (critical*15 + high*5 + medium*2 + low*1)`, clamped 0-100
- API endpoint: `GET /api/v1/projects/{slug}/health-check`
- Pydantic response schemas for findings and summary
- Frontend health check page with colour-coded score ring
- Findings grouped by category with severity badges
- Filter/expand controls for findings

### Out of Scope

- Scheduled or automated health checks (manual trigger only)
- Historical health check tracking (no score history)
- Custom rules or rule configuration
- Cross-project health analysis
- Automated fix application (suggestions only)
- Health check as part of sync workflow

### Affected User Personas

- **SDLC Developer (Darren):** Reviews project documentation health, identifies quality gaps

## Acceptance Criteria (Epic Level)

- [x] Health check analyses documents for completeness issues (missing PRD, TRD, plans, test specs)
- [x] Health check detects consistency issues (orphan references, status mismatches, missing parent links)
- [x] Health check identifies quality issues (missing status, owner, priority, story points)
- [x] Health check flags integrity issues (duplicate IDs, empty content, stale documents)
- [x] Each finding includes rule ID, severity, category, message, affected documents, and suggested fix
- [x] Score calculated from severity-weighted penalties, clamped 0-100
- [x] API returns structured health check response with findings and summary
- [x] Frontend renders score ring with colour coding (green/amber/red)
- [x] Frontend displays findings grouped by category with expand/collapse
- [x] All existing tests pass without modification
- [x] New tests cover rules engine, API endpoint, and frontend page

## Dependencies

### Blocked By

| Dependency | Type | Status | Owner | Notes |
|------------|------|--------|-------|-------|
| EP0001: Project Management | Epic | Done | Darren | Project model and API |
| EP0002: Document Sync & Parsing | Epic | Done | Darren | Document model and sync |
| EP0008: Document Relationship Navigation | Epic | Done | Darren | Relationship columns (epic, story) used by rules |

### Blocking

| Item | Type | Impact |
|------|------|--------|
| None | - | Enhancement epic, no downstream blockers |

## Risks & Assumptions

### Assumptions

- All projects have synced documents before running a health check
- The 17-rule set covers the most common documentation quality issues
- Score formula weights are reasonable defaults (no user configuration needed)
- Rules engine completes within API response time budget for projects up to 500 documents
- Inactive stories (Done, Superseded) are excluded from planning-oriented rules

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Rules too noisy for large projects | Medium | Medium | Skip inactive stories for planning rules; filter by severity |
| Score formula weights feel wrong | Low | Low | Weights are tunable constants; adjust based on feedback |
| Large projects slow down analysis | Low | Medium | Pure function, no DB queries in rules; O(n) complexity |

## Technical Considerations

### Architecture Impact

- New service module: `services/health_check.py` (pure function, no DB access)
- New API schemas: `api/schemas/health_check.py`
- New API route on existing projects router
- New frontend page: `pages/HealthCheck.tsx`
- New severity colour variables in `globals.css`

### Integration Points

- Existing document service (`get_all_documents`) provides input
- Projects router hosts the endpoint
- Frontend App.tsx adds route `/projects/:slug/health-check`
- ProjectDetail page links to health check

### Data Considerations

- No database schema changes (reads existing document data)
- Rules engine is a pure function: `list[Document] -> HealthCheckResult`
- No state stored between health check runs

**TRD Reference:** [ADR-006: Health Check Rules Engine](../trd.md#adr-006)

## Sizing & Effort

**Story Points:** 13
**Estimated Story Count:** 3 stories

**Complexity Factors:**

- 17 rules with varied logic and edge cases
- Severity weighting and score calculation
- Frontend score ring with colour-coded gradient
- Category grouping and filter/expand controls
- Handling edge cases (empty projects, archive files, review docs)

## Stakeholders

| Role | Name | Interest |
|------|------|----------|
| Product Owner | Darren | Primary user, defines requirements |
| Developer | Darren/Claude | Implementation |

## Story Breakdown

| ID | Title | Complexity | Status |
|----|-------|------------|--------|
| [US0037](../stories/US0037-health-check-rules-engine.md) | Health Check Rules Engine | High | Done |
| [US0038](../stories/US0038-health-check-api-endpoint.md) | Health Check API Endpoint | Medium | Done |
| [US0039](../stories/US0039-health-check-dashboard-page.md) | Health Check Dashboard Page | Medium | Done |

## Test Plan

**Test Specs:** Per-story test coverage. Backend: `test_health_check.py` (unit, 20 test classes), `test_api_health_check.py` (integration). Frontend: `HealthCheck.test.tsx`.

## Open Questions

None.

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-19 | Claude | Initial epic creation (retroactive, implementation complete) |
