# US0025: Frontend Dockerfile

> **Status:** Done
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** a multi-stage Dockerfile that builds the React app and serves it via nginx
**So that** the frontend is production-ready and lightweight

## Context

### Persona Reference
**Darren** - Deploys the dashboard on LAN infrastructure.
[Full persona details](../personas.md#darren)

### Background
The frontend Dockerfile uses two stages: first builds the React application with Vite using node:22-slim, second copies the built static files into an nginx:alpine image. The nginx configuration handles SPA routing and API proxying to the backend.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Infrastructure | node:22-slim (build) + nginx:alpine (serve) | Base images locked |
| PRD | KPI | Docker build < 3 minutes | Vite build must be fast |
| TRD | Architecture | nginx proxies /api/* to backend | nginx config handles routing |

---

## Acceptance Criteria

### AC1: Multi-stage build
- **Given** the frontend Dockerfile
- **When** I run `docker build -t sdlc-lens-frontend .`
- **Then** the build completes: stage 1 runs `npm ci && npm run build`, stage 2 copies dist/ to nginx

### AC2: Minimal image size
- **Given** the built image
- **When** I inspect its size
- **Then** the final image is < 50MB (nginx:alpine + static files, no Node.js)

### AC3: SPA routing works
- **Given** the container is running
- **When** I request `/projects/homelabcmd/documents` (a client-side route)
- **Then** nginx returns index.html (not 404), and the React app handles routing

### AC4: Static assets served
- **Given** the container is running
- **When** I request `/assets/main.js` (a Vite build output)
- **Then** nginx serves the file with correct Content-Type and gzip compression

### AC5: nginx configuration included
- **Given** the built image
- **When** the container starts
- **Then** nginx uses the custom configuration for SPA routing and API proxying

---

## Scope

### In Scope
- Multi-stage Dockerfile (build + serve)
- node:22-slim for npm ci + Vite build
- nginx:alpine for static file serving
- Custom nginx.conf copied into image
- .dockerignore for frontend context
- Gzip compression for static assets

### Out of Scope
- nginx API proxy configuration details (US0027)
- Docker Compose orchestration (US0026)
- TLS/HTTPS configuration

---

## Technical Notes

### Dockerfile Structure
```dockerfile
# Stage 1: Build
FROM node:22-slim AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| npm ci fails (missing lock file) | Build fails with clear error |
| Vite build fails (TypeScript errors) | Build fails with Vite error output |
| Very large build output | Still < 50MB for typical React SPA |
| nginx fails to start | Container exits with error in logs |
| Request for non-existent static file | 404 from nginx |

---

## Test Scenarios

- [ ] Docker build completes successfully
- [ ] Build stage uses node:22-slim
- [ ] Serve stage uses nginx:alpine
- [ ] Image size < 50MB
- [ ] Container starts and serves index.html
- [ ] SPA routes return index.html (not 404)
- [ ] Static assets served with correct Content-Type
- [ ] Gzip compression enabled for JS/CSS
- [ ] .dockerignore excludes node_modules, .git

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| All EP0003-EP0005 frontend stories | Code | Working React application | Draft |
| [US0027](US0027-nginx-reverse-proxy-config.md) | Config | nginx.conf file | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Docker | Infrastructure | Available |

---

## Estimation

**Story Points:** {{TBD}}
**Complexity:** Low

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial story creation from EP0006 |
