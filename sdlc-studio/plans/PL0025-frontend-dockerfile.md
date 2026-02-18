# PL0025: Frontend Dockerfile - Implementation Plan [SUPERSEDED]

> **Status:** Superseded
> **Story:** [US0025: Frontend Dockerfile](../stories/US0025-frontend-dockerfile.md)
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Created:** 2026-02-17
> **Superseded:** 2026-02-18
> **Superseded By:** [PL0024: Combined Dockerfile](PL0024-backend-dockerfile.md)
> **Language:** Dockerfile

> **Supersession Note:** The frontend build is now a stage in the combined Dockerfile (PL0024). The single-container architecture eliminates the need for a separate frontend image and nginx. Original plan preserved below for reference.

## Overview

Create a multi-stage Dockerfile for the React frontend. The build stage uses `node:22-slim` to run `npm ci && npm run build`, producing a Vite static build in `dist/`. The serve stage copies the build output into `nginx:alpine` and includes the custom `nginx.conf` from US0027. A `.dockerignore` excludes development artefacts from the build context. The final image is under 50MB with no Node.js runtime.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Multi-stage build | `docker build -t sdlc-lens-frontend .` completes: stage 1 npm ci + build, stage 2 copies dist to nginx |
| AC2 | Minimal image size | Final image < 50MB (nginx:alpine + static files, no Node.js) |
| AC3 | SPA routing works | `/projects/homelabcmd/documents` returns index.html (not 404) |
| AC4 | Static assets served | `/assets/main.js` served with correct Content-Type and gzip |
| AC5 | nginx configuration included | Container uses custom nginx.conf for SPA routing and API proxying |

---

## Technical Context

### Language & Framework
- **Build:** Node.js 22 (node:22-slim), npm ci, Vite 7 with TypeScript
- **Serve:** nginx:alpine
- **Build command:** `tsc -b && vite build` (via `npm run build`)
- **Output:** `dist/` directory with index.html and `assets/` subdirectory

### Existing Patterns

The frontend build script in `package.json` is `"build": "tsc -b && vite build"`. Vite produces hashed filenames in `dist/assets/` (e.g., `main-abc123.js`). The `nginx.conf` (created in US0027) handles SPA fallback routing, API proxying, and static asset caching.

### Dependencies
- **US0027 (nginx.conf):** The nginx configuration file must exist at `frontend/nginx.conf` before this Dockerfile can be built. US0027 should be implemented first or concurrently.

---

## Recommended Approach

**Strategy:** TDD (Integration)
**Rationale:** Dockerfile behaviour is validated by building the image and running the container. Verification includes image size checks, HTTP requests for SPA routes, and Content-Type validation for static assets.

### Test Priority
1. Dockerfile builds without errors
2. Image size within limit (< 50MB)
3. Container starts and serves index.html
4. SPA routes return index.html (not 404)
5. Static assets served with correct headers

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Create frontend Dockerfile (multi-stage) | `frontend/Dockerfile` | US0027 (nginx.conf) | [ ] |
| 2 | Create/update .dockerignore for frontend | `frontend/.dockerignore` | - | [ ] |
| 3 | Verify build completes | manual | 1, 2 | [ ] |
| 4 | Verify container serves index.html | manual | 3 | [ ] |
| 5 | Verify SPA routing | manual | 4 | [ ] |
| 6 | Verify image size < 50MB | manual | 3 | [ ] |

---

## Implementation Phases

### Phase 1: Dockerfile

**Goal:** Multi-stage Dockerfile that builds the React app and serves via nginx.

- [ ] Create `frontend/Dockerfile`:
  - **Stage 1 (builder):** `FROM node:22-slim AS builder`
    - `WORKDIR /app`
    - Copy `package.json` and `package-lock.json` first (dependency cache layer)
    - `RUN npm ci` (clean install from lockfile)
    - Copy remaining source files
    - `RUN npm run build` (produces `dist/`)
  - **Stage 2 (serve):** `FROM nginx:alpine`
    - Copy `dist/` from builder to `/usr/share/nginx/html`
    - Copy `nginx.conf` to `/etc/nginx/conf.d/default.conf`
    - `EXPOSE 80`
    - Default CMD from nginx:alpine base (nginx in foreground)

  **Layer ordering for cache efficiency:**
  1. Base image (node:22-slim)
  2. `package.json` + `package-lock.json` (dependency definition layer)
  3. `npm ci` (cached if lockfile unchanged)
  4. Source code (changes frequently)
  5. `npm run build`
  6. nginx:alpine base
  7. Copy static output

