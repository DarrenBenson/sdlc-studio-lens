# CR-01M46BZJ: Sign in with GitHub and scope every view to what the viewer can read

> **Status:** Proposed
> **Triaged-by:** Darren Benson; human; v1
> **Created:** 2026-10-05
> **Created-by:** sdlc-studio new
> **Raised-by:** Claude Opus 5.5; agent; v1
> **Affects:** backend/src/sdlc_lens/api/, backend/src/sdlc_lens/services/github_source.py, backend/src/sdlc_lens/services/github_connection.py, backend/src/sdlc_lens/config.py, frontend/src/, docs
> **Priority:** High
> **Type:** Feature
> **Size:** L

## Summary

The lens has no authentication and stores GitHub PATs reachable from the LAN. Register the lens as a GitHub App: its OAuth flow signs users in; its installation token drives sync and polling, replacing stored PATs and connections. A viewer sees only projects whose repo their account can read (checked with their token, cached briefly); admins are named by login (`SDLC_LENS_ADMIN_LOGINS`); settings, sync and project/connection management are admin-only. Local-path projects are admin-only unless granted to named logins. Existing PAT projects keep working until re-linked. Depends on: RFC-01M46B5Y.

## Impact

Required before the lens is exposed beyond the LAN or to any project manager.

## Acceptance Criteria

- [ ] An unauthenticated request to any API route other than health and login is refused
- [ ] A signed-in viewer without read access to a project's repo cannot see it in lists, search results, stats or by direct URL, each shown by a test against a mocked GitHub
- [ ] Every mutating route refuses a non-admin, and no response ever carries a token
- [ ] A project synced through the app installation needs no stored PAT; a legacy PAT project still syncs until re-linked

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
