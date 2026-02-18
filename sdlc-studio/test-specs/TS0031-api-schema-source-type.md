# TS0031: API Schema Updates

> **Status:** Done
> **Story:** [US0031: API Schema Updates](../stories/US0031-api-schema-source-type.md)
> **Epic:** [EP0007: Git Repository Sync](../epics/EP0007-git-repository-sync.md)
> **Owner:** Darren
> **Created:** 2026-02-18
> **Last Updated:** 2026-02-18

## Overview

Test specification for US0031 - API Schema Updates. Covers the Pydantic schema changes for `ProjectCreate`, `ProjectUpdate`, and `ProjectResponse` to support GitHub source fields, conditional validation (local requires `sdlc_path`, GitHub requires `repo_url`), access token masking in responses, and the corresponding API endpoint behaviour for creating, reading, and updating projects with the new source type fields.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0031](../stories/US0031-api-schema-source-type.md) | API Schema Updates | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0031 | AC1 | ProjectCreate schema updated | TC0330 | Pending |
| US0031 | AC2 | Conditional validation - local | TC0317, TC0329 | Pending |
| US0031 | AC3 | Conditional validation - github | TC0318, TC0328 | Pending |
| US0031 | AC4 | sdlc_path optional for github | TC0319 | Pending |
| US0031 | AC5 | ProjectUpdate schema updated | TC0326, TC0327 | Pending |
| US0031 | AC6 | ProjectResponse masks access_token | TC0322, TC0323, TC0324, TC0325 | Pending |
| US0031 | AC7 | ProjectResponse includes new fields | TC0330 | Pending |
| US0031 | AC9 | Path validation skipped for github | TC0319 | Pending |

**Coverage:** 8/9 ACs covered (AC8 service persistence covered by integration tests)

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | Yes | Pydantic schema validation and token masking logic |
| Integration | Yes | API endpoint behaviour with real database |
| E2E | No | Covered by integration tests |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Python 3.12, pytest, pytest-asyncio, httpx (test client) |
| External Services | None |
| Test Data | Project payloads for local and GitHub source types |

---

## Test Cases

| ID | Description | Type | Priority |
|----|-------------|------|----------|
| TC0317 | POST /projects with source_type=local requires sdlc_path | Integration | P0 |
| TC0318 | POST /projects with source_type=github requires repo_url | Integration | P0 |
| TC0319 | POST /projects with source_type=github does not require sdlc_path | Integration | P0 |
| TC0320 | POST /projects with source_type=local ignores repo fields | Integration | P1 |
| TC0321 | POST /projects defaults source_type to "local" when omitted | Integration | P0 |
| TC0322 | GET /projects returns masked access_token | Integration | P0 |
| TC0323 | GET /projects/{slug} returns masked access_token | Integration | P0 |
| TC0324 | Token masking shows "****" + last 4 chars | Unit | P0 |
| TC0325 | Token masking returns null for null token | Unit | P0 |
| TC0326 | PUT /projects/{slug} updates repo_url | Integration | P0 |
| TC0327 | PUT /projects/{slug} updates access_token | Integration | P1 |
| TC0328 | ProjectCreate validation rejects github without repo_url | Unit | P0 |
| TC0329 | ProjectCreate validation rejects local without sdlc_path | Unit | P0 |
| TC0330 | ProjectResponse includes source_type and repo fields | Unit | P0 |

---

### TC0317: POST /projects with source_type=local requires sdlc_path

**Type:** Integration | **Priority:** P0 | **Story:** US0031 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The API is running with the updated schemas | API available |
| When | I POST to `/api/v1/projects` with `{"name": "Test", "source_type": "local"}` and no `sdlc_path` | Request sent |
| Then | The API returns HTTP 422 with a validation error indicating `sdlc_path` is required | Validation fails |

**Assertions:**
- [ ] HTTP response status is 422
- [ ] Response body contains an error referencing `sdlc_path`
- [ ] Error message indicates the field is required for local source type

---

### TC0318: POST /projects with source_type=github requires repo_url

**Type:** Integration | **Priority:** P0 | **Story:** US0031 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The API is running with the updated schemas | API available |
| When | I POST to `/api/v1/projects` with `{"name": "Test", "source_type": "github"}` and no `repo_url` | Request sent |
| Then | The API returns HTTP 422 with a validation error indicating `repo_url` is required | Validation fails |

**Assertions:**
- [ ] HTTP response status is 422
- [ ] Response body contains an error referencing `repo_url`
- [ ] Error message indicates the field is required for GitHub source type

