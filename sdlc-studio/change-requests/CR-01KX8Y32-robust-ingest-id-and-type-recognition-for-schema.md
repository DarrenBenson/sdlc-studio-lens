# CR-01KX8Y32: Robust ingest: id and type recognition for schema v3 and mixed real-world artefacts

> **Status:** Proposed
> **Triaged-by:** Darren; human; v3
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Priority:** High
> **Type:** Improvement

## Summary

The lens infers document type and id from a fixed 8-type map (`utils/inference.py`) and a
`PREFIX+\d{4,}` regex. As a result, schema-v3 ULID ids (`BG-01KX8B82`), 3-5 letter prefixes
(`RFC`, `RETRO`, `RV`), hyphenated display ids (`CR-0003`), and the new type directories
(`change-requests`, `rfcs`, `retros`, `reviews`, `decisions`, `personas`, `product`) are mis-typed
as `other` or mis-identified. Introduce a shared id/type module and make inference recognise the
full type set and both id eras (sequential + ULID), with a safe fallback for genuinely non-standard
files. Also split inline `·`-separated header lines so multi-field one-liners parse into distinct
fields.

## Impact

Every CR/RFC/RETRO/RV/decision/PVD/persona in a real project currently lists as "Other", and
ULID-id artefacts (this project's own new bugs/CRs from the RV-0001 sprint) are not identified. This
is the foundation every other traceability and display change builds on - it must land first.

**Effort:** M

## Acceptance Criteria

- [ ] A shared `backend/src/sdlc_lens/utils/sdlc_ids.py` exposes: a prefix->type map covering epic/story/plan/test-spec/bug/cr/rfc/workflow/retro/review/decision/pvd/persona; an id matcher recognising sequential ids (`US0001`, `RFC0001`, `RETRO0001`, optional-hyphen `CR-0003`) and v3 ULID ids (`BG-01KX8B82`, Crockford-base32 tail); and `norm_id()` + `id_prefix()` mirroring the skill's `sdlc_md` behaviour
- [ ] `infer_type_and_id` types artefacts in change-requests/rfcs/retros/reviews/decisions/personas/product directories correctly, recognises ULID + 3-5-letter-prefix + hyphenated ids, treats `pvd.md` as a singleton, and falls back to `other` (no error) for genuinely non-standard files (`SPR-G`, date-named)
- [ ] The parser splits an inline `> **A:** x · **B:** y` header line into separate fields
- [ ] Unit tests cover ULID, hyphenated, 3-5-letter, and non-numeric ids, each new type directory, and inline-header parsing

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | Priya Nair | Raised |
