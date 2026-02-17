# Test Strategy Document

> **Project:** SDLC Studio Lens
> **Version:** 1.0.0
> **Last Updated:** 2026-02-17
> **Owner:** Darren

---

## Overview

This test strategy defines the approach for validating SDLC Studio Lens, a read-only web dashboard for browsing and searching sdlc-studio documents. The architecture consists of a FastAPI backend with SQLite/FTS5 storage and a React SPA frontend served via nginx.

Given the project's two main concerns - document parsing/sync and web dashboard presentation - the strategy emphasises thorough unit testing of the parser and sync services, API integration tests with a real SQLite database, and E2E tests for critical user flows.

The testing approach follows the **test pyramid** principle: many fast unit tests, fewer integration tests, and selective E2E tests for critical paths.

## Test Objectives

- Ensure the blockquote frontmatter parser correctly extracts metadata from all sdlc-studio document types
- Validate filesystem sync correctly detects new, changed, and deleted documents
- Verify API endpoints return correct data with proper filtering, pagination, and error handling
- Confirm FTS5 search returns relevant results with correct ranking
- Validate statistics calculations match actual document data
- Ensure the frontend renders documents, charts, and navigation correctly
- Verify Docker deployment serves both frontend and API correctly

## Scope

### In Scope
- FastAPI backend (API routes, sync service, parser, database operations)
- SQLAlchemy models and Alembic migrations
- Blockquote frontmatter parser (all document types)
- Filesystem sync service (add, update, delete, skip behaviour)
- FTS5 search functionality
- Statistics aggregation
- React frontend (components, pages, API client)
- Docker build and deployment
- E2E user flows (register project, sync, browse, search)

### Out of Scope
- Performance/load testing (deferred; LAN tool with 1-3 users)
- Security penetration testing (no auth in v1.0)
- Mobile responsiveness testing (desktop-first)
- Cross-browser testing beyond Chrome and Firefox

---

## Test Levels

### Coverage Targets

| Level | Target | Rationale |
|-------|--------|-----------|
| Unit | 90% | Core parsing and sync logic must be thoroughly tested |
| Integration | 85% | API and database interactions need strong coverage |
| E2E | 100% feature coverage | Every user-visible feature exercised at least once |

> **Why 90%?** AI-assisted development produces code faster than traditional development. Higher coverage gates ensure AI-generated code is correct and catches hallucinations early.

### Unit Testing

| Attribute | Value |
|-----------|-------|
| Coverage Target | 90% line coverage |
| Framework | pytest + pytest-asyncio |
| Coverage Tool | coverage.py |
| Responsibility | Developer (write with code) |
| Execution | Pre-commit, CI on every push |

**Focus Areas:**

#### Parser Tests (`tests/test_parser.py`)
- Parse blockquote frontmatter from PRD documents
- Parse blockquote frontmatter from epic documents
- Parse blockquote frontmatter from story documents
- Parse blockquote frontmatter from bug documents
- Parse blockquote frontmatter from plan documents
- Parse blockquote frontmatter from test-spec documents
- Handle multi-line blockquote values
- Handle missing frontmatter gracefully (return empty metadata)
- Handle malformed blockquote lines (skip invalid, parse valid)
- Extract title from first `#` heading
- Extract document ID from filename pattern
- Infer document type from filename and directory structure

#### Sync Service Tests (`tests/test_sync.py`)
- Sync adds new documents found on filesystem
- Sync updates documents with changed file hash
- Sync skips documents with unchanged file hash
- Sync removes documents deleted from filesystem
- Sync updates project sync_status to 'syncing' then 'synced'
- Sync sets sync_status to 'error' on failure
- Sync updates last_synced_at timestamp
- Sync handles empty sdlc-studio directory
- Sync handles unreadable files (logs warning, continues)
- Sync populates FTS5 index for new documents
- Sync updates FTS5 index for changed documents
- Sync removes FTS5 entries for deleted documents

#### Statistics Tests
- Calculate document counts by type
- Calculate document counts by status
- Calculate completion percentage (Done / Total stories)
- Handle projects with zero documents
- Aggregate statistics across multiple projects

### Integration Testing

