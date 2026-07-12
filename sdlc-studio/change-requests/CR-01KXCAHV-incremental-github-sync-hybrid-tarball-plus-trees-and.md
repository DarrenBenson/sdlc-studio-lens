# CR-01KXCAHV: Incremental GitHub sync: hybrid tarball plus Trees and Blobs re-sync

> **Status:** Proposed
> **Verification depth:** functional
> **Triaged-by:** Darren; human; v3
> **Depends on:** CR-01KXCA1Q
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Related:** RFC-01KXARHK (Accepted; source of D1/D3/D5/D6), BG-01KXARHJ (Fixed; its parser-epoch fix must survive)
> **Priority:** High
> **Type:** Feature

## Summary

Implements RFC-01KXARHK decisions **D1, D3, D5, D6** (axis choice **A3**).

A GitHub-source project re-syncs today by downloading the **entire repository tarball**, every time
(`github_source.fetch_github_files`). That was a deliberate "1 API call instead of N+1" trade, and it is
still the right call for a *cold* sync. For a *re*-sync it is pure waste: the whole repo crosses the wire
to discover that three files changed.

Add an incremental path. One Trees call (`?recursive=1`) returns every path plus its git blob SHA; diff
those against what we hold; fetch only the changed blobs. Steady-state re-sync cost falls from a full
tarball to **1 tree call + K small blob fetches**, where K is normally tiny.

**The engine's contract changes, and that is the whole risk of this CR.** `sync_project` currently receives
`fs_files: dict[path, (file_hash, raw_bytes)]` - *every* file, *with content*. Incrementally it instead
receives a **manifest** (path → blob_sha) plus content for only the **changed subset**. Two existing
behaviours sit directly in that blast radius:

1. **`PARSER_EPOCH` reparse** (`sync_engine.py:44`, skip logic at ~436-455). A document whose blob is
   byte-identical but whose `parser_epoch` is stale **must still re-parse**. Under the incremental path it
   has no fetched bytes - so it must re-parse from the **stored `content` column**, not a re-fetch. This is
   the mechanism that fixed BG-01KXARHJ; breaking it silently un-fixes that bug.
2. **The empty-source guard** ("source returned no documents - refusing to delete existing documents",
   ~line 425). It keys off `fs_files` being empty. Under incremental sync a **clean no-op sync legitimately
   fetches zero files.** A guard that reads that as "the source is empty" either wipes the corpus or throws
   a false error - *on the happy path*. It must key off the **manifest**, not the fetched subset.

Per RETRO-0006 ("a CR that names only one mode is an incomplete spec"), every mode is enumerated below and
each carries its own acceptance criterion.

## Impact

Re-syncs stop being O(repo) and become O(change) - the precondition for CR-01KXCAZJ's poll trigger, which
is unaffordable if every poll hit means a full tarball. This is also the most dangerous file in the product
to touch: a mistake here is not a broken screen, it is a user's document corpus deleted. Hence the
manifest-keyed guard is a named AC rather than an implementation detail, and the mutation check is
mandatory rather than optional.

**Effort:** L

## Acceptance Criteria

- [ ] **`documents.blob_sha` (nullable) is added and populated on both paths** (RFC D1). The tarball path computes it from the raw bytes it already extracts (`sha1("blob {len}\0" + bytes)`); the incremental path takes it from the Trees response. The existing `file_hash` (sha256) is not reused - it cannot be compared to a git blob SHA-1. Alembic migration; NULL means "unknown"
- [ ] **Hybrid path selection** (RFC D3). A **full tarball sync** runs when it is the first sync, *or* any document in the project has a NULL `blob_sha`, *or* a full resync is explicitly requested, *or* the changed-blob count exceeds the cap. **Incremental** runs otherwise. An upgraded install (every `blob_sha` NULL) therefore self-heals via one tarball that backfills every SHA
- [ ] **MODE - nothing changed: zero blobs fetched, zero documents touched, and critically ZERO DELETED.** The empty-source guard keys off the **manifest**, not the fetched subset (RFC D6). A no-op incremental sync must never be mistaken for an empty source. Proven by a test that **fails** against a fetch-subset-keyed guard
- [ ] **MODE - K files changed:** exactly those K blobs are fetched and exactly those K documents re-parse. Unchanged documents are neither re-parsed nor re-written
- [ ] **MODE - blob unchanged but `parser_epoch` stale:** the document **re-parses from its stored `content`** with no network fetch, so the BG-01KXARHJ fix survives the contract change. Proven by a test that bumps `PARSER_EPOCH` and asserts the derived fields (`doc_type`, `status`, `ref_id`, `epic`/`story`, `depends_on`, `aliases`) recompute while **zero blob requests** are issued
- [ ] **MODE - files deleted upstream:** paths absent from the **manifest** are deleted locally. Deletion is manifest-keyed, never fetch-keyed
- [ ] **MODE - local source:** entirely unaffected. No manifest, no blob SHA, no Trees call. Regression-tested
- [ ] **MODE - rate-limited or token revoked mid-sync** (RFC D5): raises the existing `RateLimitError` / `AuthenticationError`, sets `sync_status=error` with a legible message, and **leaves the stored corpus intact**. A throttled fetch never partial-wipes
- [ ] **Bounded worst case** (RFC D5): changed blobs per incremental sync are capped (default 200, configurable); over the cap it falls back to a tarball full sync, so the worst case is today's cost rather than worse than it. `X-RateLimit-Remaining` is respected. **A cap must speak** (RETRO-0006): any bound that diverts or drops work says so in the sync result, never silently
- [ ] **The sync result reports what happened:** fetched / skipped / reparsed-from-store / deleted counts, plus which path ran (tarball or incremental) and why
- [ ] **Mutation check is mandatory** on the empty-source guard and the epoch reparse: mutate each, prove the new tests go red. RETRO-0006's critic found three real defects that 976 passing tests missed - a green suite is not evidence here (LL0010)

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | Darren | Spawned from RFC-01KXARHK (Accepted); carries decisions D1, D3, D5, D6 |
