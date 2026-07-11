# CR-01KX8Y6H: Config and schema-version awareness (.config.yaml and .version)

> **Status:** Proposed
> **Triaged-by:** Darren; human; v3
> **Depends on:** CR-01KX8Y0M
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Priority:** Low
> **Type:** Improvement

## Summary

The sync engine only collects `.md` files, so it ignores `sdlc-studio/.config.yaml` and `.version`.
The lens therefore cannot honour a project's custom `status_vocab`, know its `schema_version`, or
respect its `profile`. Extend both source collectors to fetch these two files, store
schema_version/profile/status_vocab on the project, feed the custom `status_vocab` into the CR-C
canonicaliser, and surface the schema version/profile in the UI.

## Impact

Custom project statuses (e.g. agent-crew's `Gated`, `Built`) render grey and uncanonicalised, and
the operator has no way to see which schema version or profile a project is on. Lowest priority: the
CR-C canonicaliser already handles the built-in vocabulary; this adds per-project extension.

**Effort:** M

## Acceptance Criteria

- [ ] The local walk and the GitHub collector fetch `.config.yaml` and `.version` (non-`.md` files)
- [ ] `schema_version`, `profile`, and `status_vocab` are stored on the project (new columns + Alembic migration)
- [ ] A project's custom `status_vocab` extends the canonicaliser's vocabulary so its statuses canonicalise and colour correctly
- [ ] The project-detail page shows the project's schema version and profile
- [ ] Tests cover config parsing and a custom `status_vocab` being honoured

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | Priya Nair | Raised |
