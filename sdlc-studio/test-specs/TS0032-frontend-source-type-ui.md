# TS0032: Frontend Source Type UI

> **Status:** Done
> **Story:** [US0032: Frontend Source Type UI](../stories/US0032-frontend-source-type-ui.md)
> **Epic:** [EP0007: Git Repository Sync](../epics/EP0007-git-repository-sync.md)
> **Owner:** Darren
> **Created:** 2026-02-18
> **Last Updated:** 2026-02-18

## Overview

Test specification for US0032 - Frontend Source Type UI. Covers the React component changes for the project form source type toggle (local/GitHub), conditional field rendering, form submission with the correct payload structure, and ProjectCard display of repository URLs for GitHub-sourced projects. All tests are React component tests using Vitest and React Testing Library, rendering components in isolation with mocked API calls.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0032](../stories/US0032-frontend-source-type-ui.md) | Frontend Source Type UI | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0032 | AC2 | Source type toggle | TC0331, TC0337 | Pending |
| US0032 | AC3 | Local mode fields | TC0332 | Pending |
| US0032 | AC4 | GitHub mode fields | TC0333 | Pending |
| US0032 | AC5 | SDLC Path hidden in GitHub mode | TC0334 | Pending |
| US0032 | AC6 | Form submission with GitHub fields | TC0336 | Pending |
| US0032 | AC7 | ProjectCard shows repo URL | TC0340 | Pending |
| US0032 | AC8 | Edit form populates GitHub fields | TC0339 | Pending |
| US0032 | AC9 | Access token field is password type | TC0338 | Pending |

**Coverage:** 8/10 ACs covered (AC1 types and AC10 API client verified indirectly)

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | No | No standalone utility functions to test |
| Component | Yes | React component rendering and interaction |
| Integration | No | API integration covered by backend tests |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Node.js 22, Vitest, React Testing Library, jsdom |
| External Services | None (API calls mocked) |
| Test Data | Project objects with local and GitHub source types |

---

## Test Cases

| ID | Description | Type | Priority |
|----|-------------|------|----------|
| TC0331 | ProjectForm renders source type toggle | Component | P0 |
| TC0332 | ProjectForm shows SDLC Path field when local selected | Component | P0 |
| TC0333 | ProjectForm shows GitHub fields when github selected | Component | P0 |
| TC0334 | ProjectForm hides SDLC Path field when github selected | Component | P0 |
| TC0335 | ProjectForm submits with source_type=local and sdlc_path | Component | P0 |
| TC0336 | ProjectForm submits with source_type=github and repo fields | Component | P0 |
| TC0337 | ProjectForm defaults to local source type | Component | P0 |
| TC0338 | ProjectForm access token field is type=password | Component | P1 |
| TC0339 | ProjectForm edit mode pre-fills source type and fields | Component | P0 |
| TC0340 | ProjectCard shows repo URL for github projects | Component | P0 |
| TC0341 | ProjectCard shows sdlc_path for local projects | Component | P0 |
| TC0342 | ProjectCard shows source type badge | Component | P1 |

---

### TC0331: ProjectForm renders source type toggle

**Type:** Component | **Priority:** P0 | **Story:** US0032 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The ProjectForm component is rendered in create mode | Form rendered |
| When | I inspect the form elements | Toggle visible |
| Then | A source type toggle or selector is present with "Local" and "GitHub" options | Toggle rendered |

**Assertions:**
- [ ] An element with text "Local" is visible
- [ ] An element with text "GitHub" is visible
- [ ] The toggle is interactive (buttons or radio inputs)

---

### TC0332: ProjectForm shows SDLC Path field when local selected

**Type:** Component | **Priority:** P0 | **Story:** US0032 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The ProjectForm component is rendered with source type set to "Local" | Form rendered |
| When | I inspect the form fields | Fields visible |
| Then | The "SDLC Path" input field is visible and accessible | Field shown |

**Assertions:**
- [ ] An input labelled "SDLC Path" (or similar) is in the document
- [ ] The input is not disabled
- [ ] GitHub-specific fields (Repository URL, Branch, Access Token) are not visible

---

