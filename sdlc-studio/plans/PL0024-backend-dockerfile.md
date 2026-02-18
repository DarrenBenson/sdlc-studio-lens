# PL0024: Combined Dockerfile - Implementation Plan

> **Status:** Done
> **Story:** [US0024: Backend Dockerfile](../stories/US0024-backend-dockerfile.md)
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Created:** 2026-02-17
> **Language:** Dockerfile / Bash

## Overview

Create a three-stage Dockerfile at the project root that builds both the React frontend and FastAPI backend into a single container. Stage 1 (frontend-builder) uses `node:22-slim` to run `npm ci` and `npm run build`, producing a Vite `dist/` output. Stage 2 (backend-builder) uses `python:3.12-slim` to install Python dependencies via `pip install .` (hatchling build system). Stage 3 (runtime) uses `python:3.12-slim`, copies the installed Python packages from the backend-builder and the built frontend assets from the frontend-builder into `/app/static/`. FastAPI serves the frontend via a `StaticFiles` mount for `/assets` and a catch-all route for SPA navigation. An entrypoint script runs Alembic migrations then starts Uvicorn. A `.dockerignore` limits the build context to production-relevant files. The container runs as a non-root user and accepts configuration through `SDLC_LENS_*` environment variables.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Multi-stage build | `docker build -t sdlc-lens .` completes using three stages (frontend-builder, backend-builder, runtime) |
| AC2 | Minimal image size | Final image < 200MB (no build tools or dev dependencies) |
| AC3 | Migrations on startup | Alembic `upgrade head` runs before Uvicorn on fresh container |
| AC4 | Uvicorn serves API | GET `http://localhost:8000/api/v1/system/health` returns 200 |
| AC5 | Environment variables configurable | `-e SDLC_LENS_PORT=9000` causes Uvicorn to bind to port 9000 |
| AC6 | Frontend static file serving | GET `http://localhost:8000/` returns the frontend HTML; `/assets/*` serves static JS/CSS |

---

## Technical Context

### Language & Framework
- **Frontend runtime:** Node.js (node:22-slim base, build stage only)
- **Frontend build:** `npm ci` then `npm run build` (Vite), producing `dist/` output
- **Backend runtime:** Python 3.12 (python:3.12-slim base)
- **Build system:** hatchling (via pyproject.toml)
- **Dependency installation:** `pip install .` (no uv, no uv.lock)
- **Migrations:** Alembic with async SQLAlchemy (sqlite+aiosqlite)
- **Server:** Uvicorn
- **Static file serving:** FastAPI `StaticFiles` mount at `/assets` for JS/CSS bundles; catch-all route returns `index.html` for SPA client-side routing

### Existing Patterns

The backend uses pydantic-settings with `SDLC_LENS_` prefix for all configuration:

| Variable | Default | Description |
|----------|---------|-------------|
| `SDLC_LENS_HOST` | `0.0.0.0` | Uvicorn bind address |
| `SDLC_LENS_PORT` | `8000` | Uvicorn bind port |
| `SDLC_LENS_DATABASE_URL` | `sqlite+aiosqlite:///data/db/sdlc_lens.db` | Database connection string |
| `SDLC_LENS_LOG_LEVEL` | `INFO` | Python log level |

Alembic uses async engine via `alembic/env.py` with `PYTHONPATH=src` for imports. The application factory is `sdlc_lens.main:create_app`.

---

## Recommended Approach

**Strategy:** TDD (Integration)
**Rationale:** Docker builds and container behaviour are best validated through integration tests that build the image, run the container, and verify health endpoints. Unit testing is not applicable for Dockerfiles. Manual verification scripts confirm image size, non-root user, and migration execution.

### Test Priority
1. Dockerfile builds without errors (all three stages)
2. Image size within limit
3. Container starts and health check passes
4. Alembic migrations execute on first start
5. Environment variable overrides work
6. Non-root user enforced
7. Frontend is served at root URL

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Create combined Dockerfile (three-stage) | `Dockerfile` | - | [ ] |
| 2 | Create .dockerignore for build context | `.dockerignore` | - | [ ] |
| 3 | Create entrypoint.sh (migrations + uvicorn) | `entrypoint.sh` | - | [ ] |
| 4 | Verify build completes | manual | 1, 2, 3 | [ ] |
| 5 | Verify container runs and health check passes | manual | 4 | [ ] |
| 6 | Verify environment variable overrides | manual | 5 | [ ] |
| 7 | Verify image size < 200MB | manual | 4 | [ ] |
| 8 | Verify non-root user | manual | 5 | [ ] |
| 9 | Verify frontend served at root URL | manual | 5 | [ ] |

