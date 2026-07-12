# RFC-01KXARHK: Incremental GitHub sync: near-realtime without re-downloading the repo

> **Status:** Draft
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
Net: a GitHub project stays close to live, re-syncs cost a handful of small requests instead of a full
tarball, and BG-01KXARHJ's staleness disappears because changed files always re-parse. Local-source
projects are unaffected. A true "live view" (D1) can be added later as browse-path polish.

## Open Decisions

| # | Decision | Status |
| --- | --- | --- |
| D1 | Store the blob SHA per document, or derive the diff from the existing content hash? | Open |
| D2 | Poll interval + where the loop lives (in-process timer vs an external scheduler hitting `/sync`) | Open |
| D3 | Is the first-sync tarball worth keeping (A3), or go incremental-only (A2) for one code path? | Open |
| D4 | Webhook (B3) - in scope now for internet-reachable deploys, or deferred until there is demand? | Open |
| D5 | Rate-limit budget + backoff: cap blobs-per-sync and handle 403/rate-limit gracefully | Open |

## Spawned CRs (proposed, once accepted)

- Incremental Trees+Blobs re-sync path in `github_source` + `sync_engine` (A2/A3), storing per-file
  blob SHA and fetching only changed blobs. *Also resolves BG-01KXARHJ for GitHub sources.*
- Commit-SHA poll trigger (B2) so GitHub projects stay fresh without a manual sync.
- (Optional) live-vs-synced document view (D1); (later) GitHub App auth (C2) / webhook (B3).

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-12 | Priya Nair | Raised from the "realtime remote view" question; concluded on incremental sync + poll |
