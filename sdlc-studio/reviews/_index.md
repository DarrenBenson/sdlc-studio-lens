# Review Findings Index

Registry of all review findings for traceability and audit.

## Summary

| Metric | Value |
| -------- | ------- |
| Total Reviews | 2 |
| Open Critical Issues | 0 |
| Open Important Issues | 0 |
| Last Review | 2026-07-11 |

## Reviews by Artifact

| ID | Artifact | Type | Date | Critical | Important |
|-------|----------|------|------|----------|-----------|
| [RV-0001](RV0001-repository-review-architecture-code-quality-defensive-security.md) | repository | review generate | 2026-07-11 | 3 | 3 |
| [RV-0002](RV0002-repository-review-2-post-v3-codebase-architecture-code.md) | repository | review generate | 2026-07-11 | -- | -- |

## Reviews Requiring Attention

None. All findings from both reviews are closed.

## Closed Findings

RV-0001's three High-severity findings were each filed as a bug and each is **Fixed**:

| Finding | Bug | Status |
| --- | --- | --- |
| Path traversal in the SPA fallback route | [BG-01KX8B82](../bugs/BG-01KX8B82-path-traversal-in-spa-fallback-route-serves-arbitrary.md) | Fixed |
| Sync deletes all documents when the source returns empty (silent data loss) | [BG-01KX8BFP](../bugs/BG-01KX8BFP-sync-deletes-all-documents-when-the-source-returns.md) | Fixed |
| Canonical error shape not applied to 422 / 500 responses | [BG-01KX8BE8](../bugs/BG-01KX8BE8-canonical-error-shape-not-applied-to-validation-422.md) | Fixed |

> **Standing hazard - BG-01KX8BFP.** The fix is the "source returned no documents - refusing to delete
> existing documents" guard in `sync_engine.py`. CR-01KXCAHV changes the sync engine's contract so that a
> clean no-op incremental sync legitimately fetches **zero** files. A guard still keyed off the *fetched*
> set would read that as an empty source and **regress this High-severity data-loss bug on the happy
> path**. The guard must be re-keyed to the manifest. See RFC-01KXARHK decision D6.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-13 | Darren | Corrected a stale summary that still advertised 3 open critical issues and a release blocker, though all three were Fixed on 2026-07-11 (US-01KXCB7V). Recorded the BG-01KX8BFP hazard against CR-01KXCAHV. |
