# BG-01KXCG98: Unreadable local file is treated as deleted: its document is destroyed and the sync reports success

> **Status:** Fixed
> **Severity:** High
> **Verification depth:** functional
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Triaged-by:** Darren; human; v3
> **Related:** BG-01KX8BFP (same failure class), US-01KXCCMH (fixed here), RV-0001

## Summary

A local `.md` file that **exists but cannot be read** - a permission error, an EIO, an NFS blip, a file
locked by an editor mid-walk - was **dropped from the sync manifest** by `_walk_local_files`. The deletion
loop in `sync_project` treats a path's absence from the manifest as *"deleted upstream"*, so it **deleted
the document** for a file sitting perfectly intact on disk.

The sync then reported `sync_status = "synced"` with a fresh `last_synced_at`, because `SyncResult.errors`
was surfaced nowhere. The operator saw a green, successful, freshly-timestamped sync. Their document was
gone.

This is **BG-01KX8BFP's failure class** ("sync deletes all documents when the source returns empty"), which
was fixed for the *total* case by the empty-source guard. That guard only fires when the manifest is
entirely empty. **Every partial read failure walked straight through it.**

## Steps to Reproduce

Confirmed by an independent critic against `main`:

```
two local docs, sync            -> 2 documents stored
chmod 000 one file (it remains on disk)
sync again                      -> deleted=1  errors=1
                                   sync_status='synced'  sync_error=None
                                   documents remaining: ['epics/EP0001-one.md']
```

`stories/US0001-one.md` still exists on disk. Its document is destroyed. The sync reports success.

## Root cause

`_walk_local_files` caught the read error, logged a warning, incremented an error count that nothing acted
on, and `continue`d - so the path never became a key in the manifest:

```python
except (PermissionError, OSError) as exc:
    logger.warning("Cannot read %s: %s", md_file, exc)
    errors += 1
    continue          # <-- rel_path never enters fs_files
```

The deletion loop cannot distinguish *"the source no longer has this path"* from *"we failed to read this
path"*: both look identical to it - absent from the manifest.

## Proposed Fix

Found while building US-01KXCCMH, which asserted the invariant **"the manifest is complete - every live
path is always a key"**. The critic attacked that claim precisely because it was stated so confidently, and
found it was already false. The fix makes the invariant true rather than merely asserted:

1. **An unreadable file stays in the manifest** as `FileEntry(unreadable=True, raw=None)`. It is therefore
   present for the deletion loop, which leaves it alone **by construction** - no special case in the loop.
   The stored document is preserved untouched: the row we hold is still the best copy we have.
2. **A sync with errors no longer claims success.** `sync_status` becomes `error`, and `sync_error` names
   what was missed and confirms the documents were preserved. A tool must never report a success it did not
   achieve (LL0008) - and the false success is exactly what made this data loss invisible.

## Acceptance Criteria

- [x] A file that exists but cannot be read keeps its document; nothing is deleted
- [x] Such a sync reports `sync_status = error` with a legible message, not `synced`
- [x] A clean sync still reports `synced` with no error (no false alarm)
- [x] Mutation-checked: re-dropping the unreadable file from the manifest turns the regression test red
- **Verify:** shell cd backend && PYTHONPATH=src .venv/bin/python -m pytest tests/test_sync_dispatch.py -q -k TestUnreadableFileIsNotADeletion

## Lessons

- **Stating an invariant is not establishing one.** "Every live path is a key" went into a docstring as
  holding *by construction*. It did not hold. The claim was load-bearing for a data-loss guard, and nobody
  had checked it.
- **A guard that only catches the total case is not a guard.** The empty-source guard fires on a 100% empty
  manifest and *feels* like protection against "the source went wrong". Every partial failure - the far more
  likely one - sailed past it. When writing a defence, ask what the 1% version of the same failure does.
- **Silent success turns a bug into a disaster.** The deletion alone is bad. The deletion reported as a
  successful, freshly-timestamped sync is what stops anyone noticing.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | Darren | Found by an independent adversarial critic while reviewing US-01KXCCMH. Pre-existing on main, unrelated to incremental sync. Fixed in the same change. |
