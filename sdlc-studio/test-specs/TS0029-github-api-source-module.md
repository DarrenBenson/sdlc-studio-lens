# TS0029: GitHub API Source Module

> **Status:** Done
> **Story:** [US0029: GitHub API Source Module](../stories/US0029-github-api-source-module.md)
> **Epic:** [EP0007: Git Repository Sync](../epics/EP0007-git-repository-sync.md)
> **Owner:** Darren
> **Created:** 2026-02-18
> **Last Updated:** 2026-02-18

## Overview

Test specification for US0029 - GitHub API Source Module. Covers the `services/github_source.py` module that fetches SDLC Markdown files from GitHub repositories via the REST API. Tests verify URL parsing (owner/repo extraction with edge cases), file fetching with mocked httpx responses (public and private repos, path filtering, base64 decoding, SHA-256 hashing), and error handling for 404, 401, 403 rate limit, and network timeout scenarios. All GitHub API calls are mocked to avoid external dependencies.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0029](../stories/US0029-github-api-source-module.md) | GitHub API Source Module | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0029 | AC1 | Fetch from public repository | TC0298 | Pending |
| US0029 | AC2 | Fetch from private repository | TC0300 | Pending |
| US0029 | AC3 | URL parsing | TC0294, TC0295, TC0296, TC0297 | Pending |
| US0029 | AC4 | Path filtering | TC0299, TC0306 | Pending |
| US0029 | AC5 | Error handling - repo not found | TC0301 | Pending |
| US0029 | AC6 | Error handling - auth failure | TC0302 | Pending |
| US0029 | AC7 | Error handling - rate limit | TC0303 | Pending |

**Coverage:** 7/8 ACs covered (AC8 httpx dependency verified by import)

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | Yes | Pure functions (URL parsing) and mocked HTTP interactions |
| Integration | No | External API calls are mocked |
| E2E | No | End-to-end sync tested in TS0030 |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Python 3.12, pytest, pytest-asyncio, httpx |
| External Services | None (GitHub API mocked) |
| Test Data | Mocked JSON responses for Git Trees and Blobs API |

---

## Test Cases

| ID | Description | Type | Priority |
|----|-------------|------|----------|
| TC0294 | parse_github_url extracts owner/repo from HTTPS URL | Unit | P0 |
| TC0295 | parse_github_url handles trailing slash | Unit | P1 |
| TC0296 | parse_github_url handles .git suffix | Unit | P1 |
| TC0297 | parse_github_url rejects invalid URLs | Unit | P0 |
| TC0298 | fetch_github_files returns dict for public repo (mock) | Unit | P0 |
| TC0299 | fetch_github_files filters by repo_path (mock) | Unit | P0 |
| TC0300 | fetch_github_files includes Authorization header for private repo (mock) | Unit | P0 |
| TC0301 | fetch_github_files handles 404 (repo not found) (mock) | Unit | P0 |
| TC0302 | fetch_github_files handles 401 (auth failure) (mock) | Unit | P0 |
| TC0303 | fetch_github_files handles rate limit 403 (mock) | Unit | P1 |
| TC0304 | fetch_github_files decodes base64 blob content correctly (mock) | Unit | P0 |
| TC0305 | fetch_github_files computes SHA-256 matching local hash (mock) | Unit | P0 |
| TC0306 | fetch_github_files skips non-.md files in tree (mock) | Unit | P1 |
| TC0307 | fetch_github_files handles network timeout (mock) | Unit | P1 |

---

### TC0294: parse_github_url extracts owner/repo from HTTPS URL

**Type:** Unit | **Priority:** P0 | **Story:** US0029 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A standard GitHub HTTPS URL `https://github.com/DarrenBenson/sdlc-studio-lens` | Valid URL |
| When | I call `parse_github_url()` with this URL | Function executes |
| Then | It returns `("DarrenBenson", "sdlc-studio-lens")` | Correct extraction |

**Assertions:**
- [ ] Return value is a tuple of two strings
- [ ] First element (owner) equals `"DarrenBenson"`
- [ ] Second element (repo) equals `"sdlc-studio-lens"`

---

### TC0295: parse_github_url handles trailing slash

**Type:** Unit | **Priority:** P1 | **Story:** US0029 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A GitHub URL with trailing slash `https://github.com/owner/repo/` | URL with slash |
| When | I call `parse_github_url()` with this URL | Function executes |
| Then | It returns `("owner", "repo")` without the trailing slash affecting extraction | Correct extraction |

**Assertions:**
- [ ] Return value is `("owner", "repo")`
- [ ] No empty string in the tuple

---

