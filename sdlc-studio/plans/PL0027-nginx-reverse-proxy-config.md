# PL0027: Nginx Reverse Proxy Configuration - Implementation Plan

> **Status:** Draft
> **Story:** [US0027: Nginx Reverse Proxy Configuration](../stories/US0027-nginx-reverse-proxy-config.md)
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Created:** 2026-02-17
> **Language:** Nginx Configuration

## Overview

Create an `nginx.conf` file at `frontend/nginx.conf` that serves as the routing layer for the containerised application. The configuration handles three responsibilities: (1) proxy `/api/` requests to the backend container at `http://backend:8000`, (2) serve Vite-built static assets from `/assets/` with long-lived cache headers, and (3) fall back to `index.html` for all other paths to support React Router's client-side routing. Gzip compression is enabled for text, CSS, JavaScript, and JSON responses. Proxy headers preserve client IP and hostname information.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | API proxy | `/api/v1/projects` proxied to `http://backend:8000/api/v1/projects`; response returned to client |
| AC2 | SPA fallback routing | `/projects/homelabcmd/documents` returns index.html with status 200 |
| AC3 | Static asset serving | `/assets/main-abc123.js` served with correct Content-Type and cache headers |
| AC4 | Gzip compression | JS and CSS files served with gzip when client accepts it |
| AC5 | API error passthrough | Backend 404 errors passed through to client (nginx does not intercept) |

---

## Technical Context

### Language & Framework
- **Server:** nginx (alpine variant in Docker)
- **Configuration:** `nginx.conf` as server block (loaded as `/etc/nginx/conf.d/default.conf`)
- **Upstream:** Backend container accessible at `http://backend:8000` via Docker network DNS
- **Document root:** `/usr/share/nginx/html` (Vite build output from US0025)

### Existing Patterns

The Docker Compose network (US0026) provides DNS resolution for service names. The backend service is named `backend` and listens on port 8000. All API routes are prefixed with `/api/v1/`. Vite places hashed assets in `/assets/` and the root `index.html` references them.

### Dependencies
- **US0024 (Backend Dockerfile):** Defines the backend container name and port
- **US0025 (Frontend Dockerfile):** Copies this nginx.conf into the frontend image
- **US0026 (Docker Compose):** Provides the Docker network where `backend` hostname resolves

---

## Recommended Approach

**Strategy:** TDD (Integration)
**Rationale:** nginx configuration is best validated by running the full Docker Compose stack and making HTTP requests to verify routing, proxying, compression, and caching behaviour. Static analysis of nginx.conf can catch syntax errors (`nginx -t`) but not runtime behaviour.

### Test Priority
1. nginx syntax validation (`nginx -t`)
2. API proxy routes correctly to backend
3. SPA fallback returns index.html for client routes
4. Static assets served with cache headers
5. Gzip compression active
6. Backend errors passed through
7. Proxy headers forwarded

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Create nginx.conf with server block | `frontend/nginx.conf` | - | [ ] |
| 2 | Configure /api/ location (proxy_pass) | `frontend/nginx.conf` | - | [ ] |
| 3 | Configure /assets/ location (cache headers) | `frontend/nginx.conf` | - | [ ] |
| 4 | Configure / location (SPA fallback) | `frontend/nginx.conf` | - | [ ] |
| 5 | Configure gzip compression | `frontend/nginx.conf` | - | [ ] |
| 6 | Configure proxy headers | `frontend/nginx.conf` | - | [ ] |
| 7 | Validate syntax with nginx -t | manual | 1-6 | [ ] |
| 8 | Integration test with Docker Compose | manual | US0024, US0025, US0026 | [ ] |

---

## Implementation Phases

### Phase 1: Create nginx.conf

**Goal:** Complete nginx configuration covering all routing, caching, compression, and proxying requirements.

- [ ] Create `frontend/nginx.conf`:

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # ------------------------------------------------------------------
    # Gzip compression
    # ------------------------------------------------------------------
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_min_length 256;
    gzip_types
        text/plain
        text/css
        text/xml
        application/json
        application/javascript
        application/xml
        image/svg+xml;

    # ------------------------------------------------------------------
    # API reverse proxy
    # ------------------------------------------------------------------
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Do not intercept backend error responses
        proxy_intercept_errors off;

        # Timeouts
        proxy_connect_timeout 10s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }

    # ------------------------------------------------------------------
    # Static assets (Vite hashed filenames - long cache)
    # ------------------------------------------------------------------
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # ------------------------------------------------------------------
    # SPA fallback (React Router)
    # ------------------------------------------------------------------
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**Design decisions:**

