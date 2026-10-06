# CR-01M46BAX: Migrate the lens workspace to skill 6.1 and re-baseline it

> **Status:** Proposed
> **Triaged-by:** Darren Benson; human; v1
> **Created:** 2026-10-05
> **Created-by:** sdlc-studio new
> **Raised-by:** Claude Opus 5.5; agent; v1
> **Affects:** sdlc-studio/.version, sdlc-studio/.gitignore, sdlc-studio/.criteria-baseline.txt, AGENTS.md, CLAUDE.md
> **Priority:** High
> **Type:** Maintenance
> **Size:** M

## Summary

The lens workspace was stamped skill 4.0.0 and has not been touched since 2026-07-13; the skill is now 6.1.0. The mechanical part was done alongside RV0003 (the observability gap analysis): `project_upgrade --apply`, `migrate --apply` (25 sizing conversions), `reconcile apply` (91 index cells), `.local/` untracked, the criteria baseline captured, supersession pairs completed, and the Draft test specs retired. What remains is the judgement set `migrate` reports and never guesses.

## Impact

Every later lens CR is groomed and gated by 6.1 tooling. Until AGENTS.md is refreshed the project tells an agent to read a skill path that does not exist on this machine, and does not state that review is independent of the author.

## Acceptance Criteria

- [ ] AGENTS.md is refreshed from the 6.1 `templates/agent-instructions.md`, keeping the project sections, and `validate.py instructions` reports no finding
- [ ] The 32 Done stories whose Story Points field is still the unfilled TBD template token and EP0005's unanswered Open Question are resolved or recorded as baselined debt, and `validate.py check` reports 0 errors
- [ ] The 13 shipped v3 bugs the engagement-floor lane would fail are either planned retroactively or covered by a recorded waiver (`decisions.py waive`)
- [ ] `reconcile.py detect` reports 0 drift and `sdlc-studio/.version` records skill 6.1.0

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