### TC0296: parse_github_url handles .git suffix

**Type:** Unit | **Priority:** P1 | **Story:** US0029 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A GitHub URL with `.git` suffix `https://github.com/owner/repo.git` | URL with .git |
| When | I call `parse_github_url()` with this URL | Function executes |
| Then | It returns `("owner", "repo")` with the `.git` suffix stripped | Suffix removed |

**Assertions:**
- [ ] Second element (repo) equals `"repo"` not `"repo.git"`
- [ ] First element (owner) equals `"owner"`

---

### TC0297: parse_github_url rejects invalid URLs

**Type:** Unit | **Priority:** P0 | **Story:** US0029 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | An invalid URL such as `https://gitlab.com/owner/repo` or `not-a-url` or `https://github.com/` | Invalid input |
| When | I call `parse_github_url()` with the invalid URL | Function executes |
| Then | It raises a `ValueError` with a descriptive message | Error raised |

**Assertions:**
- [ ] `ValueError` is raised for non-GitHub hosts
- [ ] `ValueError` is raised for URLs missing owner or repo segments
- [ ] `ValueError` is raised for completely invalid URL strings
- [ ] Error message indicates why the URL is invalid

---

### TC0298: fetch_github_files returns dict for public repo (mock httpx)

**Type:** Unit | **Priority:** P0 | **Story:** US0029 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A mocked httpx response for the Git Trees API returning two `.md` files and a mocked Blobs API returning base64-encoded content | Mocked responses |
| When | I call `collect_github_files()` with a public repo URL and no access token | Function executes |
| Then | It returns a dict mapping relative file paths to `(sha256_hex, content_bytes)` tuples | Correct dict |

**Assertions:**
- [ ] Return type is `dict[str, tuple[str, bytes]]`
- [ ] Dict contains entries for each `.md` file in the mocked tree
- [ ] Each value is a tuple of `(str, bytes)` where the string is a hex SHA-256 hash
- [ ] No Authorization header sent in the mocked request

---

### TC0299: fetch_github_files filters by repo_path (mock)

**Type:** Unit | **Priority:** P0 | **Story:** US0029 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A mocked tree response containing files in `sdlc-studio/stories/US001.md`, `sdlc-studio/epics/EP001.md`, `README.md`, and `docs/guide.md` | Mixed paths |
| When | I call `collect_github_files()` with `repo_path="sdlc-studio"` | Function executes |
| Then | Only files under `sdlc-studio/` are returned, with paths relative to `sdlc-studio/` | Filtered correctly |

**Assertions:**
- [ ] Dict contains `"stories/US001.md"` and `"epics/EP001.md"`
- [ ] Dict does not contain `"README.md"` or `"docs/guide.md"`
- [ ] Paths are relative to `repo_path`, not the repository root

---

### TC0300: fetch_github_files includes Authorization header for private repo (mock)

**Type:** Unit | **Priority:** P0 | **Story:** US0029 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A mocked httpx client that records request headers | Header capture |
| When | I call `collect_github_files()` with `access_token="ghp_test1234abcd"` | Function executes |
| Then | The request includes `Authorization: Bearer ghp_test1234abcd` header | Token sent |

**Assertions:**
- [ ] Authorization header is present in the Trees API request
- [ ] Header value equals `"Bearer ghp_test1234abcd"`
- [ ] Authorization header is also present in Blob API requests

---

### TC0301: fetch_github_files handles 404 (repo not found) (mock)

**Type:** Unit | **Priority:** P0 | **Story:** US0029 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A mocked httpx response returning HTTP 404 for the Trees API call | 404 response |
| When | I call `collect_github_files()` with a non-existent repo URL | Function executes |
| Then | A `GitHubRepoNotFoundError` is raised with a descriptive message | Error raised |

**Assertions:**
- [ ] `GitHubRepoNotFoundError` is raised (not a generic exception)
- [ ] Error message contains the repository URL or owner/repo

---

### TC0302: fetch_github_files handles 401 (auth failure) (mock)

**Type:** Unit | **Priority:** P0 | **Story:** US0029 AC6

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A mocked httpx response returning HTTP 401 for the Trees API call | 401 response |
| When | I call `collect_github_files()` with an invalid access token | Function executes |
| Then | A `GitHubAuthError` is raised with a descriptive message | Error raised |

**Assertions:**
- [ ] `GitHubAuthError` is raised (not a generic exception)
- [ ] Error message indicates authentication failure

---

### TC0303: fetch_github_files handles rate limit 403 (mock)