---

## Implementation Phases

### Phase 1: Dockerfile and .dockerignore

**Goal:** Three-stage Dockerfile that builds the frontend, installs the backend, and produces a single runtime image.

- [ ] Create `Dockerfile` (project root):
  - **Stage 1 (frontend-builder):** `FROM node:22-slim AS frontend-builder`
    - `WORKDIR /build`
    - Copy `frontend/package.json` and `frontend/package-lock.json` (dependency cache layer)
    - `RUN npm ci`
    - Copy `frontend/` source
    - `RUN npm run build` - produces `dist/` with `index.html` and `assets/`
  - **Stage 2 (backend-builder):** `FROM python:3.12-slim AS backend-builder`
    - `WORKDIR /build`
    - Copy `backend/pyproject.toml` first (dependency cache layer)
    - Copy `backend/src/` and `backend/alembic/` and `backend/alembic.ini`
    - `RUN pip install --no-cache-dir .` - installs hatchling build then the package
  - **Stage 3 (runtime):** `FROM python:3.12-slim`
    - `RUN groupadd --system appuser && useradd --system --gid appuser appuser`
    - Copy installed Python packages from backend-builder to `/usr/local`
    - Copy `backend/src/`, `backend/alembic/`, `backend/alembic.ini` to `/app`
    - Copy built frontend from frontend-builder `dist/` to `/app/static/`
    - Copy `entrypoint.sh` to `/app`
    - `WORKDIR /app`
    - `RUN mkdir -p /data/db && chown -R appuser:appuser /data/db /app`
    - Set default ENV values: `SDLC_LENS_HOST=0.0.0.0`, `SDLC_LENS_PORT=8000`, `SDLC_LENS_DATABASE_URL=sqlite+aiosqlite:///data/db/sdlc_lens.db`, `SDLC_LENS_LOG_LEVEL=INFO`
    - `EXPOSE 8000`
    - `USER appuser`
    - `ENTRYPOINT ["./entrypoint.sh"]`

  **Layer ordering for cache efficiency:**
  1. Base images
  2. System user creation
  3. Frontend `package.json` / `package-lock.json` only (npm dependency layer - cached if deps unchanged)
  4. `npm ci` dependencies
  5. Frontend source code (changes frequently)
  6. `npm run build`
  7. `pyproject.toml` only (pip dependency layer - cached if deps unchanged)
  8. `pip install` dependencies
  9. Backend application source code (changes frequently)
  10. Built frontend assets copied into runtime
  11. Entrypoint

- [ ] Create `.dockerignore` (project root):
  ```
  .git/
  .gitignore
  **/.venv/
  **/__pycache__/
  **/*.pyc
  **/node_modules/
  **/dist/
  **/build/
  **/.ruff_cache/
  **/.pytest_cache/
  **/*.egg-info/
  **/.coverage
  **/htmlcov/
  backend/tests/
  backend/data/
  frontend/test/
  sdlc-studio/
  ```

**Dockerfile structure (detailed):**

```dockerfile
# Stage 1: Build frontend
FROM node:22-slim AS frontend-builder
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Build backend dependencies
FROM python:3.12-slim AS backend-builder
WORKDIR /build
COPY backend/pyproject.toml .
COPY backend/src/ src/
COPY backend/alembic/ alembic/
COPY backend/alembic.ini .
RUN pip install --no-cache-dir .

# Stage 3: Runtime
FROM python:3.12-slim
RUN groupadd --system appuser && useradd --system --gid appuser appuser

# Copy installed packages from backend-builder
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy application code
WORKDIR /app
COPY backend/src/ src/
COPY backend/alembic/ alembic/
COPY backend/alembic.ini .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Copy built frontend into static directory
COPY --from=frontend-builder /build/dist/ static/

# Create data directory for SQLite
RUN mkdir -p /data/db && chown -R appuser:appuser /data/db /app

ENV PYTHONPATH=/app/src
ENV SDLC_LENS_HOST=0.0.0.0
ENV SDLC_LENS_PORT=8000
ENV SDLC_LENS_DATABASE_URL=sqlite+aiosqlite:///data/db/sdlc_lens.db
ENV SDLC_LENS_LOG_LEVEL=INFO

EXPOSE 8000
USER appuser
ENTRYPOINT ["./entrypoint.sh"]
```

**Files:**
- `Dockerfile`
- `.dockerignore`

### Phase 2: Entrypoint Script

**Goal:** Shell script that runs Alembic migrations then starts Uvicorn.

