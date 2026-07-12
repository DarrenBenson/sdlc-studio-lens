# CR-01KXB377: Overhaul the add-project card: browse every connection at once, auto-fill the rest

> **Status:** Complete
> **Verification depth:** functional
> **Triaged-by:** Darren; human; v3
> **Depends on:** CR-01KXAZX9
> **Created:** 2026-07-12
> **Created-by:** sdlc-studio new
> **Raised-by:** Darren; human; v3
> **Priority:** High
> **Type:** Improvement

## Summary

The add-project card grew by accretion (local path -> GitHub URL -> repo selector -> connection picker) and
now leaks its implementation into the UI. Operator feedback after using it on 0.4.0:

1. **"It asks which GitHub connection."** Browsing is scoped to ONE credential (`ProjectForm.handleBrowse`
   sends a single `credential`), so with two connections registered the operator must browse twice to see
   their own repositories. Nobody thinks "which token shall I browse with"; they think "show me my repos".
   The credential is an implementation detail, not a question.
2. **"Why do I have to give a branch and an sdlc path?"** Both are already known. `handleSelectRepo`
   *already* overwrites the branch with the repo's real `default_branch` from the API, so the visible
   `main` default is a value we immediately discard; and `repo_path` (`sdlc-studio`) is the very directory
   the `has_sdlc_studio` badge check already probes. The form asks for two things the system has determined.
3. **The name is not auto-filled.** Selecting a repo fills the URL and branch but leaves the operator to
   hand-type a name that is almost always the repo's own name.

Rework the card around the operator's intent - *pick a repository* - and derive everything else.

## Impact

Adding a project is the first thing a new user does and the thing done repeatedly as repos are onboarded;
it is currently the clunkiest surface in the product. The overhaul turns a token choice plus a URL paste
plus three typed fields into **browse -> click**. It also removes a class of error (a mistyped branch or
path silently yielding an empty project) by deriving both from the repo itself.

**Effort:** M

## Acceptance Criteria

- [ ] **Browse spans every registered connection.** A backend endpoint aggregates the repositories visible across ALL stored connections (de-duplicated by `full_name`), so the operator never chooses a credential to browse. Each entry records which connection surfaced it, and that connection is what the created project is bound to. A per-connection browse remains available internally but is not the primary flow
- [ ] **Partial failure never empties the list.** A connection whose token fails (expired, rate-limited, cannot list orgs - see BG-01KXB3QF) contributes what it can; the browse returns the other connections' repos and reports the degraded ones as a non-fatal notice naming them, rather than failing wholesale
- [ ] **Selecting a repo fills everything.** Name (from the repo name, editable), `repo_url`, `repo_branch` (the repo's real `default_branch`), and `repo_path` (the detected `sdlc-studio/` directory, reusing the existing check) are all derived. The operator's minimum path to a created project is: open the card, click a repo, submit
- [ ] **Branch and sdlc path move behind an "Advanced" disclosure**, pre-filled with the derived values and editable for the rare override (a non-default branch, or a workspace not at `sdlc-studio/`). They are not part of the default flow
- [ ] **Fallbacks preserved.** Manual repo-URL entry, a one-off raw token for an unregistered credential, and the local-path source type all still work; local-source projects are unaffected by this change
- [ ] **The card is coherent.** Source type, credential, repository and derived settings read as one flow rather than four accreted ones; the sdlc-studio badge still marks ready workspaces without filtering non-adopted repos (per CR-01KXAS75)
- [ ] Tests cover: cross-connection aggregation and de-duplication; a degraded connection yielding a partial list plus a notice; auto-fill of name/branch/path on selection; the Advanced override; and the manual/local fallbacks

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-12 | Darren | Raised from hands-on feedback on the 0.4.0 add-project flow |