| Attribute | Value |
|-----------|-------|
| Scope | API routes with SQLite in-memory database |
| Framework | pytest + httpx TestClient + SQLite in-memory |
| Responsibility | Developer |
| Execution | CI on every PR |

**Focus Areas:**

#### Project API Tests (`tests/test_api_projects.py`)
- POST /projects - create project with valid data
- POST /projects - reject duplicate slug
- POST /projects - reject non-existent path
- GET /projects - list all projects
- GET /projects/{slug} - get project details
- GET /projects/{slug} - 404 for unknown slug
- PUT /projects/{slug} - update project name
- DELETE /projects/{slug} - remove project and associated documents
- POST /projects/{slug}/sync - trigger sync returns 202

#### Document API Tests (`tests/test_api_documents.py`)
- GET /projects/{slug}/documents - list all documents
- GET /projects/{slug}/documents?type=story - filter by type
- GET /projects/{slug}/documents?status=Done - filter by status
- GET /projects/{slug}/documents?type=epic&status=Done - combined filters
- GET /projects/{slug}/documents?sort=title&order=asc - sorting
- GET /projects/{slug}/documents?page=2&per_page=10 - pagination
- GET /projects/{slug}/documents/{type}/{doc_id} - get single document
- GET /projects/{slug}/documents/{type}/{doc_id} - 404 for unknown document

#### Statistics API Tests (`tests/test_api_stats.py`)
- GET /projects/{slug}/stats - returns correct counts
- GET /projects/{slug}/stats - completion percentage matches document data
- GET /stats - aggregated stats across projects
- GET /stats - handles projects with no documents

#### Search API Tests (`tests/test_api_search.py`)
- GET /search?q=term - returns matching documents
- GET /search?q=term&project=slug - filter by project
- GET /search?q=term&type=story - filter by type
- GET /search - 422 without query parameter
- GET /search?q=term - results include snippet with context
- GET /search?q=term - results ranked by relevance
- GET /search?q=nonexistent - returns empty results list

### API Contract Testing

> **Critical:** E2E tests with mocks don't catch backend bugs. Contract tests bridge this gap.

| Attribute | Value |
|-----------|-------|
| Scope | Backend responses match frontend TypeScript types |
| Framework | pytest + httpx TestClient |
| Responsibility | Developer |
| Execution | CI on every PR |

**Pattern:**
```python
# tests/test_api_contracts.py
class TestDocumentResponseContract:
    """Verify document responses contain all fields expected by frontend."""

    def test_document_list_includes_required_fields(
        self, client: TestClient, synced_project: str
    ) -> None:
        response = client.get(f"/api/v1/projects/{synced_project}/documents")
        item = response.json()["items"][0]

        # Every field the frontend Document type expects
        assert "doc_id" in item
        assert "type" in item
        assert "title" in item
        assert "status" in item
        assert "updated_at" in item
```

### End-to-End Testing

| Attribute | Value |
|-----------|-------|
| Scope | Critical user flows via browser |
| Framework | Playwright |
| Responsibility | Developer |
| Execution | Pre-release, nightly |

### E2E Feature Coverage Matrix

| Feature Area | Spec File | Test Count | Status |
|--------------|-----------|------------|--------|
| Dashboard overview | dashboard.spec.ts | ~5 | Not Started |
| Document browsing | documents.spec.ts | ~8 | Not Started |
| Document filtering | filtering.spec.ts | ~6 | Not Started |
| Document viewing | document-view.spec.ts | ~5 | Not Started |
| Project sync | sync.spec.ts | ~4 | Not Started |
| Search | search.spec.ts | ~6 | Not Started |
| Project management | settings.spec.ts | ~5 | Not Started |

**E2E Test Scenarios:**

#### Dashboard (`e2e/dashboard.spec.ts`)
- Dashboard shows project cards with stats
- Project card displays document count and completion percentage
- Project card shows last synced timestamp
- Clicking project card navigates to project detail
- Dashboard handles zero registered projects gracefully

#### Document Browsing (`e2e/documents.spec.ts`)
- Document list displays all documents for a project
- Document list shows type badge, status badge, and title
- Clicking type filter updates document list
- Clicking status filter updates document list
- Combined type and status filters work together
- Pagination controls navigate between pages
- Sort controls change document order
- Clicking a document navigates to document view

