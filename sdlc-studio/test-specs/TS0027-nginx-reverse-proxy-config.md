# TS0027: Nginx Reverse Proxy Configuration [SUPERSEDED]

> **Status:** Superseded
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-18
> **Superseded By:** [TS0024: Combined Dockerfile](TS0024-backend-dockerfile.md)

> **Supersession Note:** The single-container architecture eliminates nginx. SPA routing is now tested via FastAPI's catch-all route in TS0024. API proxying tests are no longer needed since API and frontend are served from the same process. Original spec preserved below for reference.

## Overview

Test specification for US0027 - Nginx Reverse Proxy Configuration. Covers the nginx.conf that routes API requests to the backend container and serves the React SPA for all other paths. Tests verify API proxying, SPA fallback routing, static asset serving with correct MIME types, gzip compression, cache headers, error passthrough when the backend is down, and root path serving. All tests are Docker integration tests requiring the full stack via Docker Compose.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0027](../stories/US0027-nginx-reverse-proxy-config.md) | Nginx Reverse Proxy Configuration | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0027 | AC1 | API proxy | TC0279, TC0280 | Pending |
| US0027 | AC2 | SPA fallback routing | TC0281, TC0286 | Pending |
| US0027 | AC3 | Static asset serving | TC0282, TC0284 | Pending |
| US0027 | AC4 | Gzip compression | TC0283 | Pending |
| US0027 | AC5 | API error passthrough | TC0285 | Pending |

**Coverage:** 5/5 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | No | Infrastructure config, not application code |
| Integration | Yes | Nginx routing behaviour with live backend container |
| E2E | No | Covered by integration tests through nginx |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Docker 24+, Docker Compose v2+, curl |
| External Services | None |
| Test Data | None (tests use system endpoints and static assets) |

---

## Test Cases

### TC0279: /api/v1/system/health proxied to backend successfully

**Type:** Integration | **Priority:** Critical | **Story:** US0027 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Both containers are running via `docker compose up -d` and backend is healthy | Stack active |
| When | Request `http://localhost:80/api/v1/system/health` (through nginx on port 80) | API request via nginx |
| Then | Response is HTTP 200 with JSON health status from the backend | Proxy works |

**Assertions:**
- [ ] HTTP response status is 200
- [ ] Response Content-Type is `application/json`
- [ ] Response body contains health status fields matching the backend's direct response
- [ ] Response does not contain nginx error page HTML

---

### TC0280: /api/v1/projects proxied to backend

**Type:** Integration | **Priority:** Critical | **Story:** US0027 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Both containers are running and backend is healthy | Stack active |
| When | Request `http://localhost:80/api/v1/projects` through nginx | API list request |
| Then | Response is HTTP 200 with JSON array from the backend projects endpoint | Proxy forwards correctly |

**Assertions:**
- [ ] HTTP response status is 200
- [ ] Response Content-Type is `application/json`
- [ ] Response body is a valid JSON array (empty or with project objects)
- [ ] Backend receives the request (visible in backend logs or response content)

---

### TC0281: /projects/slug/documents returns index.html (SPA routing)

**Type:** Integration | **Priority:** Critical | **Story:** US0027 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Both containers are running | Stack active |
| When | Request `http://localhost:80/projects/homelabcmd/documents` (a client-side route, not /api/) | SPA route requested |
| Then | Response is HTTP 200 with index.html content (nginx try_files fallback) | SPA fallback works |

**Assertions:**
- [ ] HTTP response status is 200 (not 404)
- [ ] Response Content-Type is `text/html`
- [ ] Response body contains `<div id="root">`
- [ ] The path `/projects/homelabcmd/documents` is not intercepted by the API proxy

---

### TC0282: /assets/*.js served with correct Content-Type

**Type:** Integration | **Priority:** High | **Story:** US0027 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Both containers are running; discover a JS asset filename from index.html | Asset path known |
| When | Request `http://localhost:80/assets/<filename>.js` | Static asset requested |
| Then | Response is HTTP 200 with Content-Type `application/javascript` | Correct MIME type |