- **`server_name _`:** Catch-all; matches any hostname (appropriate for LAN deployment).
- **`proxy_pass http://backend:8000`:** No trailing slash. The full URI (including `/api/`) is forwarded to the backend. This matches the backend's route prefix `/api/v1/...`.
- **`proxy_intercept_errors off`:** Backend error responses (404, 422, 500) pass through unchanged to the client. Nginx does not replace them with its own error pages.
- **`proxy_set_header X-Forwarded-Proto $scheme`:** Preserves the original protocol for any future HTTPS setup.
- **`gzip_vary on`:** Sends `Vary: Accept-Encoding` so caches store both compressed and uncompressed versions.
- **`gzip_proxied any`:** Compresses responses for proxied requests too.
- **`gzip_min_length 256`:** Skips compression for tiny responses where overhead exceeds benefit.
- **`expires 1y` on /assets/:** Vite uses content-hashed filenames, so long cache is safe. Changed files get new hashes.
- **`add_header Cache-Control "public, immutable"`:** Browsers never revalidate hashed assets.
- **`access_log off` on /assets/:** Reduces log noise from static asset requests.
- **`try_files $uri $uri/ /index.html`:** Standard SPA fallback. Existing files are served directly; everything else returns index.html for React Router.
- **Proxy timeouts:** `connect_timeout 10s` fails fast if backend is unreachable; `read_timeout 60s` allows for slow sync operations.

**Files:**
- `frontend/nginx.conf`

### Phase 2: Verification with Docker

**Goal:** Validate the configuration in the running Docker Compose stack.

- [ ] Syntax check: `docker run --rm -v $(pwd)/frontend/nginx.conf:/etc/nginx/conf.d/default.conf:ro nginx:alpine nginx -t`
- [ ] Start full stack: `docker-compose up -d --build`
- [ ] Test API proxy: `curl -f http://localhost/api/v1/system/health` returns 200 with JSON body
- [ ] Test API proxy (projects): `curl -f http://localhost/api/v1/projects` returns 200
- [ ] Test SPA fallback: `curl -s -o /dev/null -w "%{http_code}" http://localhost/projects/test/documents` returns 200
- [ ] Verify SPA response is HTML: `curl -s http://localhost/projects/test/documents | head -1` contains `<!DOCTYPE html>`
- [ ] Test static assets: `curl -I http://localhost/assets/` (check for hashed JS file Content-Type)
- [ ] Verify cache headers: `curl -I http://localhost/assets/index-*.js` includes `Cache-Control: public, immutable` and `Expires` header
- [ ] Test gzip: `curl -H "Accept-Encoding: gzip" -I http://localhost/assets/index-*.js` includes `Content-Encoding: gzip`
- [ ] Test API error passthrough: `curl -s -w "%{http_code}" http://localhost/api/v1/projects/nonexistent` returns 404 with JSON error body
- [ ] Test backend down: `docker-compose stop backend && curl -s -w "%{http_code}" http://localhost/api/v1/system/health` returns 502
- [ ] Verify proxy headers: check backend logs for X-Forwarded-For and X-Real-IP
- [ ] Root path: `curl -f http://localhost/` returns index.html
- [ ] Non-existent static file: `curl -s -w "%{http_code}" http://localhost/assets/nonexistent.js` returns 404
- [ ] Clean up: `docker-compose down`

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | `curl /api/v1/system/health` returns backend response | `location /api/` block | Pending |
| AC2 | `curl /projects/*/documents` returns index.html | `location /` with try_files | Pending |
| AC3 | `curl -I /assets/*.js` shows Content-Type and Cache-Control | `location /assets/` block | Pending |
| AC4 | `curl -H "Accept-Encoding: gzip"` shows Content-Encoding: gzip | `gzip on` directives | Pending |
| AC5 | `curl /api/v1/projects/nonexistent` returns 404 JSON | `proxy_intercept_errors off` | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | Backend container not running | `/api/*` requests return 502 Bad Gateway from nginx; frontend static routes unaffected | Phase 2 |
| 2 | Backend slow to respond | `proxy_read_timeout 60s` waits up to 60 seconds; returns 504 Gateway Timeout if exceeded | Phase 1 |
| 3 | Request to `/api` without trailing content | Proxied to backend which returns its own response (typically 404 or redirect) | Phase 1 |
| 4 | Large request body (future consideration) | nginx default `client_max_body_size` of 1MB applies; acceptable for read-only dashboard (no uploads) | Phase 1 |
| 5 | WebSocket upgrade request (future) | Not configured; connection upgrade fails; acceptable for v1.0 (no WebSocket features) | Phase 1 |
| 6 | Concurrent requests | nginx handles concurrently via event-driven architecture; `worker_connections` default (1024) is sufficient for LAN use | Phase 1 |
| 7 | Favicon request | Served from `/usr/share/nginx/html/favicon.ico` if present in Vite build output; otherwise falls through to index.html via try_files (React app handles 404 display) | Phase 2 |

**Coverage:** 7/7 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `proxy_pass` URI handling incorrect (double `/api/` prefix) | High | Use `proxy_pass http://backend:8000` without trailing slash so the full request URI is forwarded unchanged |
| Gzip not working for proxied responses | Medium | `gzip_proxied any` ensures proxied responses are compressed; verify with curl |
| Cache headers applied to index.html | High | Cache headers only on `/assets/` location; index.html served from `/` location without cache headers |
| Backend hostname unresolvable outside Docker | Low | Configuration only applies inside Docker Compose network; local development uses Vite proxy instead |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Integration tests pass (API proxy, SPA routing, gzip, cache headers)
- [ ] Edge cases handled
- [ ] nginx -t syntax validation passes
- [ ] API errors from backend pass through to client unchanged
- [ ] Gzip compression active for JS, CSS, and JSON
- [ ] Cache-Control headers on /assets/ with 1-year expiry
- [ ] Proxy headers (X-Forwarded-For, X-Real-IP, Host) forwarded to backend
