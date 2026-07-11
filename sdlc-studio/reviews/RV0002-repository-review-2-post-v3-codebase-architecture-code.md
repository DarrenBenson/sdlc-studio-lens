# RV-0002: Repository review 2 - post-v3 codebase (architecture, code quality, defensive security)

> **Date:** 2026-07-11
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Type:** review generate (repository re-review)

## Scope

Read-only three-leg review of the codebase **after** the RV-0001 backlog and the schema-v3
format-support sprints (~1885 lines added). Emphasis on the new surface (the pre-existing code was
audited in RV-0001): `utils/sdlc_ids.py`, `utils/sdlc_status.py`, `services/project_config.py`, the
reference-resolution in `services/documents.py`/`sync_engine.py`, migrations 007/008, and the
frontend `buildTree.ts`/`DocumentView.tsx`/badges. Each finding re-verified at its cited `file:line`;
the two High findings were confirmed with runnable repros (two independent reviewers for the ref_id
regression).

## Per-leg assessment

| Leg | Verdict | Headline |
| --- | --- | --- |
| Architecture | Needs work | `ref_id` never backfilled after migration 007 - relationship resolution breaks for existing docs post-upgrade; status logic triplicated and drifted. |
| Code quality | Solid, with gaps | New id/status/resolution code well-tested, but the resolver is never tested with a NULL `ref_id` (the exact regression), and id_head/`_strip_decoration` have untested edge cases. |
| Defensive security | Needs work | Stored XSS via `dangerouslySetInnerHTML` on FTS snippets over synced content; `decrypt_token` 500s the bulk endpoint on key rotation; the sdlc_path allowlist is bypassable via a two-step update. |

## Findings

Filed through `file_finding.py` (ids tool-allocated); Low findings auto-consolidated. All in the
`inbox` triage lane.

| ID | Title | Type | Severity | Leg |
| --- | --- | --- | --- | --- |
| BG-01KX95DB | `ref_id` not backfilled after migration 007 - relationships break post-upgrade | Bug | High | Arch/Code |
| BG-01KX95WX | Stored XSS in search results (`dangerouslySetInnerHTML` on FTS snippet over synced content) | Bug | High | Security |
| CR-01KX95HS | Centralise terminal-status / canonicalisation logic (triplicated + drifted) | CR | Medium | Arch |
| BG-01KX95CR | DocumentView breadcrumb truncates v3 ULID ids to the bare prefix | Bug | Medium | Code |
| BG-01KX95AZ | `decrypt_token` raises InvalidToken on a rotated key, 500-ing the whole project list | Bug | Medium | Security |
| BG-01KX95QP | `sdlc_path` allowlist bypassable via a two-step source_type update | Bug | Medium | Security |
| CR-01KX95FH | Low-severity bugs (consolidated): id_head word-as-ULID; status ` - ` truncation; unbounded tarball | CR | Low | Code/Sec |
| CR-01KX95WV | Low-severity CRs (consolidated): N+1 dependency resolution; GitHub .config.yaml not read | CR | Low | Arch |

### Dedup / notes

- The **ref_id regression** (BG-01KX95DB) was independently found by the architecture and code-quality
  legs, each with a runnable repro - filed once. It is a regression THIS project introduced in the v3
  sprint (migration 007 + sync's skip-on-hash), so it ranks first.
- The **XSS** (BG-01KX95WX) pre-dates the v3 sprints (EP0005 search) but GitHub sync (EP0007) turned
  the document body into an external trust boundary; RV-0001 did not surface it.
- BG-01KX95AZ (token rotation) and the GitHub-config half of CR-01KX95WV match the two follow-ups the
  v3 retro deferred - the review re-derived them independently and ranked them.
- The missing NULL-`ref_id` resolver test is folded into BG-01KX95DB's fix (add the regression test).

## Limitations

- Runtime repro of the XSS and the allowlist bypass was by code inspection + the reviewers' targeted
  DB/unit repros, not a live browser/HTTP drive; each fix should ship a regression test.
- Cleared clean by the security leg: `project_config` uses `yaml.safe_load`; `norm_id` strips LIKE
  wildcards before every query (no injection); the RV-0001 fixes (traversal containment, Fernet at
  rest, global handlers) still hold; DocumentView renders markdown without raw HTML; no tar-slip / SSRF.
- The LIKE substring-collision concern was investigated and found safe (comma-anchored + norm_id).

## Top five priorities (in order)

1. **BG-01KX95DB - ref_id backfill regression.** Ships a broken relationship graph to the live
   deployment on the next migration; re-sync cannot heal it. Backfill + reparse-when-NULL + a
   NULL-ref_id regression test.
2. **BG-01KX95WX - stored XSS in search.** Script execution in-origin from a synced (untrusted GitHub)
   document body. Stop using `dangerouslySetInnerHTML` on document-derived text.
3. **BG-01KX95QP - allowlist bypass.** Re-validate the effective post-update path and re-check in sync;
   restores the RV-0001 containment control.
4. **BG-01KX95AZ - decrypt_token 500s the bulk endpoint.** Catch InvalidToken; degrade per-project.
5. **CR-01KX95HS - centralise status logic.** Closes the drift that already produces false stale flags
   and undercounted stats (and the CR the code comment already promises).

## Verdict

The v3 work is sound in the small - the id/status/resolution modules are well-built and mostly
well-tested - but two integration-level defects escaped the per-CR reviews: a **migration/backfill
regression** that only bites on a real upgrade of an existing corpus, and a **status-logic
triplication** that has already drifted. Plus a pre-existing **stored XSS** that the external GitHub
trust boundary makes materially worse. Recommend a sprint led by the two High bugs (before the branch
is deployed to the homelab), then the three Medium bugs, then the two Low consolidations.

**Next action:** triage BG-01KX95DB and plan the sprint (this session stops at the plan for sign-off).

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | Priya Nair | Created via `new` (deterministic) |
| 2026-07-11 | Priya Nair | Filled report: 3 legs, 8 findings filed, top-5 priorities |
