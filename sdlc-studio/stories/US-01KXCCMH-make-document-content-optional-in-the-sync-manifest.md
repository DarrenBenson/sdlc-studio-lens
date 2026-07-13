# US-01KXCCMH: Make document content optional in the sync manifest, so the empty-source guard cannot misfire

> **Status:** Done
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

**This story was scoped to change no external behaviour** - the tarball and local collectors still supply
every byte, so `raw` is never actually `None` yet. It is a contract change with the incremental path not
yet built.

**It ended up changing two, because an independent critic found the invariant was already false.** Hunting
for ways to break "every live path is a key", the critic found the local walker had been **dropping an
unreadable file from the manifest** - and the deletion loop reads absence as "gone upstream", so a single
`chmod 000` **deleted the document** while the file sat intact on disk, and the sync still reported
`synced`. That is BG-01KX8BFP's failure class, live on `main`, unrelated to incremental sync. See AC6/AC7.

The lesson is worth more than the fix: I asserted the invariant held *by construction* and wrote that
claim into a docstring. It did not. Stating an invariant is not the same as establishing one - and the
critic went looking precisely because the claim was stated so confidently.

## Acceptance Criteria

### AC1: The suite passes, and no ASSERTION is changed

- **Given** this is an internal refactor with no behaviour change
- **When** the backend suite runs
- **Then** every test passes, and **not one assertion is altered** - in particular BG-01KX8BFP's empty-source regression test asserts exactly what it asserted before. If an *assertion* must change to accommodate this refactor, the refactor is wrong
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest -q

> **Honesty note - this AC originally said "passes unmodified - without being edited", and seven mock
> fixtures were edited.** The wording was wrong, not the refactor. Changing the *type* of an internal
> contract necessarily touches every test that constructs that type: seven mocks built manifests as
> `(file_hash, content)` 2-tuples and now call an `_entry()` helper that builds a real `FileEntry`.
>
> What matters is that **no assertion moved.** BG-01KX8BFP's `test_empty_source_preserves_existing_docs`
> asserts the same thing, on the same guard, and passes. The only genuinely changed assertions were made
> *stronger* (`test_returns_files_dict` now also asserts the blob SHA).
>
> The distinction to hold onto: **retyping a fixture is fine; weakening a check is not.** An AC that
> forbids all test edits will be violated by any honest type change, and an AC that is routinely violated
> teaches you to ignore it.
- **Verified:** yes (2026-07-13)

### AC2: The empty-source guard still fires when the source is genuinely empty

- **Given** a project with documents whose source now returns nothing at all
- **When** a sync runs
- **Then** the guard fires: no documents are deleted, and `sync_status` becomes `error` with the existing message
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_sync_dispatch.py -q -k TestEmptySourceGuard
- **Verified:** yes (2026-07-13)

### AC3: A contentless entry is never parsed, and stored content is never treated as a parseable source

- **Given** `documents.content` is body-only - the frontmatter blockquote carrying `status`, `epic`, `story`, `depends_on` and `aliases` is stripped before storage (`parser.py:183`), so re-parsing it would silently yield a document with no metadata
- **When** a manifest entry arrives with `raw=None`
- **Then** the engine **skips** it - it never calls `parse_document` on `doc.content`. A stale epoch is handled upstream by forcing the tarball path (RFC D7), so a document needing a re-parse always arrives with real bytes
- **Verify:** shell ! grep -qE 'parse_document\(\s*(doc|existing)\.content' backend/src/sdlc_lens/services/sync_engine.py
- **Verified:** yes (2026-07-13)

### AC4: An unchanged, epoch-current document with no bytes is simply skipped

- **Given** a manifest entry with `raw=None`, a matching hash and a current epoch
- **When** a sync runs
- **Then** the document is skipped, not re-written, and not deleted
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_sync_dispatch.py -q -k TestContentlessManifestEntries
- **Verified:** yes (2026-07-13)

### AC5: The guard is mutation-tested

