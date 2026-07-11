# CR-01KX8B1W: Low-severity bugs (consolidated)

> **Status:** Proposed
> **Triaged-by:** Darren; human; v3
> **Priority:** Low
> **Type:** Improvement
> **Date:** 2026-07-11
> **Consolidation:** low-severity-bugs
> **Created-by:** sdlc-studio file
> **Raised-by:** Tomas Reinholt; persona; v3

## Summary

A themed consolidation of Low-severity findings that individually do not warrant a standalone artefact (triage noise control, schema v3). Triage the batch, then action or reject as one.

## Consolidated Findings

- **buildTree infinite recursion on a self- or cyclic document reference**: buildTree.ts:67-70 - findByPrefix (line 22) returns the FIRST node whose doc_id starts with the reference prefix, including the node itself; the story branch (line 61) has no self-guard (unlike the epic branch's type!==epic check). A document whose story/epic frontmatter is a prefix of its own doc_id becomes its own child, and sortNodes (line 39) recurses infinitely -> RangeError blank-screens the DocumentTree page.

## Impact

The buildTree recursion throws a RangeError that blank-screens the DocumentTree page for the whole project when a single document carries a self- or cyclic story/epic reference - a hard crash from bad data, not a graceful skip.

**Effort:** S

## Acceptance Criteria

- [ ] `buildTree` never attaches a node as its own child: when `findByPrefix` resolves the parent to the node itself, it is skipped (the story branch gets the same guard the epic branch has)
- [ ] `buildTree` is cycle-safe: a two-node cyclic story/epic reference does not recurse infinitely in `sortNodes`
- [ ] A regression test covers a self-referential input and a two-node cyclic input, asserting the DocumentTree renders without a RangeError

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Consolidation opened |
