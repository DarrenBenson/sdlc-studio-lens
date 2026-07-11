# BG-01KX95QP: sdlc_path allowlist bypassable via a two-step source_type update

> **Status:** Open
> **Depends on:** BG-01KX95DB
> **Triaged-by:** Darren; human; v3
> **Severity:** Medium
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio file
> **Raised-by:** Priya Nair; persona; v3

## Summary

`update_project` only runs `_resolve_local_path` (which enforces `allowed_project_base`) when the effective source is local AND `sdlc_path` is supplied this call. Step 1: on a github project, PUT `sdlc_path`=<outside allowlist> with no `source_type` -> effective=github -> path stored unvalidated. Step 2: PUT `source_type`=local with no `sdlc_path` -> the `sdlc_path` branch is skipped, so the stored out-of-allowlist path is never re-validated. `sync_project` then walks it (only re-checking `is_dir)`, harvesting .md files outside the allowlist - defeating the RV-0001 containment control.

## Steps to Reproduce

On a github project: PUT {`sdlc_path`:'/etc'}; then PUT {`source_type`:'local'}; trigger sync; docs from outside `allowed_project_base` are harvested.

## Proposed Fix

Validate the effective post-update invariant: whenever the resulting project is `source_type` local, run `_resolve_local_path` against the resulting `sdlc_path` (re-validate on a transition to local even when `sdlc_path` is not supplied), and re-apply the allowlist check in `sync_project` before walking `sdlc_path.`

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Filed |
