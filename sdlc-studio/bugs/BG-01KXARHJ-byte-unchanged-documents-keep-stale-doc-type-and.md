# BG-01KXARHJ: Byte-unchanged documents keep stale doc_type and status after an upgrade (incomplete reparse)

> **Status:** Fixed
> **Triaged-by:** Darren; human; v3
> **Severity:** Medium
> **Verification depth:** functional
> **Created:** 2026-07-12
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3

## Summary

All document-derived fields (doc_type, canonical status, epic/story, depends_on, aliases) are computed
at parse time in `_build_doc_attrs` and stored. Sync skips a file whose content hash is unchanged
(`sync_engine.py` step 3), so after an app upgrade that changes the parsing/inference/canonicalisation
logic, a document whose content has NOT changed keeps its OLD-computed fields forever - it is never
re-parsed. BG-01KX95DB added a self-heal that re-parses rows where `ref_id IS NULL`, but migration 009
backfills `ref_id` to a non-null value, so that guard no longer fires for existing rows - it heals
`ref_id` but leaves doc_type/status/etc. stale.

**Observed live on prod (0.2.0, verifying after the upgrade):** the `homelabcmd` project, re-synced
under 0.2.0, still reports two un-canonicalised statuses -
`Complete (52/55 stories done, 3 deferred to EP0007)` and `Complete (81/88 v2.0 stories done,
EP0014 pending)` - because those two docs are byte-identical to the May snapshot, so the hash-skip
fires and they are never re-parsed. Under 0.2.0 they would canonicalise to `Complete`. The same class
of staleness applies to doc_type (a pre-upgrade "other" that new inference would type as `cr`/`rfc`
stays "other" on any byte-unchanged doc).

## Steps to Reproduce

1. Sync a project under version N (documents get doc_type/status computed by N's logic).
2. Upgrade to N+1 whose inference/canonicalisation differs; run its migrations (ref_id is backfilled).
3. Re-sync. Documents whose content is byte-unchanged are skipped by hash and NOT re-parsed.
4. Those documents display their N-era doc_type/status (e.g. a raw `Complete (81/88 ...)` status, or a
   `cr` that still reads `other`), while content-changed documents are correct.

## Proposed Fix

Introduce a parser/schema **epoch**: a module constant bumped whenever inference/canonicalisation
changes, stored per document (a `parser_epoch` column, default 0). In the sync skip condition, reparse
a document when `doc.file_hash == file_hash` **but** `doc.parser_epoch < CURRENT_PARSER_EPOCH` (the
generalisation of the ref_id-null self-heal, which becomes one case of a stale epoch). A one-off
data-migration may bump nothing (let the next sync heal), or force `parser_epoch = 0` so all existing
rows re-parse once. Add a test: a byte-unchanged row with an old epoch is re-parsed and its
doc_type/status refreshed.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-12 | Priya Nair | Raised from the 0.2.0 prod verification (2 stale statuses on homelabcmd) |
