# Product Requirements Document

**Project:** SDLC Studio Lens
**Version:** 1.0.2
**Last Updated:** 2026-02-17
**Status:** Draft
**TRD Reference:** [TRD](trd.md)

---

## 1. Project Overview

### Product Name
SDLC Studio Lens

### Purpose
A self-hosted, read-only web dashboard for browsing, searching, and visualising SDLC documents produced by sdlc-studio. Parses markdown artefacts (PRDs, TRDs, TSDs, epics, stories, bugs, plans, test specs) from registered project directories and presents them with statistics, status tracking, and cross-project search.

### Tech Stack
- **Backend:** Python 3.12+, FastAPI, Uvicorn, Pydantic v2
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS
- **Database:** SQLite with FTS5 for full-text search
- **Deployment:** Docker (two containers: backend API, frontend via nginx)

### Architecture Pattern
**Two-Container SPA + API**

- **Backend container:** FastAPI REST API serving parsed document data from SQLite
- **Frontend container:** React SPA built with Vite, served via nginx with API reverse proxy
- **Communication:** Frontend calls backend API via `/api/v1/*` proxied through nginx
- **Storage:** SQLite database with volume mount for persistence
- **Document source:** Project directories mounted as Docker volumes (read-only)

### Design System
All UI components follow the [Brand Guide](brand-guide.md):
- **Aesthetic:** Clean, data-dense dashboard - dark mode only, finance dashboard inspired
- **Colours:** Green-tinted dark backgrounds (#0B0F0D base, #111916 cards) with lime green accents (#A3E635 primary)
- **Typography:** Space Grotesk (headings), JetBrains Mono (data, code, metadata), Inter (body text)
- **Components:** Status badges, type badges, progress rings, stat cards, document cards, sidebar navigation
- **Full specification:** See [Brand Guide](brand-guide.md) for colour tokens, component CSS, Tailwind config, and chart theming

### Maturity Assessment
**Greenfield** - New application, no existing codebase.

---

## 2. Problem Statement

### Problem Being Solved
sdlc-studio generates structured markdown documents (PRDs, TRDs, TSDs, epics, stories, bugs, plans, test specs) for software projects, but there is no visual way to:

- **Browse documents:** Finding a specific epic or story requires navigating the filesystem or using `grep`
- **Track progress:** No consolidated view of story completion, epic status, or project health across documents
- **Search across projects:** No way to search for a term across all SDLC artefacts from multiple projects
- **Visualise statistics:** Document counts, status distributions, and completion percentages require manual counting
- **Share oversight:** No way for a team member or stakeholder to view project status without filesystem access

### Target Users

| Persona | Description |
|---------|-------------|
| **SDLC Developer (Primary)** | Developer using sdlc-studio to manage their SDLC artefacts, wants a visual overview without leaving the browser |

### Context
- **Document source:** sdlc-studio generates markdown files in `sdlc-studio/` directories within projects
- **Document types:** PRD, TRD, TSD, epics, stories, bugs, plans, test specs
- **Frontmatter format:** sdlc-studio uses blockquote-style metadata (`> **Key:** Value`)
- **Scale:** 1-10 projects, each with 10-200 documents
- **Deployment:** LAN-first tool, runs alongside development infrastructure
- **Workflow:** Documents edited via sdlc-studio CLI; Lens is strictly read-only

---

## 3. Goals and Success Metrics

### Primary Goals

| Goal | Description | Success Metric |
|------|-------------|----------------|
| **G1** | Unified document browsing | All registered project documents visible and navigable from dashboard |
| **G2** | Project health overview | Dashboard shows document counts, status breakdowns, and completion metrics per project |
| **G3** | Full-text search | Search returns results from any document across all registered projects in <1s |
| **G4** | Rendered document viewing | Markdown documents render with proper formatting, syntax highlighting, and frontmatter extraction |
| **G5** | Manual sync workflow | User can trigger sync per project, see sync status and last-synced timestamp |
| **G6** | Docker deployment | Single `docker-compose up` brings up both containers with project volumes |

### Key Performance Indicators (KPIs)

| KPI | Target | Measurement |
|-----|--------|-------------|
| Dashboard load time | < 2s | Browser performance (DOMContentLoaded) |
| Document list load | < 500ms | API response time for filtered document list |
| Search response time | < 1s | API response time for FTS5 query |
| Sync duration (100 docs) | < 10s | Time from sync trigger to completion |
| Docker build time | < 3 min | Total build for both containers |

---

## 4. User Personas

### Primary: SDLC Developer (Darren)

**Background:**
- Developer managing multiple projects with sdlc-studio
- Comfortable with CLI tools but wants visual oversight
- Runs development infrastructure on LAN with Docker

**Goals:**
- Quickly check project progress without reading individual files
- Find specific stories or epics across projects
- View rendered documents in a clean interface
- Understand which areas of a project are complete vs outstanding

**Pain Points:**
- Navigating filesystem to find specific SDLC documents is tedious
- No consolidated progress view across epics and stories
- Manual counting of document statuses is error-prone
- Sharing project status requires copying markdown snippets

**Behaviours:**
- Checks project status at the start of work sessions
- Searches for specific stories when planning next tasks
- Reviews document status after running sdlc-studio commands
- Prefers dark-themed developer tools

---

## 5. Feature Inventory

| Feature | Description | Status | Priority | Epic |
|---------|-------------|--------|----------|------|
| Project Registration | Register projects with name, slug, and sdlc-studio path | Not Started | P0 | EP0001 |
| Project List | View, edit, and remove registered projects | Not Started | P0 | EP0001 |
| Trigger Sync | Manually trigger filesystem sync per project | Not Started | P0 | EP0001 |
| Sync Status | Display sync progress, last-synced timestamp, error state | Not Started | P0 | EP0001 |
| Filesystem Sync | Walk sdlc-studio directory, detect new/changed/deleted files | Not Started | P0 | EP0002 |
| Markdown Parser | Parse blockquote-style frontmatter from sdlc-studio documents | Not Started | P0 | EP0002 |
| Change Detection | Compare file hashes to skip unchanged documents on re-sync | Not Started | P1 | EP0002 |
| Document List | List and filter documents by type, status, owner | Not Started | P0 | EP0003 |
| Document View | Render markdown document with extracted frontmatter sidebar | Not Started | P0 | EP0003 |
| Type Filtering | Filter document list by type (epic, story, bug, plan, etc.) | Not Started | P0 | EP0003 |
| Status Filtering | Filter document list by status (Draft, In Progress, Done, etc.) | Not Started | P1 | EP0003 |
| Multi-Project Dashboard | Overview cards showing stats for each registered project | Not Started | P0 | EP0004 |
| Project Statistics | Document counts by type, status breakdown, completion percentage | Not Started | P0 | EP0004 |
| Progress Visualisation | Progress rings and bar charts for epic/story completion | Not Started | P1 | EP0004 |
| Recent Activity | List of recently synced/changed documents | Not Started | P2 | EP0004 |
| Full-Text Search | Search across all document content using SQLite FTS5 | Not Started | P0 | EP0005 |
| Search Filters | Filter search results by project, document type, status | Not Started | P1 | EP0005 |
| Search Highlighting | Highlight matching terms in search results | Not Started | P2 | EP0005 |
| Backend Dockerfile | Multi-stage Python build (python:3.12-slim) | Not Started | P0 | EP0006 |
| Frontend Dockerfile | Multi-stage Node build (node:22-slim build, nginx:alpine serve) | Not Started | P0 | EP0006 |
| Docker Compose | Orchestration with volume mounts for projects and database | Not Started | P0 | EP0006 |
| Nginx Config | Reverse proxy to backend API, SPA routing | Not Started | P0 | EP0006 |

**Estimated Total:** 6 Epics, ~30 Stories

### Feature Details

#### Project Registration (FR1)

**User Story:** As a developer, I want to register a project by providing its name and sdlc-studio directory path so that its documents appear in the dashboard.

**Acceptance Criteria:**
- [ ] Register project with name, slug (auto-generated from name), and absolute filesystem path
- [ ] Validate that the path exists and contains an sdlc-studio directory
- [ ] Prevent duplicate slugs
- [ ] Store project in SQLite database

**Dependencies:** None
**Status:** Not Started
**Confidence:** [HIGH]

---

#### Filesystem Sync (FR2)

**User Story:** As a developer, I want to trigger a sync that reads all documents from a project's sdlc-studio directory so that the dashboard reflects the current state.

**Acceptance Criteria:**
- [ ] Walk the sdlc-studio directory recursively for `.md` files
- [ ] Parse each file to extract frontmatter metadata and content
- [ ] Compute SHA-256 hash per file; skip unchanged files on re-sync
- [ ] Detect deleted files (present in DB but missing from filesystem) and mark accordingly
- [ ] Update sync status (syncing, synced, error) and last_synced_at timestamp
- [ ] Index document content in FTS5 table for search

**Dependencies:** Project Registration
**Status:** Not Started
**Confidence:** [HIGH]

---

#### Markdown Parser (FR3)

**User Story:** As a developer, I want the system to extract structured metadata from sdlc-studio documents so that I can filter and search by status, owner, and type.

**Acceptance Criteria:**
- [ ] Parse blockquote-style frontmatter: `> **Key:** Value`
- [ ] Extract standard fields: title, status, owner, priority, epic, story points
- [ ] Handle multi-line blockquote values
- [ ] Preserve raw markdown content for rendering
- [ ] Store extracted metadata as JSON in documents table

**Dependencies:** None
**Status:** Not Started
**Confidence:** [HIGH]

---

#### Document Browsing (FR4)

**User Story:** As a developer, I want to browse documents by type and status so that I can find specific artefacts quickly.

**Acceptance Criteria:**
- [ ] List documents with columns: title, type, status, owner, last modified
- [ ] Filter by document type (epic, story, bug, plan, test-spec, prd, trd, tsd)
- [ ] Filter by status (Draft, In Progress, Done, Blocked, etc.)
- [ ] Sort by title, type, status, or last modified date
- [ ] Paginate results (50 per page default)

**Dependencies:** Filesystem Sync
**Status:** Not Started
**Confidence:** [HIGH]

---

#### Document View (FR5)

**User Story:** As a developer, I want to view a rendered document with its metadata displayed in a sidebar so that I can read it without opening a text editor.

**Acceptance Criteria:**
- [ ] Render markdown body with proper formatting and syntax highlighting
- [ ] Display extracted frontmatter in a structured sidebar panel
- [ ] Show document type badge and status badge
- [ ] Link to related documents (e.g., epic links to its stories)
- [ ] Display file path and last sync timestamp

**Dependencies:** Markdown Parser, Document Browsing
**Status:** Not Started
**Confidence:** [HIGH]

---

#### Dashboard Statistics (FR6)

**User Story:** As a developer, I want to see project health at a glance so that I know where each project stands.

**Acceptance Criteria:**
- [ ] Show per-project card with: document count, status breakdown, completion percentage
- [ ] Display progress ring for story completion (Done / Total)
- [ ] Show document type distribution (bar or donut chart)
- [ ] Display last synced timestamp per project
- [ ] Aggregate stats across all projects on main dashboard

**Dependencies:** Filesystem Sync
**Status:** Not Started
**Confidence:** [HIGH]

---

#### Full-Text Search (FR7)

**User Story:** As a developer, I want to search across all documents from all projects so that I can find relevant content regardless of where it lives.

**Acceptance Criteria:**
- [ ] Full-text search using SQLite FTS5 across document titles and content
- [ ] Filter results by project, document type, and status
- [ ] Display results with document title, type, project, and matching snippet
- [ ] Highlight search terms in snippets
- [ ] Return results in <1s for typical queries

**Dependencies:** Filesystem Sync
**Status:** Not Started
**Confidence:** [HIGH]

---

#### Docker Deployment (FR8)

**User Story:** As a developer, I want to deploy the dashboard with a single `docker-compose up` command so that setup requires no manual configuration beyond volume paths.

**Acceptance Criteria:**
- [ ] Multi-stage backend Dockerfile (python:3.12-slim) produces minimal image
- [ ] Multi-stage frontend Dockerfile (node:22-slim build, nginx:alpine serve) produces minimal image
- [ ] docker-compose.yml orchestrates both containers with shared network
- [ ] nginx proxies `/api/*` to backend container and serves SPA for all other routes
- [ ] Project directories configurable as bind-mount volumes
- [ ] Database persists via named volume
- [ ] Both containers start successfully with default configuration

**Dependencies:** All other features (deployment is final phase)
**Status:** Not Started
**Confidence:** [HIGH]

---

## 6. Functional Requirements

### Core Behaviours

| ID | Requirement | Priority |
|----|-------------|----------|
| FR1 | Project registration with path validation | P0 |
| FR2 | Manual filesystem sync with change detection | P0 |
| FR3 | Blockquote frontmatter parser | P0 |
| FR4 | Document list with type/status filtering | P0 |
| FR5 | Rendered markdown document viewer | P0 |
| FR6 | Multi-project dashboard with statistics | P0 |
| FR7 | Full-text search via FTS5 | P0 |
| FR8 | Docker deployment (two containers) | P0 |

### Input/Output Specifications

See [TRD §5: API Contracts](trd.md#5-api-contracts) for complete request/response schemas.

### Business Logic Rules

1. **Read-only documents:** The dashboard never writes to project sdlc-studio directories
2. **Manual sync only:** Sync triggers on user action, no filesystem watching or polling
3. **Change detection:** Files with unchanged SHA-256 hash are skipped during sync
4. **Deleted file handling:** Files present in DB but missing from filesystem are removed on sync
5. **Document type inference:** Determined from filename pattern (e.g., `EP0001.md` = epic, `US0001.md` = story, `prd.md` = prd)
6. **Slug generation:** Project slug derived from name (lowercase, hyphens, no special characters)

---

## 7. Non-Functional Requirements

### Performance

| Metric | Target |
|--------|--------|
| Dashboard load time | < 2s |
| API response (p50) | < 100ms |
| API response (p95) | < 500ms |
| Document list (100 results) | < 500ms |
| Search query | < 1s |
| Sync (100 documents) | < 10s |

### Security

| Control | Implementation |
|---------|----------------|
| Authentication | None (LAN-only tool, v1.0) |
| Authorisation | None (single-user) |
| Transport | HTTP (LAN only) |
| Input validation | Pydantic models on all API inputs |
| SQL injection | Parameterised queries (SQLAlchemy) |
| Path traversal | Validate project paths are within allowed directories |
| XSS | React auto-escaping, sanitised markdown rendering |

### Scalability

| Metric | Target |
|--------|--------|
| Registered projects | 1-10 |
| Documents per project | 10-200 |
| Total documents | 100-2,000 |
| Database size | < 100MB |
| Concurrent users | 1-3 |

### Availability

| Metric | Target |
|--------|--------|
| Uptime | Best effort (development tool) |
| Data durability | SQLite WAL mode, volume-mounted |
| Graceful degradation | Dashboard works if sync is in progress |

---

## 8. AI/ML Specifications

> Not applicable for v1.0.

---

## 9. Data Architecture

### Core Entities

| Entity | Purpose |
|--------|---------|
| Project | Registered project with name, slug, and sdlc-studio path |
| Document | Parsed SDLC document with type, metadata, content, and file hash |

See [TRD §6: Data Architecture](trd.md#6-data-architecture) for complete field definitions, database schema, and relationships.

### Data Flow

```
User clicks "Sync"
    ↓
Backend walks sdlc-studio/ directory
    ↓
For each .md file:
    ↓
Compute SHA-256 hash → Skip if unchanged
    ↓
Parse blockquote frontmatter → Extract metadata
    ↓
Upsert document record in SQLite
    ↓
Update FTS5 index
    ↓
Remove DB records for deleted files
    ↓
Update project sync status and timestamp
```

---

## 10. Integrations

| Integration | Purpose |
|-------------|---------|
| Filesystem (read-only) | Read sdlc-studio documents from Docker volume mounts |

No external service integrations required for v1.0.

---

## 11. Configuration Reference

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SDLC_LENS_HOST` | Backend bind address | No | `0.0.0.0` |
| `SDLC_LENS_PORT` | Backend port | No | `8000` |
| `SDLC_LENS_DATABASE_URL` | SQLite database path | No | `sqlite:///./data/sdlc_lens.db` |
| `SDLC_LENS_LOG_LEVEL` | Logging level | No | `info` |
| `SDLC_LENS_CORS_ORIGINS` | Allowed CORS origins (comma-separated) | No | `http://localhost:5173` |

### Feature Flags

None for v1.0.

---

## 12. Quality Assessment

### Tested Functionality
> To be determined post-implementation.

### Untested Areas
> All functionality (greenfield project).

### Test Patterns Used
- pytest for backend
- pytest-asyncio for async tests
- Vitest for frontend
- Playwright for E2E
- httpx TestClient for API integration tests

### Quality Assessment
> Not yet applicable.

---

## 13. Technical Debt Register

### TODO/FIXME Items Found
> None (greenfield).

### Inconsistent Patterns
> None (greenfield).

### Deprecated Dependencies
> None planned.

### Security Concerns
- [ ] Add authentication before exposing beyond LAN
- [ ] Validate project paths cannot escape allowed mount points
- [ ] Sanitise rendered markdown to prevent XSS

---

## 14. Documentation Gaps

### Undocumented Features
> Installation and deployment guide needed post-implementation.

### Missing Inline Comments
> N/A (greenfield).

### Unclear Code Sections
> N/A (greenfield).

---

## 15. Recommendations

### Critical Gaps
1. **Authentication** - No auth in v1.0; add API key or session auth before exposing to WAN
2. **Auto-sync** - Manual-only sync may become tedious; consider filesystem watcher in v2.0
3. **Git integration** - Could detect document changes from git history for richer activity tracking

### Suggested Improvements
1. Configurable sync ignore patterns (e.g., skip draft documents)
2. Document relationship graph (epic → stories visualisation)
3. Export statistics as JSON/CSV
4. Webhook on sync completion for CI integration
5. Light theme option

### Security Hardening
1. API key authentication (v2.0)
2. Rate limiting (low priority for LAN)
3. Content Security Policy headers

---

## 16. Release Plan

### v1.0 (MVP)

**Summary:** Core dashboard with project registration, sync, document browsing, statistics, search, and Docker deployment.

**Phases:**

#### Phase 1: Foundation
**Story Points:** ~40

**Epics:**
- **EP0001:** Project Management (~16 pts)
  - Project registration with path validation
  - Project list with edit/delete
  - Manual sync trigger
  - Sync status display

- **EP0002:** Document Sync & Parsing (~24 pts)
  - Filesystem walker
  - Blockquote frontmatter parser
  - Change detection (SHA-256)
  - Deleted file cleanup
  - FTS5 indexing

#### Phase 2: Browsing & Dashboard
**Story Points:** ~35

**Epics:**
- **EP0003:** Document Browsing (~20 pts)
  - Document list with filtering
  - Type and status filters
  - Rendered markdown viewer
  - Frontmatter sidebar

- **EP0004:** Dashboard & Statistics (~15 pts)
  - Multi-project overview cards
  - Completion metrics and progress rings
  - Status breakdown charts
  - Recent activity feed

#### Phase 3: Search & Deployment
**Story Points:** ~25

**Epics:**
- **EP0005:** Search (~12 pts)
  - FTS5 search endpoint
  - Search UI with filters
  - Result highlighting

- **EP0006:** Docker Deployment (~13 pts)
  - Backend Dockerfile (multi-stage)
  - Frontend Dockerfile (multi-stage)
  - docker-compose.yml
  - nginx configuration

**Estimated Total:** ~100 story points

---

## 17. Success Criteria

### v1.0 Success Criteria

- [ ] Register at least 2 projects and sync their documents
- [ ] Dashboard loads in < 2 seconds
- [ ] All document types visible and filterable
- [ ] Rendered markdown displays correctly with syntax highlighting
- [ ] Search returns relevant results in < 1 second
- [ ] `docker-compose up` deploys both containers successfully
- [ ] Data persists across container restarts
- [ ] Sync correctly detects new, changed, and deleted documents

---

## 18. Key User Flows

### Flow 1: Register a Project

```
User navigates to Settings → Projects
    ↓
Clicks "Add Project"
    ↓
Enters:
  - Name: "HomelabCmd"
  - Path: "/data/projects/HomelabCmd/sdlc-studio"
    ↓
System validates path exists
    ↓
Project appears in sidebar
    ↓
User clicks "Sync Now"
    ↓
Progress indicator shows "Syncing... 47/52 documents"
    ↓
Sync completes: "52 documents synced"
    ↓
Project card appears on dashboard with stats
```

### Flow 2: Browse Documents

```
User clicks project name in sidebar
    ↓
Sees document list (all types)
    ↓
Clicks "Stories" type filter
    ↓
List filters to show only stories
    ↓
Clicks "In Progress" status filter
    ↓
List shows in-progress stories only
    ↓
Clicks a story title
    ↓
Rendered markdown view with metadata sidebar
```

### Flow 3: Search Across Projects

```
User clicks search icon in header
    ↓
Types "authentication" in search box
    ↓
Results appear from multiple projects:
  - HomelabCmd: US0045 "API Key Authentication"
  - OtherProject: EP0003 "Authentication Epic"
    ↓
User clicks a result
    ↓
Navigated to document view with search term highlighted
```

### Flow 4: Check Project Health

```
User opens dashboard
    ↓
Sees project cards:
  - HomelabCmd: 152 stories, 98% done, last synced 10m ago
  - OtherProject: 30 stories, 45% done, last synced 2h ago
    ↓
Clicks HomelabCmd card
    ↓
Sees detailed stats:
  - Epics: 18 (16 done, 2 in progress)
  - Stories: 152 (149 done, 2 in progress, 1 not started)
  - Bugs: 3 (all resolved)
    ↓
Progress ring shows 98% completion
    ↓
Status breakdown chart shows distribution
```

---

## 19. Open Questions

- [x] **Q1:** Should document relationships (epic → stories) be inferred from metadata or require explicit linking?
  **Resolved:** Infer from metadata. The parser extracts the `epic` field from story frontmatter (e.g., `> **Epic:** EP0001`). No explicit linking needed.
- [x] **Q2:** How to handle documents that don't match any known type (custom markdown files in sdlc-studio/)?
  **Resolved:** Assign type `other`. Sync imports all `.md` files; unknown filename patterns get `doc_type = "other"` and appear in an "Other" filter category.
- [ ] **Q3:** Should sync support configurable file patterns beyond `*.md`?
- [x] **Q4:** Should the dashboard auto-refresh after sync completes, or require manual reload?
  **Resolved:** Auto-refresh. The sync API returns the final state; the frontend polls the sync status endpoint while syncing and refreshes the document list on completion.
- [x] **Q5:** Should deleted documents be permanently removed or soft-deleted with a "show deleted" toggle?
  **Resolved:** Hard delete. Documents removed from the filesystem are deleted from the database on sync. Simplifies the data model; the filesystem is the source of truth.

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-17 | 1.0.0 | Initial PRD created |
| 2026-02-17 | 1.0.1 | Review fixes: renumbered sections §1-§19 (was duplicating §4/§5), added FR8 Docker Deployment feature detail, resolved Q1 (infer relationships from metadata), Q2 (unknown types as "other"), Q4 (auto-refresh after sync), Q5 (hard delete on sync) |
| 2026-02-17 | 1.0.2 | Updated Design System to reference brand-guide.md; colour palette changed from emerald (#10B981) to lime green (#A3E635) per reference design |

---

> **Confidence Markers:** [HIGH] clear from requirements | [MEDIUM] inferred from patterns | [LOW] speculative
>
> **Status Values:** Complete | Partial | Stubbed | Broken | Not Started
