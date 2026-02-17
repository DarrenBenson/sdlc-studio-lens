# PL0024: Backend Dockerfile - Implementation Plan

> **Status:** Draft
> **Story:** [US0024: Backend Dockerfile](../stories/US0024-backend-dockerfile.md)
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Created:** 2026-02-17
> **Language:** Dockerfile / Bash

## Overview

Create a multi-stage Dockerfile for the FastAPI backend. The build stage installs Python dependencies via `pip install .` (hatchling build system). The runtime stage copies the installed packages into a slim image. An entrypoint script runs Alembic migrations then starts Uvicorn. A `.dockerignore` limits the build context to production-relevant files. The container runs as a non-root user and accepts configuration through `SDLC_LENS_*` environment variables.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Multi-stage build | `docker build -t sdlc-lens-backend .` completes using build + runtime stages |
| AC2 | Minimal image size | Final image < 200MB (no build tools or dev dependencies) |
| AC3 | Migrations on startup | Alembic `upgrade head` runs before Uvicorn on fresh container |
| AC4 | Uvicorn serves API | GET `http://localhost:8000/api/v1/system/health` returns 200 |
| AC5 | Environment variables configurable | `-e SDLC_LENS_PORT=9000` causes Uvicorn to bind to port 9000 |

---

## Technical Context

### Language & Framework
- **Runtime:** Python 3.12 (python:3.12-slim base)
- **Build system:** hatchling (via pyproject.toml)
- **Dependency installation:** `pip install .` (no uv, no uv.lock)
- **Migrations:** Alembic with async SQLAlchemy (sqlite+aiosqlite)
- **Server:** Uvicorn

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
1. Dockerfile builds without errors
2. Image size within limit
3. Container starts and health check passes
4. Alembic migrations execute on first start
5. Environment variable overrides work
6. Non-root user enforced

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Create backend Dockerfile (multi-stage) | `backend/Dockerfile` | - | [ ] |
| 2 | Create .dockerignore for backend context | `backend/.dockerignore` | - | [ ] |
| 3 | Create entrypoint.sh (migrations + uvicorn) | `backend/entrypoint.sh` | - | [ ] |
| 4 | Verify build completes | manual | 1, 2, 3 | [ ] |
| 5 | Verify container runs and health check passes | manual | 4 | [ ] |
| 6 | Verify environment variable overrides | manual | 5 | [ ] |
| 7 | Verify image size < 200MB | manual | 4 | [ ] |
| 8 | Verify non-root user | manual | 5 | [ ] |

---

## Implementation Phases

### Phase 1: Dockerfile and .dockerignore

**Goal:** Multi-stage Dockerfile that builds and installs the backend application.

- [ ] Create `backend/Dockerfile`:
  - **Stage 1 (builder):** `FROM python:3.12-slim AS builder`
    - `WORKDIR /build`
    - Copy `pyproject.toml` first (dependency cache layer)
    - `RUN pip install --no-cache-dir --prefix=/install .` - installs hatchling build then the package
    - Copy `src/` and `alembic/` and `alembic.ini`
    - Re-run `pip install --no-cache-dir --prefix=/install .` to include source
  - **Stage 2 (runtime):** `FROM python:3.12-slim`
    - `RUN groupadd --system appuser && useradd --system --gid appuser appuser`
    - Copy `/install` from builder to `/usr/local`
    - Copy `src/`, `alembic/`, `alembic.ini` to `/app`
    - `WORKDIR /app`
    - `RUN mkdir -p /data/db && chown appuser:appuser /data/db`
    - Set default ENV values: `SDLC_LENS_HOST=0.0.0.0`, `SDLC_LENS_PORT=8000`, `SDLC_LENS_DATABASE_URL=sqlite+aiosqlite:///data/db/sdlc_lens.db`, `SDLC_LENS_LOG_LEVEL=INFO`
    - `EXPOSE 8000`
    - `USER appuser`
    - `ENTRYPOINT ["./entrypoint.sh"]`

  **Layer ordering for cache efficiency:**
  1. Base image
  2. System user creation
  3. `pyproject.toml` only (dependency layer -- cached if deps unchanged)
  4. `pip install` dependencies
  5. Application source code (changes frequently)
  6. Entrypoint

- [ ] Create `backend/.dockerignore`:
  ```
  .venv/
  __pycache__/
  *.pyc
  .git/
  .gitignore
  tests/
  data/
  .ruff_cache/
  .pytest_cache/
  *.egg-info/
  dist/
  build/
  .coverage
  htmlcov/
  ```

**Dockerfile structure (detailed):**

```dockerfile
# Stage 1: Build dependencies
FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml .
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
RUN pip install --no-cache-dir .

# Stage 2: Runtime
FROM python:3.12-slim
RUN groupadd --system appuser && useradd --system --gid appuser appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
WORKDIR /app
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

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
- `backend/Dockerfile`
- `backend/.dockerignore`

### Phase 2: Entrypoint Script

**Goal:** Shell script that runs Alembic migrations then starts Uvicorn.

- [ ] Create `backend/entrypoint.sh`:
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
- `backend/entrypoint.sh`

### Phase 3: Testing and Validation

**Goal:** Verify build, run, and configuration through integration tests.

- [ ] Build image: `docker build -t sdlc-lens-backend ./backend`
- [ ] Verify build completes without errors
- [ ] Check image size: `docker image inspect sdlc-lens-backend --format='{{.Size}}'` < 200MB
- [ ] Run container: `docker run -d --name test-backend -p 8000:8000 sdlc-lens-backend`
- [ ] Health check: `curl -f http://localhost:8000/api/v1/system/health`
- [ ] Verify non-root: `docker exec test-backend whoami` returns `appuser`
- [ ] Verify env override: `docker run -e SDLC_LENS_PORT=9000 -p 9000:9000 sdlc-lens-backend` and curl port 9000
- [ ] Verify migration logs appear in `docker logs test-backend`
- [ ] Clean up: `docker stop test-backend && docker rm test-backend`

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | `docker build` completes with two stages | `backend/Dockerfile` | Pending |
| AC2 | `docker image inspect` size < 200MB | `backend/Dockerfile` | Pending |
| AC3 | `docker logs` shows "Running database migrations" | `backend/entrypoint.sh` | Pending |
| AC4 | `curl /api/v1/system/health` returns 200 | `backend/entrypoint.sh` | Pending |
| AC5 | `-e SDLC_LENS_PORT=9000` binds to 9000 | `backend/entrypoint.sh` | Pending |

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

**Coverage:** 6/6 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| pip install builds from source, slower than binary | Low | hatchling build is fast; dependencies are pure Python or have pre-built wheels |
| Alembic requires PYTHONPATH=src at runtime | Medium | Set PYTHONPATH in Dockerfile ENV and entrypoint.sh |
| SQLite file permissions in named volume | Medium | `chown appuser:appuser /data/db` in Dockerfile; volume permissions inherited |
| alembic.ini hardcodes database URL | Low | Alembic env.py can be updated to read from SDLC_LENS_DATABASE_URL; or override via `-x sqlalchemy.url=...` |

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
