# RETRO-0003: RV-0002 backlog sprint - 5 bugs + 3 CRs delivered

> **Date:** 2026-07-11
> **Batch:** bugs Open + crs Proposed (RV-0002 review backlog)
> **Goal:** done
> **Delivered:** 8 / 8   **Blocked:** 0
> **Raised-by:** Priya Nair; persona; v3

## Delivered

3 dependency-ordered waves, each unit TDD, then green commit.

- **BG-01KX95DB** (High) - sync reparses rows whose `ref_id` is NULL (self-heal) + data-migration 009 backfills `ref_id` for existing rows; fixes relationship resolution breaking after the migration-007 upgrade of an existing corpus.
- **BG-01KX95WX** (High) - SearchResults renders the FTS snippet as escaped text (splits on the literal `<mark>` markers into React nodes), closing the stored XSS from synced (untrusted GitHub) document content.
- **BG-01KX95AZ** (Med) - `decrypt_token` catches `InvalidToken` and degrades to None; a rotated/wrong key no longer 500s the whole project list.
- **BG-01KX95CR** (Med) - DocumentView breadcrumb uses `idHead` (exported from buildTree) - the full ULID id, not the bare 2-letter prefix.
- **BG-01KX95QP** (Med) - `update_project` re-validates the effective post-update `sdlc_path` (allowlist membership) on a transition to local, closing the two-step bypass; sync re-applies the containment check.
- **CR-01KX95HS** (Med) - centralise terminal-status in `sdlc_status.is_terminal`; delete the duplicated maps in health_check + stats (fixes the false Superseded-workflow stale flag).
- **CR-01KX95FH** (Low) - ULID tail must contain a digit (no more `PL-answered`->plan); `canonical_status` matches vocab before the prose-cut (custom `A - B` statuses survive); bounded GitHub tarball download/decompression.
- **CR-01KX95WV** (Low) - batched `_get_dependencies` (one `ref_id IN (...)` query); GitHub sync now reads `.config.yaml`/`.version` (the CR-F github part), populating schema_version/profile/status_vocab.

## Blocked / deferred

- None blocked. All the v3 retro's deferred follow-ups (token rotation, GitHub config) were delivered this sprint.

## What went well

- The fresh `review generate` earned its place: it found a **regression this project introduced** (the ref_id backfill gap - only bites on a real upgrade of an existing corpus, which the per-CR reviews couldn't see) and a **pre-existing stored XSS** that RV-0001 missed - both higher-value than the known loose ends.
- Parallel per-wave TDD subagents on disjoint file-surfaces delivered 8 units; the closing adversarial review found exactly 1 defect (a usability regression in the allowlist fix), fixed in one commit.
- End-to-end re-verified on real data: v3 (158 docs) + v2 agent-crew (1696 docs), 0 errors.

## What was hard / what stalled

- One subagent used `git stash`/`pop` for lint triage while siblings were mid-write in the shared tree - a real hazard; it restored cleanly, but concurrent agents must not touch the working-tree stash. The authoritative signal is always the orchestrator's post-wave integrated run.
- The GitHub-config fix changed `collect_github_files`'s return signature (now a tuple), rippling into ~10 mock sites - a contained-but-wide contract change the agent had to thread through carefully.

## Lessons

- **A migration that adds a column read by hot paths needs a backfill AND a self-heal.** ref_id was added nullable with no backfill, and sync's skip-on-hash meant re-sync never populated it - so the feature worked in tests (fresh rows) but would break on the next real upgrade. Ship the data-migration + a reparse-when-null guard together. <!-- promote: lessons add --global -->
- **`review generate` on a grown codebase finds integration-level defects the per-unit reviews structurally cannot** - the regression only manifests across the migration + sync + resolver seam, none of which the owning CR's reviewer looked at end to end.
- **A security control's fix must not over-couple** - re-validating the allowlist accidentally required the directory to exist, breaking unrelated edits. Separate the invariant (membership) from incidental checks (existence).

## Metrics

- Delivered 8/8; critic rejects 0 (1 defect found + fixed during the closing review).
- Tests: backend 594 -> 646 (+52), frontend 203 -> 207 (+4); migrations 008 -> 009. Commits: 5 on `sprint/rv0002-backlog`.
- E2E: v3 (158 docs) + v2 (1696 docs) ingest verified, 0 errors.
- Verification depth: functional (unit/integration + real-data end-to-end ingest); mutation lane not run (advisory).