---

### TC0319: POST /projects with source_type=github does not require sdlc_path

**Type:** Integration | **Priority:** P0 | **Story:** US0031 AC4, AC9

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The API is running with the updated schemas | API available |
| When | I POST to `/api/v1/projects` with `{"name": "GitHub Test", "source_type": "github", "repo_url": "https://github.com/owner/repo"}` and no `sdlc_path` | Request sent |
| Then | The API returns HTTP 201 and creates the project successfully | Project created |

**Assertions:**
- [ ] HTTP response status is 201
- [ ] Response body contains `"source_type": "github"`
- [ ] Response body contains `"sdlc_path": null` or `sdlc_path` is absent
- [ ] No filesystem path validation is performed

---

### TC0320: POST /projects with source_type=local ignores repo fields

**Type:** Integration | **Priority:** P1 | **Story:** US0031 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The API is running with the updated schemas | API available |
| When | I POST to `/api/v1/projects` with `{"name": "Local Test", "source_type": "local", "sdlc_path": "/data/test", "repo_url": "https://github.com/owner/repo"}` | Request sent |
| Then | The API returns HTTP 201; the project is created with the repo fields stored but not used for sync | Project created |

**Assertions:**
- [ ] HTTP response status is 201
- [ ] Response body contains `"source_type": "local"`
- [ ] Response body contains `"sdlc_path": "/data/test"`
- [ ] Repo fields are accepted without validation error

---

### TC0321: POST /projects defaults source_type to "local" when omitted

**Type:** Integration | **Priority:** P0 | **Story:** US0031 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The API is running with the updated schemas | API available |
| When | I POST to `/api/v1/projects` with `{"name": "Default Test", "sdlc_path": "/data/test"}` and no `source_type` | Request sent |
| Then | The API returns HTTP 201 with `source_type` defaulting to `"local"` | Default applied |

**Assertions:**
- [ ] HTTP response status is 201
- [ ] Response body contains `"source_type": "local"`
- [ ] Backward compatibility with existing API consumers maintained

---

### TC0322: GET /projects returns masked access_token

**Type:** Integration | **Priority:** P0 | **Story:** US0031 AC6

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A GitHub project exists with `access_token="ghp_abcdef1234567890"` | Project stored |
| When | I GET `/api/v1/projects` | Request sent |
| Then | The project in the response list has `access_token` masked as `"****7890"` | Token masked |

**Assertions:**
- [ ] `access_token` value is `"****7890"` (last 4 characters preserved)
- [ ] The full token is never exposed in the response
- [ ] Other fields (`repo_url`, `repo_branch`, etc.) are returned in full

---

### TC0323: GET /projects/{slug} returns masked access_token

**Type:** Integration | **Priority:** P0 | **Story:** US0031 AC6

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A GitHub project exists with `access_token="ghp_abcdef1234567890"` and slug `"test-github"` | Project stored |
| When | I GET `/api/v1/projects/test-github` | Request sent |
| Then | The response has `access_token` masked as `"****7890"` | Token masked |

**Assertions:**
- [ ] `access_token` value is `"****7890"`
- [ ] The full token is not present anywhere in the response body
- [ ] All other project fields are correct and complete

---

### TC0324: Token masking shows "****" + last 4 chars

**Type:** Unit | **Priority:** P0 | **Story:** US0031 AC6

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A token string `"ghp_abcdef1234567890"` | Known token |
| When | The masking function processes this token | Function executes |
| Then | The result is `"****7890"` | Masked correctly |

**Assertions:**
- [ ] Output equals `"****7890"`
- [ ] For a token shorter than 4 characters (e.g., `"abc"`), output is `"****abc"`
- [ ] For an exactly 4-character token (e.g., `"abcd"`), output is `"****abcd"`

---

### TC0325: Token masking returns null for null token

**Type:** Unit | **Priority:** P0 | **Story:** US0031 AC6

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A `None` value for the access_token field | Null token |
| When | The masking function processes this value | Function executes |
| Then | The result is `None` | Null preserved |

**Assertions:**
- [ ] Output is `None` (not `"****"` or empty string)
- [ ] An empty string input also returns `None`

---

### TC0326: PUT /projects/{slug} updates repo_url

**Type:** Integration | **Priority:** P0 | **Story:** US0031 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | An existing GitHub project with slug `"test-github"` | Project exists |
| When | I PUT to `/api/v1/projects/test-github` with `{"repo_url": "https://github.com/new-owner/new-repo"}` | Request sent |
| Then | The API returns HTTP 200 and the project's `repo_url` is updated | Field updated |

