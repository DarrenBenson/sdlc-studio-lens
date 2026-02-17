# TS0025: Frontend Dockerfile

> **Status:** Draft
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0025 - Frontend Dockerfile. Covers the multi-stage Docker build that compiles the React application with Vite (node:22-slim) and serves it via nginx:alpine. Tests verify image size, correct base images at each stage, SPA routing, static asset serving, and .dockerignore exclusions. All tests are Docker integration tests requiring a working Docker installation.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0025](../stories/US0025-frontend-dockerfile.md) | Frontend Dockerfile | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0025 | AC1 | Multi-stage build | TC0262, TC0263 | Pending |
| US0025 | AC2 | Minimal image size | TC0264, TC0265 | Pending |
| US0025 | AC3 | SPA routing works | TC0267 | Pending |
| US0025 | AC4 | Static assets served | TC0266, TC0268 | Pending |
| US0025 | AC5 | nginx configuration included | TC0266, TC0267 | Pending |

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
| Test Data | None (Vite builds from source) |

---

## Test Cases

### TC0262: Multi-stage build completes successfully

**Type:** Integration | **Priority:** Critical | **Story:** US0025 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The frontend Dockerfile exists at `frontend/Dockerfile` | File present |
| When | Run `docker build -t sdlc-lens-frontend ./frontend` | Build executes |
| Then | Build exits with code 0 and image tagged `sdlc-lens-frontend` appears in `docker images` | Image created |

**Assertions:**
- [ ] `docker build` exit code is 0
- [ ] `docker images sdlc-lens-frontend --format '{{.Repository}}'` returns `sdlc-lens-frontend`
- [ ] Build output shows at least two FROM stages (builder + serve)

---

### TC0263: Build stage uses node:22-slim

**Type:** Integration | **Priority:** High | **Story:** US0025 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The frontend Dockerfile | File readable |
| When | Inspect the Dockerfile content for the build stage FROM directive | Stage base identified |
| Then | The build stage uses `node:22-slim` as its base image | Correct build base |

**Assertions:**
- [ ] Dockerfile contains `FROM node:22-slim` (or `node:22-slim AS builder`)
- [ ] The final image does not contain `node` or `npm` binaries (build tools excluded from serve stage)

---

### TC0264: Serve stage uses nginx:alpine

**Type:** Integration | **Priority:** High | **Story:** US0025 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The `sdlc-lens-frontend` image has been built | Image exists |
| When | Run `docker run --rm sdlc-lens-frontend nginx -v` | Version retrieved |
| Then | Output shows nginx version, confirming nginx:alpine is the runtime base | Correct serve base |

**Assertions:**
- [ ] `nginx -v` outputs a version string (e.g., `nginx/1.x.x`)
- [ ] Image does not contain Node.js runtime (`node --version` fails)

---

### TC0265: Image size under 50MB

**Type:** Integration | **Priority:** High | **Story:** US0025 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The `sdlc-lens-frontend` image has been built | Image exists |
| When | Run `docker images sdlc-lens-frontend --format '{{.Size}}'` | Size retrieved |
| Then | Reported size is less than 50MB | Image is minimal |

**Assertions:**
- [ ] Image size in bytes is less than 52,428,800 (50 * 1024 * 1024)

---

### TC0266: Container starts and serves index.html at /

**Type:** Integration | **Priority:** Critical | **Story:** US0025 AC4, AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The `sdlc-lens-frontend` image has been built | Image ready |
| When | Run `docker run -d -p 8080:80 --name frontend-test sdlc-lens-frontend` and request `http://localhost:8080/` | Container starts |
| Then | Response is HTTP 200 with HTML content containing the React app mount point | Index page served |

**Assertions:**
- [ ] HTTP response status is 200
- [ ] Response Content-Type is `text/html`
- [ ] Response body contains `<div id="root">` (React mount point)
- [ ] Container status is `running`

---

### TC0267: SPA routes return index.html (not 404)

**Type:** Integration | **Priority:** Critical | **Story:** US0025 AC3, AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The `sdlc-lens-frontend` container is running on port 8080 | Container active |
| When | Request `http://localhost:8080/projects/homelabcmd/documents` (a client-side route) | SPA route requested |
| Then | Response is HTTP 200 with index.html content, not a 404 error | SPA fallback works |

**Assertions:**
- [ ] HTTP response status is 200 (not 404)
- [ ] Response body contains `<div id="root">`
- [ ] Requesting `/settings` also returns 200 with index.html
- [ ] Requesting `/search?q=test` also returns 200 with index.html

---

### TC0268: Static assets served with correct Content-Type

**Type:** Integration | **Priority:** High | **Story:** US0025 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The `sdlc-lens-frontend` container is running on port 8080 | Container active |
| When | Request a JS asset file from `/assets/` (discover filename from index.html script tag) | Asset requested |
| Then | Response is HTTP 200 with Content-Type `application/javascript` | Correct MIME type |

**Assertions:**
- [ ] JS files return Content-Type containing `application/javascript` or `text/javascript`
- [ ] CSS files (if separate) return Content-Type containing `text/css`
- [ ] Response body is non-empty and contains valid content

---

### TC0269: .dockerignore excludes node_modules, .git

**Type:** Integration | **Priority:** Medium | **Story:** US0025 (build hygiene)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | The `sdlc-lens-frontend` container is running | Container active |
| When | Check for excluded paths inside the container filesystem | Search for artefacts |
| Then | `node_modules/` and `.git/` directories do not exist in the served content | Excluded correctly |

**Assertions:**
- [ ] `curl -sf http://localhost:8080/node_modules/` returns 404 or 403
- [ ] `curl -sf http://localhost:8080/.git/` returns 404 or 403
- [ ] The nginx html root does not contain source TypeScript files

---

## Fixtures

```bash
# Build the frontend image
docker build -t sdlc-lens-frontend ./frontend

# Start a container for testing (port 8080 to avoid conflicts)
docker run -d -p 8080:80 --name frontend-test sdlc-lens-frontend

# Wait for nginx to be ready
for i in $(seq 1 10); do
  curl -sf http://localhost:8080/ && break
  sleep 1
done

# Discover asset filenames from index.html
ASSET_JS=$(curl -s http://localhost:8080/ | grep -oP '/assets/[^"]+\.js' | head -1)

# Cleanup after all tests
docker stop frontend-test 2>/dev/null
docker rm frontend-test 2>/dev/null
docker rmi sdlc-lens-frontend 2>/dev/null
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0262 | Multi-stage build completes successfully | Pending | - |
| TC0263 | Build stage uses node:22-slim | Pending | - |
| TC0264 | Serve stage uses nginx:alpine | Pending | - |
| TC0265 | Image size under 50MB | Pending | - |
| TC0266 | Container starts and serves index.html | Pending | - |
| TC0267 | SPA routes return index.html (not 404) | Pending | - |
| TC0268 | Static assets served with correct Content-Type | Pending | - |
| TC0269 | .dockerignore excludes node_modules, .git | Pending | - |

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
