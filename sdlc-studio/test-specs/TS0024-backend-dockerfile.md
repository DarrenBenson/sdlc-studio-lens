# TS0024: Backend Dockerfile

> **Status:** Draft
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0024 - Backend Dockerfile. Covers the multi-stage Docker build for the Python backend, verifying image size, base image, container startup with Alembic migrations, environment variable configuration, non-root execution, and graceful shutdown. All tests are Docker integration tests requiring a working Docker installation.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0024](../stories/US0024-backend-dockerfile.md) | Backend Dockerfile | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0024 | AC1 | Multi-stage build | TC0253 | Pending |
| US0024 | AC2 | Minimal image size | TC0254, TC0255 | Pending |
| US0024 | AC3 | Migrations run on startup | TC0257 | Pending |
| US0024 | AC4 | Uvicorn serves API | TC0256 | Pending |
| US0024 | AC5 | Environment variables configurable | TC0258 | Pending |

**Coverage:** 5/5 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | No | Infrastructure config, not application code |
| Integration | Yes | Docker build + container runtime validation |
| E2E | No | Covered by integration tests against running container |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Docker 24+, curl |
| External Services | None |
| Test Data | None (Alembic migrations create schema) |

---

## Test Cases

### TC0253: Multi-stage build completes successfully

**Type:** Integration | **Priority:** Critical | **Story:** US0024 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The backend Dockerfile exists at `backend/Dockerfile` | File present |
| When | Run `docker build -t sdlc-lens-backend ./backend` | Build executes |
| Then | Build exits with code 0 and image tagged `sdlc-lens-backend` appears in `docker images` | Image created |

**Assertions:**
- [ ] `docker build` exit code is 0
- [ ] `docker images sdlc-lens-backend --format '{{.Repository}}'` returns `sdlc-lens-backend`
- [ ] Build output shows at least two FROM stages (builder + runtime)

---

### TC0254: Final image base is python:3.12-slim

**Type:** Integration | **Priority:** High | **Story:** US0024 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The `sdlc-lens-backend` image has been built | Image exists |
| When | Inspect the image with `docker inspect sdlc-lens-backend` | Metadata retrieved |
| Then | The image history or labels show python:3.12-slim as the runtime base | Correct base image |

**Assertions:**
- [ ] `docker run --rm sdlc-lens-backend python --version` outputs `Python 3.12.x`
- [ ] Image does not contain `node`, `npm`, or `gcc` binaries (build tools excluded)

---

### TC0255: Image size under 200MB

**Type:** Integration | **Priority:** High | **Story:** US0024 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The `sdlc-lens-backend` image has been built | Image exists |
| When | Run `docker images sdlc-lens-backend --format '{{.Size}}'` | Size retrieved |
| Then | Reported size is less than 200MB | Image is minimal |

**Assertions:**
- [ ] Image size in bytes is less than 209,715,200 (200 * 1024 * 1024)

---

### TC0256: Container starts and health check passes

**Type:** Integration | **Priority:** Critical | **Story:** US0024 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The `sdlc-lens-backend` image has been built | Image ready |
| When | Run `docker run -d -p 8000:8000 --name backend-test sdlc-lens-backend` and wait up to 15 seconds | Container starts |
| Then | `curl -sf http://localhost:8000/api/v1/system/health` returns HTTP 200 | Health check passes |

**Assertions:**
- [ ] HTTP response status is 200
- [ ] Response body is valid JSON containing a health status field
- [ ] Container status is `running` (not `exited` or `restarting`)

---

### TC0257: Alembic migrations run on first start

**Type:** Integration | **Priority:** Critical | **Story:** US0024 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A fresh container with an empty database volume (no pre-existing SQLite file) | Clean state |
| When | Start the container and wait for readiness (health check passes) | Container boots |
| Then | Container logs contain Alembic migration output and the database file exists | Schema created |

**Assertions:**
- [ ] `docker logs backend-test` contains "Running upgrade" or "alembic" migration output
- [ ] Database file exists inside the container at the configured path
- [ ] A subsequent API call (e.g., GET `/api/v1/projects`) returns 200, confirming schema is operational

