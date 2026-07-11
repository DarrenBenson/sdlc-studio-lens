# RETRO-0002: Schema v3 format-support sprint - 6 CRs delivered

> **Date:** 2026-07-11
> **Batch:** crs Proposed (CR-A..F: bring the lens up to date with sdlc-studio format evolution)
> **Goal:** done
> **Delivered:** 6 / 6   **Blocked:** 0
> **Raised-by:** Priya Nair; persona; v3

## Delivered

4 dependency-ordered waves (A -> {B,E} -> C -> {D,F}), each unit TDD, then green commit.

- **CR-01KX8Y32** (High) - shared `utils/sdlc_ids.py`: prefix->type map + id matcher for sequential AND v3 ULID ids + `norm_id`; inference recognises new type dirs (change-requests/rfcs/retros/reviews/decisions/personas/product) and ULID/hyphenated/3-5-letter ids; parser splits inline `·`-separated headers.
- **CR-01KX8Y2G** (High) - reference resolution via normalised `ref_id` (CR-0003 / CR0003 / [[CR-0496]] / ULID all resolve); `depends_on`/`aliases` columns (migration 007); `get_related_documents` gains depends_on + dependents; alias resolution for renumbered docs.
- **CR-01KX8Y0M** (Med) - `utils/sdlc_status.py`: STATUS_VOCAB + canonical_status (strips bold/prose/parentheses, per-type); sync stores canonical status; StatusBadge colours the full v3 vocab + inbox.
- **CR-01KX8YMC** (Med) - health-check uses sdlc_ids + status normaliser + v3 terminal sets; exempts record types; adds an inbox-triage rule.
- **CR-01KX8YD6** (Med) - TypeBadge labels + filter for new types; DocumentView promotes v3 fields + renders depends_on/dependents link sections; buildTree `findByRef` matches on normalised id head (ULID-safe).
- **CR-01KX8Y6H** (Low) - `project_config.py` parses `.config.yaml`/`.version` (PyYAML); schema_version/profile/status_vocab columns (migration 008); custom vocab feeds canonicalisation; ProjectDetail shows the schema version. GitHub config extraction deferred.

## Blocked / deferred

- None blocked. GitHub `.config.yaml` extraction deferred within CR-F (Low; local fully wired).

## What went well

- Real-world end-to-end proof: ingesting this repo's own v3 workspace (148 docs, 0 errors) AND agent-crew's messy v2 (1696 docs, 0 errors, no crash) - CRs/RFCs/retros/reviews now type correctly, ULID + hyphenated + wiki-link refs resolve (30/30 sampled in v2), statuses canonicalise, config parses.
- Parallel per-wave subagents on disjoint files (CR-B by hand + CR-E agent; CR-D + CR-F agents) delivered with zero merge conflict - the file-surface wave ordering held.
- The closing adversarial review bit: it found 2 real defects (workflow mis-exempted; backend self-reference unguarded) that the per-wave tests missed, both fixed.

## What was hard / what stalled

- Two waves ran subagents that each ran the full suite mid-flight and saw transient failures from siblings' in-progress edits; only the orchestrator's post-wave integrated run was authoritative.
- Changing `extract_doc_id`'s contract (raw-text -> id-or-None) and `_STANDARD_FIELDS` rippled into 3 existing tests that encoded the old permissive behaviour - updated deliberately, not worked around.

## Lessons

- **Normalise ids in ONE place and reuse it everywhere.** A single `sdlc_ids`/`norm_id` module let inference, relationship resolution, health-check, and (mirrored) the frontend buildTree all speak the same id language; the earlier per-file `[A-Z]{2}\d{4}` regexes were the root cause of every gap. <!-- promote: lessons add --global -->
- **The frontend and backend must apply the same guards.** buildTree guarded self-references but the backend `/related` endpoint did not - divergent invariants across the stack are a defect class the adversarial full-diff review is well-placed to catch.
- **A tolerant status canonicaliser beats a status enum.** Real statuses carry prose/bold/parentheses; `canonical_status` (longest-token-first, strip decoration, return-stripped-if-unknown) handles the mess without dropping custom project statuses.

## Metrics

- Delivered 6/6; critic rejects 0 (2 defects found and fixed during the closing review).
- Tests: backend 484 -> 594 (+110), frontend 175 -> 203 (+28); migrations 006 -> 008. Commits: 8 on `sprint/v3-format-support`.
- E2E: v3 (148 docs) + v2 (1696 docs) ingest verified, 0 errors, health/stats/relationships all run.
- Verification depth: functional (unit/integration + a real-data end-to-end ingest harness); mutation lane not run (advisory).
