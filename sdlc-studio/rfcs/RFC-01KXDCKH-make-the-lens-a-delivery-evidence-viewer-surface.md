# RFC-01KXDCKH: Make the lens a delivery-evidence viewer: surface AC verification, critic verdicts and the sprint itself

> **Status:** Draft
> **Triaged-by:** Darren; human; v3
> **Raised-by:** Darren; human; v3
> **Priority:** High
> **Created:** 2026-07-13
> **Created-by:** sdlc-studio new
> **Related:** RETRO-0007 (the sprint whose evidence is invisible), CR-01KXCAHV (the sync contract this would extend)

## Summary

The lens is an excellent **document browser** and is not yet a **delivery-evidence viewer**.

A census of this repo's own `sdlc-studio/` tree: **185 of 195 `.md` files are ingested**, across 16 doc
types including 7 retros and 4 review documents. The ten that are not are the `_index.md` files, which are
derived output and correctly excluded - the lens derives its own views.

So the artefacts are *present*. What is absent is everything that makes a sprint **legible as delivery**:

1. **Whether "Done" means done.** A story's `Verify:` / `Verified:` lines sit in its **body text**.
   `_STANDARD_FIELDS` is `{status, owner, priority, story_points, epic, story, depends_on, aliases}` - so AC
   verification is never parsed into a field. It cannot be filtered, counted, or shown as a column. The lens
   can tell you a story is `Done`; it cannot tell you whether **a single one of its acceptance criteria
   actually passed**. That is the entire point of the discipline, and it is the one question the dashboard
   cannot answer. This sprint produced 27 passing ACs and 6 manual ones - none of it visible.
2. **Retros and reviews are orphaned.** RETRO-0007 is ingested, but its `> **Batch:** CR-01KXCA1Q,
   CR-01KXCAHV` is a non-standard field, so it lands in `metadata_json` as loose text - and `documents.py`
   has **no relationship rule for `retro`**. You can read the retro; you cannot click through to the work it
   is about, and from a CR you cannot reach the retro that discussed it. The learning is in the corpus and
   disconnected from the thing it was learned on.
3. **Critic verdicts are flat prose.** `critic-verdicts.md` *is* ingested (as `doc_type=review`) but as
   unstructured text, so "how many High findings were confirmed this sprint, and how many refuted" is
   unanswerable. Given the critic found a **confirmed High on all three of its runs** in RETRO-0007's sprint,
   that is the most interesting number the sprint produced.
4. **There is no sprint entity.** No `sprint` doc type exists. Which units were in a batch, what was
   delivered, what was blocked, lives in `.local/sprint-plan.json` and in retro prose.

Three of the four share one root cause: **the sprint's machine-readable state is JSON under `.local/`, and
the sync only speaks Markdown.**

## Problem / constraints (established, not assumed)

Facts checked against the code and the tree, because two of them change the answer:

- **`.local/` IS committed to git** in this project (`git ls-files` lists `verify-report.json`,
  `sprint-plan.json`, `telemetry.jsonl`, `review-state.json`). So a **GitHub**-source project *can* see it.
  But the name says "local", and there is no guarantee every consuming project commits it. **A design that
  requires `.local/` must degrade gracefully to "no evidence available", never to a broken sync.**
- **The walker deliberately skips every dotted directory** (`sync_engine.py:192` -
  `child.name.startswith(".")`), and all three fetch paths (local walk, tarball, Trees) filter to `.md`.
  So surfacing `.local/*.json` touches **the sync contract we have just rebuilt and mutation-proofed**. That
  is an argument for care, not for avoidance - the `FileEntry` manifest was designed to carry exactly this
  kind of extension.
- **`verify-report.json` is keyed by the story's file stem - which IS the lens's `doc_id`.** The join is
  free. Its shape per story: `{ac_count, verified, failed, stale, manual, passed[], failures[], flips[],
  verified_at}`. This is precisely the missing data, already in the right shape.
- **`critic-verdicts.md` is already a structured Markdown TABLE** (`| Unit | Verdict | Reviewer | Author |
  Date | Issues |`), append-only, latest-row-per-unit-wins. **It needs no JSON at all** - only a table parser.
  This meaningfully shrinks the problem: the critic-verdict half is a Markdown feature, not a sidecar feature.
- **`sprint-plan.json` is OVERWRITTEN on every `sprint plan` run.** It is *current state*, not history.
  Ingesting it therefore yields **the latest sprint and nothing before it**. Any ambition to browse *past*
  sprints cannot be met by reading it - this is the decisive constraint on Axis C, and it is easy to miss.

## Design Options

### Axis A - where does the evidence come from?

