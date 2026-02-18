# EP0007: Git Repository Sync

> **Status:** Done
> **Owner:** Darren
> **Created:** 2026-02-18
> **Target Release:** Phase 4 (Remote Sources)
> **Story Points:** 18

## Summary

Add GitHub repository sync as an alternative document source alongside local filesystem. Projects can be configured with a GitHub repository URL, branch, subdirectory path, and optional access token for private repos. The sync engine dispatches to the appropriate source (local or GitHub) and produces the same document records regardless of origin. Designed extensibly so future providers (GitLab, Bitbucket) can be added.

## Inherited Constraints

Constraints that flow from PRD and TRD to this Epic.

### From PRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Architecture | Read-only access to document sources | GitHub API calls are read-only (GET only) |
| Business Rule | Manual sync only | GitHub sync triggered by user, no webhooks or polling |
| Business Rule | Change detection via SHA-256 | GitHub blobs hashed with SHA-256 for skip logic |
| Security | Token masking in API responses | Access tokens show only last 4 characters |
| KPI | Sync (100 docs) < 10s | GitHub API latency may be higher; use recursive tree fetch |

### From TRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Tech Stack | SQLAlchemy 2.0 async | New columns use mapped_column with async session |
| Tech Stack | Pydantic v2 | Schema validation with model_validator for conditional fields |
| Infrastructure | Alembic migrations | New migration for schema changes |
| Architecture | Single container | httpx added to runtime dependencies |

> **Note:** Inherited constraints MUST propagate to child Stories. Check Story templates include these constraints.

## Business Context

### Problem Statement

SDLC Studio Lens currently only syncs documents from local filesystem paths mounted as Docker volumes. When deployed in Docker, this requires bind-mounting every project's sdlc-studio directory into the container. For remote repositories (e.g., projects hosted on GitHub), there is no way to sync documents without cloning the repo to the host first.

**PRD Reference:** [§5 Feature Inventory](../prd.md#5-feature-inventory) (FR9)

### Value Proposition

GitHub repository sync allows the deployed container to pull SDLC documents directly from remote repositories. This eliminates the need for local filesystem access and simplifies deployment for projects hosted on GitHub.

### Success Metrics

| Metric | Current State | Target | Measurement Method |
|--------|---------------|--------|-------------------|
| Source types supported | 1 (local) | 2 (local + github) | Feature test |
| GitHub sync (50 docs) | N/A | < 15s | Wall clock |
| Private repo support | N/A | Working with PAT | Manual test |
| Existing test regression | 378 tests pass | 378 tests still pass | Test suite |

## Scope

### In Scope

- Database schema changes: source_type, repo_url, repo_branch, repo_path, access_token columns
- Alembic migration for new columns with backward-compatible defaults
- GitHub API source module using httpx (Trees + Blobs endpoints)
- Sync engine refactoring to accept pluggable file sources
- API schema updates with conditional validation (local vs github fields)
- Token masking in API responses
- Frontend source type toggle in ProjectForm
- ProjectCard display of repository URL for GitHub projects
- httpx added to runtime dependencies

### Out of Scope

- GitLab, Bitbucket, or other providers (future work)
- Webhook-triggered sync (manual only)
- Git binary or clone operations (pure REST API)
- Token encryption at rest (future security hardening)
- Branch listing or repository browsing UI
- Submodule support
- GitHub API rate limit management beyond basic error handling

### Affected User Personas

- **SDLC Developer (Darren):** Registers projects from GitHub repos, syncs remote documents

## Acceptance Criteria (Epic Level)

- [ ] Register a project with source_type "github" and a valid GitHub repository URL
- [ ] Sync fetches .md files from the specified branch and subdirectory
- [ ] Public repositories sync without an access token
- [ ] Private repositories sync with a valid PAT
- [ ] Access tokens are masked in GET /projects and GET /projects/{slug} responses
- [ ] Local filesystem sync continues to work unchanged for existing projects
- [ ] Sync produces identical document records regardless of source type
- [ ] All existing tests pass without modification
- [ ] New tests cover GitHub source, sync dispatch, API schemas, and frontend form

## Dependencies

### Blocked By

| Dependency | Type | Status | Owner | Notes |
|------------|------|--------|-------|-------|
| EP0001: Project Management | Epic | Done | Darren | Project model and API |
| EP0002: Document Sync & Parsing | Epic | Done | Darren | Sync engine to refactor |
| EP0006: Docker Deployment | Epic | Done | Darren | Container to rebuild |

### Blocking

| Item | Type | Impact |
|------|------|--------|
| None | - | Enhancement epic, no downstream blockers |

## Risks & Assumptions

### Assumptions

- GitHub REST API remains stable (v3)
- httpx is suitable for async HTTP calls within FastAPI
- GitHub personal access tokens (PATs) provide sufficient access for private repos
- Repository sizes are moderate (< 1000 .md files per sync)
- Network connectivity from the Docker container to api.github.com

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| GitHub API rate limiting (60 req/hr unauthenticated) | Medium | High | Recommend using PAT (5000 req/hr); handle 403 gracefully |
| Large repos with many blobs cause slow sync | Low | Medium | Recursive tree fetches all paths in one call; parallel blob fetches |
| GitHub API changes or downtime | Low | Medium | Pin to v3 API; clear error messages on failure |
| Access token leaked in logs | Medium | High | Never log tokens; mask in responses; use SecretStr in Pydantic |

## Technical Considerations

### Architecture Impact

- Project model gains 5 new nullable columns
- Sync engine refactored from monolithic to dispatch pattern
- New service module (github_source.py) added
- httpx becomes a runtime dependency (was dev-only)

### Integration Points

- GitHub REST API (api.github.com)
- Existing sync engine (refactored, not replaced)
- Project CRUD API (extended schemas)
- Frontend ProjectForm (conditional fields)

### Data Considerations

- New columns have server defaults for backward compatibility
- sdlc_path becomes nullable (not needed for GitHub projects)
- access_token stored as plain text (encryption deferred to future)
- Migration is additive only (no data loss)

**TRD Reference:** [§6 Data Architecture](../trd.md#6-data-architecture)

## Sizing & Effort

**Story Points:** 18
**Estimated Story Count:** 5 stories

**Complexity Factors:**

- GitHub API integration with async HTTP client
- Conditional validation in Pydantic schemas
- Sync engine refactoring without breaking existing behaviour
- Frontend form with conditional field visibility
- Token security (masking, no logging)

## Stakeholders

| Role | Name | Interest |
|------|------|----------|
| Product Owner | Darren | Primary user, defines requirements |
| Developer | Darren/Claude | Implementation |

## Story Breakdown

| ID | Title | Complexity | Status |
|----|-------|------------|--------|
| [US0028](../stories/US0028-database-schema-github-source.md) | Database Schema & Project Model | Medium | Not Started |
| [US0029](../stories/US0029-github-api-source-module.md) | GitHub API Source Module | High | Not Started |
| [US0030](../stories/US0030-sync-engine-source-dispatch.md) | Sync Engine Source Dispatch | Medium | Not Started |
| [US0031](../stories/US0031-api-schema-source-type.md) | API Schema Updates | Medium | Not Started |
| [US0032](../stories/US0032-frontend-source-type-ui.md) | Frontend Source Type UI | Medium | Not Started |

## Test Plan

**Test Spec:** To be generated per story (TS0028-TS0032).

## Open Questions

None.

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-18 | Claude | Initial epic creation from PRD FR9 |
