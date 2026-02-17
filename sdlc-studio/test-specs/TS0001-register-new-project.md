# TS0001: Register a New Project

> **Status:** Draft
> **Epic:** [EP0001: Project Management](../epics/EP0001-project-management.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0001 - Register a New Project. Covers the POST /api/v1/projects endpoint including successful registration, slug generation, path validation, duplicate detection, and Pydantic validation. Tests span unit (slug generation) and integration (API endpoint) levels.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0001](../stories/US0001-register-new-project.md) | Register a New Project | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0001 | AC1 | Successful project registration | TC0001, TC0002 | Covered |
| US0001 | AC2 | Auto-generated slug from name | TC0003, TC0004, TC0005, TC0006 | Covered |
| US0001 | AC3 | Path validation rejects non-existent directory | TC0007, TC0008 | Covered |
| US0001 | AC4 | Duplicate slug rejection | TC0009, TC0010 | Covered |
| US0001 | AC5 | Pydantic validation on request body | TC0011, TC0012, TC0013 | Covered |

**Coverage:** 5/5 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | Yes | Slug generation is a pure function with many edge cases |
| Integration | Yes | API endpoint requires database and HTTP layer validation |
| E2E | No | No frontend in this story; API-only |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Python 3.12+, pytest, pytest-asyncio, httpx |
| External Services | None (SQLite in-memory for tests) |
| Test Data | Filesystem tmp_path for path validation tests |

---

## Test Cases

### TC0001: Register project with valid name and path

**Type:** Integration | **Priority:** Critical | **Story:** US0001 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A valid project name "HomelabCmd" and an existing directory path | Directory exists at tmp_path/sdlc-studio |
| When | POST /api/v1/projects with {"name": "HomelabCmd", "sdlc_path": "<tmp_path>/sdlc-studio"} | Request accepted |
| Then | Response is 201 with JSON body | Body contains slug, name, sdlc_path, sync_status, last_synced_at, document_count, created_at |

**Assertions:**
- [ ] Status code is 201
- [ ] Response body "slug" equals "homelabcmd"
- [ ] Response body "name" equals "HomelabCmd"
- [ ] Response body "sdlc_path" matches the provided path
- [ ] Response body "sync_status" equals "never_synced"
- [ ] Response body "last_synced_at" is null
- [ ] Response body "document_count" equals 0
- [ ] Response body "created_at" is a valid ISO 8601 timestamp

---

### TC0002: Response body field types are correct

**Type:** Integration | **Priority:** High | **Story:** US0001 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A successful registration | TC0001 passes |
| When | Inspecting the response body | All fields present |
| Then | Each field has the correct type | Types match schema |

**Assertions:**
- [ ] "slug" is a non-empty string
- [ ] "name" is a non-empty string
- [ ] "sdlc_path" is a non-empty string
- [ ] "sync_status" is a string (one of: never_synced, syncing, synced, error)
- [ ] "last_synced_at" is null or ISO 8601 string
- [ ] "document_count" is an integer >= 0
- [ ] "created_at" is an ISO 8601 string

---

### TC0003: Slug from name with spaces

**Type:** Unit | **Priority:** High | **Story:** US0001 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Name "My Cool Project" | Input string |
| When | generate_slug("My Cool Project") | Slug generated |
| Then | Result is "my-cool-project" | Lowercase with hyphens |

**Assertions:**
- [ ] generate_slug("My Cool Project") returns "my-cool-project"

---

### TC0004: Slug from name with special characters

**Type:** Unit | **Priority:** High | **Story:** US0001 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Names with various special characters | Multiple inputs |
| When | generate_slug() is called for each | Slugs generated |
| Then | Special characters removed, hyphens used | Clean slugs |

**Assertions:**
- [ ] generate_slug("Hello World!") returns "hello-world"
- [ ] generate_slug("test__project") returns "test-project"
- [ ] generate_slug("--leading-trailing--") returns "leading-trailing"
- [ ] generate_slug("Multiple   Spaces") returns "multiple-spaces"

---

### TC0005: Slug from name with unicode characters

