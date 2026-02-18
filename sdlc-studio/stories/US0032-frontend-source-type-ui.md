# US0032: Frontend Source Type UI

> **Status:** Done
> **Epic:** [EP0007: Git Repository Sync](../epics/EP0007-git-repository-sync.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-18

## User Story

**As a** SDLC Developer (Darren)
**I want** the frontend project form to support configuring GitHub repository sources alongside local paths
**So that** I can create and edit GitHub-sourced projects through the dashboard UI

## Context

### Persona Reference
**Darren** - Uses the dashboard UI to create and manage projects, preferring a clear visual distinction between local and GitHub sources.
[Full persona details](../personas.md#darren)

### Background
The current project creation and edit forms only support a local SDLC path field. To support GitHub repository sync, the form needs a source type toggle (local/github) that conditionally shows the relevant fields. In local mode, the existing SDLC Path field is shown. In GitHub mode, fields for Repository URL, Branch, Subdirectory Path, and Access Token are shown instead. The TypeScript types, API client, and project card component must also be updated to handle the new fields. The access token field uses a password input to avoid exposing the value on screen.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Tech Stack | React 19, TypeScript, Tailwind CSS 4 | Standard React patterns |
| TRD | Tech Stack | Vite 7, react-router-dom 7 | Existing build and routing |
| PRD | UX | Consistent with existing dashboard style | Reuse existing form components and layout |
| PRD | Security | Access tokens not displayed in plain text | Password input type for token field |

---

## Acceptance Criteria

### AC1: TypeScript types updated
- **Given** the types in `types/index.ts`
- **When** I inspect them
- **Then** `Project`, `ProjectCreate`, and `ProjectUpdate` include `source_type`, `repo_url`, `repo_branch`, `repo_path`, and `access_token` fields with correct types

### AC2: Source type toggle
- **Given** the project creation form
- **When** I view the form
- **Then** there is a toggle or selector to choose between "Local" and "GitHub" source types

### AC3: Local mode fields
- **Given** the source type is set to "Local"
- **When** I view the form
- **Then** the SDLC Path field is visible and required, and GitHub-specific fields are hidden

### AC4: GitHub mode fields
- **Given** the source type is set to "GitHub"
- **When** I view the form
- **Then** the following fields are visible: Repository URL (required), Branch (default "main"), Subdirectory Path (default "sdlc-studio"), Access Token (optional, password input)

### AC5: SDLC Path hidden in GitHub mode
- **Given** the source type is set to "GitHub"
- **When** I view the form
- **Then** the SDLC Path field is hidden and not required

### AC6: Form submission with GitHub fields
- **Given** a completed project form with source_type="github"
- **When** I submit the form
- **Then** the API receives the GitHub fields and creates the project successfully

### AC7: ProjectCard shows repository URL
- **Given** a project with `source_type="github"` and a `repo_url`
- **When** I view the project card on the dashboard
- **Then** the repo URL is displayed instead of the local sdlc_path

### AC8: Edit form populates GitHub fields
- **Given** an existing GitHub-sourced project
- **When** I open the edit form
- **Then** the source type toggle is set to "GitHub" and the GitHub fields are populated with existing values

### AC9: Access token field is password type
- **Given** the project form in GitHub mode
- **When** I view the Access Token field
- **Then** the input type is "password" so the value is masked during entry

### AC10: API client updated
- **Given** the API client in `api/client.ts`
- **When** I inspect the project creation and update functions
- **Then** they pass the new fields to the backend API

---

## Scope

### In Scope
- Update `types/index.ts` with new fields on Project, ProjectCreate, ProjectUpdate
- Update ProjectForm component with source type toggle
- Conditional field rendering based on source type
- Password input for access token
- Update ProjectCard to show repo URL for GitHub projects
- Update `api/client.ts` if needed for new fields
- Form validation (repo_url required when source_type is "github")

### Out of Scope
- GitHub repository browser or autocomplete
- Token validation against GitHub API from the frontend
- OAuth flow for GitHub authentication
- Visual indicator of sync status specific to GitHub
- Repository webhook configuration UI

---

## Technical Notes

### Source Type Toggle
A segmented control or radio group works well for a binary choice. Example using Tailwind:
```tsx
<div className="flex gap-2">
  <button
    type="button"
    className={`px-4 py-2 rounded ${sourceType === "local" ? "bg-brand-primary text-white" : "bg-gray-200"}`}
    onClick={() => setSourceType("local")}
  >
    Local
  </button>
  <button
    type="button"
    className={`px-4 py-2 rounded ${sourceType === "github" ? "bg-brand-primary text-white" : "bg-gray-200"}`}
    onClick={() => setSourceType("github")}
  >
    GitHub
  </button>
</div>
```

### Type Updates
```typescript
// types/index.ts
interface Project {
  // ... existing fields ...
  source_type: "local" | "github";
  repo_url: string | null;
  repo_branch: string;
  repo_path: string;
  access_token: string | null; // Masked from API
}

interface ProjectCreate {
  name: string;
  sdlc_path?: string | null;
  source_type?: "local" | "github";
  repo_url?: string | null;
  repo_branch?: string;
  repo_path?: string;
  access_token?: string | null;
}
```

### Conditional Rendering Pattern
```tsx
{sourceType === "local" && (
  <Input label="SDLC Path" required ... />
)}
{sourceType === "github" && (
  <>
    <Input label="Repository URL" required placeholder="https://github.com/owner/repo" ... />
    <Input label="Branch" defaultValue="main" ... />
    <Input label="Subdirectory Path" defaultValue="sdlc-studio" ... />
    <Input label="Access Token" type="password" placeholder="Optional - for private repos" ... />
  </>
)}
```

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Toggle source type clears other mode's fields | Form resets GitHub fields when switching to local and vice versa |
| Submit GitHub form without repo_url | Client-side validation error: "Repository URL is required" |
| Submit local form without sdlc_path | Client-side validation error: "SDLC Path is required" |
| Edit GitHub project and change to local | sdlc_path becomes required; GitHub fields cleared |
| Edit local project and change to GitHub | repo_url becomes required; sdlc_path cleared |
| API returns masked access_token | Edit form shows masked value; empty field means "keep existing" |
| Very long repository URL | Field wraps or truncates in project card display |
| Project card for local project | Displays sdlc_path as before (no regression) |

---

## Test Scenarios

- [ ] types/index.ts includes source_type, repo_url, repo_branch, repo_path on Project
- [ ] types/index.ts includes new fields on ProjectCreate and ProjectUpdate
- [ ] Source type toggle renders and switches between local and github
- [ ] Local mode shows SDLC Path field, hides GitHub fields
- [ ] GitHub mode shows Repository URL, Branch, Subdirectory Path, Access Token fields
- [ ] GitHub mode hides SDLC Path field
- [ ] Repository URL field is required in GitHub mode
- [ ] Access Token field has type="password"
- [ ] Branch field defaults to "main"
- [ ] Subdirectory Path field defaults to "sdlc-studio"
- [ ] Form submission sends correct fields for local project
- [ ] Form submission sends correct fields for GitHub project
- [ ] ProjectCard shows repo_url for GitHub projects
- [ ] ProjectCard shows sdlc_path for local projects (regression)
- [ ] Edit form populates correctly for GitHub project
- [ ] Edit form populates correctly for local project
- [ ] api/client.ts passes new fields to API

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0031](US0031-api-schema-source-type.md) | API | Backend accepts and returns new fields | Not Started |

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
| 2026-02-18 | Claude | Initial story creation from EP0007 |
