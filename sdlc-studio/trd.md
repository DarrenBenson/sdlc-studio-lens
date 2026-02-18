# Technical Requirements Document

**Project:** SDLC Studio Lens
**Version:** 1.1.0
**Status:** Draft
**Last Updated:** 2026-02-18
**PRD Reference:** [PRD](prd.md)

---

## 1. Executive Summary

### Purpose
This Technical Requirements Document describes the architecture, technology stack, data models, API contracts, and infrastructure for SDLC Studio Lens - a read-only web dashboard for browsing and searching SDLC documents produced by sdlc-studio.

### Scope

**v1.0:**
- React SPA frontend served by FastAPI
- FastAPI REST API backend with SQLite storage
- Blockquote frontmatter markdown parser
- Filesystem sync service with change detection
- GitHub repository sync via REST API (Trees + Blobs)
- Full-text search via SQLite FTS5
- Single-container Docker deployment
- Multi-project support

**Not Covered:**
- Document editing or creation (read-only dashboard)
- Webhook triggers
- Authentication or multi-user support
- Filesystem watching or auto-sync
- Mobile native applications

### Key Decisions
- **Single-container deployment** - FastAPI serves both API and built frontend static files
- **SQLite with FTS5** - simple, self-contained, sufficient for 1-10 projects
- **Manual sync only** - user-triggered, no filesystem watcher or polling
- **Blockquote frontmatter parser** - matches sdlc-studio's `> **Key:** Value` format
- **No authentication** - LAN-first tool, auth deferred to v2.0
- **Read-only filesystem access** - never writes to project directories

---

## 2. Project Classification

**Project Type:** web_application

**Classification Rationale:** SDLC Studio Lens is a web-based dashboard with a FastAPI backend serving a React SPA frontend. It reads documents from the filesystem, stores parsed data in SQLite, and serves it via a REST API.

**Architecture Implications:**

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Default Pattern | Layered monolith | Per reference-architecture.md for web applications |
| Pattern Used | Single-container SPA + API | FastAPI serves both API and frontend static files |
| Deviation Rationale | Single container simplifies deployment; FastAPI handles SPA routing via catch-all |
| Frontend | React SPA | Single-page application with client-side routing |
| Backend | FastAPI REST API | Async Python with Pydantic validation |
| Database | SQLite + FTS5 | Self-contained, suitable for document-scale data |

---

## 3. Architecture Overview

### System Context