**Type:** Unit | **Priority:** Medium | **Story:** US0001 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Name "Projet Numero Un" with accented characters | Unicode input |
| When | generate_slug() is called | Non-ASCII stripped |
| Then | Result contains only [a-z0-9-] | ASCII-only slug |

**Assertions:**
- [ ] generate_slug("Projet Numero Un") returns "projet-numero-un" (accents stripped)
- [ ] Result matches regex ^[a-z0-9-]+$

---

### TC0006: Slug from name producing empty result

**Type:** Unit | **Priority:** High | **Story:** US0001 AC2 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Name "!!!" (only special characters) | Pathological input |
| When | generate_slug("!!!") | Empty after sanitisation |
| Then | Returns empty string or raises ValueError | Caller handles empty slug |

**Assertions:**
- [ ] generate_slug("!!!") returns "" (empty string)

---

### TC0007: Path validation rejects non-existent directory

**Type:** Integration | **Priority:** Critical | **Story:** US0001 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Path "/data/projects/nonexistent/sdlc-studio" does not exist | No such directory |
| When | POST /api/v1/projects with that path | Request processed |
| Then | Response is 400 with error code PATH_NOT_FOUND | Error response |

**Assertions:**
- [ ] Status code is 400
- [ ] Response body has "error.code" equal to "PATH_NOT_FOUND"
- [ ] Response body has "error.message" containing "does not exist"

---

### TC0008: Path validation rejects file (not directory)

**Type:** Integration | **Priority:** High | **Story:** US0001 AC3 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Path points to a file, not a directory | File exists at path |
| When | POST /api/v1/projects with that path | Request processed |
| Then | Response is 400 with error code PATH_NOT_FOUND | Rejects non-directory |

**Assertions:**
- [ ] Status code is 400
- [ ] Response body has "error.code" equal to "PATH_NOT_FOUND"
- [ ] Response body has "error.message" indicating path is not a directory

---

### TC0009: Duplicate slug rejection

**Type:** Integration | **Priority:** Critical | **Story:** US0001 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A project "HomelabCmd" already exists with slug "homelabcmd" | First registration succeeds |
| When | POST /api/v1/projects with name "HomelabCmd" again | Second registration attempted |
| Then | Response is 409 with error code CONFLICT | Duplicate prevented |

**Assertions:**
- [ ] First request returns 201
- [ ] Second request returns 409
- [ ] Response body has "error.code" equal to "CONFLICT"
- [ ] Response body has "error.message" containing "slug already exists"

---

### TC0010: Duplicate slug from different name (same slug output)

**Type:** Integration | **Priority:** Medium | **Story:** US0001 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Project "Hello World" exists (slug: "hello-world") | First registration |
| When | POST with name "Hello_World" (also produces "hello-world") | Same slug generated |
| Then | Response is 409 CONFLICT | Slug collision detected |

**Assertions:**
- [ ] Second request returns 409
- [ ] Error code is "CONFLICT"

---

### TC0011: Missing name field returns 422

**Type:** Integration | **Priority:** Critical | **Story:** US0001 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Request body {"sdlc_path": "/some/path"} (missing name) | Incomplete request |
| When | POST /api/v1/projects | Pydantic validation |
| Then | Response is 422 with validation error details | Field required |

**Assertions:**
- [ ] Status code is 422
- [ ] Response body contains detail about missing "name" field

---

### TC0012: Missing sdlc_path field returns 422

**Type:** Integration | **Priority:** High | **Story:** US0001 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Request body {"name": "Test"} (missing sdlc_path) | Incomplete request |
| When | POST /api/v1/projects | Pydantic validation |
| Then | Response is 422 with validation error details | Field required |

**Assertions:**
- [ ] Status code is 422
- [ ] Response body contains detail about missing "sdlc_path" field

---

### TC0013: Empty name string returns 422

**Type:** Integration | **Priority:** High | **Story:** US0001 AC5 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Request body {"name": "", "sdlc_path": "/some/path"} | Empty name |
| When | POST /api/v1/projects | Pydantic validation |
| Then | Response is 422 with validation error | min_length violated |

