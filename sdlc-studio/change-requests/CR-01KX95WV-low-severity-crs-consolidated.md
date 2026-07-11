# CR-01KX95WV: Low-severity crs (consolidated)

> **Status:** Complete
> **Depends on:** BG-01KX95DB, BG-01KX95QP, CR-01KX95FH
> **Triaged-by:** Darren; human; v3
> **Priority:** Low
> **Type:** Improvement
> **Date:** 2026-07-11
> **Consolidation:** low-severity-crs
> **Created-by:** sdlc-studio file
> **Raised-by:** Priya Nair; persona; v3

## Summary

A themed consolidation of Low-severity findings that individually do not warrant a standalone artefact (triage noise control, schema v3). Triage the batch, then action or reject as one.

## Consolidated Findings

- **Batch relationship resolution: remove N+1 in _get_dependencies and the leading-wildcard LIKE scans**: _get_dependencies issues one query per declared dependency (N+1); _get_dependents and the aliases branch use leading-wildcard `LIKE '%,x,%'` patterns that cannot use ix_documents_ref_id and force table scans. Storing depends_on/aliases as a comma-joined string in one column defeats indexing.
- **Read .config.yaml/.version for GitHub-source projects (config asymmetry)**: Only the local sync branch reads .config.yaml/.version; github projects never populate schema_version/profile/status_vocab, so custom statuses do not canonicalise and no schema version shows. This is the CR-F github part deferred in the v3 sprint - an undocumented asymmetry for a headline feature.

## Impact

Latent efficiency (an N+1 loop and leading-wildcard LIKE scans on every document-detail view) plus a config asymmetry that silently disables a headline schema-v3 feature for GitHub-source projects.

**Effort:** M

## Acceptance Criteria

- [ ] _get_dependencies resolves all dependencies in a single ref_id IN (...) query (no per-dep round-trip)
- [ ] GitHub-source sync reads .config.yaml/.version and populates schema_version/profile/status_vocab like the local branch

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Consolidation opened |
