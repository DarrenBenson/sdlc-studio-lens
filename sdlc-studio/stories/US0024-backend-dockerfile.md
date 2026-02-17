# US0024: Backend Dockerfile

> **Status:** Draft
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** a multi-stage Dockerfile for the backend that produces a minimal Python image
**So that** the backend can be deployed as a lightweight, reproducible container

## Context

### Persona Reference
**Darren** - Deploys and runs the dashboard on LAN infrastructure using Docker.
[Full persona details](../personas.md#darren)

### Background
The backend Dockerfile uses a multi-stage build: first stage installs dependencies with uv, second stage copies the application into a slim runtime image. Alembic migrations run on container startup before Uvicorn starts.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Infrastructure | python:3.12-slim base image | Base image locked |
| PRD | KPI | Docker build < 3 minutes | Layer ordering for cache efficiency |
| TRD | Tech Stack | uv for dependency management | pip not used directly |

---

## Acceptance Criteria

### AC1: Multi-stage build
- **Given** the backend Dockerfile
- **When** I run `docker build -t sdlc-lens-backend .`
- **Then** the build completes successfully using two stages: build (with uv) and runtime (slim)

### AC2: Minimal image size
- **Given** the built image
- **When** I inspect its size
- **Then** the final image is < 200MB (no build tools, node, or dev dependencies)

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

---

## Scope

### In Scope
- Multi-stage Dockerfile (build + runtime)
- python:3.12-slim as runtime base
- uv for dependency installation in build stage
- Alembic migration execution in entrypoint
- Uvicorn as ASGI server
- Environment variable configuration (host, port, db path, log level)
- .dockerignore for backend context
- Non-root user for security

### Out of Scope
- Frontend build (US0025)
- Docker Compose orchestration (US0026)
- CI/CD pipeline

---

## Technical Notes

### Dockerfile Structure
```dockerfile
# Stage 1: Build
FROM python:3.12-slim AS builder
# Install uv, copy pyproject.toml, install deps

# Stage 2: Runtime
FROM python:3.12-slim
# Copy installed packages and application code
# Set non-root user
# Run alembic upgrade head && uvicorn
```

### Layer Ordering (Cache Efficiency)
1. Base image
2. System dependencies
3. Copy pyproject.toml + uv.lock (dependency layer)
4. Install Python dependencies (cached if lock unchanged)
5. Copy application code (changes frequently)
6. Set entrypoint

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Database file does not exist on first start | Alembic creates it via migrations |
| Migration fails | Container exits with error; logs show migration failure |
| Database volume not mounted | SQLite creates file at default path (ephemeral) |
| uv.lock out of sync with pyproject.toml | Build fails; developer must run `uv lock` first |
| Port conflict (port already in use) | Uvicorn fails to bind; container exits with error |
| SIGTERM signal | Uvicorn graceful shutdown |

---

## Test Scenarios

- [ ] Docker build completes successfully
- [ ] Built image uses python:3.12-slim base
- [ ] Image size < 200MB
- [ ] Container starts and health check passes
- [ ] Alembic migrations run on first start
- [ ] Environment variables override defaults
- [ ] Container runs as non-root user
- [ ] .dockerignore excludes tests, __pycache__, .git
- [ ] Graceful shutdown on SIGTERM

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| All EP0001-EP0005 stories | Code | Working backend application | Draft |

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
