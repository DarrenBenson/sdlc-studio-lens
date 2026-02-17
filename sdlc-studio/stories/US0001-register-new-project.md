# US0001: Register a New Project

> **Status:** Done
> **Epic:** [EP0001: Project Management](../epics/EP0001-project-management.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** to register a project by providing its name and sdlc-studio directory path
**So that** its documents can be synced and displayed in the dashboard

## Context

### Persona Reference
**Darren** - Developer managing multiple projects with sdlc-studio, wants visual oversight without filesystem navigation.
[Full persona details](../personas.md#darren)

### Background
This is the entry point for all dashboard functionality. Before any documents can be browsed, searched, or visualised, at least one project must be registered. Registration captures the project name (for display) and the absolute path to its sdlc-studio directory (for sync).

---

## Inherited Constraints

> See Epic for full constraint chain. Key constraints for this story:

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| Epic | Architecture | Read-only filesystem access | Validation reads path but never writes |
| PRD | Security | No authentication (LAN-only) | No auth middleware on endpoint |
| TRD | Data Model | SQLite with slug uniqueness constraint | DB-level duplicate prevention |
| TRD | Protocol | Manual sync only | Registration does not trigger sync |

---

## Acceptance Criteria

### AC1: Successful project registration
- **Given** a valid project name "HomelabCmd" and an existing sdlc-studio directory path "/data/projects/HomelabCmd/sdlc-studio"
- **When** I POST to `/api/v1/projects` with `{"name": "HomelabCmd", "sdlc_path": "/data/projects/HomelabCmd/sdlc-studio"}`
- **Then** I receive 201 with JSON containing slug "homelabcmd", name "HomelabCmd", sdlc_path, sync_status "never_synced", last_synced_at null, document_count 0, and created_at timestamp

### AC2: Auto-generated slug from name
- **Given** a project name "My Cool Project"
- **When** I register the project
- **Then** the slug is auto-generated as "my-cool-project" (lowercase, hyphens, no special characters)

### AC3: Path validation rejects non-existent directory
- **Given** a path "/data/projects/nonexistent/sdlc-studio" that does not exist on the filesystem
- **When** I POST to `/api/v1/projects` with that path
- **Then** I receive 400 with error code "PATH_NOT_FOUND" and message "Project sdlc-studio path does not exist on filesystem"

### AC4: Duplicate slug rejection
- **Given** a project "HomelabCmd" already exists with slug "homelabcmd"
- **When** I POST to `/api/v1/projects` with name "HomelabCmd" (producing the same slug)
- **Then** I receive 409 with error code "CONFLICT" and message "Project slug already exists"

### AC5: Pydantic validation on request body
- **Given** a request body missing the required "name" field
- **When** I POST to `/api/v1/projects` with `{"sdlc_path": "/some/path"}`
- **Then** I receive 422 with error code "VALIDATION_ERROR" and details about the missing field

---

## Scope

### In Scope
- POST /api/v1/projects endpoint
- Pydantic request model (name: str, sdlc_path: str)
- Pydantic response model (slug, name, sdlc_path, sync_status, last_synced_at, document_count, created_at)
- Slug generation algorithm (lowercase, replace spaces/special chars with hyphens)
- Path existence validation using pathlib
- SQLite projects table creation (Alembic migration)
- SQLAlchemy Project model
- Error response format: `{"error": {"code": "...", "message": "..."}}`

### Out of Scope
- Project update and delete (US0002)
- Sync trigger (US0003)
- Frontend UI (US0004)
- Checking whether the directory contains .md files (sync handles this)

---

## Technical Notes

### API Contract

**Request:**
```
POST /api/v1/projects
Content-Type: application/json

{
  "name": "HomelabCmd",
  "sdlc_path": "/data/projects/HomelabCmd/sdlc-studio"
}
```

**Response (201):**
```json
{
  "slug": "homelabcmd",
  "name": "HomelabCmd",
  "sdlc_path": "/data/projects/HomelabCmd/sdlc-studio",
  "sync_status": "never_synced",
  "last_synced_at": null,
  "document_count": 0,
  "created_at": "2026-02-17T10:00:00Z"
}
```

### Data Requirements
- Projects table with columns: id, slug, name, sdlc_path, sync_status, sync_error, last_synced_at, created_at, updated_at
- Slug column: UNIQUE, NOT NULL
- sync_status default: "never_synced"
- Alembic initial migration creates the table

### Slug Generation Algorithm
```
1. Convert to lowercase
2. Replace spaces and underscores with hyphens
3. Remove characters not matching [a-z0-9-]
4. Collapse consecutive hyphens
5. Strip leading/trailing hyphens
```

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Path exists but is a file, not a directory | 400 PATH_NOT_FOUND with message indicating path is not a directory |
| Name with only special characters (e.g., "!!!") | 422 VALIDATION_ERROR - slug would be empty after sanitisation |
| Very long name (>200 characters) | 422 VALIDATION_ERROR - name exceeds maximum length |
| Path with trailing slash vs without | Both accepted; normalised internally before validation |
| Name with unicode characters (e.g., "Projet Numero Un") | Slug strips non-ASCII: "projet-numero-un" |
| Empty name string | 422 VALIDATION_ERROR - name cannot be empty |
| Empty sdlc_path string | 422 VALIDATION_ERROR - sdlc_path cannot be empty |
| Path with symlinks | Resolve symlinks before validation; validate resolved path exists |
| Concurrent registration with same slug | Database UNIQUE constraint returns 409 CONFLICT |

---

## Test Scenarios

- [ ] Register project with valid name and path returns 201
- [ ] Response body contains all expected fields with correct types
- [ ] Slug generated correctly from name with spaces
- [ ] Slug generated correctly from name with special characters
- [ ] Duplicate slug returns 409 CONFLICT
- [ ] Non-existent path returns 400 PATH_NOT_FOUND
- [ ] Path that is a file (not directory) returns 400
- [ ] Missing name field returns 422
- [ ] Missing sdlc_path field returns 422
- [ ] Empty name returns 422
- [ ] sync_status defaults to "never_synced"
- [ ] document_count defaults to 0
- [ ] created_at is set to current timestamp

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| None | - | First story in pipeline | - |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| SQLite database setup | Infrastructure | Not Started |
| Alembic migration framework | Infrastructure | Not Started |

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
| 2026-02-17 | Claude | Initial story creation from EP0001 |
