# CR-01KXAS75: GitHub repo selector: browse repos and orgs to add, flagging sdlc-studio workspaces

> **Status:** Proposed
> **Depends on:** CR-01KXARM8
> **Triaged-by:** Darren; human; v3
> **Created:** 2026-07-12
> **Created-by:** sdlc-studio new
> **Raised-by:** Elena Foss; persona; v3
> **Priority:** Medium
> **Type:** Feature

## Summary

Adding a GitHub project is manual today: the operator types `repo_url` + `repo_branch` + `repo_path`
into `ProjectForm`, and the lens has no way to list the repos a token can see. Add a **repo selector**:
given a token, browse/search the authenticated user's repositories and organisations (and org repos),
and pick one to register - auto-filling the source fields. **Every** repo is listed (public + private
+ org), with the ones that already contain an `sdlc-studio/` workspace **flagged**, not filtered:
an operator may want to register a repo that is *not yet* on sdlc-studio precisely to adopt the process
and watch it populate. Type-neutral to source: local-source projects are unaffected.

## Impact

Removes error-prone URL typing and makes onboarding a repo a browse-and-click. The flag guides the
operator to ready workspaces while still allowing a non-sdlc-studio repo to be added and watched as it
migrates - the "I'm upgrading this project and want to see it appear" case. Pairs with the GitHub
work in RFC-01KXARHK (incremental sync) and CR-01KXARM8 (health) as the GitHub-integration theme.

**Effort:** M

## Acceptance Criteria

- [ ] A backend endpoint lists the repositories a supplied token can see - the user's own repos plus their organisations and org repos - paginated and searchable (name/owner filter), using the GitHub API (`/user/repos`, `/user/orgs`, `/orgs/{org}/repos`)
- [ ] The token is supplied for the browse session and carried onto the created project (stored encrypted, as today); private repos require `repo` scope; the endpoint is rate-limit aware (paginates, backs off on 403)
- [ ] Each listed repo carries an `has_sdlc_studio` flag indicating whether it contains an `sdlc-studio/` directory - detection must not blow the rate limit (e.g. lazy/on-demand per repo, or a single tree lookup when a repo is expanded), and **all** repos remain listed regardless of the flag
- [ ] `ProjectForm`'s GitHub flow offers the selector: enter/choose a token, browse/search repos + orgs, sdlc-studio repos are visually flagged (badge), and selecting one auto-fills `repo_url`/`repo_branch`/`repo_path`; manual entry remains available as a fallback
- [ ] Tests cover the list/search/flag endpoint (mocked GitHub API) and the picker's flag rendering + auto-fill

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-12 | Elena Foss | Raised |
