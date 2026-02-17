# PL0026: Docker Compose Orchestration - Implementation Plan

> **Status:** Draft
> **Story:** [US0026: Docker Compose Orchestration](../stories/US0026-docker-compose-orchestration.md)
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Created:** 2026-02-17
> **Language:** YAML / Bash

## Overview

Create a `docker-compose.yml` at the project root that orchestrates the backend and frontend containers. The compose file defines a shared Docker network, a named volume for SQLite database persistence at `/data/db`, configurable bind mounts for project sdlc-studio directories (read-only), environment variable pass-through to the backend, and health checks for both services. The frontend depends on a healthy backend before starting. A `.env.example` template documents all configurable values.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Single command deployment | `docker-compose up` starts both services; dashboard accessible at http://localhost:80 |
| AC2 | Database persistence | Data survives `docker-compose down` / `docker-compose up` cycle (named volume) |
| AC3 | Project volume mounts | sdlc-studio directories accessible in backend container at configured paths (read-only) |
| AC4 | Environment variable pass-through | SDLC_LENS_HOST, SDLC_LENS_PORT, SDLC_LENS_DATABASE_URL, SDLC_LENS_LOG_LEVEL available to backend |
| AC5 | Health checks | `docker-compose ps` shows both services as healthy |

---

## Technical Context

### Language & Framework
- **Compose:** Docker Compose v2 (Compose Specification)
- **Backend:** python:3.12-slim running FastAPI/Uvicorn (from US0024)
- **Frontend:** nginx:alpine serving React build (from US0025)
- **Database:** SQLite at `/data/db/sdlc_lens.db` inside backend container

### Existing Patterns

The backend health endpoint is `GET /api/v1/system/health`. The backend binds to `0.0.0.0:8000` by default. The frontend nginx listens on port 80 and proxies `/api/` to `http://backend:8000`. The Docker network's DNS resolves `backend` to the backend container's IP.

### Dependencies
- **US0024:** Backend Dockerfile must exist at `backend/Dockerfile`
- **US0025:** Frontend Dockerfile must exist at `frontend/Dockerfile`
- **US0027:** nginx.conf must exist at `frontend/nginx.conf` (used by frontend Dockerfile)

---

## Recommended Approach

**Strategy:** TDD (Integration)
**Rationale:** Docker Compose orchestration is validated end-to-end by running `docker-compose up` and verifying the full stack operates correctly. Tests cover service startup ordering, data persistence across restarts, and volume mount accessibility.

### Test Priority
1. Both services start with `docker-compose up`
2. Frontend reachable at http://localhost:80
3. API proxy works (frontend -> backend via nginx)
4. Database persists across down/up cycle
5. Health checks pass for both services
6. Environment variables configurable

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Create docker-compose.yml | `docker-compose.yml` | US0024, US0025, US0027 | [ ] |
| 2 | Create .env.example template | `.env.example` | - | [ ] |
| 3 | Verify compose up starts both services | manual | 1 | [ ] |
| 4 | Verify database persistence | manual | 3 | [ ] |
| 5 | Verify health checks | manual | 3 | [ ] |
| 6 | Verify project volume mounts | manual | 3 | [ ] |
| 7 | Verify environment variable pass-through | manual | 3 | [ ] |

---

## Implementation Phases

### Phase 1: docker-compose.yml

**Goal:** Compose file with both services, networking, volumes, and health checks.

- [ ] Create `docker-compose.yml` at project root:

```yaml
services:
  backend:
    build: ./backend
    container_name: sdlc-lens-backend
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
    networks:
      - sdlc-net
    restart: unless-stopped

  frontend:
    build: ./frontend
    container_name: sdlc-lens-frontend
    ports:
      - "${FRONTEND_PORT:-80}:80"
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:80"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - sdlc-net
    restart: unless-stopped

volumes:
  db-data:

networks:
  sdlc-net:
```

**Design decisions:**
- **Backend health check uses Python urllib** rather than curl because the slim Python image does not include curl. Python is always available.
- **Frontend health check uses wget** because nginx:alpine includes wget (via busybox) but not curl.
- **`start_period: 15s`** on backend gives Alembic time to run migrations before the first health check.
- **`restart: unless-stopped`** keeps containers running after host reboot.
- **`FRONTEND_PORT`** allows overriding the host port binding (defaults to 80).
- **Project volume mounts** are commented out as placeholders; users uncomment and set paths for their projects.
- **Named volume `db-data`** persists the SQLite database across container restarts and removals.
- **Network `sdlc-net`** enables `backend` hostname resolution from the frontend nginx container.

