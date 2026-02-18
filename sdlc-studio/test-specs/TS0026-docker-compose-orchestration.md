# TS0026: Docker Compose Orchestration

> **Status:** Draft
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-18

## Overview

Test specification for US0026 - Docker Compose Orchestration. Covers the docker-compose.yml that brings up a single `app` container serving both the API and frontend via a unified image. Tests verify service startup, dashboard accessibility, health checks, database persistence across restart cycles, read-only project volume mounts, environment variable configuration, clean shutdown, and startup time. All tests are Docker integration tests requiring Docker and Docker Compose.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0026](../stories/US0026-docker-compose-orchestration.md) | Docker Compose Orchestration | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0026 | AC1 | Single command deployment | TC0270, TC0271 | Pending |
| US0026 | AC2 | Database persistence | TC0273 | Pending |
| US0026 | AC3 | Project volume mounts | TC0274 | Pending |
| US0026 | AC4 | Environment variable pass-through | TC0275 | Pending |
| US0026 | AC5 | Health check | TC0272 | Pending |

**Coverage:** 5/5 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | No | Infrastructure orchestration, not application code |
| Integration | Yes | Docker Compose service lifecycle and container management |
| E2E | No | Covered by integration tests against running stack |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Docker 24+, Docker Compose v2+, curl |
| External Services | None |
| Test Data | None (Alembic migrations create schema) |

---

## Test Cases

### TC0270: docker compose up starts the container

**Type:** Integration | **Priority:** Critical | **Story:** US0026 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A docker-compose.yml exists in the project root | File present |
| When | Run `docker compose up -d` from the project root | Compose starts |
| Then | The `app` service is listed as running in `docker compose ps` | Service up |

**Assertions:**
- [ ] `docker compose up -d` exit code is 0
- [ ] `docker compose ps --format json` shows 1 service
- [ ] App service state is `running`

---

### TC0271: Dashboard accessible at http://localhost:80

**Type:** Integration | **Priority:** Critical | **Story:** US0026 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The container is running via `docker compose up -d` | Stack active |
| When | Request `http://localhost:80/` | Dashboard requested |
| Then | Response is HTTP 200 with HTML content containing the React app | Dashboard served |

**Note:** Port 80 on the host is mapped from port 8000 inside the container, where Uvicorn serves both the API and the built frontend static assets.

**Assertions:**
- [ ] HTTP response status is 200
- [ ] Response Content-Type is `text/html`
- [ ] Response body contains `<div id="root">`

---

### TC0272: Service health check passes via docker compose ps

**Type:** Integration | **Priority:** Critical | **Story:** US0026 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The container is running and has had time to start (up to 30 seconds) | Stack active |
| When | Run `docker compose ps` and inspect the app service health | Health checked |
| Then | App service shows health status as `healthy` | Health check passes |

**Assertions:**
- [ ] `docker compose ps` shows app as `healthy` (not `unhealthy` or `starting`)
- [ ] `docker compose exec app curl -sf http://localhost:8000/api/v1/system/health` returns 200

---

### TC0273: Database persists across down/up cycle

**Type:** Integration | **Priority:** Critical | **Story:** US0026 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The container is running; create a project via POST to the API | Data exists |
| When | Run `docker compose down` followed by `docker compose up -d` and wait for health | Stack restarted |
| Then | The previously created project is still retrievable via GET `/api/v1/projects` | Data persisted |

**Assertions:**
- [ ] GET `/api/v1/projects` returns the project created before the restart
- [ ] Project name, slug, and sdlc_path match the original values
- [ ] The named volume `db-data` (or equivalent) still exists after `docker compose down` (without `-v`)

---

### TC0274: Project volumes mounted read-only in app container

**Type:** Integration | **Priority:** High | **Story:** US0026 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | docker-compose.yml mounts a host project directory into the app container | Volume configured |
| When | Attempt to write a file inside the mounted project directory from within the app container | Write attempted |
| Then | The write operation fails with a read-only filesystem error | Mount is read-only |

**Assertions:**
- [ ] `docker compose exec app touch /data/projects/test-write 2>&1` returns a read-only error
- [ ] Files from the host project directory are readable inside the container
- [ ] `docker compose exec app ls /data/projects/` lists the mounted project directory

---

### TC0275: Environment variables configurable via .env

**Type:** Integration | **Priority:** High | **Story:** US0026 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A `.env` file with `SDLC_LENS_LOG_LEVEL=debug` in the project root | Env file present |
| When | Run `docker compose up -d` | Stack starts with env overrides |
| Then | The app container receives the configured environment variable | Env var applied |

**Assertions:**
- [ ] `docker compose exec app printenv SDLC_LENS_LOG_LEVEL` outputs `debug`
- [ ] `docker compose exec app printenv SDLC_LENS_DATABASE_URL` outputs the configured database URL
- [ ] Application logs show the configured log level in effect

---

### TC0277: docker compose down stops cleanly

**Type:** Integration | **Priority:** High | **Story:** US0026 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The container is running via `docker compose up -d` | Stack active |
| When | Run `docker compose down` | Shutdown initiated |
| Then | The container stops and is removed; `docker compose ps` shows no services | Clean shutdown |

**Assertions:**
- [ ] `docker compose down` exit code is 0
- [ ] `docker compose ps` returns no running services
- [ ] No orphan containers remain from the compose project

---

### TC0278: Container starts within 10 seconds

**Type:** Integration | **Priority:** Medium | **Story:** US0026 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The image is already built (no build time included) | Image cached |
| When | Run `docker compose up -d` and measure time until the service is running | Startup timed |
| Then | The app service reaches `running` state within 10 seconds | Fast startup |

**Assertions:**
- [ ] Time from `docker compose up -d` to the app service showing `running` in `docker compose ps` is under 10 seconds
- [ ] Health check passes within 10 seconds of container start

---

## Fixtures

```bash
# Build the image first (not counted in startup time)
docker compose build

# Start the app service
docker compose up -d

# Wait for health check (up to 30 seconds)
for i in $(seq 1 30); do
  HEALTH=$(docker compose ps --format json | grep -c '"healthy"')
  [ "$HEALTH" -ge 1 ] && break
  sleep 1
done

# Create a test project for persistence tests
curl -sf -X POST http://localhost:80/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Compose Test", "sdlc_path": "/data/projects/test"}'

# Cleanup after all tests
docker compose down
docker volume rm $(docker volume ls -q --filter name=sdlc) 2>/dev/null
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0270 | docker compose up starts the container | Pending | - |
| TC0271 | Dashboard accessible at http://localhost:80 | Pending | - |
| TC0272 | Service health check passes via docker compose ps | Pending | - |
| TC0273 | Database persists across down/up cycle | Pending | - |
| TC0274 | Project volumes mounted read-only in app container | Pending | - |
| TC0275 | Environment variables configurable via .env | Pending | - |
| TC0277 | docker compose down stops cleanly | Pending | - |
| TC0278 | Container starts within 10 seconds | Pending | - |

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
| 2026-02-18 | Claude | Updated for single-container architecture; removed TC0276 (frontend depends_on no longer applicable); renamed services from backend/frontend to app |
