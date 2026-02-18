# US0024: Combined Dockerfile

> **Status:** Done
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** a combined Dockerfile that builds both the frontend and backend into a single image
**So that** the entire application can be deployed as one lightweight, reproducible container

## Context

### Persona Reference
**Darren** - Deploys and runs the dashboard on LAN infrastructure using Docker.
[Full persona details](../personas.md#darren)

### Background
The combined Dockerfile uses a three-stage build. The first stage (frontend-builder) uses node:22-slim to install npm dependencies and run the Vite production build. The second stage (backend-builder) uses python:3.12-slim to install Python dependencies with uv. The third stage (runtime) uses python:3.12-slim, copies the installed Python packages, backend application code, and built frontend static files into a minimal image. Alembic migrations run on container startup before Uvicorn starts. FastAPI serves both the API endpoints and the built frontend static files from a single process.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Infrastructure | python:3.12-slim base image | Runtime base image locked |
| TRD | Infrastructure | node:22-slim for frontend build stage | Frontend build stage base image locked |
| PRD | KPI | Docker build < 3 minutes | Layer ordering for cache efficiency |
| TRD | Tech Stack | uv for dependency management | pip not used directly |
| TRD | Architecture | Single container serves API and frontend | No nginx or reverse proxy needed |

---

## Acceptance Criteria

### AC1: Three-stage build
- **Given** the combined Dockerfile
- **When** I run `docker build -t sdlc-lens .`
- **Then** the build completes successfully using three stages: frontend-builder (node:22-slim), backend-builder (python:3.12-slim with uv), and runtime (python:3.12-slim)

### AC2: Minimal image size
- **Given** the built image
- **When** I inspect its size
- **Then** the final image is < 250MB (no build tools, Node.js, or dev dependencies; includes frontend static assets)

### AC3: Migrations run on startup
- **Given** a fresh container with no database
- **When** the container starts
- **Then** Alembic migrations run before Uvicorn starts, creating the schema

### AC4: Uvicorn serves API
- **Given** the container is running
- **When** I request GET `http://localhost:8000/api/v1/system/health`
- **Then** I receive a 200 response with health status

### AC5: Environment variables configurable
- **Given** the container
- **When** I pass `-e SDLC_LENS_PORT=9000`
- **Then** Uvicorn binds to port 9000 instead of the default 8000

### AC6: Frontend static files served
- **Given** the container is running
- **When** I request GET `http://localhost:8000/`
- **Then** I receive the frontend index.html with a 200 response

---

## Scope

### In Scope
- Three-stage Dockerfile (frontend-builder + backend-builder + runtime)
- node:22-slim for npm ci + Vite build in frontend-builder stage
- python:3.12-slim as backend-builder and runtime base
- uv for dependency installation in backend-builder stage
- Copying built frontend assets into runtime image
- FastAPI static file serving for frontend assets
- Alembic migration execution in entrypoint
- Uvicorn as ASGI server
- Environment variable configuration (host, port, db path, log level)
- .dockerignore for build context
- Non-root user for security

### Out of Scope
- Docker Compose orchestration (US0026)
- CI/CD pipeline
- TLS/HTTPS configuration

---

## Technical Notes

### Dockerfile Structure
```dockerfile
# Stage 1: Frontend build
FROM node:22-slim AS frontend-builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Backend build
FROM python:3.12-slim AS backend-builder
# Install uv, copy pyproject.toml, install deps

# Stage 3: Runtime
FROM python:3.12-slim
# Copy installed packages and application code
# Copy frontend build output from frontend-builder to /app/static
# Set non-root user
# Run alembic upgrade head && uvicorn
```

### Layer Ordering (Cache Efficiency)
1. Base image (per stage)
2. System dependencies
3. Copy dependency manifests (package.json / pyproject.toml + uv.lock)
4. Install dependencies (cached if manifests unchanged)
5. Copy source code (changes frequently)
6. Frontend: run Vite build
7. Runtime: copy artifacts from both builder stages
8. Set entrypoint

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Database file does not exist on first start | Alembic creates it via migrations |
| Migration fails | Container exits with error; logs show migration failure |
| Database volume not mounted | SQLite creates file at default path (ephemeral) |
| uv.lock out of sync with pyproject.toml | Build fails; developer must run `uv lock` first |
| npm ci fails (missing lock file) | Frontend build stage fails with clear error |
| Vite build fails (TypeScript errors) | Frontend build stage fails with Vite error output |
| /app/static directory missing (no frontend build) | FastAPI serves API only; requests to / return 404 |
| Port conflict (port already in use) | Uvicorn fails to bind; container exits with error |
| SIGTERM signal | Uvicorn graceful shutdown |

---

## Test Scenarios

- [ ] Docker build completes successfully with three stages
- [ ] Frontend-builder stage uses node:22-slim
- [ ] Backend-builder stage uses python:3.12-slim
- [ ] Runtime stage uses python:3.12-slim
- [ ] Image size < 250MB
- [ ] Container starts and health check passes
- [ ] Alembic migrations run on first start
- [ ] Environment variables override defaults
- [ ] Container runs as non-root user
- [ ] .dockerignore excludes tests, __pycache__, node_modules, .git
- [ ] Graceful shutdown on SIGTERM
- [ ] GET / returns frontend index.html
- [ ] Frontend static assets served with correct Content-Type
- [ ] SPA client-side routes return index.html (not 404)

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| All EP0001-EP0005 stories | Code | Working backend and frontend application | Done |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Docker | Infrastructure | Available |

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
| 2026-02-17 | Claude | Initial story creation from EP0006 |
| 2026-02-18 | Claude | Revised for single-container architecture: three-stage build, frontend assets served by FastAPI, removed US0025 dependency |
