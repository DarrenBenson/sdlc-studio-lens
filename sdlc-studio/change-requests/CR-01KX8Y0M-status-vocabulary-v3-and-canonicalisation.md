# CR-01KX8Y0M: Status vocabulary v3 and canonicalisation

> **Status:** Complete
> **Triaged-by:** Darren; human; v3
> **Depends on:** CR-01KX8Y2G
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio new
> **Raised-by:** Tomas Reinholt; persona; v3
> **Priority:** Medium
> **Type:** Improvement

## Summary

`StatusBadge` colours only 8 legacy statuses (everything else renders grey), and real-world statuses
carry trailing prose (`Done - implemented 2026-07-08...`), bold (`**Done**`), or parentheses
(`Complete (81/88)`). Add a status canonicaliser that reduces a raw status to its vocabulary token
(mirroring the skill's `canonical_status`), colour the full schema-v3 vocabulary plus the `inbox`
triage lane per lifecycle stage, and recognise the full terminal set in completion stats.

## Impact

New and real statuses render as undifferentiated grey, and completion percentages under-count
terminal states (a plan/CR at `Complete`, a bug at `Fixed`/`Verified`), so the dashboard
misrepresents project state - the lens's primary job.

**Effort:** M

## Acceptance Criteria

- [ ] A canonicaliser reduces `**Done** - implemented...`, `Done · **CR:** ...`, and `Complete (81/88)` to the vocabulary token (`Done`/`Complete`), longest-token-first, retaining the raw value
- [ ] `StatusBadge` colours the full v3 vocabulary per type (terminal green, in-flight blue, blocked/rejected red, draft grey), including `inbox`, Complete, Proposed, Fixed, Verified, Closed, Won't Fix, Won't Implement, Deferred, Superseded, Approved, Accepted
- [ ] `services/stats.py` completion recognises the full terminal set (Complete/Fixed/Verified/Closed/Accepted/Won't-*)
- [ ] Tests cover the canonicaliser (prose-suffixed, bolded, parenthesised), badge rendering, and the stats terminal set

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | Tomas Reinholt | Raised |