- **A1. Ingest `.local/*.json` as sidecar state.** Extend the sync to carry a small allow-list of JSON files
  alongside the `.md` tree. Authoritative (it is the machine's own report, not a human-stamped line), and it
  is the only source for the sprint batch. Cost: touches all three fetch paths; depends on `.local/` being
  committed.
- **A2. Markdown only.** Teach the parser to extract AC blocks (`Given/When/Then/Verify/Verified`) from a
  story body, and to read the `critic-verdicts.md` table. No sync-contract change, works in any repo whether
  or not `.local/` is committed. But it trusts the **stamped** `Verified:` line in the file rather than the
  machine's report - the two can drift, and the story file is exactly the artefact a person might hand-edit.
  Gives no sprint entity.
- **A3. Hybrid (recommended).** Markdown for what Markdown already structures - the critic-verdicts table,
  and the AC blocks. JSON sidecar for what only the machine knows - `verify-report.json`. This is not a
  compromise: it is the observation that the two halves have genuinely different sources of truth, and the
  critic-verdict half never needed a sidecar in the first place.

### Axis B - how is the evidence stored?

- **B1. Columns on `documents`** (`ac_total, ac_passed, ac_failed, ac_manual, verified_at`). Cheap to query,
  sorts and filters for free, one migration. Denormalised onto the doc it describes.
- **B2. A separate `document_verification` table.** Cleaner separation, per-AC granularity (which AC failed,
  not just how many). More machinery; needs a join for every list view.
- **B3. Stuff it in `metadata_json`.** Zero migration. Unqueryable - cannot answer "show me every Done story
  with a failing AC", which is the whole point.

### Axis C - is a sprint a first-class artefact?

- **C1. Derive it from `sprint-plan.json`.** No new artefact type. **But that file is overwritten every plan
  run**, so you get the current sprint and *no history at all*. A sprint view that forgets every previous
  sprint is close to useless.
- **C2. A durable `sprints/SP-*.md` artefact, committed.** Written at sprint close (the retro already knows
  the batch). Git-versioned, so history survives; ingests through the existing `.md` path with only a
  `DIR_TO_TYPE`/`PREFIX_TO_TYPE` entry. Requires a skill-side change to emit it.
- **C3. Derive the sprint from the retro.** The retro already names its `Batch:`, is committed, and is
  one-per-sprint. Make `Batch:` a **first-class relationship field** and the retro *becomes* the sprint
  record - no new artefact type, full history, and it fixes gap 2 (orphaned retros) at the same time.

### Axis D - the relationship gap

Independent of the above: `retro`/`review` need relationship rules so `Batch:` (and a review's subject)
resolve to real documents. This is small, self-contained, and delivers value on its own.

## Recommendation

**A3 + B1 + C3 + D**, staged so each step ships value alone:

1. **D first (cheapest, standalone).** Relationship rules for `retro` and `review`; promote `Batch:` to a
   parsed reference list. Retros stop being orphans; a CR gains a "discussed in RETRO-0007" link. No
   migration beyond reusing `depends_on`-style normalisation.
2. **Critic verdicts, from Markdown (A2 half).** Parse the `critic-verdicts.md` table into structured rows.
   Answers "what did the critic find, and was it confirmed or refuted" with **no sidecar and no sync change**.
3. **AC verification (A1 half + B1).** Ingest `verify-report.json` as a sidecar, join on `doc_id` (free), and
   project onto `documents` as `ac_total/ac_passed/ac_failed/ac_manual/verified_at`. Now the dashboard can
   answer the only question that matters: **does Done mean done?** Show a story that is `Done` with a failing
   or stale AC as the loudest thing on the screen.
4. **The sprint view, from the retro (C3).** With `Batch:` resolving, a retro *is* a sprint record - it has
   the units, the outcome, the lessons and (per the skill's own retro template) the critic loop. Roll the
   verification and verdict data up over its batch and you have a sprint page for free, with full history,
   without inventing an artefact type or reading a file that gets overwritten.

Net: **no new doc type, one migration, and the sync contract is extended once** - for the single JSON file
that carries information no Markdown file has.

## Open Decisions

| # | Decision | Status |
| --- | --- | --- |
| D1 | Sidecar allow-list: `verify-report.json` only, or also `telemetry.jsonl` / `review-state.json`? Each one added is sync surface and parse risk; start at one. | Open |
| D2 | When `.local/` is absent (a project that gitignores it), the evidence view must degrade to "not available" and the sync must stay green. Confirm that is acceptable rather than a hard requirement to commit `.local/`. | Open |
| D3 | Is a *stale* AC (`Verified: stale`) shown as a failure, or as its own state? A Done story whose verifier no longer runs is arguably worse than one that never had one. | Open |
| D4 | Bounds: `.local` JSON is untrusted input from a synced repo. Size cap + defensive parse, reusing the existing `_MAX_MEMBER_BYTES` discipline. What is the cap? | Open |
| D5 | Does C3 (retro-as-sprint) need a skill-side change to guarantee every retro carries a machine-readable `Batch:`, or is the current human-written line enough? | Open |

## Spawned CRs (proposed, once accepted)

- Relationship rules for `retro` / `review`; `Batch:` as a parsed reference field (step 1).
- Structured critic-verdict table parsing + a findings view (step 2).
- `verify-report.json` sidecar ingest + AC verification columns + "Done but not verified" surfacing (step 3).
- Sprint view rolled up from the retro's batch (step 4).

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | Darren | Raised from the question "what sprint artefacts can the lens actually show?" - census found the documents are nearly all ingested, but none of the delivery *evidence* is |