### TC0333: ProjectForm shows GitHub fields when github selected

**Type:** Component | **Priority:** P0 | **Story:** US0032 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The ProjectForm component is rendered | Form rendered |
| When | I click the "GitHub" source type option | GitHub mode selected |
| Then | Fields for Repository URL, Branch, Subdirectory Path, and Access Token are visible | GitHub fields shown |

**Assertions:**
- [ ] An input labelled "Repository URL" (or similar) is visible
- [ ] An input labelled "Branch" (or similar) is visible with default value "main"
- [ ] An input labelled "Subdirectory Path" (or similar) is visible with default value "sdlc-studio"
- [ ] An input labelled "Access Token" (or similar) is visible

---

### TC0334: ProjectForm hides SDLC Path field when github selected

**Type:** Component | **Priority:** P0 | **Story:** US0032 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The ProjectForm component is rendered with source type set to "Local" | Form in local mode |
| When | I click the "GitHub" source type option | Switched to GitHub |
| Then | The "SDLC Path" input field is no longer visible | Field hidden |

**Assertions:**
- [ ] The "SDLC Path" input is not in the document after switching
- [ ] No validation error appears for missing SDLC Path in GitHub mode
- [ ] The form remains functional without the SDLC Path field

---

### TC0335: ProjectForm submits with source_type=local and sdlc_path

**Type:** Component | **Priority:** P0 | **Story:** US0032 AC6

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The ProjectForm component is rendered with a mocked onSubmit handler | Form rendered |
| When | I fill in the name field, set source type to "Local", fill in the SDLC Path, and submit | Form submitted |
| Then | The onSubmit handler receives a payload with `source_type: "local"` and `sdlc_path` set | Correct payload |

**Assertions:**
- [ ] Submitted payload contains `source_type` equal to `"local"`
- [ ] Submitted payload contains `sdlc_path` with the entered value
- [ ] Submitted payload contains `name` with the entered value
- [ ] GitHub-specific fields are not included or are null

---

### TC0336: ProjectForm submits with source_type=github and repo fields

**Type:** Component | **Priority:** P0 | **Story:** US0032 AC6

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The ProjectForm component is rendered with a mocked onSubmit handler | Form rendered |
| When | I fill in the name field, set source type to "GitHub", fill in Repository URL, and submit | Form submitted |
| Then | The onSubmit handler receives a payload with `source_type: "github"`, `repo_url`, `repo_branch`, and `repo_path` | Correct payload |

**Assertions:**
- [ ] Submitted payload contains `source_type` equal to `"github"`
- [ ] Submitted payload contains `repo_url` with the entered value
- [ ] Submitted payload contains `repo_branch` (default or entered)
- [ ] Submitted payload contains `repo_path` (default or entered)
- [ ] `sdlc_path` is not included or is null

---

### TC0337: ProjectForm defaults to local source type

**Type:** Component | **Priority:** P0 | **Story:** US0032 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The ProjectForm component is rendered in create mode with no initial values | Fresh form |
| When | I inspect the initial state of the source type toggle | Default checked |
| Then | The "Local" option is selected by default | Local is default |

**Assertions:**
- [ ] The "Local" toggle/button has the active/selected visual state
- [ ] The "SDLC Path" field is visible (local mode fields shown)
- [ ] GitHub fields are not visible

---

### TC0338: ProjectForm access token field is type=password

**Type:** Component | **Priority:** P1 | **Story:** US0032 AC9

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The ProjectForm component is rendered with source type set to "GitHub" | GitHub mode |
| When | I inspect the Access Token input element | Element inspected |
| Then | The input has `type="password"` to mask the entered value | Password type |

**Assertions:**
- [ ] The Access Token input element has attribute `type` equal to `"password"`
- [ ] Entered characters are not visible as plain text

---

### TC0339: ProjectForm edit mode pre-fills source type and fields

**Type:** Component | **Priority:** P0 | **Story:** US0032 AC8

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The ProjectForm component is rendered in edit mode with an existing GitHub project (source_type="github", repo_url="https://github.com/owner/repo", repo_branch="develop", repo_path="docs") | Edit mode |
| When | I inspect the form's initial state | Fields inspected |
| Then | The "GitHub" toggle is active and all GitHub fields are pre-filled with the project's values | Fields populated |