SDLC Studio Lens reads sdlc-studio document directories from the local filesystem (mounted as Docker volumes) and presents them through a web interface:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Docker Compose Stack                              │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                     Application Container                           │  │
│  │                     (python:3.12-slim)                              │  │
│  │                                                                     │  │
│  │  Browser ──▶ :8000 (mapped to host :80)                            │  │
│  │                                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐   │  │
│  │  │                    FastAPI Application                       │   │  │
│  │  │                                                              │   │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │   │  │
│  │  │  │ API Routes   │  │ Services     │  │ Database         │  │   │  │
│  │  │  │              │  │              │  │                  │  │   │  │
│  │  │  │ /api/v1/*    │  │ sync.py      │  │ SQLite + FTS5   │  │   │  │
│  │  │  │  /projects   │  │ parser.py    │  │ projects table  │  │   │  │
│  │  │  │  /documents  │  │              │  │ documents table │  │   │  │
│  │  │  │  /stats      │  │              │  │ documents_fts   │  │   │  │
│  │  │  │  /search     │  │              │  │                  │  │   │  │
│  │  │  │  /system     │  │              │  │                  │  │   │  │
│  │  │  ├──────────────┤  └──────────────┘  └──────────────────┘  │   │  │
│  │  │  │ Static Files │                                           │   │  │
│  │  │  │ /assets/*    │  React SPA (Vite build output)            │   │  │
│  │  │  │ /*  fallback │  index.html (SPA routing)                 │   │  │
│  │  │  └──────────────┘                                           │   │  │
│  │  └─────────────────────────────────────────────────────────────┘   │  │
│  │                                                                     │  │
│  │  Volume Mounts:                                                     │  │
│  │    /data/db ──▶ SQLite database (persistent)                       │  │
│  │    /data/projects/ProjectA/sdlc-studio ──▶ Read-only docs          │  │
│  │    /data/projects/ProjectB/sdlc-studio ──▶ Read-only docs          │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Architecture Pattern

**Single-Container SPA + API**

- Single container: FastAPI serves the REST API and built React SPA static files
- Vite-built frontend assets served via `StaticFiles` mount and SPA fallback route
- API routes registered first, taking priority over the catch-all static file handler

**Rationale:**
- Simpler deployment with a single container and process
- No nginx configuration or inter-container networking required
- FastAPI's `StaticFiles` efficiently serves hashed Vite build assets
- Catch-all route returns `index.html` for SPA client-side routing

### Component Overview

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| Dashboard SPA | Document browsing, search, statistics visualisation | React 19 + Vite + Tailwind CSS |
| API Server | REST endpoints, sync orchestration, search, static file serving | FastAPI + Uvicorn |
| Sync Service | Walk filesystem, detect changes, parse documents | Python (pathlib, hashlib) |
| GitHub Source | Fetch .md files from GitHub repos via REST API (Trees + Blobs) | Python (httpx AsyncClient) |
| Parser | Extract blockquote frontmatter from markdown | Python (regex-based) |
| Database | Document storage, metadata, full-text search | SQLite + FTS5 |

---

## 4. Technology Stack

### Core Technologies

| Category | Technology | Version | Rationale |
|----------|-----------|---------|-----------|
| Language (Backend) | Python | 3.12+ | Type hints, asyncio, pathlib |
| Language (Frontend) | TypeScript | 5.0+ | Type safety, tooling |
| Backend Framework | FastAPI | >=0.115.0 | Async, Pydantic v2, OpenAPI 3.1 |
| Frontend Framework | React | 19 | Component model, hooks, ecosystem |
| Build Tool | Vite | 6.0+ | Fast builds, ESM native |
| UI Styling | Tailwind CSS | 4.0+ | Utility-first, dark theme support |
| Markdown Rendering | react-markdown | >=9.0.0 | Markdown to React components |
| Syntax Highlighting | rehype-highlight | >=7.0.0 | Code block highlighting |
| Charts | Recharts | >=2.10.0 | React-native charts |
| Validation | Pydantic | >=2.0.0 | Runtime validation, serialisation |
| Settings | Pydantic Settings | >=2.0.0 | Environment variable loading |
| ASGI Server | Uvicorn | >=0.30.0 | High performance, asyncio |
| ORM | SQLAlchemy | >=2.0.0 | Async support, type hints |
| Async SQLite | aiosqlite | >=0.20.0 | Async SQLite driver |
| Database | SQLite | 3.40+ | FTS5 support, zero config |
| Migrations | Alembic | >=1.14.0 | Version-controlled schema changes |
| HTTP Client (Backend) | httpx | >=0.27.0 | Async HTTP client for GitHub REST API |
| HTTP Client (Frontend) | fetch (built-in) | N/A | Native browser API, no dependency needed |

### Build & Development

| Tool | Purpose |
|------|---------|
| uv | Python package management |
| npm | Node package management |
| pytest | Backend testing (>=8.0.0) |
| pytest-asyncio | Async test support (>=0.24.0) |
| coverage.py | Coverage reporting |
| Ruff | Python linting and formatting |
| Vitest | Frontend testing |
| React Testing Library | Component testing |
| Playwright | E2E testing |
| Docker | Containerisation |
| docker-compose | Orchestration |

### Infrastructure Services

| Service | Provider | Purpose |
|---------|----------|---------|
| SQLite | Embedded | Data storage, FTS5 search |

---

## 5. API Contracts

### API Style

**REST** with JSON request/response bodies

- Base path: `/api/v1`
- OpenAPI 3.1.0 specification
- Swagger UI at `/api/docs`
- ReDoc at `/api/redoc`

### Authentication

**None** for v1.0 (LAN-only tool).

### Endpoints Overview

#### System

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/system/health` | Health check (DB connectivity, version) | No |

#### Projects

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/projects` | List all registered projects | No |
| POST | `/api/v1/projects` | Register a new project | No |
| GET | `/api/v1/projects/{slug}` | Get project details with stats summary | No |
| PUT | `/api/v1/projects/{slug}` | Update project name or path | No |
| DELETE | `/api/v1/projects/{slug}` | Remove project and its documents | No |
| POST | `/api/v1/projects/{slug}/sync` | Trigger filesystem sync | No |

#### Documents

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/projects/{slug}/documents` | List documents with filtering | No |
| GET | `/api/v1/projects/{slug}/documents/{type}/{doc_id}` | Get single document with content | No |

**Query Parameters for Document List:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by document type (epic, story, bug, plan, test-spec, prd, trd, tsd) |
| `status` | string | Filter by status (Draft, In Progress, Done, Blocked, etc.) |
| `sort` | string | Sort field (title, type, status, updated_at) |
| `order` | string | Sort order (asc, desc) |
| `page` | integer | Page number (default: 1) |
| `per_page` | integer | Results per page (default: 50, max: 100) |

#### Statistics

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/projects/{slug}/stats` | Get project statistics | No |
| GET | `/api/v1/stats` | Get aggregated stats across all projects | No |

#### Search

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/search` | Full-text search across all projects | No |

**Query Parameters for Search:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query (required) |
| `project` | string | Filter by project slug |
| `type` | string | Filter by document type |
| `status` | string | Filter by status |
| `page` | integer | Page number (default: 1) |
| `per_page` | integer | Results per page (default: 20, max: 50) |

### Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

Standard error codes:
- `NOT_FOUND` (404) - Project or document does not exist
- `CONFLICT` (409) - Project slug already exists
- `VALIDATION_ERROR` (422) - Invalid request body
- `SYNC_IN_PROGRESS` (409) - Sync already running for this project
- `PATH_NOT_FOUND` (400) - Project sdlc-studio path does not exist on filesystem

### Request/Response Schemas

#### Create Project

`ProjectCreate` and `ProjectResponse` include `source_type`, `repo_url`, `repo_branch`, `repo_path`, and masked `access_token` fields. Validation is conditional on `source_type`: local projects require `sdlc_path`; github projects require `repo_url`.

**Request (local):**
```json
{
  "name": "HomelabCmd",
  "source_type": "local",
  "sdlc_path": "/data/projects/HomelabCmd/sdlc-studio"
}
```

**Request (github):**
```json
{
  "name": "HomelabCmd",
  "source_type": "github",
  "repo_url": "https://github.com/DarrenBenson/homelabcmd",
  "repo_branch": "main",
  "repo_path": "sdlc-studio",
  "access_token": "ghp_xxxxxxxxxxxx"
}
```

**Response (201):**
```json
{
  "slug": "homelabcmd",
  "name": "HomelabCmd",
  "source_type": "local",
  "sdlc_path": "/data/projects/HomelabCmd/sdlc-studio",
  "repo_url": null,
  "repo_branch": "main",
  "repo_path": "sdlc-studio",
  "access_token": null,
  "sync_status": "never_synced",
  "last_synced_at": null,
  "document_count": 0,
  "created_at": "2026-02-17T10:00:00Z"
}
```

> **Note:** `access_token` is masked in responses (e.g., `"ghp_****xxxx"`) and never returned in full.

#### List Documents

**Response (200):**
```json
{
  "items": [
    {
      "doc_id": "EP0001",
      "type": "epic",
      "title": "Project Management",
      "status": "Done",
      "owner": "Darren",
      "story_points": null,
      "priority": "P0",
      "updated_at": "2026-02-17T10:30:00Z"
    }
  ],
  "total": 152,
  "page": 1,
  "per_page": 50,
  "pages": 4
}
```

#### Get Document

**Response (200):**
```json
{
  "doc_id": "US0001",
  "type": "story",
  "title": "Server Registration Form",
  "status": "Done",
  "owner": "Darren",
  "priority": "P0",
  "story_points": 5,
  "epic": "EP0001",
  "metadata": {
    "created": "2026-01-18",
    "sprint": "Sprint 1"
  },
  "content": "# Server Registration Form\n\n> **Type:** Story\n> **Status:** Done\n...",
  "file_path": "stories/US0001.md",
  "file_hash": "a1b2c3d4...",
  "synced_at": "2026-02-17T10:30:00Z"
}
```

#### Project Statistics

**Response (200):**
```json
{
  "slug": "homelabcmd",
  "name": "HomelabCmd",
  "total_documents": 152,
  "by_type": {
    "epic": 18,
    "story": 120,
    "bug": 5,
    "plan": 3,
    "test-spec": 2,
    "prd": 1,
    "trd": 1,
    "tsd": 1,
    "personas": 1
  },
  "by_status": {
    "Done": 145,
    "In Progress": 4,
    "Draft": 2,
    "Not Started": 1
  },
  "completion_percentage": 95.4,
  "last_synced_at": "2026-02-17T10:30:00Z"
}
```

#### Search Results

**Response (200):**
```json
{
  "items": [
    {
      "doc_id": "US0045",
      "type": "story",
      "title": "API Key Authentication",
      "project_slug": "homelabcmd",
      "project_name": "HomelabCmd",
      "status": "Done",
      "snippet": "...implement <mark>authentication</mark> via API key header...",
      "score": 0.95
    }
  ],
  "total": 12,
  "page": 1,
  "per_page": 20,
  "query": "authentication"
}
```

#### Sync Trigger

**Response (202):**
```json
{
  "slug": "homelabcmd",
  "sync_status": "syncing",
  "message": "Sync started"
}
```

---

## 6. Data Architecture

### Data Models

#### Project

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal ID |
| slug | TEXT | UNIQUE, NOT NULL | URL-friendly identifier (e.g., "homelabcmd") |
| name | TEXT | NOT NULL | Display name (e.g., "HomelabCmd") |
| source_type | VARCHAR(20) | NOT NULL, DEFAULT 'local' | Source type: "local" or "github" |
| sdlc_path | TEXT | NULLABLE | Absolute path to sdlc-studio directory (required for local projects) |
| repo_url | TEXT | NULLABLE | GitHub repository URL (required for github projects) |
| repo_branch | VARCHAR(255) | NOT NULL, DEFAULT 'main' | Git branch to sync from |
| repo_path | VARCHAR(500) | NOT NULL, DEFAULT 'sdlc-studio' | Path within repository to sdlc-studio directory |
| access_token | TEXT | NULLABLE | GitHub personal access token (for private repos) |
| sync_status | TEXT | NOT NULL, DEFAULT 'never_synced' | never_synced, syncing, synced, error |
| sync_error | TEXT | NULLABLE | Error message from last failed sync |
| last_synced_at | TIMESTAMP | NULLABLE | Timestamp of last successful sync |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When the project was registered |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When the project was last modified |

#### Document

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal ID |
| project_id | INTEGER | FOREIGN KEY (projects.id), NOT NULL | Owning project |
| doc_type | TEXT | NOT NULL | Document type (epic, story, bug, plan, test-spec, prd, trd, tsd) |
| doc_id | TEXT | NOT NULL | Document identifier from filename (e.g., "EP0001", "US0045", "prd") |
| title | TEXT | NOT NULL | Document title extracted from heading or frontmatter |
| status | TEXT | NULLABLE | Status from frontmatter (Draft, In Progress, Done, etc.) |
| owner | TEXT | NULLABLE | Owner from frontmatter |
| priority | TEXT | NULLABLE | Priority from frontmatter (P0, P1, P2, P3) |
| story_points | INTEGER | NULLABLE | Story points from frontmatter |
| epic | TEXT | NULLABLE | Parent epic ID from frontmatter |
| metadata | TEXT | NULLABLE | Additional frontmatter as JSON |
| content | TEXT | NOT NULL | Raw markdown content |
| file_path | TEXT | NOT NULL | Relative path within sdlc-studio directory |
| file_hash | TEXT | NOT NULL | SHA-256 hash of file content for change detection |
| synced_at | TIMESTAMP | NOT NULL | When this document was last synced |

**Unique constraint:** `(project_id, doc_type, doc_id)`

#### FTS5 Virtual Table

```sql
CREATE VIRTUAL TABLE documents_fts USING fts5(
    title,
    content,
    content=documents,
    content_rowid=id,
    tokenize="unicode61 tokenchars '_'"
);
```

### Relationships

```
projects 1──▶ N documents
documents ──▶ documents_fts (FTS5 shadow table)
```

### Storage Strategy

| Data Type | Storage | Rationale |
|-----------|---------|-----------|
| Project metadata | SQLite (projects table) | Relational, queryable |
| Document metadata | SQLite (documents table) | Filterable, sortable |
| Document content | SQLite (documents.content) | Avoids filesystem reads on view |
| Search index | SQLite FTS5 (documents_fts) | Built-in full-text search |
| Database file | Docker volume (/data/db) | Persistence across restarts |

### Migrations

Alembic for version-controlled schema migrations. Initial migration creates both tables and FTS5 virtual table.

---

## 7. Integration Patterns

### External Services

| Service | Protocol | Purpose |
|---------|----------|---------|
| GitHub REST API | HTTPS | Fetch repository tree and file blobs for github-sourced projects |

Local-sourced projects depend only on the local filesystem. GitHub-sourced projects call the GitHub REST API (Trees + Blobs endpoints) via httpx AsyncClient. An optional personal access token supports private repositories.

### Filesystem Access

| Aspect | Detail |
|--------|--------|
| Access mode | Read-only |
| Mount type | Docker volume (bind mount) |
| Path format | Absolute paths configured per project |
| File pattern | `**/*.md` within sdlc-studio directory |
| Error handling | Log and skip unreadable files; report in sync status |

---

## 8. Infrastructure

### Deployment Topology

Single Docker container orchestrated via docker-compose:

1. **sdlc-lens-app** - FastAPI application serving both API and built React frontend

### Docker Images

| Stage | Base Image | Purpose |
|-------|-----------|---------|
| frontend-builder | node:22-slim | Vite build step |
| backend-builder | python:3.12-slim | Python dependency installation |
| runtime | python:3.12-slim | FastAPI serving API + frontend static files |

### Environment Strategy

| Environment | Purpose | Characteristics |
|-------------|---------|-----------------|
| Development | Local development | Vite dev server + uvicorn with reload |
| Docker | Production-like | Single container via docker-compose |

### Scaling Strategy

Vertical only. Single instance of each container. SQLite does not support concurrent writers, so horizontal scaling of the backend is not supported.

---

## 9. Security Considerations

### Threat Model

| Threat | Likelihood | Impact | Mitigation |
|--------|-----------|--------|------------|
| Unauthorised access | Low (LAN) | Low | No auth in v1.0; add in v2.0 |
| Path traversal | Medium | High | Validate paths stay within configured directories |
| XSS via markdown | Medium | Medium | Sanitise rendered markdown; React auto-escaping |
| SQL injection | Low | High | Parameterised queries via SQLAlchemy |
| Token leakage | Medium | High | Mask access_token in API responses; store encrypted at rest in future |
| Denial of service | Low | Low | LAN-only; rate limiting deferred |

### Security Controls

| Control | Implementation |
|---------|----------------|
| Authentication | None (v1.0, LAN-only) |
| Authorisation | None (single-user) |
| Encryption at rest | None (LAN tool, no sensitive data) |
| Encryption in transit | None (HTTP, LAN-only) |
| Input validation | Pydantic models on all API inputs |
| Path validation | Resolve and verify paths before filesystem access |

---

## 10. Performance Requirements

### Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Dashboard load (p50) | < 2s | Browser DOMContentLoaded |
| API response (p50) | < 100ms | Server-side timing |
| API response (p95) | < 500ms | Server-side timing |
| Search query (p50) | < 500ms | FTS5 query time |
| Search query (p95) | < 1s | FTS5 query time |
| Sync (100 docs) | < 10s | Wall clock time |

---

## 11. Architecture Decision Records

### ADR-001: SQLite over PostgreSQL

**Status:** Accepted

**Context:** Need a database for storing parsed documents and search index. Options: PostgreSQL, SQLite.

**Decision:** Use SQLite with FTS5 for full-text search.

**Consequences:**
- Positive: Zero configuration, single-file database, built-in FTS5, easy backup
- Positive: No additional container required
- Negative: Single-writer limitation (acceptable for 1-3 concurrent users)
- Negative: No concurrent write scaling

---

### ADR-002: Manual Sync over Filesystem Watching

**Status:** Accepted

**Context:** Documents change when the user runs sdlc-studio commands. Options: filesystem watcher (inotify/watchdog), polling, manual trigger.

**Decision:** Manual sync triggered by user clicking a button.

**Consequences:**
- Positive: Simple implementation, no background processes
- Positive: Predictable behaviour (user controls when data refreshes)
- Positive: No inotify limits or cross-platform concerns
- Negative: Data may be stale until user triggers sync
- Negative: Extra click required after running sdlc-studio

---

### ADR-003: Blockquote Frontmatter Parser

**Status:** Accepted

**Context:** sdlc-studio documents use `> **Key:** Value` blockquote format for metadata rather than YAML frontmatter (`---`). Need a parser to extract this.

**Decision:** Build a custom regex-based parser for blockquote frontmatter.

**Consequences:**
- Positive: Handles the exact format sdlc-studio produces
- Positive: No dependency on YAML frontmatter libraries
- Negative: Custom parser requires thorough testing
- Negative: Must handle edge cases (multi-line values, nested blockquotes)

---

### ADR-004: No Authentication for v1.0

**Status:** Accepted

**Context:** Dashboard will run on LAN alongside other development tools. Adding auth increases complexity.

**Decision:** No authentication in v1.0. Add API key auth in v2.0 if needed.

**Consequences:**
- Positive: Simpler development, no credential management
- Positive: Matches other LAN tools (Heimdall, Portainer)
- Negative: Cannot expose to WAN without adding auth
- Negative: Any LAN user can access all project data

---

### ADR-005: Single-Container Deployment

**Status:** Accepted (revised)

**Context:** Could serve React build from FastAPI (single container) or use separate nginx container.

**Decision:** Single container - FastAPI serves both API and built frontend static files via `StaticFiles` mount and SPA fallback route.

**Consequences:**
- Positive: Simpler deployment with one container and one process
- Positive: No nginx configuration or inter-container networking needed
- Positive: Smaller operational footprint (one image, one health check)
- Positive: Same-origin requests eliminate CORS complexity
- Negative: Cannot restart API independently of frontend serving
- Negative: Uvicorn handles static files (less optimised than nginx, but acceptable for LAN use)

---

## 12. Open Technical Questions

- [x] **Q:** Should FTS5 use porter stemmer or unicode61 tokeniser?
  **Resolved:** unicode61 with `tokenchars '_'`. Technical documents need exact matching (searching "plan" should not match "planned"/"planning" when plan is a document type). Adding underscore as a token character keeps snake_case identifiers (sync_status, last_synced_at) as single searchable terms. The corpus is small (100-2000 docs) so stemming's recall benefit is unnecessary.

- [ ] **Q:** Should sync run in a background task or block the API response?
  **Context:** Large projects may take >10s to sync; blocking would timeout the HTTP request

- [x] **Q:** Should document content be stored in SQLite or read from filesystem on demand?
  **Resolved:** Store in SQLite. The documents table stores `content TEXT NOT NULL` (§6 Data Architecture). Avoids filesystem reads at view time; the DB is the read cache, the filesystem is the source of truth refreshed on sync.

---

## 13. Implementation Constraints

### Must Have
- Python 3.12+ for backend
- React 19 with TypeScript for frontend
- SQLite with FTS5 for search
- Docker deployment with docker-compose
- Read-only filesystem access to project directories
- Blockquote frontmatter parser matching sdlc-studio format

### Won't Have (This Version)
- Authentication or authorisation
- Document editing or creation
- Webhook triggers or push-based sync
- Filesystem watching or auto-sync
- WebSocket real-time updates
- Multi-user support
- Mobile-specific layouts

---

## 14. UI/UX Design

> **Authoritative source:** The [Brand Guide](brand-guide.md) is the definitive reference for all visual design decisions including colours, typography, spacing, components, and Tailwind configuration. The summary below is for quick reference only.

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  ┌─────────┐  SDLC Studio Lens    🔍 Search...    │
│  │         │                                            │
│  │ Sidebar │  ┌─────────────────────────────────────┐  │
│  │         │  │                                      │  │
│  │ Projects│  │           Main Content               │  │
│  │ ├ Proj1 │  │                                      │  │
│  │ ├ Proj2 │  │  Dashboard / Document List /         │  │
│  │ └ Proj3 │  │  Document View / Search Results      │  │
│  │         │  │                                      │  │
│  │ ─────── │  │                                      │  │
│  │ Settings│  │                                      │  │
│  │         │  │                                      │  │
│  └─────────┘  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Pages

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | Dashboard | Multi-project overview with stat cards |
| `/projects/:slug` | ProjectDetail | Single project stats and document type breakdown |
| `/projects/:slug/documents` | DocumentList | Filterable document list |
| `/projects/:slug/documents/:type/:docId` | DocumentView | Rendered markdown with metadata sidebar |
| `/search` | SearchResults | Cross-project search results |
| `/settings` | Settings | Project management (add, edit, remove) |

### Colour System

> Full palette in [Brand Guide §3](brand-guide.md). Key tokens:

| Token | Hex | Usage |
|-------|-----|-------|
| `bg-base` | #0B0F0D | Page background (green-tinted dark) |
| `bg-surface` | #111916 | Card and panel backgrounds |
| `bg-elevated` | #1C2520 | Hover states, inputs |
| `text-primary` | #F0F6F0 | Headlines, important content |
| `text-secondary` | #B0BEC5 | Body text, descriptions |
| `text-tertiary` | #78909C | Labels, timestamps |
| `accent-primary` | #A3E635 | Primary actions, active states (lime green) |
| `accent-hover` | #BEF264 | Hover states |
| `status-done` | #A3E635 | Done/complete status |
| `status-progress` | #3B82F6 | In progress status |
| `status-draft` | #78909C | Draft status |
| `status-blocked` | #EF4444 | Blocked/error status |
| `status-warning` | #F59E0B | Warning states |

### Typography

| Usage | Font | Weight |
|-------|------|--------|
| Headings | Space Grotesk | 600 (semibold) |
| Body text | Inter | 400 (regular) |
| Code, metadata, doc IDs | JetBrains Mono | 400 (regular) |
| Stat numbers | JetBrains Mono | 700 (bold) |

---

## 15. Backend Project Structure

```
backend/
├── src/
│   └── sdlc_lens/
│       ├── __init__.py
│       ├── main.py                    # FastAPI app factory
│       ├── config.py                  # Pydantic Settings
│       ├── api/
│       │   ├── __init__.py
│       │   ├── deps.py                # Dependency injection (DB session)
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── system.py          # Health check
│       │       ├── projects.py        # Project CRUD + sync trigger
│       │       ├── documents.py       # Document list + detail
│       │       ├── stats.py           # Statistics endpoints
│       │       └── search.py          # Full-text search
│       ├── api/schemas/
│       │   ├── __init__.py
│       │   ├── projects.py            # Project request/response models
│       │   ├── documents.py           # Document response models
│       │   ├── stats.py               # Statistics response models
│       │   └── search.py              # Search response models
│       ├── db/
│       │   ├── __init__.py
│       │   ├── session.py             # Async SQLAlchemy session
│       │   └── models/
│       │       ├── __init__.py
│       │       ├── project.py         # Project model
│       │       └── document.py        # Document model
│       └── services/
│           ├── __init__.py
│           ├── github_source.py       # GitHub repo sync via REST API (Trees + Blobs), httpx AsyncClient
│           ├── parser.py              # Blockquote frontmatter parser
│           └── sync.py                # Filesystem sync service
├── tests/
│   ├── conftest.py                    # Fixtures (test client, DB, sample data)
│   ├── test_parser.py                 # Parser unit tests
│   ├── test_sync.py                   # Sync service tests
│   ├── test_api_projects.py           # Project endpoint tests
│   ├── test_api_documents.py          # Document endpoint tests
│   ├── test_api_stats.py              # Stats endpoint tests
│   ├── test_api_search.py             # Search endpoint tests
│   ├── test_api_contracts.py          # Contract tests
│   └── fixtures/
│       └── sample-project/            # Sample sdlc-studio directory
├── alembic/                           # Database migrations
├── alembic.ini
├── pyproject.toml
└── Dockerfile
```

### Frontend Project Structure

```
frontend/
├── src/
│   ├── main.tsx                       # App entry point
│   ├── App.tsx                        # Router setup
│   ├── api/
│   │   └── client.ts                  # API client (fetch)
│   ├── components/
│   │   ├── Layout.tsx                 # Shell with sidebar
│   │   ├── Sidebar.tsx                # Project navigation
│   │   ├── StatusBadge.tsx            # Document status badge
│   │   ├── StatsCard.tsx              # Stat display card
│   │   ├── ProgressRing.tsx           # Circular progress indicator
│   │   ├── DocumentCard.tsx           # Document list item
│   │   └── SearchBar.tsx              # Global search input
│   ├── pages/
│   │   ├── Dashboard.tsx              # Multi-project overview
│   │   ├── ProjectDetail.tsx          # Single project stats
│   │   ├── DocumentList.tsx           # Filtered document list
│   │   ├── DocumentView.tsx           # Rendered markdown viewer
│   │   ├── SearchResults.tsx          # Search results page
│   │   └── Settings.tsx               # Project management
│   ├── types/
│   │   └── index.ts                   # TypeScript interfaces
│   └── styles/
│       └── globals.css                # Tailwind directives, custom properties
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
└── Dockerfile
```

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-17 | 1.0.0 | Initial TRD created |
| 2026-02-17 | 1.0.1 | Review fix: committed to fetch (built-in) over Axios for frontend HTTP client |
| 2026-02-17 | 1.0.2 | Review fixes: updated stale fetch/axios comment in frontend structure, resolved open question Q3 (content stored in SQLite), added test_api_contracts.py and fixtures/ to backend test structure |
| 2026-02-17 | 1.0.3 | Resolved FTS5 tokeniser question: unicode61 with tokenchars '_'; updated FTS5 virtual table DDL |
| 2026-02-17 | 1.0.4 | Updated §14 UI/UX to reference brand-guide.md as authoritative source; updated colour tokens to match brand guide (lime green palette) |
| 2026-02-18 | 1.0.5 | Architecture changed from two-container to single-container deployment; updated diagram, component overview, deployment topology, Docker images, ADR-005; removed nginx from infrastructure services |
| 2026-02-18 | 1.1.0 | EP0007 Git Repository Sync: added GitHub REST API source (Trees + Blobs); new Project columns (source_type, repo_url, repo_branch, repo_path, access_token); sdlc_path now nullable; new services/github_source.py module; httpx runtime dependency; updated API schemas with conditional validation |