**Assertions:**
- [ ] Status code is 422
- [ ] Response body indicates name cannot be empty

---

### TC0014: Very long name returns 422

**Type:** Integration | **Priority:** Medium | **Story:** US0001 AC5 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Name with 201 characters | Exceeds max_length=200 |
| When | POST /api/v1/projects | Pydantic validation |
| Then | Response is 422 | max_length violated |

**Assertions:**
- [ ] Status code is 422

---

### TC0015: Path with trailing slash accepted

**Type:** Integration | **Priority:** Low | **Story:** US0001 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Valid path with trailing slash "/data/sdlc-studio/" | Path exists |
| When | POST /api/v1/projects | Path normalised |
| Then | Response is 201 | Registration succeeds |

**Assertions:**
- [ ] Status code is 201

---

### TC0016: sync_status defaults to never_synced

**Type:** Integration | **Priority:** High | **Story:** US0001 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A successful registration | TC0001 passes |
| When | Checking sync_status | Field value |
| Then | sync_status is "never_synced" | Default applied |

**Assertions:**
- [ ] Response body "sync_status" equals "never_synced"

---

### TC0017: document_count defaults to 0

**Type:** Integration | **Priority:** Medium | **Story:** US0001 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A newly registered project | No sync has run |
| When | Checking document_count | Field value |
| Then | document_count is 0 | No documents yet |

**Assertions:**
- [ ] Response body "document_count" equals 0

---

### TC0018: Name-only special characters returns 422 (empty slug)

**Type:** Integration | **Priority:** Medium | **Story:** US0001 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Name "!!!" with only special characters | Slug would be empty |
| When | POST /api/v1/projects | Validation fails |
| Then | Response is 422 VALIDATION_ERROR | Empty slug detected |

**Assertions:**
- [ ] Status code is 422
- [ ] Error indicates slug would be empty after sanitisation

---

## Fixtures

```yaml
valid_project:
  name: "HomelabCmd"
  sdlc_path: "<tmp_path>/sdlc-studio"

project_with_spaces:
  name: "My Cool Project"
  sdlc_path: "<tmp_path>/sdlc-studio"

duplicate_name:
  name: "HomelabCmd"
  sdlc_path: "<tmp_path>/sdlc-studio-2"

missing_name:
  sdlc_path: "/some/path"

missing_path:
  name: "TestProject"

empty_name:
  name: ""
  sdlc_path: "/some/path"

long_name:
  name: "<201 character string>"
  sdlc_path: "<tmp_path>/sdlc-studio"

special_chars_name:
  name: "!!!"
  sdlc_path: "<tmp_path>/sdlc-studio"
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0001 | Register project with valid name and path | Pending | - |
| TC0002 | Response body field types are correct | Pending | - |
| TC0003 | Slug from name with spaces | Pending | - |
| TC0004 | Slug from name with special characters | Pending | - |
| TC0005 | Slug from name with unicode characters | Pending | - |
| TC0006 | Slug from name producing empty result | Pending | - |
| TC0007 | Path validation rejects non-existent directory | Pending | - |
| TC0008 | Path validation rejects file (not directory) | Pending | - |
| TC0009 | Duplicate slug rejection | Pending | - |
| TC0010 | Duplicate slug from different name | Pending | - |
| TC0011 | Missing name field returns 422 | Pending | - |
| TC0012 | Missing sdlc_path field returns 422 | Pending | - |
| TC0013 | Empty name string returns 422 | Pending | - |
| TC0014 | Very long name returns 422 | Pending | - |
| TC0015 | Path with trailing slash accepted | Pending | - |
| TC0016 | sync_status defaults to never_synced | Pending | - |
| TC0017 | document_count defaults to 0 | Pending | - |
| TC0018 | Name-only special characters returns 422 | Pending | - |

---

## Traceability

| Artefact | Reference |
|----------|-----------|
| PRD | [sdlc-studio/prd.md](../prd.md) |
| Epic | [EP0001](../epics/EP0001-project-management.md) |
| TSD | [sdlc-studio/tsd.md](../tsd.md) |

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec from US0001 story plan |
