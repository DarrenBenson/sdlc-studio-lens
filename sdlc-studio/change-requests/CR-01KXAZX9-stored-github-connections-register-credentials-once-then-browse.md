# CR-01KXAZX9: Stored GitHub connections: register credentials once, then browse and add repos in two clicks

> **Status:** Complete
> **Verification depth:** functional
> **Triaged-by:** Darren; human; v3
> **Depends on:** CR-01KXAS75
> **Created:** 2026-07-12
> **Created-by:** sdlc-studio new
> **Raised-by:** Darren; human; v3
> **Priority:** Medium
> **Type:** Feature

## Summary

CR-01KXAS75 gave the operator a repo *selector*, but not a stored *credential*. The token still lives
in two unhelpful places: `projects.access_token` (a per-project column, so the same PAT is
re-encrypted and duplicated onto every repo added) and `ProjectForm`'s transient `useState("")` (so
the browse flow demands a **fresh paste of the PAT every single time** - even for the second repo from
the same account). The selector removed the URL typing but not the credential typing, and adding the
Nth repo is still as slow as the first.

Introduce a first-class **GitHub connection**: a labelled, validated, encrypted credential registered
once in Settings, after which browsing and adding a repo is a pick-and-click. Multiple named
connections are supported (e.g. `personal`, `work`) - one PAT already spans all of an account's orgs,
so the multiplicity is about multiple *accounts*, not orgs.

## Impact

Turns repo onboarding from "find the PAT, paste it, browse, fill, submit" into "pick connection,
browse, click" - the difference between a chore and a two-click action, and the whole point of the
selector. It also removes a real data-hygiene problem: today the same secret is copied into a column
on every project row, so rotating a PAT means editing every project that uses it; a connection makes
the credential single-source, and rotation a one-field edit.

**Effort:** M

## Acceptance Criteria

- [ ] A `github_connections` table (Alembic migration) stores: unique `label`, the GitHub `login` resolved at save time, the Fernet-encrypted `access_token`, `created_at`, `last_validated_at`. The raw token is never returned by any endpoint - responses carry `mask_token()` output only, consistent with the existing project schemas
- [ ] Registering a connection **validates the token** (`GET /user`) and stores the resolved `login`; an invalid or expired token is rejected at save with the canonical error shape, not stored
- [ ] CRUD endpoints for connections (list / create / delete), plus a re-validate action; deleting a connection that projects still reference is refused with a clear error naming those projects (no silent orphaning of a project's credential)
- [ ] The repo-browse and has-sdlc-studio endpoints (CR-01KXAS75) accept a **`connection_id`** as an alternative to a raw `access_token`, resolving the token server-side; the raw-token path remains for a one-off browse without registering
- [ ] `projects` gains a nullable `connection_id` FK; sync resolves a GitHub project's token from its connection when set, falling back to the project's own `access_token` column so **existing projects keep working unchanged** (no forced migration of stored tokens)
- [ ] Settings offers connection management: add (label + token, validated, showing the resolved login), list (label, login, masked token, last validated), delete. `ProjectForm`'s GitHub flow offers a **connection picker** whose selection drives Browse with no paste; manual token entry remains available as a fallback
- [ ] Tests cover: connection CRUD + token validation (mocked GitHub API), the masked-token invariant (no raw token in any response body), browse-by-connection_id, delete-in-use refusal, and the sync token-resolution precedence (connection over per-project column)

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-12 | Darren | Raised from the post-0.3.0 UX review: the selector still demands a PAT paste per repo |
