# RFC-01KXARHK: Incremental GitHub sync: near-realtime without re-downloading the repo

> **Status:** Accepted
> **Triaged-by:** Darren; human; v3
> **Raised-by:** Priya Nair; persona; v3
> **Priority:** Medium
> **Created:** 2026-07-12
> **Created-by:** sdlc-studio new
> **Related:** BG-01KXARHJ (stale reparse), CR-01KX95FH (tarball bounds), CR-01KX95WV (github config)

## Summary

A GitHub-source project currently syncs by **downloading the entire repository tarball on every
sync** (`github_source.fetch_github_files` - a deliberate "1 API call instead of N+1" choice), then
re-parsing. This is simple and cheap in API calls, but it re-downloads the whole repo each time,
goes stale between manual syncs, and - because a re-sync skips byte-unchanged files by hash - leaves
some documents on old-parser output (BG-01KXARHJ). This RFC explores whether the lens can offer a
**near-realtime view of a remote (incl. private) GitHub repo without re-downloading everything**, and
concludes on the fetch strategy + freshness trigger. It is a design decision with real trade-offs
(fewer-but-larger vs more-but-smaller requests; manual vs polled vs pushed freshness; PAT vs App).

## Problem / constraint

- **The lens's value is aggregate:** FTS5 search, the relationship/tree graph, stats/completion, and
  the health-check rules engine all run over the **whole parsed corpus**. They cannot run against a
  repo that has not been materialised locally.
- Therefore a **pure "fetch-on-view, store nothing" realtime model is not viable**: answering one
  search/stats query would re-fetch every file, and GitHub's rate limit (5,000 req/hr authenticated)
  plus a network round-trip per document make it both slow and quota-fatal on a real repo. The store
  stays. The question is only *how the store is kept fresh from the remote*.
- The current cost: a full tarball per sync (bandwidth + no incremental), staleness between manual
  syncs, and the byte-unchanged reparse gap (BG-01KXARHJ).

## Design Options

### Axis 1 - fetch strategy
- **A1. Full tarball each sync (current).** 1 API call, whole repo. Best for the *first* sync; wasteful
  for re-syncs; no per-file freshness.