**Type:** Unit | **Priority:** P1 | **Story:** US0029 AC7

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A mocked httpx response returning HTTP 403 with `X-RateLimit-Remaining: 0` header | Rate limited |
| When | I call `collect_github_files()` | Function executes |
| Then | A `GitHubRateLimitError` is raised with a descriptive message | Error raised |

**Assertions:**
- [ ] `GitHubRateLimitError` is raised (not a generic `GitHubAuthError`)
- [ ] Error message mentions rate limiting
- [ ] If `X-RateLimit-Reset` header is present, reset time is included in the message

---

### TC0304: fetch_github_files decodes base64 blob content correctly (mock)

**Type:** Unit | **Priority:** P0 | **Story:** US0029 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A mocked Blob API response with known base64-encoded content (e.g., `"IyBIZWxsbw=="` which decodes to `"# Hello"`) | Known content |
| When | I call `collect_github_files()` and retrieve the file content | Function executes |
| Then | The content bytes in the returned dict match the decoded value | Correct decoding |

**Assertions:**
- [ ] Content bytes equal `b"# Hello"` for the encoded input
- [ ] Decoding handles multi-line base64 content (GitHub uses line-wrapped base64)

---

### TC0305: fetch_github_files computes SHA-256 matching local hash (mock)

**Type:** Unit | **Priority:** P0 | **Story:** US0029 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A mocked blob with known content `b"# Test Document\n"` | Known content |
| When | I call `collect_github_files()` and retrieve the hash for that file | Function executes |
| Then | The SHA-256 hex string matches `hashlib.sha256(b"# Test Document\n").hexdigest()` | Hash matches |

**Assertions:**
- [ ] Hash in the returned tuple matches independently computed SHA-256
- [ ] Hash is a 64-character lowercase hex string

---

### TC0306: fetch_github_files skips non-.md files in tree (mock)

**Type:** Unit | **Priority:** P1 | **Story:** US0029 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A mocked tree response containing `README.md`, `script.py`, `image.png`, and `docs/guide.md` all within the `repo_path` | Mixed file types |
| When | I call `collect_github_files()` | Function executes |
| Then | Only `.md` files are fetched and returned; `.py` and `.png` files are excluded | Filtered by extension |

**Assertions:**
- [ ] Dict contains only keys ending in `.md`
- [ ] No Blob API request made for non-`.md` files
- [ ] `script.py` and `image.png` are not in the returned dict

---

### TC0307: fetch_github_files handles network timeout (mock)

**Type:** Unit | **Priority:** P1 | **Story:** US0029 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A mocked httpx client that raises `httpx.TimeoutException` on the Trees API call | Timeout simulated |
| When | I call `collect_github_files()` | Function executes |
| Then | A `GitHubSourceError` is raised with a message indicating a network timeout | Error raised |

**Assertions:**
- [ ] `GitHubSourceError` (or a subclass) is raised
- [ ] Error message mentions timeout or network connectivity
- [ ] The original `httpx.TimeoutException` is chained or referenced

---

## Test Data Requirements

| Data Item | Description | Used By |
|-----------|-------------|---------|
| Tree API response (public) | JSON with `tree` array containing `.md` and non-`.md` blob entries | TC0298, TC0299, TC0306 |
| Blob API response | JSON with `content` (base64) and `encoding` fields | TC0298, TC0304, TC0305 |
| Tree API 404 response | HTTP 404 with GitHub error JSON | TC0301 |
| Tree API 401 response | HTTP 401 with GitHub error JSON | TC0302 |
| Tree API 403 response | HTTP 403 with rate limit headers | TC0303 |

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0294 | parse_github_url extracts owner/repo from HTTPS URL | Pending | - |
| TC0295 | parse_github_url handles trailing slash | Pending | - |
| TC0296 | parse_github_url handles .git suffix | Pending | - |
| TC0297 | parse_github_url rejects invalid URLs | Pending | - |
| TC0298 | fetch_github_files returns dict for public repo | Pending | - |
| TC0299 | fetch_github_files filters by repo_path | Pending | - |
| TC0300 | fetch_github_files includes Authorization header for private repo | Pending | - |
| TC0301 | fetch_github_files handles 404 (repo not found) | Pending | - |
| TC0302 | fetch_github_files handles 401 (auth failure) | Pending | - |
| TC0303 | fetch_github_files handles rate limit 403 | Pending | - |
| TC0304 | fetch_github_files decodes base64 blob content correctly | Pending | - |
| TC0305 | fetch_github_files computes SHA-256 matching local hash | Pending | - |
| TC0306 | fetch_github_files skips non-.md files in tree | Pending | - |
| TC0307 | fetch_github_files handles network timeout | Pending | - |

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
