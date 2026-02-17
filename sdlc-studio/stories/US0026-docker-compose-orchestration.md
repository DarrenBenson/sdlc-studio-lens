# US0026: Docker Compose Orchestration

> **Status:** Draft
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** a docker-compose.yml that starts both containers with database persistence and project volumes
**So that** I can deploy the full dashboard with a single command

## Context

### Persona Reference
**Darren** - Expects `docker-compose up` to bring up the full stack with minimal configuration.
[Full persona details](../personas.md#darren)

### Background
The docker-compose.yml orchestrates both the backend and frontend containers with a shared Docker network, a named volume for the SQLite database, and configurable bind mounts for project sdlc-studio directories. Environment variables are passed to the backend for configuration.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Architecture | Two containers (backend + frontend/nginx) | Two services in compose |
| PRD | Architecture | Data persists across container restarts | Named volume for database |
| PRD | Architecture | Project directories as Docker volumes (read-only) | Bind mounts |

---

## Acceptance Criteria

### AC1: Single command deployment
- **Given** a docker-compose.yml in the project root
- **When** I run `docker-compose up`
- **Then** both backend and frontend containers start and the dashboard is accessible at http://localhost:80

### AC2: Database persistence
- **Given** both containers are running and data has been synced
- **When** I run `docker-compose down` and then `docker-compose up`
- **Then** previously synced data is still available (SQLite database persisted via named volume)

### AC3: Project volume mounts
- **Given** a docker-compose.yml with project volume configuration
- **When** the backend container starts
- **Then** the project sdlc-studio directories are accessible at the configured mount paths (read-only)

### AC4: Environment variable pass-through
- **Given** environment variables defined in docker-compose.yml or .env file
- **When** the backend container starts
- **Then** SDLC_LENS_HOST, SDLC_LENS_PORT, SDLC_LENS_DATABASE_URL, and SDLC_LENS_LOG_LEVEL are available to the application

### AC5: Health checks
- **Given** both containers are running
- **When** I run `docker-compose ps`
- **Then** both services show as healthy (backend health check at /api/v1/system/health, frontend health check via nginx)

---

## Scope

### In Scope
- docker-compose.yml with backend and frontend services
- Shared Docker network
- Named volume for SQLite database (/data/db)
- Bind mount configuration for project directories
- Environment variable configuration
- Health checks for both services
- depends_on with health condition for startup ordering
- .env file template for configuration

### Out of Scope
- Docker Swarm or Kubernetes
- Automated backup
- TLS/HTTPS
- CI/CD pipeline integration

---

## Technical Notes

### docker-compose.yml Structure
```yaml
services:
  backend:
    build: ./backend
    volumes:
      - db-data:/data/db
      - /path/to/project1/sdlc-studio:/data/projects/project1/sdlc-studio:ro
    environment:
      - SDLC_LENS_DATABASE_URL=sqlite:///data/db/sdlc_lens.db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/system/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy

volumes:
  db-data:
```

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Backend health check fails | Frontend waits; docker-compose reports unhealthy |
| Volume mount path does not exist on host | Container starts but sync will fail for that project |
| Port 80 already in use | docker-compose up fails with port conflict error |
| .env file missing | Defaults used from application config |
| Database volume deleted | Fresh database created on next startup; Alembic migrations run |
| Containers restarted individually | Data persists; services reconnect |

---

## Test Scenarios

- [ ] docker-compose up starts both containers
- [ ] Dashboard accessible at http://localhost:80
- [ ] Backend health check passes
- [ ] Database persists across docker-compose down/up cycle
- [ ] Project volumes mounted read-only in backend
- [ ] Environment variables configurable
- [ ] Frontend depends_on backend health
- [ ] docker-compose down stops both containers cleanly
- [ ] Containers start within 10 seconds

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0024](US0024-backend-dockerfile.md) | Config | Backend Dockerfile | Draft |
| [US0025](US0025-frontend-dockerfile.md) | Config | Frontend Dockerfile | Draft |
| [US0027](US0027-nginx-reverse-proxy-config.md) | Config | nginx configuration | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Docker and docker-compose | Infrastructure | Available |

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
