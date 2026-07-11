# BG-01KX8BY1: Blocking tarball extraction and filesystem walk run on the event loop during sync

> **Status:** Fixed
> **Depends on:** BG-01KX8B04
> **Triaged-by:** Darren; human; v3
> **Severity:** Medium
> **Verification depth:** functional
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio file
> **Raised-by:** Priya Nair; persona; v3

## Summary

`sync_project` runs as an async background task. `github_source.py`:169 calls the synchronous `_extract_md_from_tarball` (gzip decompress + in-memory walk) and `collect_local_files` does a synchronous recursive filesystem walk + `read_bytes`, both directly on the event loop, stalling all concurrent HTTP request handling for the sync duration.

## Steps to Reproduce

Trigger a sync of a large repo/directory while issuing other API requests; observe request handling stalls until the sync's blocking sections complete.

## Proposed Fix

Offload blocking sections with `anyio.to_thread.run_sync` / `asyncio.to_thread` (tarball extraction, filesystem walk, hashing), or run the whole sync in a worker thread.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Filed |
