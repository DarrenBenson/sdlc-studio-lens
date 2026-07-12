# CR-01KX9WMA: Update CI actions to Node-24-native versions (Node 20 deprecation)

> **Status:** In Progress
> **Triaged-by:** Darren; human; v3
> **Created:** 2026-07-12
> **Created-by:** sdlc-studio new
> **Raised-by:** Priya Nair; persona; v3
> **Priority:** Low
> **Type:** Improvement

## Summary

The `v0.2.0` release run flagged: "Node.js 20 is deprecated" - the SHA-pinned actions in
`.github/workflows/release.yml` (`actions/checkout`, `actions/setup-node`, `actions/setup-python`,
`docker/*`, `softprops/action-gh-release`) target the Node 20 runtime and are being force-run on
Node 24. The v3 sprint pinned these to commit SHAs (a security win), which froze them at their
Node-20 era. They still run, but GitHub will eventually stop the Node-20 shim. Bump each pinned SHA
to a Node-24-native release, keeping the SHA-pin + version comment convention, ideally with
Dependabot's `github-actions` ecosystem to keep them current.

## Impact

Non-urgent: CI works today (Node 24 shim). But the deprecation warning will become a hard failure
when GitHub retires the shim, breaking the release pipeline. Bumping now removes the warning and
future-proofs releases; adding Dependabot stops the SHA pins going stale again.

**Effort:** S

## Acceptance Criteria

- [x] Every action in `release.yml` is pinned to a Node-24-native release SHA (with a version comment), verified via `gh api`/the action's releases
- [ ] The release run produces no Node-20 deprecation annotation *(verifies on the next tag/release run - see below)*
- [x] A `.github/dependabot.yml` enables the `github-actions` ecosystem so the pins stay current

## Implementation (2026-07-12)

All 7 actions in `release.yml` re-pinned to their latest **`node24`** releases; each `runs.using`
confirmed `node24` via `gh api repos/<action>/contents/action.yml?ref=<tag>`:

| Action | was | now |
| --- | --- | --- |
| `actions/checkout` (x3) | `34e1148…` v4 | `9c091bb…` v7.0.0 |
| `actions/setup-python` | `a26af69…` v5 | `ece7cb0…` v6.3.0 |
| `actions/setup-node` | `49933ea…` v4 | `48b55a0…` v6.4.0 |
| `docker/setup-buildx-action` | `8d2750c…` v3 | `bb05f3f…` v4.2.0 |
| `docker/login-action` | `c94ce9f…` v3 | `af1e73f…` v4.4.0 |
| `docker/build-push-action` | `10e90e3…` v6 | `53b7df9…` v7.3.0 |
| `softprops/action-gh-release` | `3bb1273…` v2 | `718ea10…` v3.0.1 |

Added `.github/dependabot.yml` (`github-actions` ecosystem, weekly) so the pins stay current.

**Note - major-version bumps:** the SHA freeze also froze the majors, so these are major bumps
(checkout v4->v7, setup-node v4->v6, etc.). Usage here is basic (checkout, `node-version`,
`python-version`, buildx/login/build-push, gh-release with `generate_release_notes`) so no config
changes are needed, but **AC2 is confirmed by the next actual release run** (tag push) showing no
Node-20 annotation - it cannot be verified without a release.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-12 | Priya Nair | Raised |
| 2026-07-12 | Darren Benson | Implemented: all 7 actions re-pinned to node24 releases (verified via gh api) + dependabot.yml added. AC1/AC3 done; AC2 verifies on next release. In review. |
