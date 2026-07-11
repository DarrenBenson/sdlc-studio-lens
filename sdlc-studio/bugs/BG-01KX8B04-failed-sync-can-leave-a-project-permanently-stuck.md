# BG-01KX8B04: Failed sync can leave a project permanently stuck in 'syncing'

> **Status:** Fixed
> **Depends on:** BG-01KX8BFP
> **Triaged-by:** Darren; human; v3
> **Severity:** Medium
> **Verification depth:** functional
> **Created:** 2026-07-11
> **Created-by:** sdlc-studio file
> **Raised-by:** Tomas Reinholt; persona; v3

## Summary

`run_sync_task` (sync.py:52-59) wraps the initial select and `sync_project` with no try/except, while `trigger_sync` has already committed `sync_status`='syncing'. `sync_project` self-handles most errors, but its own except block commits (`sync_engine.py`:347) which can re-raise under DB contention, and the initial select can fail. Any escape leaves the row 'syncing', so every future POST /sync returns 409 forever. Related: the check-then-set in `trigger_sync` (sync.py:36-41) is non-atomic, letting two concurrent syncs both pass the guard.

## Steps to Reproduce

Force `sync_project` (or its error handler's commit) to raise; observe the project remains `sync_status`='syncing' and all subsequent sync requests 409 until a manual DB edit.

## Proposed Fix

Wrap `run_sync_task` in try/except that on failure re-fetches the project in a fresh session and sets `sync_status`='error'. Make the transition atomic (UPDATE ... WHERE `sync_status`!='syncing', treat rowcount 0 as in-progress). Add a test forcing `sync_project` to raise.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-11 | audit | Filed |
