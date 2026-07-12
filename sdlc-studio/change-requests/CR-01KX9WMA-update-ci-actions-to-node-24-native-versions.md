# CR-01KX9WMA: Update CI actions to Node-24-native versions (Node 20 deprecation)

> **Status:** Proposed
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

- [ ] Every action in `release.yml` is pinned to a Node-24-native release SHA (with a version comment), verified via `gh api`/the action's releases
- [ ] The release run produces no Node-20 deprecation annotation
- [ ] A `.github/dependabot.yml` enables the `github-actions` ecosystem so the pins stay current

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-12 | Priya Nair | Raised |