**Assertions:**
- [ ] "GitHub" option is selected/active
- [ ] Repository URL input has value `"https://github.com/owner/repo"`
- [ ] Branch input has value `"develop"`
- [ ] Subdirectory Path input has value `"docs"`
- [ ] SDLC Path field is not visible

---

### TC0340: ProjectCard shows repo URL for github projects

**Type:** Component | **Priority:** P0 | **Story:** US0032 AC7

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A ProjectCard component rendered with a GitHub project (`source_type: "github"`, `repo_url: "https://github.com/owner/repo"`) | Card rendered |
| When | I inspect the card content | Content visible |
| Then | The repository URL is displayed on the card | URL shown |

**Assertions:**
- [ ] Text containing `"https://github.com/owner/repo"` or `"owner/repo"` is visible
- [ ] The local `sdlc_path` is not prominently displayed (or is absent)

---

### TC0341: ProjectCard shows sdlc_path for local projects

**Type:** Component | **Priority:** P0 | **Story:** US0032 AC7 (regression)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A ProjectCard component rendered with a local project (`source_type: "local"`, `sdlc_path: "/data/projects/test"`) | Card rendered |
| When | I inspect the card content | Content visible |
| Then | The local SDLC path is displayed on the card | Path shown |

**Assertions:**
- [ ] Text containing `"/data/projects/test"` is visible
- [ ] No GitHub-specific information (repo URL) is displayed
- [ ] Card layout and styling are consistent with before the source type changes

---

### TC0342: ProjectCard shows source type badge

**Type:** Component | **Priority:** P1 | **Story:** US0032 AC7

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A ProjectCard component rendered with a GitHub project | Card rendered |
| When | I inspect the card for a source type indicator | Badge visible |
| Then | A badge or label indicating "GitHub" is displayed on the card | Badge shown |

**Assertions:**
- [ ] An element with text "GitHub" (or a GitHub icon) is visible on the card
- [ ] For a local project, the badge shows "Local" or equivalent
- [ ] The badge visually distinguishes the two source types

---

## Test Data Requirements

| Data Item | Description | Used By |
|-----------|-------------|---------|
| Local project object | `{ name: "Local Project", source_type: "local", sdlc_path: "/data/projects/test", repo_url: null }` | TC0332, TC0335, TC0341 |
| GitHub project object | `{ name: "GitHub Project", source_type: "github", repo_url: "https://github.com/owner/repo", repo_branch: "develop", repo_path: "docs", access_token: "****1234" }` | TC0333, TC0339, TC0340, TC0342 |
| Empty form state | No initial project data (create mode) | TC0331, TC0337 |
| Mocked onSubmit handler | `vi.fn()` for capturing form submission payloads | TC0335, TC0336 |

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0331 | ProjectForm renders source type toggle | Pending | - |
| TC0332 | ProjectForm shows SDLC Path field when local selected | Pending | - |
| TC0333 | ProjectForm shows GitHub fields when github selected | Pending | - |
| TC0334 | ProjectForm hides SDLC Path field when github selected | Pending | - |
| TC0335 | ProjectForm submits with source_type=local and sdlc_path | Pending | - |
| TC0336 | ProjectForm submits with source_type=github and repo fields | Pending | - |
| TC0337 | ProjectForm defaults to local source type | Pending | - |
| TC0338 | ProjectForm access token field is type=password | Pending | - |
| TC0339 | ProjectForm edit mode pre-fills source type and fields | Pending | - |
| TC0340 | ProjectCard shows repo URL for github projects | Pending | - |
| TC0341 | ProjectCard shows sdlc_path for local projects | Pending | - |
| TC0342 | ProjectCard shows source type badge | Pending | - |

---

## Traceability

| Artefact | Reference |
|----------|-----------|
| PRD | [sdlc-studio/prd.md](../prd.md) |
| Epic | [EP0007](../epics/EP0007-git-repository-sync.md) |

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-18 | Claude | Initial spec |
