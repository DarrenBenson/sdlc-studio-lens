# CR-01KX8Y2G: Traceability: resolve references and relationships across id forms and new relations

> **Status:** Complete
> **Triaged-by:** Darren; human; v3
> **Depends on:** CR-01KX8Y32
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Priority:** High
> **Type:** Improvement

## Summary

Relationship and reference extraction (`services/documents.py`, `sync_engine.extract_doc_id`) uses a
hardcoded `[A-Z]{2}\d{4}` regex and only walks the epic/story hierarchy. So ULID, hyphenated, and
`[[wiki-link]]` references do not resolve, and `Depends on`, CR->story, and `Aliases` (v3 migration)
links are ignored. Use the CR-A id matcher + `norm_id` to resolve references by normalised id;
capture `depends_on`; resolve `Aliases`; and extend related-documents to include dependency and
CR-derived-story relations.

## Impact

Cross-references between artefacts are the core value of the relationship and tree views. They
silently break for every new id form (ULID, hyphenated, wiki-link) and for every dependency link, so
a v3 or real-world project shows a broken or empty graph.

**Effort:** M

## Acceptance Criteria

- [ ] `extract_doc_id` and the document reference matcher resolve `CR-0003`, `CR0003`, `[[CR-0496]]`, and ULID ids to the same document via `norm_id`
- [ ] A `depends_on` value is captured (new nullable column + Alembic migration) and surfaced in related documents
- [ ] `Aliases` (v3 migration) resolve so an old sequential-id reference finds the renumbered document
- [ ] `get_related_documents` includes Depends-on and CR->derived-story relations
- [ ] Tests cover ULID + hyphenated + wiki-link references, depends-on, and alias resolution fixtures

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | Priya Nair | Raised |
