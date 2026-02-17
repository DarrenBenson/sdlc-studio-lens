# TS0026: Docker Compose Orchestration

> **Status:** Draft
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0026 - Docker Compose Orchestration. Covers the docker-compose.yml that brings up both backend and frontend containers with a single command. Tests verify service startup, dashboard accessibility, health checks, database persistence across restart cycles, read-only project volume mounts, environment variable configuration, startup ordering via depends_on, clean shutdown, and startup time. All tests are Docker integration tests requiring Docker and Docker Compose.

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
| US0026 | AC5 | Health checks | TC0272, TC0276 | Pending |

**Coverage:** 5/5 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | No | Infrastructure orchestration, not application code |
| Integration | Yes | Docker Compose service lifecycle and inter-container communication |
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

### TC0270: docker compose up starts both containers

**Type:** Integration | **Priority:** Critical | **Story:** US0026 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A docker-compose.yml exists in the project root | File present |
| When | Run `docker compose up -d` from the project root | Compose starts |
| Then | Both `backend` and `frontend` services are listed as running in `docker compose ps` | Both services up |

**Assertions:**
- [ ] `docker compose up -d` exit code is 0
- [ ] `docker compose ps --format json` shows 2 services
- [ ] Backend service state is `running`
- [ ] Frontend service state is `running`

---

### TC0271: Dashboard accessible at http://localhost:80

**Type:** Integration | **Priority:** Critical | **Story:** US0026 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Both containers are running via `docker compose up -d` | Stack active |
| When | Request `http://localhost:80/` | Dashboard requested |
| Then | Response is HTTP 200 with HTML content containing the React app | Dashboard served |

**Assertions:**
- [ ] HTTP response status is 200
- [ ] Response Content-Type is `text/html`
- [ ] Response body contains `<div id="root">`

---

### TC0272: Backend health check passes via docker compose ps

**Type:** Integration | **Priority:** Critical | **Story:** US0026 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Both containers are running and the backend has had time to start (up to 30 seconds) | Stack active |
| When | Run `docker compose ps` and inspect the backend service health | Health checked |
| Then | Backend service shows health status as `healthy` | Health check passes |

**Assertions:**
- [ ] `docker compose ps` shows backend as `healthy` (not `unhealthy` or `starting`)
- [ ] `docker compose exec backend curl -sf http://localhost:8000/api/v1/system/health` returns 200

---

### TC0273: Database persists across down/up cycle

**Type:** Integration | **Priority:** Critical | **Story:** US0026 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Both containers are running; create a project via POST to the backend API | Data exists |
| When | Run `docker compose down` followed by `docker compose up -d` and wait for health | Stack restarted |
| Then | The previously created project is still retrievable via GET `/api/v1/projects` | Data persisted |

**Assertions:**
- [ ] GET `/api/v1/projects` returns the project created before the restart
- [ ] Project name, slug, and sdlc_path match the original values
- [ ] The named volume `db-data` (or equivalent) still exists after `docker compose down` (without `-v`)

---

### TC0274: Project volumes mounted read-only in backend

**Type:** Integration | **Priority:** High | **Story:** US0026 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | docker-compose.yml mounts a host project directory into the backend container | Volume configured |
| When | Attempt to write a file inside the mounted project directory from within the backend container | Write attempted |
| Then | The write operation fails with a read-only filesystem error | Mount is read-only |

**Assertions:**
- [ ] `docker compose exec backend touch /data/projects/test-write 2>&1` returns a read-only error
- [ ] Files from the host project directory are readable inside the container
- [ ] `docker compose exec backend ls /data/projects/` lists the mounted project directory

---

### TC0275: Environment variables configurable via .env

**Type:** Integration | **Priority:** High | **Story:** US0026 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | A `.env` file with `SDLC_LENS_LOG_LEVEL=debug` in the project root | Env file present |
| When | Run `docker compose up -d` | Stack starts with env overrides |
| Then | The backend container receives the configured environment variable | Env var applied |

**Assertions:**
- [ ] `docker compose exec backend printenv SDLC_LENS_LOG_LEVEL` outputs `debug`
- [ ] `docker compose exec backend printenv SDLC_LENS_DATABASE_URL` outputs the configured database URL
- [ ] Backend logs show the configured log level in effect

---

### TC0276: Frontend depends on backend health (startup ordering)

**Type:** Integration | **Priority:** High | **Story:** US0026 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | docker-compose.yml has `depends_on: backend: condition: service_healthy` for frontend | Dependency configured |
| When | Run `docker compose up -d` and observe startup sequence | Services start |
| Then | Frontend container starts only after backend health check passes | Ordering enforced |

**Assertions:**
- [ ] `docker compose ps` shows backend as `healthy` when frontend is `running`
- [ ] docker-compose.yml contains `condition: service_healthy` in frontend depends_on
- [ ] If backend health check fails, frontend does not reach `running` state

---

### TC0277: docker compose down stops both cleanly

**Type:** Integration | **Priority:** High | **Story:** US0026 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Both containers are running via `docker compose up -d` | Stack active |
| When | Run `docker compose down` | Shutdown initiated |
| Then | Both containers stop and are removed; `docker compose ps` shows no services | Clean shutdown |

**Assertions:**
- [ ] `docker compose down` exit code is 0
- [ ] `docker compose ps` returns no running services
- [ ] No orphan containers remain from the compose project

---

### TC0278: Both containers start within 10 seconds

**Type:** Integration | **Priority:** Medium | **Story:** US0026 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Both images are already built (no build time included) | Images cached |
| When | Run `docker compose up -d` and measure time until both services are running | Startup timed |
| Then | Both services reach `running` state within 10 seconds | Fast startup |

**Assertions:**
- [ ] Time from `docker compose up -d` to both services showing `running` in `docker compose ps` is under 10 seconds
- [ ] Backend health check passes within 10 seconds of container start

---

## Fixtures

```bash
# Build images first (not counted in startup time)
docker compose build

# Start the full stack
docker compose up -d

# Wait for health checks (up to 30 seconds)
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
| TC0270 | docker compose up starts both containers | Pending | - |
| TC0271 | Dashboard accessible at http://localhost:80 | Pending | - |
| TC0272 | Backend health check passes via docker compose ps | Pending | - |
| TC0273 | Database persists across down/up cycle | Pending | - |
| TC0274 | Project volumes mounted read-only in backend | Pending | - |
| TC0275 | Environment variables configurable via .env | Pending | - |
| TC0276 | Frontend depends on backend health | Pending | - |
| TC0277 | docker compose down stops both cleanly | Pending | - |
| TC0278 | Both containers start within 10 seconds | Pending | - |

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
