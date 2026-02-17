# EP0001: Project Management

> **Status:** Done
> **Owner:** Darren
> **Created:** 2026-02-17
> **Target Release:** Phase 1 (Foundation)
> **Story Points:** 16

## Summary

Register, manage, and sync sdlc-studio projects. This epic delivers the core data onboarding workflow: a user registers a project by providing its sdlc-studio directory path, triggers a sync to import documents, and monitors sync status. It establishes the project entity model, CRUD API, and settings UI that all other epics depend on.

## Inherited Constraints

Constraints that flow from PRD and TRD to this Epic.

### From PRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Performance | Dashboard load < 2 seconds | Project list must use efficient queries |
| Security | No authentication (LAN-only) | No auth middleware needed |
| Design | Dark theme with lime green accents ([Brand Guide](../brand-guide.md)) | All UI components follow brand guide |
| Architecture | Read-only filesystem access | Never write to project directories |

### From TRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Architecture | Two-container SPA + API | API routes in FastAPI, UI in React SPA |
| Tech Stack | Python 3.12+/FastAPI, React 19/TypeScript | Backend and frontend stack locked |
| Data Model | SQLite storage | Projects table with slug, name, path, sync_status |
| Protocol | Manual sync only | User-triggered, no filesystem watching |

> **Note:** Inherited constraints MUST propagate to child Stories. Check Story templates include these constraints.

## Business Context

### Problem Statement

Before SDLC Studio Lens exists, there is no way to register or manage sdlc-studio project directories for dashboard viewing. Users need a simple mechanism to point the dashboard at their project directories and trigger document import.

**PRD Reference:** [§2 Problem Statement](../prd.md#2-problem-statement)

### Value Proposition

One-time project registration with a single sync click imports all SDLC documents into the dashboard. No configuration files, no CLI flags - just a path and a button.

### Success Metrics

| Metric | Current State | Target | Measurement Method |
|--------|---------------|--------|-------------------|
| Projects registered | 0 | 2+ (HomelabCmd + another) | Database count |
| Time to register project | N/A | < 30 seconds | User observation |
| Sync trigger to completion | N/A | < 10s for 100 docs | API timing |

## Scope

### In Scope

- Project registration with name and sdlc-studio directory path
- Auto-generated slug from project name
- Path validation (directory exists, contains .md files)
- Duplicate slug prevention
- Project list (view all registered projects)
- Project update (edit name or path)
- Project deletion (cascade deletes associated documents)
- Manual sync trigger via API and UI button
- Sync status tracking (never_synced, syncing, synced, error)
- Sync error message storage and display
- Last-synced-at timestamp
- Settings page UI for project management

### Out of Scope

- Document parsing and storage (EP0002)
- Document browsing and viewing (EP0003)
- Dashboard statistics (EP0004)
- Search functionality (EP0005)
- Docker deployment (EP0006)
- Auto-sync or filesystem watching
- Project import/export
- Bulk project registration

### Affected User Personas

- **SDLC Developer (Darren):** Primary beneficiary - registers projects and triggers sync to populate the dashboard

## Acceptance Criteria (Epic Level)

- [ ] Can register a project with name and valid sdlc-studio directory path
- [ ] Path validation rejects non-existent directories
- [ ] Duplicate slugs are rejected with appropriate error
- [ ] Project list displays all registered projects with sync status
- [ ] Can edit project name and path
- [ ] Can delete a project (and its documents are removed)
- [ ] Sync button triggers document import and shows progress state
- [ ] Sync status updates from "syncing" to "synced" on success
- [ ] Sync status shows "error" with message on failure
- [ ] Last-synced-at timestamp displays correctly
- [ ] Settings page provides project CRUD interface

## Dependencies

### Blocked By

| Dependency | Type | Status | Owner | Notes |
|------------|------|--------|-------|-------|
| None | - | - | - | First epic, no dependencies |

### Blocking

| Item | Type | Impact |
|------|------|--------|
| EP0002: Document Sync & Parsing | Epic | Cannot sync documents without registered projects |
| EP0003: Document Browsing | Epic | Cannot browse without project data |
| EP0004: Dashboard & Statistics | Epic | Cannot show stats without project data |
| EP0005: Search | Epic | Cannot search without project data |

## Risks & Assumptions

### Assumptions

- Project sdlc-studio directories are accessible from the Docker container via volume mounts
- Directory paths are absolute and stable (not ephemeral)
- Slug generation from project name is sufficient (no custom slugs needed)
- SQLite is adequate for the number of registered projects (1-10)

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Volume mount paths differ between dev and Docker | Medium | Medium | Document path mapping in docker-compose |
| Path validation passes but sync fails (permissions) | Low | Medium | Check read permissions during validation |
| Concurrent sync requests for same project | Low | Medium | Return 409 SYNC_IN_PROGRESS if already syncing |

## Technical Considerations

### Architecture Impact

- Establishes SQLite database schema (projects table)
- Creates Alembic migration infrastructure
- Defines FastAPI application factory and dependency injection
- Sets up React Router and layout shell
- Establishes API client pattern (fetch-based)

### Integration Points

- React Settings page → POST/PUT/DELETE /api/v1/projects
- React Sidebar → GET /api/v1/projects (project list)
- Sync button → POST /api/v1/projects/{slug}/sync
- Sidebar → project.sync_status for status indicator

### Data Considerations

- Projects table: low volume (1-10 rows), low write frequency
- Slug uniqueness enforced at database level
- Cascading delete removes all associated documents

**TRD Reference:** [§6 Data Architecture](../trd.md#6-data-architecture)

## Sizing & Effort

**Story Points:** 16
**Estimated Story Count:** ~5 stories

**Complexity Factors:**

- Full-stack implementation (backend API + frontend UI)
- Database schema and migration setup
- Path validation across Docker volume boundaries
- Sync status state machine (never_synced → syncing → synced/error)

## Stakeholders

| Role | Name | Interest |
|------|------|----------|
| Product Owner | Darren | Primary user, defines requirements |
| Developer | Darren/Claude | Implementation |

## Story Breakdown

| ID | Title | Complexity | Status |
|----|-------|------------|--------|
| [US0001](../stories/US0001-register-new-project.md) | Register a New Project | Medium | Draft |
| [US0002](../stories/US0002-project-list-and-management-api.md) | Project List and Management API | Low | Draft |
| [US0003](../stories/US0003-trigger-sync-and-track-status.md) | Trigger Sync and Track Status | Medium | Draft |
| [US0004](../stories/US0004-settings-page-project-management.md) | Settings Page - Project Management | Medium | Draft |
| [US0005](../stories/US0005-sidebar-project-navigation.md) | Sidebar Project Navigation | Low | Draft |

## Test Plan

**Test Spec:** To be generated via `/sdlc-studio test-spec --epic EP0001`.

## Open Questions

None.

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial epic creation from PRD |