---

### TC0258: Environment variables override defaults

**Type:** Integration | **Priority:** High | **Story:** US0024 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The `sdlc-lens-backend` image has been built | Image ready |
| When | Run `docker run -d -p 9000:9000 -e SDLC_LENS_PORT=9000 --name backend-env-test sdlc-lens-backend` | Container starts with custom port |
| Then | `curl -sf http://localhost:9000/api/v1/system/health` returns HTTP 200 | Uvicorn binds to port 9000 |

**Assertions:**
- [ ] HTTP 200 received on port 9000
- [ ] Port 8000 is not listening inside the container
- [ ] `docker logs backend-env-test` shows Uvicorn binding to `0.0.0.0:9000`

---

### TC0259: Container runs as non-root user

**Type:** Integration | **Priority:** High | **Story:** US0024 (security)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The `sdlc-lens-backend` container is running | Container active |
| When | Run `docker exec backend-test whoami` | User identity retrieved |
| Then | The output is not `root` | Non-root user confirmed |

**Assertions:**
- [ ] `whoami` output is not `root`
- [ ] Process UID inside the container is not 0
- [ ] Uvicorn process runs under the application user

---

### TC0260: .dockerignore excludes tests, __pycache__, .git

**Type:** Integration | **Priority:** Medium | **Story:** US0024 (build hygiene)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The `sdlc-lens-backend` container is running | Container active |
| When | Check for excluded paths inside the container filesystem | Search for artefacts |
| Then | `tests/`, `__pycache__/`, and `.git/` directories do not exist in the image | Excluded correctly |

**Assertions:**
- [ ] `docker exec backend-test ls /app/tests 2>&1` returns an error (directory not found)
- [ ] `docker exec backend-test find /app -name __pycache__ -type d` returns no results
- [ ] `docker exec backend-test ls /app/.git 2>&1` returns an error (directory not found)

---

### TC0261: Graceful shutdown on SIGTERM

**Type:** Integration | **Priority:** Medium | **Story:** US0024 (operational)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The `sdlc-lens-backend` container is running and healthy | Container active |
| When | Send `docker stop backend-test` (sends SIGTERM, then SIGKILL after timeout) | Shutdown signal sent |
| Then | Container exits within 10 seconds with exit code 0 | Graceful shutdown |

**Assertions:**
- [ ] `docker stop` completes in under 10 seconds (no SIGKILL required)
- [ ] Container exit code is 0
- [ ] `docker logs backend-test` shows Uvicorn shutdown message (e.g., "Shutting down")

---

## Fixtures

```bash
# Build the backend image
docker build -t sdlc-lens-backend ./backend

# Start a container for testing
docker run -d -p 8000:8000 --name backend-test sdlc-lens-backend

# Wait for health check
for i in $(seq 1 15); do
  curl -sf http://localhost:8000/api/v1/system/health && break
  sleep 1
done

# Cleanup after all tests
docker stop backend-test 2>/dev/null
docker rm backend-test 2>/dev/null
docker stop backend-env-test 2>/dev/null
docker rm backend-env-test 2>/dev/null
docker rmi sdlc-lens-backend 2>/dev/null
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0253 | Multi-stage build completes successfully | Pending | - |
| TC0254 | Final image base is python:3.12-slim | Pending | - |
| TC0255 | Image size under 200MB | Pending | - |
| TC0256 | Container starts and health check passes | Pending | - |
| TC0257 | Alembic migrations run on first start | Pending | - |
| TC0258 | Environment variables override defaults | Pending | - |
| TC0259 | Container runs as non-root user | Pending | - |
| TC0260 | .dockerignore excludes tests, __pycache__, .git | Pending | - |
| TC0261 | Graceful shutdown on SIGTERM | Pending | - |

---

## Traceability

| Artefact | Reference |
|----------|-----------|
| PRD | [sdlc-studio/prd.md](../prd.md) |
| Epic | [EP0006](../epics/EP0006-docker-deployment.md) |

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec |
