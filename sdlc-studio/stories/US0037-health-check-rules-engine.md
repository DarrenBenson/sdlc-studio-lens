# US0037: Health Check Rules Engine

> **Status:** Done
> **Epic:** [EP0009: Project Health Check](../epics/EP0009-project-health-check.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-18
> **Story Points:** 5

## User Story

**As a** SDLC Developer (Darren)
**I want** a rules engine that analyses project documents for quality issues
**So that** I can identify documentation gaps, inconsistencies, and integrity problems automatically

## Context

### Persona Reference
**Darren** - Maintains multiple SDLC projects and needs automated quality checks to keep documentation healthy.
[Full persona details](../personas.md#darren)

### Background
SDLC projects accumulate documents over time (PRD, TRD, epics, stories, plans, test specs, bugs). Without automated analysis, it's easy to miss quality issues: stories without plans, orphan references to deleted documents, epics marked Done with incomplete children, or documents without status fields.

This story implements a pure-function rules engine that accepts a list of Document objects and returns structured findings. The engine runs 17 rules across 4 categories (completeness, consistency, quality, integrity) with severity-weighted scoring.

---

## Inherited Constraints

> See Epic for full constraint chain. Key constraints for this story:

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Decision (ADR-006) | Pure function, no DB access | Engine receives document list, returns result |
| PRD | KPI | API response < 500ms | Rules must complete fast for up to 500 docs |
| PRD | Architecture | Read-only | No document mutations in rules |

---

## Acceptance Criteria

### AC1: Pure function signature
- **Given** a list of Document objects and a project slug
- **When** I call `run_health_check(documents, project_slug)`
- **Then** it returns a `HealthCheckResult` with findings, summary, and score

### AC2: Completeness rules (5 rules)
- **Given** a set of project documents
- **When** the health check runs
- **Then** it checks for: MISSING_PRD, MISSING_TRD, MISSING_PLAN, MISSING_TEST_SPEC, EPIC_NO_STORIES

### AC3: Consistency rules (6 rules)
- **Given** a set of project documents
- **When** the health check runs
- **Then** it checks for: STORY_NO_EPIC, PLAN_NO_STORY, TEST_SPEC_NO_STORY, ORPHAN_REFERENCE, STATUS_MISMATCH, STALE_ARTEFACT_STATUS

### AC4: Quality rules (4 rules)
- **Given** a set of project documents
- **When** the health check runs
- **Then** it checks for: MISSING_STATUS, MISSING_OWNER, MISSING_PRIORITY, MISSING_STORY_POINTS

### AC5: Integrity rules (3 rules)
- **Given** a set of project documents
- **When** the health check runs
- **Then** it checks for: DUPLICATE_DOC_ID, EMPTY_CONTENT, STALE_DOCUMENT

### AC6: Severity weighting and score
- **Given** health check findings
- **When** the score is calculated
- **Then** `score = 100 - (critical*15 + high*5 + medium*2 + low*1)`, clamped to 0-100

### AC7: Finding structure
- **Given** a detected issue
- **When** a HealthFinding is created
- **Then** it includes: rule_id, severity, category, message, affected_documents, suggested_fix

### AC8: Inactive story exclusion
- **Given** stories with status Done, Complete, Won't Implement, or Superseded
- **When** planning-oriented rules run (MISSING_PLAN, MISSING_TEST_SPEC, MISSING_PRIORITY, MISSING_STORY_POINTS)
- **Then** those stories are skipped (plans are pre-implementation artefacts)

### AC9: Empty project handling
- **Given** a project with zero documents
- **When** the health check runs
- **Then** it returns score 100, zero findings

---

## Scope

### In Scope
- `HealthFinding`, `AffectedDocument`, `HealthCheckResult` dataclasses
- 17 rule functions (one per rule)
- `run_health_check()` orchestrator function
- Score calculation with severity weights
- Skip logic for inactive stories and project-level documents

### Out of Scope
- API endpoint (US0038)
- Frontend dashboard (US0039)
- Custom rule configuration
- Historical score tracking

---

## Technical Notes

### Module Structure
```python
# services/health_check.py
@dataclass(frozen=True)
class HealthFinding: ...
@dataclass
class HealthCheckResult: ...

def run_health_check(documents, project_slug, now=None) -> HealthCheckResult: ...
```

### Rule Categories
| Category | Rules | Severities |
|----------|-------|------------|
| Completeness | 5 | critical, high, medium |
| Consistency | 6 | high, medium, low |
| Quality | 4 | high, medium, low |
| Integrity | 3 | critical, high, low |

---

## Test Scenarios

- [x] Empty project returns score 100
- [x] Missing PRD fires MISSING_PRD (critical)
- [x] Missing TRD fires MISSING_TRD (high)
- [x] Story without plan fires MISSING_PLAN (medium)
- [x] Story without test-spec fires MISSING_TEST_SPEC (medium)
- [x] Epic-scoped test-specs suppress MISSING_TEST_SPEC for covered stories
- [x] Epic with no stories fires EPIC_NO_STORIES (high)
- [x] Story without epic fires STORY_NO_EPIC (high)
- [x] Plan without story fires PLAN_NO_STORY (medium)
- [x] Test-spec without story fires TEST_SPEC_NO_STORY (medium)
- [x] Orphan epic reference fires ORPHAN_REFERENCE (medium)
- [x] Done epic with incomplete children fires STATUS_MISMATCH (low)
- [x] Stale artefact with Done parent fires STALE_ARTEFACT_STATUS (low)
- [x] Document without status fires MISSING_STATUS (high)
- [x] Epic/story without owner fires MISSING_OWNER (medium)
- [x] Active story without priority fires MISSING_PRIORITY (low)
- [x] Active story without points fires MISSING_STORY_POINTS (low)
- [x] Duplicate doc_id fires DUPLICATE_DOC_ID (critical)
- [x] Empty content fires EMPTY_CONTENT (high)
- [x] Stale document (30+ days) fires STALE_DOCUMENT (low)
- [x] Score formula calculates correctly with mixed severities

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| None | - | Builds on existing Document model from EP0001/EP0002 | - |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

---

## Estimation

**Story Points:** 5
**Complexity:** High

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-19 | Claude | Initial story creation (retroactive, implementation complete) |
