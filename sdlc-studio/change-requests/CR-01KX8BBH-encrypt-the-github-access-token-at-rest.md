# CR-01KX8BBH: Encrypt the GitHub access token at rest

> **Status:** Complete
> **Depends on:** BG-01KX8BJY
> **Triaged-by:** Darren; human; v3
> **Priority:** Medium
> **Type:** Improvement
> **Date:** 2026-07-11
> **Created-by:** sdlc-studio file
> **Raised-by:** Priya Nair; persona; v3

## Summary

project.py:97 persists the raw PAT into a plain Text column (db/models/project.py:28). It is masked in responses (`mask_token)` and not logged, but sits in cleartext in the SQLite DB on the mounted volume; combined with the path-traversal bug it is directly exfiltratable, and any DB backup or volume snapshot leaks it.

## Acceptance Criteria

- [ ] The token is encrypted at rest (app-level envelope encryption with a key from config/env) OR stored via an external secret manager with only a reference in the DB
- [ ] Existing stored tokens are migrated and rotated once encryption is in place
- [ ] DB file permissions are restricted

## Impact

A stored PAT grants read (and possibly write) access to private GitHub repos. In cleartext it is recoverable from the SQLite DB file, any volume snapshot or backup, and - via BG-01KX8B82 (path traversal) - directly over HTTP. Encryption at rest closes the largest single-secret exposure in the app.

**Effort:** M

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Raised |