- **A2. Incremental via Git Trees + Blobs (recommended).** One Trees call (`?recursive=1`) returns every
  path + blob SHA; diff those SHAs against what is stored; fetch only the **changed** blobs (Contents/
  Blobs API). Re-sync cost = 1 tree call + K changed blobs (K is usually small), and only changed files
  re-parse - which also closes BG-01KXARHJ. Trade-off: more calls than the tarball when many files
  changed, and the first sync is 1 + N (vs the tarball's 1).
- **A3. Hybrid.** Tarball for the initial/full sync (cheapest cold start), incremental (A2) for every
  re-sync (cheapest steady state). Best of both; slightly more code (two paths).
- **A4. Pure on-demand / no store.** Rejected above - breaks search/stats/relationships/health and
  exhausts the rate limit.

### Axis 2 - freshness trigger
- **B1. Manual sync (current).** The operator triggers it; simplest; goes stale.
- **B2. Cheap commit-SHA poll on a timer.** Poll the branch's head commit SHA (1 call); unchanged ->
  do nothing, changed -> run the A2/A3 incremental sync. Near-realtime, **no inbound endpoint** - fits
  a homelab instance behind NPM. Recommended default.
- **B3. GitHub webhook (push event -> sync now).** Lowest latency, but needs the lens **reachable from
  GitHub** (a public URL / tunnel), which the LAN deployment is not without extra plumbing. Offer as an
  opt-in for internet-reachable deployments.

### Axis 3 - auth (private repos)
- **C1. PAT (current).** Already stored Fernet-encrypted + masked; works for Trees/Blobs/Contents and
  webhooks. Sufficient. (Rotation robustness is handled by BG-01KX95AZ.)
- **C2. GitHub App (installation tokens).** Finer scopes, per-install tokens, cleaner webhooks/private
  access - a better long-term auth model but heavier to set up. Later.

### Axis 4 - optional live document view
- **D1. Live-vs-synced on the document page.** When a doc is opened, optionally fetch its *current*
  GitHub version and show a "live" badge / diff against the last-synced copy. A browse-path add-on;
  does **not** replace the sync (aggregates still use the store). Pure polish - out of the core scope.

## Recommendation

**A3 + B2 + C1**, with B3/C2/D1 as opt-in/later:
1. **A3 - hybrid fetch:** keep the tarball for the initial/full sync; add an **incremental Trees+Blobs
   path** for re-syncs that diffs blob SHAs and fetches only changed files. Store each file's blob SHA
   (or keep using the content hash, mapping to it) so the diff is a cheap SHA compare.
2. **B2 - commit-SHA poll trigger:** a short-interval background check of the branch head SHA runs the
   incremental sync only when the repo actually moved - near-realtime, no inbound endpoint.
3. **C1 - keep the encrypted PAT;** revisit a GitHub App (C2) only if webhooks/private-scope demands grow.
Net: a GitHub project stays close to live and re-syncs cost a handful of small requests instead of a full
tarball. Local-source projects are unaffected. A true "live view" (D1) can be added later as browse-path
polish.

> **Correction (2026-07-13):** an earlier draft of this section claimed incremental sync would also
> resolve BG-01KXARHJ's staleness. It does not need to - `PARSER_EPOCH` (`sync_engine.py:44`) already
> fixed that and **BG-01KXARHJ is Fixed**. The benefit is already banked, so it is not counted here.
> The obligation runs the other way: the incremental path must **preserve** epoch reparse (see D6).

## Resolved Decisions

Resolved 2026-07-13 (Darren). Axes settled: **A3 + B2 + C1**; D1 (live view) out of scope.

| # | Decision | Resolution |
| --- | --- | --- |
| D1 | Store the blob SHA per document, or derive it from the existing content hash? | **Store it.** New nullable `documents.blob_sha` column. The stored `file_hash` is a sha256 of the bytes, so it cannot be compared to a git blob SHA-1; and recomputing the blob SHA from stored *text* would require a decode/re-encode round-trip - a fragility class we decline. Populate it on **both** paths: the tarball path computes it from the raw bytes it already extracts (`sha1("blob {len}\0" + bytes)`), the incremental path takes it from the Trees response. **NULL = unknown** → that project takes a full (tarball) sync next, which backfills every `blob_sha` in one call. The tarball path is therefore also the backfill and repair path. |
| D2 | Poll interval + where the loop lives | **In-process asyncio task** in the FastAPI app. The deployment is a single container running a single Uvicorn worker, so there is no multi-worker duplicate-poll problem and no external scheduler to own. Interval from config (default 300s; `0` disables). Per-project **opt-in** (`projects.auto_sync`). Start jittered so N projects do not poll in lockstep. Poll = branch head SHA (1 call) compared against a stored `last_synced_commit_sha`. |
| D3 | Keep the first-sync tarball (A3), or go incremental-only (A2)? | **A3 hybrid.** Tarball on: first sync, any NULL `blob_sha` in the project, an explicit full-resync request, or a changed-blob count over the D5 cap. Incremental otherwise. The tarball path earns its keep as cold start, backfill, repair, and the bounded-worst-case escape hatch. |
| D4 | Webhook (B3) in scope now? | **Deferred.** The lens is LAN-only behind NPM at `lens.home.lan` and is not reachable from GitHub without a tunnel. The poll (B2) gets near-realtime with no inbound endpoint. Revisit only if an internet-reachable deployment appears. |
| D5 | Rate-limit budget + backoff | **Cap changed blobs per incremental sync** (default 200, configurable). Over the cap → fall back to a tarball full sync, which bounds the worst case at today's cost rather than degrading it. Respect `X-RateLimit-Remaining`; on 403/429 raise the existing `RateLimitError`, set `sync_status=error` with a legible message, and **leave the stored corpus intact** - never partial-wipe on a throttled fetch. |
| D6 | *(new)* What is the sync engine's contract once content is no longer fetched for every file? | The engine moves from "here is every file **with content**" to "here is the **manifest** (path → blob_sha) plus content for the **changed subset**". Two consequences are load-bearing: (a) the `parser_epoch` reparse of an **unchanged** blob must re-parse from the **stored `content`** column, not a re-fetch; (b) the existing "source returned no documents - refusing to delete existing documents" guard must key off the **manifest**, not the fetched subset - a clean no-op sync legitimately fetches **zero** files, and a guard that reads that as "the source is empty" is a data-loss or false-error bug on the happy path. |

## Modes this change touches

Per RETRO-0006 ("a CR that names only one mode is an incomplete spec"), every mode the sync path
serves, and what each does after this change. Each gets an acceptance criterion.

| Mode | Behaviour |
| --- | --- |
| Local source | Unaffected. No manifest, no blob SHA, no poll. |
| GitHub, first sync | Tarball. Computes and stores `blob_sha` per file. |
| GitHub, re-sync, nothing changed | Trees call only. Zero blobs fetched. Zero documents touched, **zero deleted**. |
| GitHub, re-sync, K files changed | Trees call + K blob fetches. Only those K re-parse. |
| GitHub, re-sync, blob unchanged but `parser_epoch` stale | Re-parses from **stored content**. No fetch. |
| GitHub, re-sync, files deleted upstream | Absent from the manifest → deleted locally. Manifest-keyed, not fetch-keyed. |
| GitHub, re-sync, K over the cap | Falls back to a tarball full sync. |
| GitHub, upgraded install (NULL `blob_sha`) | Falls back to a tarball full sync, which backfills. |
| GitHub, token revoked / rate-limited mid-sync | `sync_status=error`, corpus left intact. |
| D5 | Rate-limit budget + backoff: cap blobs-per-sync and handle 403/rate-limit gracefully | Open |

## Spawned CRs

- **CR-01KXCAHV** - Incremental Trees+Blobs re-sync path in `github_source` + `sync_engine` (A3),
  storing per-file `blob_sha` and fetching only changed blobs. Carries D1, D3, D5, D6.
- **CR-01KXCAZJ** - Commit-SHA poll trigger (B2) so GitHub projects stay fresh without a manual sync.
  Carries D2. Depends on the incremental path.
- Not spawned: live-vs-synced document view (D1 axis 4), GitHub App auth (C2), webhook (B3) - all
  deferred, see the resolved-decisions table.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-12 | Priya Nair | Raised from the "realtime remote view" question; concluded on incremental sync + poll |
| 2026-07-13 | Darren | Resolved D1-D5, added D6 (the sync-engine contract change) and the mode table; corrected the stale BG-01KXARHJ claim; Accepted; spawned CR-01KXCAHV + CR-01KXCAZJ |
