# TS0036: Document Tree View - Test Specification

> **Status:** Complete
> **Story:** [US0036: Document Tree View](../stories/US0036-document-tree-view.md)
> **Epic:** [EP0008: Document Relationship Navigation](../epics/EP0008-document-relationship-navigation.md)
> **Created:** 2026-02-18

## Test Cases

| TC ID | Description | Type | Status |
|-------|-------------|------|--------|
| TC0379 | buildTree produces correct hierarchy (epics at root, stories nested, plans nested, sorted) | Unit | Automated |
| TC0380 | Orphan documents placed at root when parent not found | Unit | Automated |
| TC0381 | Page renders at /projects/:slug/tree | Component | Automated |
| TC0382 | Type badges shown on nodes | Component | Automated |
| TC0383 | Status badges shown on nodes | Component | Automated |
| TC0384 | Document title links to document view page | Component | Automated |
| TC0385 | Expand/collapse toggles work | Component | Automated |
| TC0386 | Empty project shows message | Component | Automated |
| TC0387 | Loading state shown while fetching | Component | Automated |
| TC0388 | Error state shown when API fails | Component | Automated |
| TC0389 | Breadcrumb navigation (Project / Tree View) | Component | Automated |

## Test File

- `frontend/src/pages/DocumentTree.test.tsx` - 14 test functions

## Summary

| Metric | Value |
|--------|-------|
| Total Test Cases | 11 |
| Total Test Functions | 14 |
| All Passing | Yes |