**Assertions:**
- [ ] HTTP response status is 200
- [ ] Response body contains `"repo_url": "https://github.com/new-owner/new-repo"`
- [ ] Other fields remain unchanged

---

### TC0327: PUT /projects/{slug} updates access_token

**Type:** Integration | **Priority:** P1 | **Story:** US0031 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | An existing GitHub project with slug `"test-github"` and an existing access token | Project exists |
| When | I PUT to `/api/v1/projects/test-github` with `{"access_token": "ghp_newtoken9876"}` | Request sent |
| Then | The API returns HTTP 200 and the response shows the new masked token `"****9876"` | Token updated |

**Assertions:**
- [ ] HTTP response status is 200
- [ ] Response body contains `"access_token": "****9876"`
- [ ] The new token is persisted (verified by subsequent GET returning the same masked value)

---

### TC0328: ProjectCreate validation rejects github without repo_url

**Type:** Unit | **Priority:** P0 | **Story:** US0031 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A `ProjectCreate` Pydantic model | Model available |
| When | I instantiate it with `source_type="github"` and no `repo_url` | Validation runs |
| Then | A `ValidationError` is raised with a message about `repo_url` being required | Validation fails |

**Assertions:**
- [ ] `pydantic.ValidationError` is raised
- [ ] Error details reference `repo_url`
- [ ] Error message mentions GitHub source type

---

### TC0329: ProjectCreate validation rejects local without sdlc_path

**Type:** Unit | **Priority:** P0 | **Story:** US0031 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A `ProjectCreate` Pydantic model | Model available |
| When | I instantiate it with `source_type="local"` and no `sdlc_path` | Validation runs |
| Then | A `ValidationError` is raised with a message about `sdlc_path` being required | Validation fails |

**Assertions:**
- [ ] `pydantic.ValidationError` is raised
- [ ] Error details reference `sdlc_path`
- [ ] Error message mentions local source type

---

### TC0330: ProjectResponse includes source_type and repo fields

**Type:** Unit | **Priority:** P0 | **Story:** US0031 AC1, AC7

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A `ProjectResponse` Pydantic model | Model available |
| When | I serialise a GitHub project to the response schema | Model serialised |
| Then | The JSON output includes `source_type`, `repo_url`, `repo_branch`, `repo_path`, and `access_token` (masked) | All fields present |

**Assertions:**
- [ ] `source_type` field is present with value `"github"`
- [ ] `repo_url` field is present with the repository URL
- [ ] `repo_branch` field is present with the branch name
- [ ] `repo_path` field is present with the subdirectory path
- [ ] `access_token` field is present and masked

---

## Test Data Requirements

| Data Item | Description | Used By |
|-----------|-------------|---------|
| Local project payload | `{"name": "Local", "source_type": "local", "sdlc_path": "/data/test"}` | TC0317, TC0320, TC0321, TC0329 |
| GitHub project payload | `{"name": "GitHub", "source_type": "github", "repo_url": "https://github.com/owner/repo"}` | TC0318, TC0319, TC0328 |
| GitHub project with token | Project with `access_token="ghp_abcdef1234567890"` | TC0322, TC0323, TC0324, TC0326, TC0327 |
| Null token project | GitHub project with `access_token=None` | TC0325 |

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0317 | POST /projects with source_type=local requires sdlc_path | Pending | - |
| TC0318 | POST /projects with source_type=github requires repo_url | Pending | - |
| TC0319 | POST /projects with source_type=github does not require sdlc_path | Pending | - |
| TC0320 | POST /projects with source_type=local ignores repo fields | Pending | - |
| TC0321 | POST /projects defaults source_type to "local" when omitted | Pending | - |
| TC0322 | GET /projects returns masked access_token | Pending | - |
| TC0323 | GET /projects/{slug} returns masked access_token | Pending | - |
| TC0324 | Token masking shows "****" + last 4 chars | Pending | - |
| TC0325 | Token masking returns null for null token | Pending | - |
| TC0326 | PUT /projects/{slug} updates repo_url | Pending | - |
| TC0327 | PUT /projects/{slug} updates access_token | Pending | - |
| TC0328 | ProjectCreate validation rejects github without repo_url | Pending | - |
| TC0329 | ProjectCreate validation rejects local without sdlc_path | Pending | - |
| TC0330 | ProjectResponse includes source_type and repo fields | Pending | - |

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
