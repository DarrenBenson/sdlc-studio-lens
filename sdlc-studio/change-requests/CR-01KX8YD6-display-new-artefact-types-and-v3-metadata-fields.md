# CR-01KX8YD6: Display new artefact types and v3 metadata fields

> **Status:** Proposed
> **Triaged-by:** Darren; human; v3
> **Depends on:** CR-01KX8Y0M, CR-01KX8Y2G
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio new
> **Raised-by:** Elena Foss; persona; v3
> **Priority:** Medium
> **Type:** Improvement

## Summary

`TypeBadge` has no labels for cr/rfc/retro/review/decision/pvd/persona/workflow (they render as raw
capitalised type names), and `DocumentView` buries the v3 metadata fields in the generic table. Add
friendly type labels + colours and type-filter entries; render the known v3 fields (Raised-by,
Depends on, Verification depth, Triaged-by, Consolidation, Created-by) with labels and clickable id
links (via the CR-B resolver); and make the tree view place new types sensibly.

## Impact

New artefact types read as ugly raw labels ("Cr", "Rfc"), and the rich v3 metadata (authorship,
dependencies, verification depth) that the parser already captures is invisible without links, so
the operator cannot navigate a v3 project's structure.

**Effort:** M

## Acceptance Criteria

- [ ] `TypeBadge` shows friendly labels + colours for cr, rfc, retro, review, decision, pvd, persona, workflow; the `DocumentList` type filter includes them
- [ ] `DocumentView` renders Raised-by, Depends on, Verification depth, Triaged-by, Consolidation, and Created-by with labels and clickable id links, while the generic metadata table still shows the long field tail
- [ ] `DocumentTree` places the new types sensibly in the hierarchy
- [ ] Tests cover badge labels, the type filter, and detail-field rendering

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | Elena Foss | Raised |
