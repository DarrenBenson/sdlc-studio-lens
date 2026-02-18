# US0027: Nginx Reverse Proxy Configuration [SUPERSEDED]

> **Status:** Superseded
> **Epic:** [EP0006: Docker Deployment](../epics/EP0006-docker-deployment.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17
> **Superseded:** 2026-02-18
> **Superseded By:** [US0024: Combined Dockerfile](US0024-backend-dockerfile.md)

> **Supersession Note:** The single-container architecture eliminates nginx entirely. SPA routing is now handled by a FastAPI catch-all route that serves index.html for non-API, non-file paths. API routes take priority as they are registered before the catch-all. Static assets are served via FastAPI's StaticFiles mount.

## User Story

**As a** SDLC Developer (Darren)
**I want** nginx to proxy API requests to the backend and serve the SPA for all other routes
**So that** the application works correctly with a single entry point on port 80

## Context

### Persona Reference
**Darren** - Expects the dashboard to work seamlessly at http://localhost with no manual proxy setup.
[Full persona details](../personas.md#darren)

### Background
The nginx configuration is the routing layer between the browser and the application. It serves three purposes: (1) serve React static files for all non-API routes, (2) proxy `/api/*` requests to the backend container, and (3) handle SPA routing by returning index.html for all unmatched paths.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Networking | nginx proxies /api/* to backend:8000 | proxy_pass directive |
| TRD | Architecture | SPA routing (all non-API paths return index.html) | try_files fallback |
| PRD | Performance | Dashboard load < 2 seconds | Gzip compression, cache headers |

---

## Acceptance Criteria

### AC1: API proxy
- **Given** nginx is running in the frontend container
- **When** a request arrives at `/api/v1/projects`
- **Then** nginx proxies it to `http://backend:8000/api/v1/projects` and returns the backend response

### AC2: SPA fallback routing
- **Given** nginx is serving the React build
- **When** a request arrives at `/projects/homelabcmd/documents` (a client-side route)
- **Then** nginx returns index.html with status 200 (React Router handles the route)

### AC3: Static asset serving
- **Given** Vite build output in /usr/share/nginx/html/assets/
- **When** a request arrives at `/assets/main-abc123.js`
- **Then** nginx serves the file with correct Content-Type and cache-control headers

### AC4: Gzip compression
- **Given** nginx configuration includes gzip directives
- **When** a browser requests a JS or CSS file with Accept-Encoding: gzip
- **Then** the response is gzip-compressed

### AC5: API error passthrough
- **Given** the backend returns a 404 error for a missing resource
- **When** nginx proxies the request
- **Then** the 404 status and error body are passed through to the client (nginx does not intercept API errors)

---

## Scope

### In Scope
- nginx.conf with server block
- Location block for `/api/` → proxy_pass to backend
- Location block for static files with cache headers
- try_files fallback to index.html for SPA routing
- Gzip compression for text, JS, CSS, JSON
- Proxy headers (X-Forwarded-For, X-Real-IP, Host)
- Access logging

### Out of Scope
- TLS/HTTPS configuration
- Rate limiting
- Load balancing
- Custom error pages

---

## Technical Notes

### nginx.conf
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    # API proxy
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Static assets with long cache
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Backend container not running | /api/* requests return 502 Bad Gateway |
| Backend slow to respond | nginx waits (default 60s timeout); returns 504 if exceeded |
| Request to /api without trailing content | Proxied to backend |
| Large file upload (if any) | nginx default client_max_body_size (1MB) applies |
| WebSocket upgrade request (future) | Not configured; would fail (acceptable for v1.0) |
| Concurrent requests | nginx handles concurrently (worker_connections default) |
| Favicon request | Served from /usr/share/nginx/html/favicon.ico or 404 |

---

## Test Scenarios

- [ ] /api/v1/system/health proxied to backend successfully
- [ ] /api/v1/projects proxied to backend
- [ ] /projects/slug/documents returns index.html (SPA routing)
- [ ] /assets/*.js served with correct Content-Type
- [ ] Gzip compression active for JS files
- [ ] Cache-Control headers on /assets/ files
- [ ] Backend down returns 502 for /api/* requests
- [ ] Root path (/) returns index.html
- [ ] Unknown static file returns 404

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0024](US0024-backend-dockerfile.md) | Service | Backend container name/port | Draft |
| [US0025](US0025-frontend-dockerfile.md) | Config | Frontend Dockerfile copies nginx.conf | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

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
| 2026-02-18 | Claude | Marked as superseded - SPA routing now handled by FastAPI catch-all route |
