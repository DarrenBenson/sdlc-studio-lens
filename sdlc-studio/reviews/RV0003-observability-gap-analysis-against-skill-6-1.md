# RV-0003: Observability gap analysis against skill 6.1

> **Date:** 2026-10-05
> **Created-by:** sdlc-studio new
> **Raised-by:** Claude Opus 5.5; agent; v1

## Scope

Where the lens stands against sdlc-studio 6.1.0, measured against a new goal: a full observability plane for
anyone reviewing an sdlc-studio project, including a project manager with no harness and no code access. Covered:
the lens code (backend, frontend, sync, parser, health check), its own sdlc-studio workspace, and the data a 6.1
project commits to git. The lens was last changed on 2026-07-13 and its workspace was stamped skill 4.0.0.

Decisions taken with the operator on 2026-10-05: keep the self-hosted web app; migrate this workspace to 6.1 first;
show a multi-project portfolio; sign in with GitHub (a viewer sees the projects whose repo their account can read);
show money as well as tokens, labelled an estimate.

## Findings

### What 6.1 commits that a reviewer could use

| Source (under `sdlc-studio/`) | Holds | Lens today |
| --- | --- | --- |
| `reports/RPT####.json` (+ `.md` twin) | Sprint report of record: goal and verdict, estimates (points, minutes, tokens forecast vs actual), delivered, known issues, sign-off, cost by model, DORA, calibration, rulings, waivers, lessons | `.json` never ingested; `.md` twin is plain prose |
| `reports/runs/RUN-*.json` | Signed run record: batch, per-unit minutes and tokens, appetite, goal verdict | Not ingested |
| `retros/RETRO*.md`, `retros/VELOCITY.md`, `retros/evidence/*.jsonl` | Keep/Stop/Try, carried issues, velocity and estimate accuracy, per-unit actuals and forecasts | Retros orphaned; rest not ingested |
| `reviews/critic-verdicts.md` | Independent review verdict per unit | Flat prose |
| `decisions.md`, `lessons.jsonl` | Decision register; lesson classes with hits | Prose / not ingested |
| `deploy-log.md` | Deploys for DORA | Prose |
| `Verify:` / `Verified:` per criterion | Whether each acceptance criterion was checked | Buried in body text |

Two properties of that data shape the design. It is not in the published format contract (`reference-schema.md`
covers markdown only), and the report shape has already changed once (RPT0002-0005 are schema 1, later ones
schema 2). Report figures cite `.local/` files as their source, which a reader without a harness cannot open.

### Gap matrix

| Capability | Gap | Ticket |
| --- | --- | --- |
| Format compatibility | Vocabulary and id prefixes frozen at 4.0.0 and copied into four frontend files; no epic Superseded, issue, charter, report, handoff, decision or lesson types; no `archive/` folders; 6.x headers unread | CR-01M46BEX |
| Ingestion | Sync admits only `.md` on all three fetch paths | RFC-01M46B5Y, CR-01M46BKF |
| Structured evidence | Verdict, decision, velocity and deploy tables and per-criterion verification unparsed; retros unlinked | CR-01M46B00 |
| Sprints and reports | No sprint entity, no report view | CR-01M46B9P |
| Cost and estimation | Story points only; no forecast vs actual, tokens, money or velocity | CR-01M46BFX |
| DORA and flow | None | CR-01M46BPJ |
| Quality evidence | "Done but not verified" invisible; review independence not shown | CR-01M46B04 |
| Lessons, decisions, retros | Not structured | CR-01M46BT9 |
| Portfolio | Dashboard counts documents only | CR-01M46BC2 |
| Access | No authentication; stored GitHub tokens reachable from the LAN | CR-01M46BZJ |
| Non-technical readers | Developer-only persona, jargon labels, no export or print | CR-01M46BQ8, CR-01M46B36 |
| Workspace and ops hygiene | Skill 4.0.0 workspace; stale indexes; prod compose pins `0.1.0-alpha.1` | CR-01M46BAX, BG-01M46B27 |

### Upstream (sdlc-studio) gaps

Raised in the sdlc-studio repository:

| Id | Finding |
| --- | --- |
| CR0609 | Publish a versioned evidence annex for reports, run records, lessons and evidence logs |
| CR0610 | Report figures reviewable without `.local/`; optional pricing snapshot and money in the record |
| BG0946 | `reports/_index.md` Last Updated not restamped when a report is filed |
| BG0947 | `reference-outputs.md` terminal-status table contradicts the code (this lens copied it) |
| BG0948 | No baseline emitter for pre-existing placeholder findings; v3 ids can never be baselined |

Until CR0609 lands the lens pins the observed shapes as fixtures; money uses a lens price table until CR0610.

### Done in this pass

- Workspace upgraded to skill 6.1.0, `.gitignore` seeded, `.local/` untracked (files kept on disk).
- `migrate --apply`: 25 legacy Effort/Points values converted to T-shirt Size.
- `reconcile apply`: 91 index cells corrected; three supersession pairs completed. Drift is 0.
- Criteria baseline captured from `validate.py check --emit-baseline` (13 shipped bugs with no criteria).
- TS0001-TS0005 set Complete (covered by `test_api_projects`, `test_api_project_crud`, `test_slug`,
  `test_sync_api`, `Settings.test.tsx`, `e2e/specs/settings.spec.ts`, `Sidebar.test.tsx`); TS0024 and TS0026 set
  Superseded (Docker cases never automated).
- RFC-01KXDCKH Superseded by RFC-01M46B5Y.

### Known debt left open

- 32 Done stories with an unfilled Story Points template token and an unanswered Open Question on EP0005 still fail
  `validate.py check`; owned by CR-01M46BAX.
- 13 shipped v3 bugs would fail the engagement-floor lane; owned by CR-01M46BAX.
- The new tickets are in `inbox`: triage must be done by a seat other than their raiser.

## Verdict

The lens is a sound browser for 4.0-era markdown and nothing more. Reaching the goal needs one migration
pass (done here, with the judgement items ticketed), one architectural decision (RFC-01M46B5Y: ingest the committed
record, never re-derive a competing figure, never read `.local/`), and twelve feature CRs in roughly four sprints:

1. Foundation: CR-01M46BAX, BG-01M46B27, CR-01M46BQ8, CR-01M46BEX; RFC-01M46B5Y accepted.
2. Ingestion: CR-01M46BKF, CR-01M46B00, CR-01M46B9P.
3. Analytics: CR-01M46BFX, CR-01M46BPJ, CR-01M46B04, CR-01M46BT9.
4. Access and portfolio: CR-01M46BZJ first (needed before any exposure beyond the LAN), then CR-01M46BC2 and
   CR-01M46B36.

Each CR is decomposed with `refine` before it is planned.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
