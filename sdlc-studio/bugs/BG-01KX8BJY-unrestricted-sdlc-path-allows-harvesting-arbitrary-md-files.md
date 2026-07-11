# BG-01KX8BJY: Unrestricted sdlc_path allows harvesting arbitrary .md files from the host

> **Status:** Fixed
> **Triaged-by:** Darren; human; v3
> **Severity:** Medium
> **Verification depth:** functional
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio file
> **Raised-by:** Priya Nair; persona; v3

## Summary

project.py:79 validates a user-supplied `sdlc_path` with only Path(`sdlc_path).resolve()`+`is_dir()`; there is no allowlist base. `collect_local_files` then recursively walks that directory and stores every .md file, retrievable via the documents API. A LAN user can register `sdlc_path`=/ or /home and exfiltrate all Markdown on the host filesystem.

## Steps to Reproduce

POST /api/v1/projects with `source_type`=local, `sdlc_path`=/home (or /); trigger sync; read the harvested documents via the documents API.

## Proposed Fix

Constrain `sdlc_path` to an allowlisted mount base (e.g. /data/projects); reject any resolved path not `is_relative_to` that base. In Docker mount project dirs read-only under that base.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Filed |
