# PL0026: Docker Compose Orchestration - Implementation Plan

> **Status:** Draft
> **Story:** [US0026: Docker Compose Orchestration](../stories/US0026-docker-compose-orchestration.md)
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Created:** 2026-02-17
> **Language:** YAML / Bash

## Overview

Create a `docker-compose.yml` at the project root that runs a single `app` container. The compose file defines a named volume for SQLite database persistence at `/data/db`, configurable bind mounts for project sdlc-studio directories (read-only), environment variable pass-through, and a health check for the service. FastAPI serves both the API and the built frontend static assets from a single container. A `.env.example` template documents all configurable values.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Single command deployment | `docker-compose up` starts the container; dashboard accessible at http://localhost:80 |
| AC2 | Database persistence | Data survives `docker-compose down` / `docker-compose up` cycle (named volume) |
| AC3 | Project volume mounts | sdlc-studio directories accessible in the container at configured paths (read-only) |
| AC4 | Environment variable pass-through | SDLC_LENS_HOST, SDLC_LENS_PORT, SDLC_LENS_DATABASE_URL, SDLC_LENS_LOG_LEVEL available to the application |
| AC5 | Health check | `docker-compose ps` shows the service as healthy |

---

## Technical Context

### Language & Framework
- **Compose:** Docker Compose v2 (Compose Specification)
- **Application:** Single container running FastAPI/Uvicorn, serving both the API and built frontend static assets (from US0024)
- **Database:** SQLite at `/data/db/sdlc_lens.db` inside the container

### Existing Patterns

The health endpoint is `GET /api/v1/system/health`. FastAPI serves the React build as static files and handles API routes, all on port 8000. The compose file maps host port 80 to container port 8000.

### Dependencies
- **US0024:** Combined Dockerfile must exist at the project root (`Dockerfile`)

---

## Recommended Approach

**Strategy:** TDD (Integration)
**Rationale:** Docker Compose orchestration is validated end-to-end by running `docker-compose up` and verifying the application operates correctly. Tests cover service startup, data persistence across restarts, and volume mount accessibility.

### Test Priority
1. Container starts with `docker-compose up`
2. Dashboard reachable at http://localhost:80
3. API reachable at http://localhost:80/api/v1/system/health
4. Database persists across down/up cycle
5. Health check passes for the service
6. Environment variables configurable

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Create docker-compose.yml | `docker-compose.yml` | US0024 | [ ] |
| 2 | Create .env.example template | `.env.example` | - | [ ] |
| 3 | Verify compose up starts the service | manual | 1 | [ ] |
| 4 | Verify database persistence | manual | 3 | [ ] |
| 5 | Verify health check | manual | 3 | [ ] |
| 6 | Verify project volume mounts | manual | 3 | [ ] |
| 7 | Verify environment variable pass-through | manual | 3 | [ ] |

---

## Implementation Phases

### Phase 1: docker-compose.yml

**Goal:** Compose file with a single `app` service, volume, and health check.

- [ ] Create `docker-compose.yml` at project root:

```yaml
services:
  app:
    build: .
    container_name: sdlc-lens-app
    ports:
      - "${APP_PORT:-80}:8000"
    volumes:
      - db-data:/data/db
      # Project mounts (add your project paths here):
      # - /path/to/project/sdlc-studio:/data/projects/project-name/sdlc-studio:ro
    environment:
      - SDLC_LENS_HOST=${SDLC_LENS_HOST:-0.0.0.0}
      - SDLC_LENS_PORT=${SDLC_LENS_PORT:-8000}
      - SDLC_LENS_DATABASE_URL=${SDLC_LENS_DATABASE_URL:-sqlite+aiosqlite:///data/db/sdlc_lens.db}
      - SDLC_LENS_LOG_LEVEL=${SDLC_LENS_LOG_LEVEL:-INFO}
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/system/health')"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s
    restart: unless-stopped

volumes:
  db-data:
```