- **Given** a gate never seen red is not a gate (LL0010)
- **When** the guard is mutated to key off the *fetched* subset rather than the manifest
- **Then** at least one test fails
- **Verify:** manual mutate the guard AND the deletion loop to key off the fetched subset; both must go red
- **Verified:** manual (2026-07-13) - BOTH mutants killed. (1) Guard re-keyed to `not any(e.raw is not None ...)`: 3 tests red. (2) Deletion loop re-keyed to the fetched subset: 3 tests red, including `test_a_fully_contentless_manifest_deletes_nothing` - i.e. the mutant DOES delete every document on a healthy no-op sync, which is BG-01KX8BFP regressing, caught. Restored: 755 pass.

### AC6: A file that EXISTS but cannot be READ is never treated as deleted

- **Given** an independent critic proved the invariant "every live path is a key" was **false on main today**: the local walker dropped an unreadable file from the manifest, and the deletion loop reads absence as "gone upstream" - so a single `chmod 000` **destroyed the document** while the file sat intact on disk
- **When** a file's bytes cannot be read (permissions, EIO, an NFS blip, an editor lock)
- **Then** the path **stays in the manifest**, marked `unreadable=True`; the stored document is left exactly as it was and is **not deleted**. The invariant now holds *by construction* rather than by assertion
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_sync_dispatch.py -q -k TestUnreadableFileIsNotADeletion
- **Verified:** yes (2026-07-13)

### AC7: A sync with errors does not report success

- **Given** `sync_status` was set to `synced` unconditionally, so a sync that skipped files - or, per AC6, silently deleted one - still showed the operator a green, freshly-timestamped success. `SyncResult.errors` was surfaced nowhere
- **When** any file could not be processed
- **Then** `sync_status` is `error` and `sync_error` names what was missed; the affected documents are preserved. A tool must never report a success it did not achieve (LL0008)
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_sync.py -q -k TestSyncUnreadableFile
- **Verified:** yes (2026-07-13)

> **This changed an existing assertion, and that deserves saying plainly.** `test_skips_unreadable` asserted
> `sync_status == "synced"` under the comment *"Sync should still succeed overall"*. That assertion
> **encoded the bug**: it is what made the AC6 data loss invisible. It is the only assertion changed in this
> story, and it was changed because it was wrong, not because it was inconvenient.

### AC8: A blob_sha that contradicts its own bytes is refused

- **Given** we store the manifest's `blob_sha` rather than recomputing it, and the skip condition never revisits a non-NULL `blob_sha` - so a wrong value would be wrong **for ever**: the path would look changed on every sync (defeating the feature) or unchanged for ever (the document silently never updates again)
- **When** a source supplies bytes whose real blob SHA differs from the entry's
- **Then** the sync refuses to store it, logs loudly and counts an error
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_sync_dispatch.py -q -k TestManifestBlobShaIsChecked
- **Verified:** yes (2026-07-13)

## Mutation results (2026-07-13)

Every mutation of the load-bearing logic is **killed**:

| Mutation | Result |
| --- | --- |
| Empty-source guard keyed on the fetched subset | **killed** (3 red) |
| Deletion loop keyed on the fetched subset | **killed** (3 red) - incl. "a fully contentless manifest deletes nothing", i.e. the mutant *does* delete every document on a healthy no-op sync |
| Contentless-needs-reparse silently skipped | **killed** |
| `needs_blob_sha_backfill` clause dropped | **killed** |
| `stale_epoch` clause dropped | **killed** *(was SURVIVING - the critic found `needs_blob_sha_backfill` had hollowed out BG-01KXARHJ's test so it passed for the wrong reason; the fixture now defuses every other reason-to-reparse so only the epoch can do the work)* |
| `blob_sha` consistency check removed | **killed** |
| Unreadable file dropped from the manifest | **killed** (this is AC6's data loss) |
| `blob_sha=entry.blob_sha` → `compute_blob_sha(raw)` | **survives - equivalent mutant.** Not a test gap: AC8's check errors out unless the two are equal, so at that point they are provably identical and the choice cannot matter. Recorded rather than papered over. |

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCAHV (RFC D6) |
