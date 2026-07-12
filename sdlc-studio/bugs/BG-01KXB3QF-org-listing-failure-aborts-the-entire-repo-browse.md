# BG-01KXB3QF: Org listing failure aborts the entire repo browse instead of degrading

> **Status:** Open
> **Triaged-by:** Darren; human; v3
> **Created:** 2026-07-12
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Severity:** Medium
> **Verification depth:** functional

## Summary

`list_repositories` (`services/github_source.py`) collects the user's own repos first, then enumerates
their orgs via `_fetch_org_logins` (line ~429). That helper calls `_handle_error_response(resp)`, which
**raises** on any non-2xx, and the surrounding `try` catches only `httpx.TimeoutException` and
`httpx.ConnectError`. So a refusal from `GET /user/orgs` propagates out of `list_repositories` and the
**whole browse fails**, discarding the user's own repos that were already fetched successfully.

This bites exactly the operator following least-privilege advice: a **fine-grained PAT** is scoped to a
single resource owner and is commonly not permitted to enumerate `/user/orgs`, and a classic PAT lacking
`read:org` may also be refused. The token can see plenty of repos; the browse shows none of them and
reports an access error instead.

## Steps to Reproduce

1. Register a GitHub connection whose token cannot list orgs (a fine-grained PAT, or a classic PAT
   without `read:org`).
2. Open the add-project form and click Browse.
3. The browse fails with an auth/access error and an empty list, even though `GET /user/repos` succeeded
   moments earlier and returned repos the token can legitimately see.

## Proposed Fix

Degrade rather than abort: treat a failure to enumerate orgs (and a failure to list any individual org's
repos) as a **partial result**, not a fatal error. Return the repos that were collected, and surface a
non-fatal notice in the UI ("Your organisations could not be listed with this token; showing your own
repositories"). Only a failure of the *primary* `GET /user/repos` call should fail the browse.

Tests: a 403 from `/user/orgs` still returns the user's repos; a 403 from one org's repo list still
returns the other orgs' repos plus the user's; a failure of `/user/repos` itself still raises.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-12 | Priya Nair | Raised while documenting the PAT scopes the lens requires |
