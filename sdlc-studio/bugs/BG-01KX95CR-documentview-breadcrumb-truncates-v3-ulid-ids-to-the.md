# BG-01KX95CR: DocumentView breadcrumb truncates v3 ULID ids to the bare prefix

> **Status:** Fixed
> **Triaged-by:** Darren; human; v3
> **Severity:** Medium
> **Verification depth:** functional
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio file
> **Raised-by:** Elena Foss; persona; v3

## Summary

DocumentView.tsx:160 renders breadcrumb link text as `parent.doc_id.split('-')[0]`. For a legacy id (`EP0007-git-sync`) this gives `EP0007`, but for a v3 ULID `doc_id` (`US-01JQK3F8-story`) it gives just `US`, so every ULID-era ancestor breadcrumb reads `US`/`EP`/`BG` and is indistinguishable. The frontend already has the correct `idHead()` helper in buildTree.ts.

## Steps to Reproduce

Open a document whose ancestor has a v3 ULID id; the breadcrumb shows only the 2-letter prefix.

## Proposed Fix

Export `idHead()` from buildTree.ts and use it for the breadcrumb display id (fall back to the full `doc_id)`; do not split on the first hyphen.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Filed |