**Design decisions:**
- **Health check uses Python urllib** rather than curl because the slim Python image does not include curl. Python is always available.
- **`start_period: 15s`** gives Alembic time to run migrations before the first health check.
- **`restart: unless-stopped`** keeps the container running after host reboot.
- **Port mapping `80:8000`** maps host port 80 (or `APP_PORT`) to the container's Uvicorn port 8000. FastAPI serves both the API and frontend static assets on the same port.
- **`APP_PORT`** allows overriding the host port binding (defaults to 80).
- **Project volume mounts** are commented out as placeholders; users uncomment and set paths for their projects.
- **Named volume `db-data`** persists the SQLite database across container restarts and removals.
- **No networks block** needed -- a single container requires no inter-service networking.

**Files:**
- `docker-compose.yml`

### Phase 2: .env.example

**Goal:** Template documenting all configurable environment variables.

- [ ] Create `.env.example` at project root:

```bash
# SDLC Studio Lens - Environment Configuration
# Copy this file to .env and adjust values as needed.

# Application configuration
SDLC_LENS_HOST=0.0.0.0
SDLC_LENS_PORT=8000
SDLC_LENS_DATABASE_URL=sqlite+aiosqlite:///data/db/sdlc_lens.db
SDLC_LENS_LOG_LEVEL=INFO

# Host port (mapped to container port 8000)
APP_PORT=80
```

**Files:**
- `.env.example`

### Phase 3: Testing and Validation

**Goal:** End-to-end verification of the compose stack.

- [ ] Start stack: `docker-compose up -d --build`
- [ ] Verify container running: `docker-compose ps` shows the service as "Up" and "healthy"
- [ ] Verify dashboard: `curl -f http://localhost:80/` returns index.html
- [ ] Verify API: `curl -f http://localhost:80/api/v1/system/health` returns 200
- [ ] Test persistence:
  1. Create a project via API
  2. `docker-compose down`
  3. `docker-compose up -d`
  4. Verify project still exists via API
- [ ] Verify volume mount: `docker exec sdlc-lens-app ls /data/projects/` (if configured)
- [ ] Verify env override: modify `.env` with `SDLC_LENS_LOG_LEVEL=DEBUG`, restart, check logs
- [ ] Clean up: `docker-compose down -v` (removes volumes for clean slate)

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | `docker-compose up` starts the container; `curl :80` returns HTML | `docker-compose.yml` | Pending |
| AC2 | Data survives `down` / `up` cycle | `volumes: db-data` | Pending |
| AC3 | `docker exec` lists mounted project dirs | bind mount config | Pending |
| AC4 | `docker exec` env shows SDLC_LENS_* vars | `environment` block | Pending |
| AC5 | `docker-compose ps` shows healthy | `healthcheck` block | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | Volume mount path does not exist on host | Container starts but the mount point is empty; sync for that project fails with a clear filesystem error from the sync service | Phase 1 |
| 2 | Port 80 already in use on host | `docker-compose up` fails with port conflict error; user can set `APP_PORT=8080` in `.env` | Phase 1 |
| 3 | .env file missing | Compose uses default values from `${VAR:-default}` syntax; application runs with built-in defaults | Phase 2 |
| 4 | Database volume deleted (`docker-compose down -v`) | Fresh database created on next startup; Alembic migrations rebuild the schema | Phase 3 |
| 5 | Container crashes | `restart: unless-stopped` restarts the container automatically; named volume data persists | Phase 1 |

**Coverage:** 5/5 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Health check timing (migrations slow on large DB) | Medium | `start_period: 15s` gives generous startup window; increase if needed |
| SQLite file locking in Docker named volume | Low | SQLite WAL mode handles concurrent reads; single-writer avoids lock contention |
| Users forget to configure project volume mounts | Medium | Commented examples in docker-compose.yml and .env.example provide guidance |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Integration tests pass (docker-compose up, health check, API and dashboard accessible)
- [ ] Edge cases handled
- [ ] .env.example documents all configurable variables
- [ ] Database persists across container restarts
- [ ] Health check configured for the single service
