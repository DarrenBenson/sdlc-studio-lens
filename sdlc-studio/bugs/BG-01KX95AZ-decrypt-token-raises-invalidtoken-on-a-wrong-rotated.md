# BG-01KX95AZ: decrypt_token raises InvalidToken on a wrong/rotated key, 500-ing the whole project list

> **Status:** Fixed
> **Triaged-by:** Darren; human; v3
> **Severity:** Medium
> **Verification depth:** functional
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio file
> **Raised-by:** Priya Nair; persona; v3

## Summary

crypto.py `decrypt_token` calls `fernet.decrypt(...)` with no try/except; cryptography raises `InvalidToken` when the configured key cannot decrypt an `enc:v1:` value (key rotated/changed/corrupted). `mask_token` calls it for every project in `_project_response`, so a single undecryptable token makes the entire `GET /projects` and `GET /projects/{slug}` fail (generic 500); sync of an affected project also 500s. A recoverable misconfiguration becomes a hard availability failure on a bulk endpoint. (Matches a known deferred follow-up.)

## Steps to Reproduce

Configure `SDLC_LENS_TOKEN_ENCRYPTION_KEY`, store a github project token, then change/rotate the key; GET /projects returns 500 for ALL projects, not just the affected one.

## Proposed Fix

Wrap the fernet.decrypt in try/except InvalidToken; for `mask_token` return a sentinel ('****'/None) and log a warning naming the affected project; for the sync path set a clear `sync_error` ('stored token could not be decrypted - re-enter the access token') instead of a bare 500.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Filed |
