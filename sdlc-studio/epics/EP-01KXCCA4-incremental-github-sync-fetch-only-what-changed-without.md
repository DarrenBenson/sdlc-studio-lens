# EP-01KXCCA4: Incremental GitHub sync: fetch only what changed, without regressing the empty-source guard

> **Status:** Ready
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Triaged-by:** Darren; human; v3
> **Change Request:** [CR-01KXCAHV](../change-requests/CR-01KXCAHV-incremental-github-sync-hybrid-tarball-plus-trees-and.md)
> **Depends on:** EP-01KXCBC9
> **Priority:** High

## Summary

Implements RFC-01KXARHK decisions D1, D3, D5, D6. A GitHub re-sync currently downloads the whole repository
tarball to discover that three files changed. Add a Trees+Blobs incremental path so a re-sync costs one tree
call plus K changed blobs, keeping the tarball for cold start, backfill, repair, and the over-cap escape hatch.

## The design that makes the dangerous bug unrepresentable

`sync_project` today receives `fs_files: dict[path, (file_hash, raw_bytes)]` - every path, with content - and
two behaviours key off it:

- **line ~424:** `if not fs_files and existing_docs:` - the empty-source guard. This guard **is** the fix for
  **BG-01KX8BFP** ("sync deletes all documents when the source returns empty"), a **High**-severity data-loss
  finding from RV-0001.
- **line ~500:** `if rel_path not in fs_files:` - the deletion loop.

The obvious implementation of "fetch only what changed" is to pass only the changed files. That is a trap. A
no-op sync would pass **zero** files, the guard would read it as an empty source, and the deletion loop would
consider every document absent. It would **regress a High-severity data-loss bug on the most common path in
the system** - the sync where nothing changed.

So we do not re-key those two call sites. Instead:

> **The manifest stays complete; only the content becomes optional.**
> `fs_files` continues to hold **every path in the repo**. Unchanged files simply carry `raw=None`.

The guard and the deletion loop then need **no change whatsoever** - `fs_files` is never empty on a healthy
sync, and every live path is still a key. The failure mode is not defended against; it is made impossible to
express. (RETRO-0006: *"Derive, do not store, a value that is a function of a selection... prefer that over
remembering to clear it."* The same principle, applied to a guard rather than a field.)

## The parser-epoch trap (RFC D7)

What optional content forces us to handle honestly is the **`PARSER_EPOCH` reparse**: a document whose blob
is unchanged but whose epoch is stale must still re-parse, and now has no fetched bytes.

The obvious answer - "re-parse it from the stored `content` column" - **does not work, and this epic was
originally specified to do exactly that.** `parser.py:183` sets `body = lines[frontmatter_end:]`, so
`documents.content` holds only the body *after* the frontmatter blockquote. The title heading and the whole
`> **Status:** …` block are stripped before storage. `status`, `owner`, `priority`, `epic`, `story`,
`depends_on` and `aliases` are **not in that column at all**. Re-parsing it recovers nothing.

Building it as first written would have left every document on stale derived fields after an app upgrade -
**BG-01KXARHJ, resurrected, and silent.** The second data-loss-class regression this epic nearly shipped, and
like the first it was hiding inside an assumption that read as obviously true.

So: **a stale `parser_epoch` forces the tarball path**, exactly as a NULL `blob_sha` does. One tarball,
everything re-parses from real bytes, all epochs go current, and the next sync is incremental again. An epoch
bump only happens on an app upgrade, so steady state is untouched - and we reuse a path that already exists
instead of inventing one that cannot work.

## Story Breakdown

- [x] [US-01KXCC76: Store a git blob SHA per document](../stories/US-01KXCC76-store-a-git-blob-sha-per-document.md)
- [ ] [US-01KXCCMH: Make document content optional in the sync manifest, so the empty-source guard cannot misfire](../stories/US-01KXCCMH-make-document-content-optional-in-the-sync-manifest.md)
- [ ] [US-01KXCCTV: Fetch only changed blobs via Trees and Blobs, with a tarball fallback](../stories/US-01KXCCTV-fetch-only-changed-blobs-via-trees-and-blobs.md)

The stories are ordered so that **no behaviour changes until the last one**. US-01KXCC76 adds a column and
populates it. US-01KXCCMH changes the engine's internal contract while the tarball still supplies every byte,
so the entire existing suite - including BG-01KX8BFP's regression test - must pass **unmodified**. Only
US-01KXCCTV starts withholding content. If the suite needs editing before that point, the refactor is wrong.

## Acceptance Criteria

- [ ] A GitHub re-sync where nothing changed costs one Trees call, fetches zero blobs, writes zero documents and **deletes zero documents**
- [ ] A re-sync where K files changed fetches exactly K blobs and re-parses exactly K documents
- [ ] A project holding any document below `PARSER_EPOCH` takes the **tarball** path, so every document re-parses from real bytes (RFC D7). Stored `content` is never treated as a re-parseable source
- [ ] BG-01KX8BFP's regression test passes **unmodified** throughout
- [ ] BG-01KXARHJ's parser-epoch behaviour survives, proven by bumping `PARSER_EPOCH` and asserting derived fields recompute after an incremental-mode project syncs
- [ ] Local-source projects are untouched
- [ ] Over the changed-blob cap, or on any NULL `blob_sha`, the sync falls back to a tarball - and **says so** in the result
- [ ] A rate limit or a revoked token leaves the stored corpus intact
- [ ] The empty-source guard and the deletion loop are **mutation-tested**: mutate each, prove a test goes red

## Risks

- **This is the highest-stakes file in the product.** A mistake here is not a broken screen, it is a user's corpus deleted. The mitigation is structural (complete manifest, optional content) rather than behavioural (remember to check the right thing).
- ~~`parse_document` must behave identically whether fed a fetched blob or a stored `content` string.~~ **Resolved by removing the premise:** `content` is body-only and is never re-parsed. See RFC D7 above. The risk register keeps this line because the assumption that produced it looked obviously safe and was not.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | sdlc | Created via `new` (deterministic) |
| 2026-07-13 | Darren | Authored from CR-01KXCAHV; chose the complete-manifest / optional-content design so the BG-01KX8BFP regression is unrepresentable rather than merely tested against |
