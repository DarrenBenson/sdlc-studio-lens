# US0026: Docker Compose Orchestration

> **Status:** Done
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** a docker-compose.yml that starts the application container with database persistence and project volumes
**So that** I can deploy the full dashboard with a single command

## Context

### Persona Reference
**Darren** - Expects `docker-compose up` to bring up the full stack with minimal configuration.
[Full persona details](../personas.md#darren)

### Background
The docker-compose.yml orchestrates a single application container where FastAPI serves both the API and the pre-built frontend static files. Configuration includes a named volume for the SQLite database and configurable bind mounts for project sdlc-studio directories. Environment variables are passed to the container for configuration.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Architecture | Single container (FastAPI serves API + frontend) | One service in compose |
| PRD | Architecture | Data persists across container restarts | Named volume for database |
| PRD | Architecture | Project directories as Docker volumes (read-only) | Bind mounts |

---

## Acceptance Criteria

### AC1: Single command deployment
- **Given** a docker-compose.yml in the project root
- **When** I run `docker-compose up`
- **Then** the container starts and the dashboard is accessible at http://localhost:80

### AC2: Database persistence
- **Given** the container is running and data has been synced
- **When** I run `docker-compose down` and then `docker-compose up`
- **Then** previously synced data is still available (SQLite database persisted via named volume)

### AC3: Project volume mounts
- **Given** a docker-compose.yml with project volume configuration
- **When** the container starts
- **Then** the project sdlc-studio directories are accessible at the configured mount paths (read-only)

### AC4: Environment variable pass-through
- **Given** environment variables defined in docker-compose.yml or .env file
- **When** the container starts
- **Then** SDLC_LENS_HOST, SDLC_LENS_PORT, SDLC_LENS_DATABASE_URL, and SDLC_LENS_LOG_LEVEL are available to the application

### AC5: Health check
- **Given** the container is running
- **When** I run `docker-compose ps`
- **Then** the service shows as healthy (health check at /api/v1/system/health)

---

## Scope

### In Scope
- docker-compose.yml with a single application service
- Named volume for SQLite database (/data/db)
- Bind mount configuration for project directories
- Environment variable configuration
- Health check for the application service

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
  app:
    build: .
    ports:
      - "80:8000"
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

volumes:
  db-data:
```

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Health check fails | docker-compose reports unhealthy |
| Volume mount path does not exist on host | Container starts but sync will fail for that project |
| Port 80 already in use | docker-compose up fails with port conflict error |
| .env file missing | Defaults used from application config |
| Database volume deleted | Fresh database created on next startup; Alembic migrations run |
| Container restarted | Data persists via named volume |

---

## Test Scenarios

- [ ] docker-compose up starts the container
- [ ] Dashboard accessible at http://localhost:80
- [ ] Health check passes at /api/v1/system/health
- [ ] Database persists across docker-compose down/up cycle
- [ ] Project volumes mounted read-only in the container
- [ ] Environment variables configurable
- [ ] docker-compose down stops the container cleanly
- [ ] Container starts within 10 seconds

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0024](US0024-backend-dockerfile.md) | Config | Combined Dockerfile (API + frontend) | Draft |

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
| 2026-02-18 | Claude | Updated for single-container architecture (FastAPI serves API + frontend) |
