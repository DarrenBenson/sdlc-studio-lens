# US-01KXCCMH: Make document content optional in the sync manifest, so the empty-source guard cannot misfire

> **Status:** Ready
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Triaged-by:** Darren; human; v3
> **Epic:** EP-01KXCCA4
> **Change Request:** [CR-01KXCAHV](../change-requests/CR-01KXCAHV-incremental-github-sync-hybrid-tarball-plus-trees-and.md)
> **Depends on:** US-01KXCC76
> **Persona:** Priya Nair (Engineering amigo)
> **Priority:** High
> **Story Points:** 3

## User Story

**As a** maintainer of the sync engine
**I want** the manifest to list every path while the content of unchanged files is optional
**So that** "fetch only what changed" cannot be mistaken for "the source is empty"

## Background

Two call sites in `sync_project` key off `fs_files`:

```python
if not fs_files and existing_docs:            # ~line 424 - the empty-source guard
    ... refuse to delete, mark the sync failed

for rel_path, doc in existing_docs.items():   # ~line 500 - the deletion loop
    if rel_path not in fs_files:
        await session.delete(doc)
```

That guard **is the fix for BG-01KX8BFP** - "sync deletes all documents when the source returns empty", a
High-severity data-loss finding from RV-0001.

The tempting way to build incremental sync is to hand `sync_project` only the changed files. Do that and a
no-op sync passes an empty dict: the guard fires spuriously, and if it did not, the deletion loop would delete
**every document in the project**. A High-severity data-loss bug, regressed, on the commonest path there is.

This story removes that possibility structurally, before any incremental fetching exists:

> **The manifest keeps every path. Only the content becomes optional.**

`fs_files` entries carry `(file_hash, raw | None, blob_sha)`. Unchanged files will later arrive with
`raw=None`, but they are **still keys in the manifest**. The guard and the deletion loop therefore need no
change and cannot misfire.

The one thing optional content genuinely forces: a document whose blob is unchanged but whose `parser_epoch`
is stale has no bytes to parse. **It cannot re-parse from the stored `content` column** - `parser.py:183`
stores body-only text, with the frontmatter blockquote (and therefore `status`, `epic`, `story`,
`depends_on`, `aliases`) stripped out. A stale epoch instead **forces the tarball path** (RFC D7), so the
bytes are real. This story simply must not pretend otherwise.

**This story changes no external behaviour.** The tarball and local collectors still supply every byte, so
`raw` is never actually `None` yet. It is a contract change with the incremental path not yet built.

## Acceptance Criteria

### AC1: The entire existing suite passes unmodified

- **Given** this is an internal refactor with no behaviour change
- **When** the backend suite runs
- **Then** every test passes **without being edited** - and in particular BG-01KX8BFP's empty-source regression test is untouched. If a test must change to accommodate this refactor, the refactor is wrong
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest -q

### AC2: The empty-source guard still fires when the source is genuinely empty

- **Given** a project with documents whose source now returns nothing at all
- **When** a sync runs
- **Then** the guard fires: no documents are deleted, and `sync_status` becomes `error` with the existing message
- **Verify:** pytest backend/tests/services/test_sync_engine.py -k empty_source

### AC3: A contentless entry is never parsed, and stored content is never treated as a parseable source

- **Given** `documents.content` is body-only - the frontmatter blockquote carrying `status`, `epic`, `story`, `depends_on` and `aliases` is stripped before storage (`parser.py:183`), so re-parsing it would silently yield a document with no metadata
- **When** a manifest entry arrives with `raw=None`
- **Then** the engine **skips** it - it never calls `parse_document` on `doc.content`. A stale epoch is handled upstream by forcing the tarball path (RFC D7), so a document needing a re-parse always arrives with real bytes
- **Verify:** shell ! grep -qE 'parse_document\(\s*(doc|existing)\.content' backend/src/sdlc_lens/services/sync_engine.py

### AC4: An unchanged, epoch-current document with no bytes is simply skipped

- **Given** a manifest entry with `raw=None`, a matching hash and a current epoch
- **When** a sync runs
- **Then** the document is skipped, not re-written, and not deleted
- **Verify:** pytest backend/tests/services/test_sync_engine.py -k skips_contentless_unchanged

### AC5: The guard is mutation-tested

- **Given** a gate never seen red is not a gate (LL0010)
- **When** the guard is mutated to key off the *fetched* subset rather than the manifest
- **Then** at least one test fails
- **Verify:** manual mutate the guard to `if not any(raw for _, raw, _ in fs_files.values())`, run the suite, confirm red, revert

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCAHV (RFC D6) |
