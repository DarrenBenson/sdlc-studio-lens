# US0031: API Schema Updates

> **Status:** Done
> **Epic:** [EP0007: Git Repository Sync](../epics/EP0007-git-repository-sync.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-18

## User Story

**As a** SDLC Developer (Darren)
**I want** the API schemas and project endpoints to support creating and updating GitHub-sourced projects
**So that** I can manage both local and GitHub projects through the same REST API

## Context

### Persona Reference
**Darren** - Interacts with the API to create projects pointing to GitHub repositories.
[Full persona details](../personas.md#darren)

### Background
The existing Pydantic schemas (`ProjectCreate`, `ProjectUpdate`, `ProjectResponse`) and the project service layer only handle local filesystem projects via `sdlc_path`. To support GitHub sources, the schemas need new fields (`source_type`, `repo_url`, `repo_branch`, `repo_path`, `access_token`) with conditional validation: local projects require `sdlc_path`, while GitHub projects require `repo_url`. The response schema must mask the `access_token` for security (showing only the last 4 characters or null). The project service functions (`create_project`, `update_project`) must accept and persist the new fields, and path validation must be skipped for GitHub-sourced projects.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Tech Stack | Pydantic v2 for validation | Use model_validator for conditional logic |
| TRD | API | REST JSON API with /api/v1 prefix | Existing endpoint paths unchanged |
| PRD | Security | Access tokens not exposed in responses | Mask token in ProjectResponse |
| PRD | Error Format | `{"error": {"code": "...", "message": "..."}}` | Validation errors follow existing format |

---

## Acceptance Criteria

### AC1: ProjectCreate schema updated
- **Given** the updated `ProjectCreate` Pydantic model
- **When** I inspect it
- **Then** it includes `source_type` (default "local"), `repo_url` (optional), `repo_branch` (default "main"), `repo_path` (default "sdlc-studio"), `access_token` (optional)

### AC2: Conditional validation - local
- **Given** a `ProjectCreate` payload with `source_type="local"`
- **When** `sdlc_path` is missing or empty
- **Then** validation fails with a descriptive error

### AC3: Conditional validation - github
- **Given** a `ProjectCreate` payload with `source_type="github"`
- **When** `repo_url` is missing or empty
- **Then** validation fails with a descriptive error

### AC4: sdlc_path optional for github
- **Given** a `ProjectCreate` payload with `source_type="github"` and no `sdlc_path`
- **When** the payload is validated
- **Then** validation passes (sdlc_path is not required for GitHub projects)

### AC5: ProjectUpdate schema updated
- **Given** the updated `ProjectUpdate` Pydantic model
- **When** I inspect it
- **Then** it includes the same optional fields as ProjectCreate (all optional for partial updates)

### AC6: ProjectResponse masks access_token
- **Given** a project with an access_token set
- **When** the API returns the project in a response
- **Then** the `access_token` field shows `"****<last4>"` (e.g. `"****ab1f"`) or null if no token is set

### AC7: ProjectResponse includes new fields
- **Given** the updated `ProjectResponse` Pydantic model
- **When** I inspect it
- **Then** it includes `source_type`, `repo_url`, `repo_branch`, `repo_path`, and `access_token` (masked)

### AC8: Project service accepts new fields
- **Given** the project service functions `create_project` and `update_project`
- **When** called with GitHub source fields
- **Then** the new fields are persisted to the database

### AC9: Path validation skipped for github
- **Given** a `ProjectCreate` payload with `source_type="github"`
- **When** the project is created
- **Then** no filesystem path validation is performed on `sdlc_path`

---

## Scope

### In Scope
- Update `ProjectCreate` schema with new fields and conditional validation
- Update `ProjectUpdate` schema with new optional fields
- Update `ProjectResponse` schema with new fields and token masking
- Update `create_project` service function
- Update `update_project` service function
- Skip path validation for GitHub source_type
- Conditional Pydantic validation using `model_validator`

### Out of Scope
- Frontend form changes (US0032)
- GitHub API integration (US0029)
- Sync engine changes (US0030)
- Token encryption at rest
- Source type migration (changing a project from local to github)

---

## Technical Notes

### Conditional Validation
```python
from pydantic import model_validator

class ProjectCreate(BaseModel):
    name: str
    sdlc_path: str | None = None
    source_type: str = "local"
    repo_url: str | None = None
    repo_branch: str = "main"
    repo_path: str = "sdlc-studio"
    access_token: str | None = None

    @model_validator(mode="after")
    def validate_source_fields(self) -> "ProjectCreate":
        if self.source_type == "local" and not self.sdlc_path:
            raise ValueError("sdlc_path is required for local source type")
        if self.source_type == "github" and not self.repo_url:
            raise ValueError("repo_url is required for github source type")
        return self
```

### Token Masking in Response
```python
class ProjectResponse(BaseModel):
    # ... existing fields ...
    source_type: str
    repo_url: str | None
    repo_branch: str
    repo_path: str
    access_token: str | None  # Masked in serialisation

    @field_validator("access_token", mode="before")
    @classmethod
    def mask_token(cls, v: str | None) -> str | None:
        if v is None or len(v) == 0:
            return None
        return f"****{v[-4:]}"
```

### Allowed source_type Values
Only `"local"` and `"github"` are valid. A `Literal["local", "github"]` type or explicit validation should be used.

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| source_type not "local" or "github" | Validation error: invalid source_type |
| GitHub project with sdlc_path also set | Accepted; sdlc_path stored but not used for sync |
| Local project with repo_url also set | Accepted; repo_url stored but not used for sync |
| access_token is empty string | Treated as no token (normalised to null) |
| access_token shorter than 4 characters | Masked as `"****"` plus the full token (all characters shown) |
| Update changes source_type from local to github | Accepted if new required fields present |
| Partial update omits source_type | source_type unchanged |
| repo_url with invalid format | Accepted at API layer; validation at sync time (US0029) |

---

## Test Scenarios

- [ ] ProjectCreate with source_type="local" and sdlc_path passes validation
- [ ] ProjectCreate with source_type="local" and no sdlc_path fails validation
- [ ] ProjectCreate with source_type="github" and repo_url passes validation
- [ ] ProjectCreate with source_type="github" and no repo_url fails validation
- [ ] ProjectCreate with source_type="github" and no sdlc_path passes validation
- [ ] ProjectCreate with invalid source_type fails validation
- [ ] ProjectUpdate with partial GitHub fields passes validation
- [ ] ProjectResponse masks access_token to last 4 characters
- [ ] ProjectResponse returns null for absent access_token
- [ ] ProjectResponse includes source_type, repo_url, repo_branch, repo_path
- [ ] create_project persists new fields to database
- [ ] update_project persists new fields to database
- [ ] Path validation skipped for github source_type
- [ ] POST /api/v1/projects with GitHub fields returns 201
- [ ] GET /api/v1/projects returns masked access_token

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0028](US0028-database-schema-github-source.md) | Schema | Project model with new columns | Not Started |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Pydantic v2 | Library | Available |

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
| 2026-02-18 | Claude | Initial story creation from EP0007 |
