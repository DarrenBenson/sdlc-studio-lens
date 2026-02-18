# TS0035: Document View Navigation - Test Specification

> **Status:** Complete
> **Story:** [US0035: Document View Navigation](../stories/US0035-document-view-navigation.md)
> **Epic:** [EP0008: Document Relationship Navigation](../epics/EP0008-document-relationship-navigation.md)
> **Created:** 2026-02-18

## Test Cases

| TC ID | Description | Type | Status |
|-------|-------------|------|--------|
| TC0372 | Hierarchy breadcrumbs show ancestor chain for plan (3 levels) | Component | Automated |
| TC0373 | Ancestor breadcrumb links have correct href | Component | Automated |
| TC0374 | Related panel shows parent documents in sidebar | Component | Automated |
| TC0375 | Related panel shows child documents in sidebar | Component | Automated |
| TC0376 | Relationships panel hidden when no parents or children | Component | Automated |
| TC0377 | Document renders when relationships API fails | Component | Automated |
| TC0378 | Story field shown in properties sidebar | Component | Automated |

## Test File

- `frontend/src/pages/DocumentView.test.tsx` - 16 tests (9 existing + 7 new)

## Summary

| Metric | Value |
|--------|-------|
| Total Test Cases | 7 |
| Total Test Functions | 7 |
| All Passing | Yes |