#### Document View (`e2e/document-view.spec.ts`)
- Document renders markdown content correctly
- Metadata sidebar shows frontmatter fields
- Status badge reflects document status
- Code blocks have syntax highlighting
- Tables render correctly

#### Project Sync (`e2e/sync.spec.ts`)
- Sync button triggers sync and shows progress
- Sync completion updates document list
- Sync failure shows error message
- Sync status shows last synced timestamp

#### Search (`e2e/search.spec.ts`)
- Search returns results matching query
- Search results show document title, type, and project
- Search results include matching snippet
- Clicking search result navigates to document view
- Search with no results shows empty state
- Search filters narrow results by project and type

### Frontend Unit Testing

| Attribute | Value |
|-----------|-------|
| Coverage Target | 70% line coverage |
| Framework | Vitest + React Testing Library |
| Coverage Tool | @vitest/coverage-v8 |
| Responsibility | Developer |
| Execution | Pre-commit, CI on every push |

**Focus Areas:**

#### Component Tests
- StatusBadge renders correct colour for each status
- StatsCard displays count and label
- ProgressRing renders percentage correctly
- DocumentCard displays title, type, status
- SearchBar triggers search on enter/submit
- Sidebar renders project list and active state

#### API Client Tests
- fetchProjects returns project list
- fetchDocuments handles query parameters
- fetchStats returns statistics
- search handles query and filters
- API client handles error responses

#### Page Tests
- Dashboard renders project cards
- DocumentList renders with filter controls
- DocumentView renders markdown content
- SearchResults renders result items
- Settings renders project form

---

## Test Environments

| Environment | Purpose | URL | Data |
|-------------|---------|-----|------|
| Local | Development testing | localhost:5173 (frontend), localhost:8000 (API) | Fixtures |
| Docker | Integration testing | localhost:80 | Sample project volumes |
| CI | Automated testing | N/A | SQLite in-memory + fixtures |

## Test Data Strategy

### Approach

**Fixtures-based:** Test fixtures provide sample sdlc-studio documents covering all document types and edge cases.

**Fixture Set:**
- Sample project directory with representative documents:
  - `prd.md` - PRD with full frontmatter
  - `trd.md` - TRD with full frontmatter
  - `tsd.md` - TSD with full frontmatter
  - `epics/EP0001.md` - Epic with status Done
  - `epics/EP0002.md` - Epic with status In Progress
  - `stories/US0001.md` - Story with all frontmatter fields
  - `stories/US0002.md` - Story with minimal frontmatter
  - `bugs/BG0001.md` - Bug report
  - `plans/PL0001.md` - Implementation plan
  - `test-specs/TS0001.md` - Test specification
  - `malformed.md` - Document with invalid frontmatter (edge case)

### Sensitive Data
No sensitive data in test fixtures. All document content is synthetic.

---

## Automation Strategy

### Automation Candidates
- Regression tests for parser across all document types
- Happy path scenarios for all API endpoints
- Sync service behaviour (add, update, delete, skip)
- Search relevance validation
- Frontend component rendering

### Manual Testing
- Exploratory testing of markdown rendering edge cases
- Visual verification of chart and progress ring appearance
- Usability assessment of document navigation

### Automation Framework Stack

| Layer | Tool | Language |
|-------|------|----------|
| E2E/UI | Playwright | TypeScript |
| API Integration | pytest + httpx | Python |
| Backend Unit | pytest + pytest-asyncio | Python |
| Frontend Unit | Vitest + React Testing Library | TypeScript |

---

## CI/CD Integration

### Pipeline Stages

1. **Pre-commit:** Ruff lint, Ruff format check, unit tests
2. **PR:** Unit + integration tests (backend and frontend)
3. **Merge to main:** Full E2E suite against Docker deployment
4. **Pre-release:** Full suite + Docker build verification

### Quality Gates

| Gate | Criteria | Blocking |
|------|----------|----------|
| Backend unit coverage | >= 90% | Yes |
| Frontend unit coverage | >= 70% | Yes |
| Integration tests | 100% pass | Yes |
| E2E critical path | 100% pass | Yes |
| E2E full suite | >= 95% pass | No (alerts) |
| Ruff lint | 0 errors | Yes |

