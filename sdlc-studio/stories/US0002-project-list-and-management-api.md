# US0002: Project List and Management API

> **Status:** Done
> **Epic:** [EP0001: Project Management](../epics/EP0001-project-management.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** to list, view, update, and delete registered projects via the API
**So that** I can manage my project registrations and keep them current

## Context

### Persona Reference
**Darren** - Developer managing multiple projects with sdlc-studio.
[Full persona details](../personas.md#darren)

### Background
After registering projects (US0001), the developer needs CRUD operations to maintain the project list. This includes listing all projects, viewing details for a specific project, updating name or path, and removing projects that are no longer needed.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| Epic | Data Model | Cascading delete removes documents | DELETE must remove associated documents |
| PRD | Security | No authentication | No auth checks on endpoints |
| TRD | API | Projects identified by slug in URL | URL pattern: /api/v1/projects/{slug} |

---

## Acceptance Criteria

### AC1: List all registered projects
- **Given** two projects "HomelabCmd" and "SDLCLens" are registered
- **When** I GET `/api/v1/projects`
- **Then** I receive 200 with an array of 2 project objects, each containing slug, name, sdlc_path, sync_status, last_synced_at, document_count, and created_at

### AC2: Get project details by slug
- **Given** a project "HomelabCmd" exists with slug "homelabcmd"
- **When** I GET `/api/v1/projects/homelabcmd`
- **Then** I receive 200 with the full project object including stats summary

### AC3: Update project name and path
- **Given** a project "HomelabCmd" exists with slug "homelabcmd"
- **When** I PUT `/api/v1/projects/homelabcmd` with `{"name": "HomelabCmd v2", "sdlc_path": "/data/projects/HomelabCmdV2/sdlc-studio"}`
- **Then** I receive 200 with updated project details; slug remains "homelabcmd" (slug does not change on update)

### AC4: Delete project with cascade
- **Given** a project "HomelabCmd" exists with 50 synced documents
- **When** I DELETE `/api/v1/projects/homelabcmd`
- **Then** I receive 204 No Content, and both the project and all 50 associated documents are removed from the database

### AC5: Not found for unknown slug
- **Given** no project with slug "nonexistent" exists
- **When** I GET, PUT, or DELETE `/api/v1/projects/nonexistent`
- **Then** I receive 404 with error code "NOT_FOUND" and message "Project not found"

---

## Scope

### In Scope
- GET /api/v1/projects (list all)
- GET /api/v1/projects/{slug} (get one)
- PUT /api/v1/projects/{slug} (update)
- DELETE /api/v1/projects/{slug} (remove with cascade)
- Pydantic response models
- Pydantic update request model (partial update - name and/or sdlc_path)
- Path re-validation on update (if sdlc_path changes)
- Cascading delete of documents and FTS5 entries

### Out of Scope
- Project registration (US0001)
- Sync trigger (US0003)
- Frontend UI (US0004)
- Slug regeneration on name change (slug is immutable)

---

## Technical Notes

### API Contracts

**List Projects:**
```
GET /api/v1/projects → 200 [ProjectResponse, ...]
```

**Get Project:**
```
GET /api/v1/projects/{slug} → 200 ProjectResponse | 404
```

**Update Project:**
```
PUT /api/v1/projects/{slug}
{"name": "New Name", "sdlc_path": "/new/path/sdlc-studio"}
→ 200 ProjectResponse | 404 | 400 PATH_NOT_FOUND
```

**Delete Project:**
```
DELETE /api/v1/projects/{slug} → 204 | 404
```

### Data Requirements
- Cascading delete: when a project is deleted, all rows in documents table with matching project_id are deleted, along with their FTS5 entries
- updated_at timestamp refreshed on PUT

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| List projects with zero registered | 200 with empty array `[]` |
| Update with non-existent new path | 400 PATH_NOT_FOUND; project unchanged |
| Update with only name (no sdlc_path) | 200; only name updated, path unchanged |
| Update with only sdlc_path (no name) | 200; only path updated, name unchanged |
| Delete project that is currently syncing | 204; delete proceeds, sync operation orphaned |
| PUT with empty body | 422 VALIDATION_ERROR |
| Slug with special characters in URL | 404 if no match (slugs are lowercase alphanumeric + hyphens) |
| GET project includes document_count | Count reflects current synced documents |
| Concurrent delete requests for same project | First succeeds 204, second returns 404 |

---

## Test Scenarios

- [ ] GET /projects returns all registered projects
- [ ] GET /projects returns empty array when none registered
- [ ] GET /projects/{slug} returns correct project details
- [ ] GET /projects/{slug} returns 404 for unknown slug
- [ ] PUT /projects/{slug} updates name successfully
- [ ] PUT /projects/{slug} updates sdlc_path with path validation
- [ ] PUT /projects/{slug} rejects non-existent new path
- [ ] PUT /projects/{slug} keeps slug unchanged even if name changes
- [ ] DELETE /projects/{slug} returns 204
- [ ] DELETE /projects/{slug} cascades to documents table
- [ ] DELETE /projects/{slug} returns 404 for unknown slug
- [ ] Response includes document_count field

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0001](US0001-register-new-project.md) | Schema | Projects table and model | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

---

## Estimation

**Story Points:** {{TBD}}
**Complexity:** Low

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial story creation from EP0001 |
