# BG-01KX95DB: ref_id not backfilled after migration 007: relationship resolution breaks for existing docs post-upgrade

> **Status:** Open
> **Triaged-by:** Darren; human; v3
> **Severity:** High
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio file
> **Raised-by:** Priya Nair; persona; v3

## Summary

Migration 007 adds `ref_id` (and re-normalises epic/story/`depends_on`/aliases) as nullable with NO data backfill. `_find_doc_by_clean_id` (documents.py) now resolves targets by `Document.ref_id == norm`, replacing the old `doc_id LIKE`. But sync skips unchanged files by hash (`sync_engine.py` step 3: `if doc.file_hash == file_hash: continue`) BEFORE `_build_doc_attrs` runs, so a plain re-sync never populates `ref_id` for existing rows. Result: after the migrations land on the live deployment, every pre-existing document has `ref_id`=NULL and parent breadcrumbs, depends-on and dependents panels go blank; re-sync cannot heal it (hash matches -> skipped). Confirmed by two independent reviewers with in-memory repros.

## Steps to Reproduce

Sync a project (rows get `ref_id`=NULL as if pre-migration), then resolve relationships: `get_related_documents` returns [] for parents/dependents of any unchanged doc. A re-sync does not fix it because the file hash is unchanged.

## Proposed Fix

Add a data-migration (009) that backfills `ref_id` = `norm_id(id_head(doc_id))` and re-normalises epic/story/`depends_on`/aliases for all rows; AND/OR make sync reparse a row when `ref_id` IS NULL even if the hash matches (`if doc and doc.file_hash == file_hash and doc.ref_id is not None: skip`). Add a regression test that builds a target row with `ref_id`=None and asserts resolution still works after the fix.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Filed |