**Files:**
- `docker-compose.yml`

### Phase 2: .env.example

**Goal:** Template documenting all configurable environment variables.

- [ ] Create `.env.example` at project root:

```bash
# SDLC Studio Lens - Environment Configuration
# Copy this file to .env and adjust values as needed.

# Backend configuration
SDLC_LENS_HOST=0.0.0.0
SDLC_LENS_PORT=8000
SDLC_LENS_DATABASE_URL=sqlite+aiosqlite:///data/db/sdlc_lens.db
SDLC_LENS_LOG_LEVEL=INFO

# Frontend port (host port mapped to nginx container port 80)
FRONTEND_PORT=80
```

**Files:**
- `.env.example`

### Phase 3: Testing and Validation

**Goal:** End-to-end verification of the compose stack.

- [ ] Start stack: `docker-compose up -d --build`
- [ ] Verify both containers running: `docker-compose ps` shows both services as "Up" and "healthy"
- [ ] Verify frontend: `curl -f http://localhost:80/` returns index.html
- [ ] Verify API proxy: `curl -f http://localhost:80/api/v1/system/health` returns 200
- [ ] Test persistence:
  1. Create a project via API
  2. `docker-compose down`
  3. `docker-compose up -d`
  4. Verify project still exists via API
- [ ] Verify volume mount: `docker exec sdlc-lens-backend ls /data/projects/` (if configured)
- [ ] Verify env override: modify `.env` with `SDLC_LENS_LOG_LEVEL=DEBUG`, restart, check logs
- [ ] Verify depends_on: stop backend, observe frontend waits on restart
- [ ] Clean up: `docker-compose down -v` (removes volumes for clean slate)

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | `docker-compose up` starts both; `curl :80` returns HTML | `docker-compose.yml` | Pending |
| AC2 | Data survives `down` / `up` cycle | `volumes: db-data` | Pending |
| AC3 | `docker exec` lists mounted project dirs | bind mount config | Pending |
| AC4 | `docker exec` env shows SDLC_LENS_* vars | `environment` block | Pending |
| AC5 | `docker-compose ps` shows healthy | `healthcheck` blocks | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | Backend health check fails on startup | `start_period: 15s` allows time for migrations; `retries: 3` tolerates transient failures; frontend `depends_on` with `condition: service_healthy` waits | Phase 1 |
| 2 | Volume mount path does not exist on host | Container starts but the mount point is empty; sync for that project will fail with a clear filesystem error from the sync service | Phase 1 |
| 3 | Port 80 already in use on host | `docker-compose up` fails with port conflict error; user can set `FRONTEND_PORT=8080` in `.env` | Phase 1 |
| 4 | .env file missing | Compose uses default values from `${VAR:-default}` syntax; application runs with built-in defaults | Phase 2 |
| 5 | Database volume deleted (`docker-compose down -v`) | Fresh database created on next startup; Alembic migrations rebuild the schema | Phase 3 |
| 6 | Containers restarted individually | `restart: unless-stopped` restarts crashed containers; named volume data persists; services reconnect via Docker DNS | Phase 1 |

**Coverage:** 6/6 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Backend health check timing (migrations slow on large DB) | Medium | `start_period: 15s` gives generous startup window; increase if needed |
| SQLite file locking in Docker named volume | Low | SQLite WAL mode handles concurrent reads; single-writer (backend only) avoids lock contention |
| Host firewall blocks container-to-container traffic | Low | Docker network `sdlc-net` uses internal bridge; no host firewall involved |
| Users forget to configure project volume mounts | Medium | Commented examples in docker-compose.yml and .env.example provide guidance |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Integration tests pass (docker-compose up, health checks, API proxy)
- [ ] Edge cases handled
- [ ] .env.example documents all configurable variables
- [ ] Database persists across container restarts
- [ ] Health checks configured for both services
- [ ] depends_on with service_healthy condition works