**Assertions:**
- [ ] HTTP response status is 200
- [ ] Response Content-Type contains `application/javascript` or `text/javascript`
- [ ] Response body is non-empty and contains JavaScript content
- [ ] Request is served by nginx directly (not proxied to backend)

---

### TC0283: Gzip compression active for JS files

**Type:** Integration | **Priority:** High | **Story:** US0027 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Both containers are running | Stack active |
| When | Request a JS asset with `Accept-Encoding: gzip` header via `curl -H "Accept-Encoding: gzip" -sI http://localhost:80/assets/<filename>.js` | Gzip-capable request |
| Then | Response includes `Content-Encoding: gzip` header | Compression active |

**Assertions:**
- [ ] Response header `Content-Encoding` is `gzip`
- [ ] Compressed response is smaller than the uncompressed asset size
- [ ] Gzip also applies to CSS files (if present)
- [ ] Gzip applies to `application/json` responses from the API proxy

---

### TC0284: Cache-Control headers on /assets/ files

**Type:** Integration | **Priority:** High | **Story:** US0027 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Both containers are running | Stack active |
| When | Request a JS asset and inspect response headers via `curl -sI http://localhost:80/assets/<filename>.js` | Headers inspected |
| Then | Response includes `Cache-Control` header with long-lived caching directives | Cache headers set |

**Assertions:**
- [ ] Response header `Cache-Control` contains `public`
- [ ] Response header `Cache-Control` contains `immutable` or a long max-age (e.g., `max-age=31536000`)
- [ ] Response includes an `Expires` header or equivalent long cache directive

---

### TC0285: Backend down returns 502 for /api/* requests

**Type:** Integration | **Priority:** High | **Story:** US0027 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Frontend container is running but backend container is stopped via `docker compose stop backend` | Backend offline |
| When | Request `http://localhost:80/api/v1/system/health` through nginx | API request with no backend |
| Then | Response is HTTP 502 Bad Gateway | Error passthrough |

**Assertions:**
- [ ] HTTP response status is 502
- [ ] Non-API routes (e.g., `/`) still return 200 with index.html (frontend unaffected)
- [ ] After `docker compose start backend` and health check passes, API requests return 200 again

---

### TC0286: Root path (/) returns index.html

**Type:** Integration | **Priority:** Critical | **Story:** US0027 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Both containers are running | Stack active |
| When | Request `http://localhost:80/` | Root path requested |
| Then | Response is HTTP 200 with the React app's index.html | Root serves SPA |

**Assertions:**
- [ ] HTTP response status is 200
- [ ] Response Content-Type is `text/html`
- [ ] Response body contains `<div id="root">`
- [ ] Response body contains `<script` tags referencing `/assets/` paths (Vite build output)

---

## Fixtures

```bash
# Start the full stack
docker compose up -d

# Wait for both services to be healthy (up to 30 seconds)
for i in $(seq 1 30); do
  curl -sf http://localhost:80/api/v1/system/health && break
  sleep 1
done

# Discover a JS asset filename for static asset tests
ASSET_JS=$(curl -s http://localhost:80/ | grep -oP '/assets/[^"]+\.js' | head -1)

# For TC0285: stop backend, test, then restart
docker compose stop backend
# ... run TC0285 assertions ...
docker compose start backend

# Cleanup after all tests
docker compose down
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0279 | /api/v1/system/health proxied to backend | Pending | - |
| TC0280 | /api/v1/projects proxied to backend | Pending | - |
| TC0281 | /projects/slug/documents returns index.html | Pending | - |
| TC0282 | /assets/*.js served with correct Content-Type | Pending | - |
| TC0283 | Gzip compression active for JS files | Pending | - |
| TC0284 | Cache-Control headers on /assets/ files | Pending | - |
| TC0285 | Backend down returns 502 for /api/* requests | Pending | - |
| TC0286 | Root path (/) returns index.html | Pending | - |

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
| 2026-02-18 | Claude | Marked as superseded - SPA routing now tested via FastAPI in TS0024 |