**Dockerfile structure:**

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

**Files:**
- `frontend/Dockerfile`

### Phase 2: .dockerignore

**Goal:** Exclude development artefacts from build context to speed up builds and reduce image size.

- [ ] Create `frontend/.dockerignore`:
  ```
  node_modules/
  dist/
  .git/
  .gitignore
  test/
  *.test.ts
  *.test.tsx
  .vscode/
  .idea/
  coverage/
  README.md
  eslint.config.js
  tsconfig.node.json
  vite.config.ts
  ```

  Note: `vite.config.ts` is needed at build time for the Vite build. It should NOT be excluded. Corrected list:

  ```
  node_modules/
  dist/
  .git/
  .gitignore
  test/
  *.test.ts
  *.test.tsx
  .vscode/
  .idea/
  coverage/
  README.md
  ```

  Note: `eslint.config.js`, `tsconfig.node.json`, and `vite.config.ts` are required for the build process (`tsc -b` reads tsconfig, Vite reads vite.config.ts). Keep them in the context.

**Files:**
- `frontend/.dockerignore`

### Phase 3: Testing and Validation

**Goal:** Verify build, image size, and runtime behaviour.

- [ ] Build image: `docker build -t sdlc-lens-frontend ./frontend`
- [ ] Verify build completes without errors
- [ ] Check image size: `docker image inspect sdlc-lens-frontend --format='{{.Size}}'` < 50MB
- [ ] Run container: `docker run -d --name test-frontend -p 8080:80 sdlc-lens-frontend`
- [ ] Verify root: `curl -f http://localhost:8080/` returns index.html
- [ ] Verify SPA route: `curl -f http://localhost:8080/projects/test/documents` returns index.html
- [ ] Verify static asset: `curl -I http://localhost:8080/assets/` returns files with correct Content-Type
- [ ] Verify no Node.js in final image: `docker exec test-frontend which node` returns not found
- [ ] Clean up: `docker stop test-frontend && docker rm test-frontend`

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | `docker build` completes with two stages | `frontend/Dockerfile` | Pending |
| AC2 | `docker image inspect` size < 50MB | `frontend/Dockerfile` | Pending |
| AC3 | `curl /projects/*/documents` returns index.html | `frontend/nginx.conf` (US0027) | Pending |
| AC4 | `curl /assets/*.js` returns correct Content-Type | `frontend/nginx.conf` (US0027) | Pending |
| AC5 | nginx uses custom config | `COPY nginx.conf` in Dockerfile | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | npm ci fails (missing or out-of-sync lock file) | Build fails with clear npm error; developer must run `npm install` to regenerate lock file | Phase 1 |
| 2 | Vite build fails (TypeScript errors) | `tsc -b` step fails first with type errors; build aborts with non-zero exit | Phase 1 |
| 3 | Very large build output | Vite tree-shakes and minifies; typical React SPA is 1-3MB; well within 50MB limit | Phase 1 |
| 4 | nginx fails to start (bad config) | Container exits immediately; error visible in `docker logs`; fix nginx.conf and rebuild | Phase 3 |
| 5 | Request for non-existent static file | nginx returns 404 (correct behaviour; `try_files` only falls back to index.html for non-asset paths) | Phase 3 |

**Coverage:** 5/5 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| nginx.conf not yet created (US0027 dependency) | High | Implement US0027 first; or stub nginx.conf for initial build testing |
| npm ci slow on first build (no cache) | Low | Lockfile layer caching means subsequent builds only re-run npm ci if dependencies change |
| Vite base path misconfigured | Medium | Default base `/` is correct for nginx serving from root; no changes needed |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Integration tests pass (Docker build + run)
- [ ] Edge cases handled
- [ ] .dockerignore covers node_modules, tests, and development files
- [ ] Image size < 50MB
- [ ] SPA routing works for client-side routes
- [ ] Static assets served with correct Content-Type
