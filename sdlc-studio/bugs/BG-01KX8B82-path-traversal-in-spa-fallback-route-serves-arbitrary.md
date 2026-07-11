# BG-01KX8B82: Path traversal in SPA fallback route serves arbitrary files

> **Status:** Fixed
> **Triaged-by:** Darren; human; v3
> **Severity:** High
> **Verification depth:** functional
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio file
> **Raised-by:** Priya Nair; persona; v3

## Summary

In the Docker deployment (main.py:46-48) the catch-all @app.get('/{path:path}') builds `file_path` = `_STATIC_DIR` / path from the raw URL path and returns FileResponse guarded only by `is_file()` - no containment to `_STATIC_DIR.` Encoded ../ segments resolve outside the static root (LFI), exposing app source and the SQLite DB (which stores GitHub PATs at rest). The same handler also returns index.html with HTTP 200 for unknown /api/v1 paths instead of a canonical JSON 404.

## Steps to Reproduce

Deploy in Docker so /app/static exists; GET a URL whose path contains percent-encoded ../ traversal segments; observe a file outside the static root served.

## Proposed Fix

Resolve and contain: target=(`_STATIC_DIR`/path).resolve(); serve only if `target.is_relative_to(_STATIC_DIR.resolve())` and `is_file()`, else index.html. Exclude api/ paths (return canonical JSON 404). Prefer StaticFiles(html=True), which guards traversal.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Filed |