- [ ] Create `entrypoint.sh` (project root):
  ```bash
  #!/bin/sh
  set -e

  echo "Running database migrations..."
  PYTHONPATH=src alembic upgrade head

  echo "Starting Uvicorn..."
  exec uvicorn "sdlc_lens.main:create_app" \
      --factory \
      --host "${SDLC_LENS_HOST:-0.0.0.0}" \
      --port "${SDLC_LENS_PORT:-8000}" \
      --log-level "${SDLC_LENS_LOG_LEVEL:-info}"
  ```
- [ ] Note: `exec` replaces the shell process so Uvicorn receives SIGTERM directly
- [ ] Note: `set -e` exits on migration failure (prevents Uvicorn starting with broken schema)
- [ ] Note: `PYTHONPATH=src` required for Alembic to import `sdlc_lens.db.models`

**Files:**
- `entrypoint.sh`

### Phase 3: Testing and Validation

**Goal:** Verify build, run, configuration, and frontend serving through integration tests.

- [ ] Build image: `docker build -t sdlc-lens .`
- [ ] Verify build completes without errors (all three stages)
- [ ] Check image size: `docker image inspect sdlc-lens --format='{{.Size}}'` < 200MB
- [ ] Run container: `docker run -d --name test-app -p 8000:8000 sdlc-lens`
- [ ] Health check: `curl -f http://localhost:8000/api/v1/system/health`
- [ ] Frontend check: `curl -f http://localhost:8000/` returns HTML containing expected content
- [ ] Verify non-root: `docker exec test-app whoami` returns `appuser`
- [ ] Verify env override: `docker run -e SDLC_LENS_PORT=9000 -p 9000:9000 sdlc-lens` and curl port 9000
- [ ] Verify migration logs appear in `docker logs test-app`
- [ ] Clean up: `docker stop test-app && docker rm test-app`

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | `docker build` completes with three stages | `Dockerfile` | Pending |
| AC2 | `docker image inspect` size < 200MB | `Dockerfile` | Pending |
| AC3 | `docker logs` shows "Running database migrations" | `entrypoint.sh` | Pending |
| AC4 | `curl /api/v1/system/health` returns 200 | `entrypoint.sh` | Pending |
| AC5 | `-e SDLC_LENS_PORT=9000` binds to 9000 | `entrypoint.sh` | Pending |
| AC6 | `curl http://localhost:8000/` returns frontend HTML | `Dockerfile` | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | Database file does not exist on first start | Alembic `upgrade head` creates the database and schema from scratch | Phase 2 |
| 2 | Migration fails (corrupted DB or schema conflict) | `set -e` in entrypoint exits immediately; container stops with non-zero code; error visible in `docker logs` | Phase 2 |
| 3 | Database volume not mounted | SQLite creates file at default path `/data/db/sdlc_lens.db` inside container (ephemeral; lost on container removal) | Phase 1 |
| 4 | Port conflict (port already in use on host) | Uvicorn fails to bind; container exits with error; user must choose a different host port mapping | Phase 3 |
| 5 | SIGTERM signal received | `exec` in entrypoint means Uvicorn receives SIGTERM directly and performs graceful shutdown | Phase 2 |
| 6 | pyproject.toml changed but source unchanged | Cache invalidation is correct: pyproject.toml layer invalidates pip install layer, source layer remains cached until source changes | Phase 1 |
| 7 | Frontend build failure (npm or Vite errors) | Build fails at stage 1; Docker build exits with non-zero code; error output visible in build log; no runtime image produced | Phase 1 |

**Coverage:** 7/7 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| pip install builds from source, slower than binary | Low | hatchling build is fast; dependencies are pure Python or have pre-built wheels |
| Alembic requires PYTHONPATH=src at runtime | Medium | Set PYTHONPATH in Dockerfile ENV and entrypoint.sh |
| SQLite file permissions in named volume | Medium | `chown appuser:appuser /data/db` in Dockerfile; volume permissions inherited |
| alembic.ini hardcodes database URL | Low | Alembic env.py can be updated to read from SDLC_LENS_DATABASE_URL; or override via `-x sqlalchemy.url=...` |
| Frontend build increases image build time | Low | Frontend-builder stage is cached independently; only rebuilds when frontend source changes |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Integration tests pass (Docker build + run)
- [ ] Edge cases handled
- [ ] .dockerignore covers sensitive/unnecessary files
- [ ] Container runs as non-root user (appuser)
- [ ] Image size < 200MB
- [ ] entrypoint.sh runs migrations before Uvicorn
- [ ] Environment variables override defaults
- [ ] Frontend served from root URL via FastAPI static file mount
