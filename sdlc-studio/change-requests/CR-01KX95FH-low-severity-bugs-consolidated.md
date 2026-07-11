# CR-01KX95FH: Low-severity bugs (consolidated)

> **Status:** Proposed
> **Depends on:** CR-01KX95HS
> **Triaged-by:** Darren; human; v3
> **Priority:** Low
> **Type:** Improvement
> **Date:** 2026-07-11
> **Consolidation:** low-severity-bugs
> **Created-by:** sdlc-studio file
> **Raised-by:** Tomas Reinholt; persona; v3

## Summary

A themed consolidation of Low-severity findings that individually do not warrant a standalone artefact (triage noise control, schema v3). Triage the batch, then action or reject as one.

## Consolidated Findings

- **id_head mis-reads a hyphenated word as a v3 ULID id**: sdlc_ids `_ID_HEAD_RE` ULID branch is case-insensitive Crockford base32, so an 8+ letter word without i/l/o/u after a known prefix is read as a ULID: id_head('PL-answered')='PL-answered' (type plan), 'US-abcdefgh', 'TS-standby0'. Real v3 ids always contain digits, so exposure is low, but it is a latent correctness gap and untested.
- **_strip_decoration truncates a custom status containing ' - ' before extra_vocab can match**: sdlc_status `_strip_decoration` cuts at the first ' - '/'(' separator BEFORE the (longest-first) vocab match, so a project status_vocab token with an internal ' - ' is silently truncated: canonical_status('Ready - for QA', 'story', extra_vocab=['Ready - for QA']) -> 'Ready', contradicting the documented extra_vocab contract. Standard vocab has no internal ' - ', so impact is limited to custom vocabularies; untested.
- **Unbounded GitHub tarball download and in-memory gzip decompression (resource exhaustion)**: fetch_github_files reads the entire tarball via response.content and _extract_md_from_tarball iterates every member into memory with no cap on response size, decompressed size, or per-member size. repo_url/branch are operator-supplied and may point at an untrusted/huge/gzip-bomb repo, which can exhaust the single-process service's memory. Self-inflicted on a LAN tool, but unbounded external input.

## Impact

Individually minor, but together they erode trust in the id/status parsing the whole app depends on (phantom ids from word-shaped tails, silently truncated custom statuses) and add an unbounded-input resource risk on the GitHub sync path.

**Effort:** M

## Acceptance Criteria

- [ ] id_head requires a digit in the ULID tail so `XX-<word>` is rejected (with a negative test)
- [ ] an extra_vocab/vocab token containing ' - ' canonicalises to itself, not a truncation
- [ ] the GitHub tarball download + decompression are bounded (byte cap + decompressed budget) with a clear sync_error when exceeded

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Consolidation opened |