---

## Defect Management

### Severity Definitions

| Severity | Definition | SLA |
|----------|------------|-----|
| Critical | Dashboard unusable, data corruption | Next session |
| High | Major feature broken (sync, search, browsing) | 2 days |
| Medium | Feature impaired, workaround exists | Backlog (prioritised) |
| Low | Minor issue, cosmetic | Backlog |

---

## Tools & Infrastructure

| Purpose | Tool |
|---------|------|
| Test Management | GitHub Issues |
| CI/CD | GitHub Actions |
| Browser Automation | Playwright |
| Backend Coverage | coverage.py |
| Frontend Coverage | @vitest/coverage-v8 |
| Linting | Ruff (Python), ESLint (TypeScript) |
| Formatting | Ruff (Python), Prettier (TypeScript) |

---

## Test Organisation

### Backend

```text
backend/tests/
├── conftest.py                # Shared fixtures (test client, DB, sample docs)
├── test_parser.py             # Parser unit tests (~15 tests)
├── test_sync.py               # Sync service tests (~12 tests)
├── test_api_projects.py       # Project endpoint tests (~9 tests)
├── test_api_documents.py      # Document endpoint tests (~8 tests)
├── test_api_stats.py          # Statistics endpoint tests (~4 tests)
├── test_api_search.py         # Search endpoint tests (~7 tests)
├── test_api_contracts.py      # Contract tests (~10 tests)
└── fixtures/
    └── sample-project/        # Sample sdlc-studio directory
        ├── prd.md
        ├── trd.md
        ├── tsd.md
        ├── epics/
        │   ├── EP0001.md
        │   └── EP0002.md
        ├── stories/
        │   ├── US0001.md
        │   └── US0002.md
        ├── bugs/
        │   └── BG0001.md
        ├── plans/
        │   └── PL0001.md
        └── test-specs/
            └── TS0001.md
```

### Frontend

```text
frontend/src/
├── components/
│   ├── StatusBadge.test.tsx
│   ├── StatsCard.test.tsx
│   ├── ProgressRing.test.tsx
│   ├── DocumentCard.test.tsx
│   ├── SearchBar.test.tsx
│   └── Sidebar.test.tsx
├── pages/
│   ├── Dashboard.test.tsx
│   ├── DocumentList.test.tsx
│   ├── DocumentView.test.tsx
│   ├── SearchResults.test.tsx
│   └── Settings.test.tsx
└── api/
    └── client.test.ts
```

### E2E

```text
e2e/
├── dashboard.spec.ts
├── documents.spec.ts
├── filtering.spec.ts
├── document-view.spec.ts
├── sync.spec.ts
├── search.spec.ts
└── settings.spec.ts
```

### Naming Conventions

| Convention | Pattern | Example |
|------------|---------|---------|
| Backend test file | `test_{module}.py` | `test_parser.py` |
| Backend test class | `Test{Feature}` | `TestBlockquoteParser` |
| Backend test method | `test_{behaviour}` | `test_parses_status_from_frontmatter` |
| Frontend test file | `{Component}.test.tsx` | `StatusBadge.test.tsx` |
| Frontend test | `it('should {behaviour}')` | `it('should render done status in green')` |
| E2E spec file | `{feature}.spec.ts` | `search.spec.ts` |
| E2E test | `test('{user action}')` | `test('search returns matching documents')` |

---

## Anti-Patterns and Pitfalls

| Anti-Pattern | Why It's Bad | Do This Instead |
|--------------|--------------|-----------------|
| Mocking SQLAlchemy in unit tests | Misses real query behaviour | Use SQLite in-memory for integration tests |
| Testing parser with trivial inputs only | Misses edge cases in real documents | Use fixture files copied from actual sdlc-studio output |
| E2E tests with mocked API responses | Doesn't catch backend bugs | Add contract tests verifying backend responses match frontend types |
| Hardcoded file paths in sync tests | Tests break on different machines | Use tmp_path fixture for test directories |
| Testing only happy paths for sync | Misses deletion and error handling | Test all four sync behaviours: add, update, delete, skip |

---

## Related Specifications

- [Product Requirements Document](prd.md)
- [Technical Requirements Document](trd.md)

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Darren | Initial TSD created |
