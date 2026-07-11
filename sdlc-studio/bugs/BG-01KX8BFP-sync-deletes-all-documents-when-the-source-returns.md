# BG-01KX8BFP: Sync deletes all documents when the source returns empty (silent data loss)

> **Status:** Open
> **Triaged-by:** Darren; human; v3
> **Severity:** High
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio file
> **Raised-by:** Priya Nair; persona; v3

## Summary

`sync_engine.py`:324-328 deletes every existing document whose path is absent from `fs_files`, with no guard against `fs_files` being empty. A wrong `repo_path`/branch, an emptied local directory, or a partial fetch returning {} deletes ALL documents and then sets `sync_status`='synced' (line 331) with no error raised.

## Steps to Reproduce

Register a GitHub project with a `repo_path` matching nothing (or empty the local sdlc dir); trigger sync; all documents are deleted and status becomes 'synced'.

## Proposed Fix

Before the Step 4 delete pass, if `fs_files` is empty but `existing_docs` is non-empty, abort with `sync_status`='error' ('source returned no documents - refusing to delete'). Optionally add a deletion-ratio threshold before mass-deleting.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Filed |
