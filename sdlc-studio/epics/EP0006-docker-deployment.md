# EP0006: Docker Deployment

> **Status:** Done
> **Owner:** Darren
> **Created:** 2026-02-17
> **Target Release:** Phase 3 (Search & Deployment)
> **Story Points:** 13

## Summary

Package and deploy the application as a single Docker container orchestrated via docker-compose. This epic delivers a multi-stage Dockerfile that builds the frontend (Vite) and backend (Python) into a single runtime image where FastAPI serves both the API and the built frontend static files. A docker-compose.yml brings up the container with configurable project volume mounts.

## Inherited Constraints

Constraints that flow from PRD and TRD to this Epic.

### From PRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| KPI | Docker build time < 3 minutes | Multi-stage builds must be optimised |
| Architecture | Project directories as Docker volumes (read-only) | Bind mounts for sdlc-studio paths |
| Architecture | Data persists across container restarts | Named volume for SQLite database |
| Performance | Dashboard load < 2 seconds | nginx must serve static assets efficiently |

### From TRD

| Type | Constraint | Impact on Epic |
|------|------------|----------------|
| Infrastructure | python:3.12-slim for runtime | Base image locked |
| Infrastructure | node:22-slim for frontend build stage | Build-only stage |
| Architecture | Single container (FastAPI serves API + frontend) | One service in docker-compose |

> **Note:** Inherited constraints MUST propagate to child Stories. Check Story templates include these constraints.

## Business Context

### Problem Statement

Without containerised deployment, the dashboard requires manual setup of Python, Node.js, and build tools. Docker deployment enables single-command setup and consistent environments across development and production.

**PRD Reference:** [§5 Feature Inventory](../prd.md#5-feature-inventory) (FR8)

### Value Proposition

`docker-compose up` brings up the full dashboard with zero manual configuration beyond specifying project volume paths. Containers are small, start fast, and persist data across restarts.

### Success Metrics

| Metric | Current State | Target | Measurement Method |
|--------|---------------|--------|-------------------|
| Time to deploy from scratch | N/A | < 5 minutes (pull + up) | Wall clock |
| Docker build time | N/A | < 3 minutes | Build timing |
| Container startup time | N/A | < 10 seconds | Docker logs |
| Data persistence | N/A | Survives restart | Manual test |

## Scope

### In Scope

- Combined Dockerfile (three-stage: frontend build, backend deps, runtime)
  - node:22-slim for Vite build (produces dist/)
  - python:3.12-slim for dependency installation and runtime
  - Built frontend copied into /app/static/ in runtime image
  - Alembic migrations run on startup
  - Uvicorn as ASGI server
- FastAPI static file serving
  - Mount /assets as StaticFiles (Vite hashed bundles)
  - Catch-all route serves files from /app/static/ or falls back to index.html
  - API routes registered first, taking priority
- docker-compose.yml
  - Single service (app)
  - Named volume for SQLite database (/data/db)
  - Bind mounts for project sdlc-studio directories (read-only)
  - Environment variable configuration
  - Health check
- .dockerignore files for build contexts

### Out of Scope

- Kubernetes deployment manifests
- CI/CD pipeline for automated builds
- Image registry publishing
- TLS/HTTPS configuration
- Docker Swarm or multi-host deployment
- Automated backup of SQLite database

### Affected User Personas

- **SDLC Developer (Darren):** Deploys and runs the dashboard on LAN infrastructure

## Acceptance Criteria (Epic Level)

- [ ] Combined Dockerfile builds successfully and produces a minimal image
- [ ] FastAPI serves both API endpoints and built frontend static files
- [ ] SPA fallback routing returns index.html for client-side routes
- [ ] docker-compose up starts the container with default configuration
- [ ] Project directories configurable as bind-mount volumes (read-only)
- [ ] SQLite database persists via named volume across container restarts
- [ ] Container starts successfully within 10 seconds
- [ ] Docker build completes in < 3 minutes
- [ ] Environment variables configurable (host, port, db path, log level)
- [ ] Health check endpoint accessible

## Dependencies

### Blocked By

| Dependency | Type | Status | Owner | Notes |
|------------|------|--------|-------|-------|
| EP0001: Project Management | Epic | Done | Darren | Working backend API |
| EP0002: Document Sync & Parsing | Epic | Done | Darren | Sync service complete |
| EP0003: Document Browsing | Epic | Done | Darren | Frontend pages complete |
| EP0004: Dashboard & Statistics | Epic | Done | Darren | Dashboard complete |
| EP0005: Search | Epic | Done | Darren | Search complete |

### Blocking

| Item | Type | Impact |
|------|------|--------|
| None | - | Final epic in delivery pipeline |

## Risks & Assumptions

### Assumptions

- Docker and docker-compose are available on the deployment host
- Sufficient disk space for Docker images (~500MB combined)
- Project directories are accessible to Docker via bind mounts
- No firewall blocks between containers on Docker network
- SQLite file locking works correctly within Docker volumes

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SQLite locking issues with Docker volumes | Low | High | Test with named volumes; use WAL mode |
| nginx config incorrect for SPA routing | Medium | Medium | Test all route patterns; verify fallback |
| Build cache invalidation causes slow rebuilds | Medium | Low | Order Dockerfile layers for cache efficiency |
| Volume permissions differ between host and container | Medium | Medium | Document required permissions; use appropriate user IDs |

## Technical Considerations

### Architecture Impact

- Finalises the deployment topology
- Establishes Docker image naming and tagging convention
- Defines environment variable interface for runtime configuration
- Creates the nginx reverse proxy layer between user and API

### Integration Points

- Host port 80 → Container port 8000 (FastAPI/Uvicorn)
- Host filesystem → Container via bind mounts (read-only)
- Named volume → Container at /data/db
- docker-compose → single service

### Data Considerations

- SQLite database stored in named volume (/data/db/sdlc_lens.db)
- WAL mode for concurrent read access
- Alembic migrations run on backend container startup
- Project directories mounted read-only (no risk of accidental writes)

**TRD Reference:** [§8 Infrastructure](../trd.md#8-infrastructure)

## Sizing & Effort

**Story Points:** 13
**Estimated Story Count:** ~4 stories

**Complexity Factors:**

- Multi-stage Dockerfile optimisation (layer ordering, cache efficiency)
- nginx configuration for SPA routing + API proxy
- Docker networking between containers
- Volume mount configuration for both database and project directories
- Environment variable pass-through from compose to application

## Stakeholders

| Role | Name | Interest |
|------|------|----------|
| Product Owner | Darren | Primary user, defines requirements |
| Developer | Darren/Claude | Implementation |

## Story Breakdown

| ID | Title | Complexity | Status |
|----|-------|------------|--------|
| [US0024](../stories/US0024-backend-dockerfile.md) | Combined Dockerfile | Medium | Done |
| [US0025](../stories/US0025-frontend-dockerfile.md) | Frontend Dockerfile | Low | Superseded |
| [US0026](../stories/US0026-docker-compose-orchestration.md) | Docker Compose Orchestration | Medium | Done |
| [US0027](../stories/US0027-nginx-reverse-proxy-config.md) | Nginx Reverse Proxy Configuration | Low | Superseded |

> **Note:** US0025 and US0027 are superseded by the single-container architecture. Frontend build is now a stage in the combined Dockerfile (US0024), and SPA routing is handled by FastAPI instead of nginx.

## Test Plan

**Test Spec:** To be generated via `/sdlc-studio test-spec --epic EP0006`.

## Open Questions

None.

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial epic creation from PRD |
| 2026-02-18 | Claude | Updated for single-container architecture; US0025 and US0027 marked as superseded |
