# TS0014: Document List Page

> **Status:** Done
> **Epic:** [EP0003: Document Browsing](../epics/EP0003-document-browsing.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0014 - Document List Page. Covers document list rendering, filtering, pagination, and navigation.

## AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0014 | AC1 | Document list with badges | TC0169, TC0170, TC0171 | Covered |
| US0014 | AC2 | Type filter | TC0172 | Covered |
| US0014 | AC3 | Status filter | TC0173 | Covered |
| US0014 | AC4 | Pagination | TC0177 | Covered |
| US0014 | AC5 | Click navigates to view | TC0174 | Covered |

**Coverage:** 5/5 ACs covered

## Test Cases (TC0169-TC0178)

- TC0169: Document list renders document titles
- TC0170: Type badges shown for documents
- TC0171: Status badges shown for documents
- TC0172: Type filter calls API with type param
- TC0173: Status filter calls API with status param
- TC0174: Click navigates to document view route
- TC0175: Empty state shown when no documents
- TC0176: Loading state shown during fetch
- TC0177: Pagination info displayed
- TC0178: Error state on API failure

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0169 | Document titles | Pass | `DocumentList.test.tsx` |
| TC0170 | Type badges | Pass | `DocumentList.test.tsx` |
| TC0171 | Status badges | Pass | `DocumentList.test.tsx` |
| TC0172 | Type filter | Pass | `DocumentList.test.tsx` |
| TC0173 | Status filter | Pass | `DocumentList.test.tsx` |
| TC0174 | Click navigation | Pass | `DocumentList.test.tsx` |
| TC0175 | Empty state | Pass | `DocumentList.test.tsx` |
| TC0176 | Loading state | Pass | `DocumentList.test.tsx` |
| TC0177 | Pagination info | Pass | `DocumentList.test.tsx` |
| TC0178 | Error state | Pass | `DocumentList.test.tsx` |

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec from US0014 story |
