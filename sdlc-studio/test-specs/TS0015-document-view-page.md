# TS0015: Document View Page

> **Status:** Done
> **Epic:** [EP0003: Document Browsing](../epics/EP0003-document-browsing.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0015 - Document View Page. Covers markdown rendering, metadata sidebar, and error handling.

## AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0015 | AC1 | Render markdown | TC0179, TC0180 | Covered |
| US0015 | AC3 | Frontmatter sidebar | TC0181, TC0182 | Covered |
| US0015 | AC5 | Document metadata bar | TC0183, TC0184 | Covered |

**Coverage:** 3/5 ACs covered (AC2 syntax highlighting and AC4 table rendering tested visually)

## Test Cases (TC0179-TC0186)

- TC0179: Document title rendered
- TC0180: Markdown content rendered
- TC0181: Frontmatter sidebar shows status badge
- TC0182: Frontmatter sidebar shows owner and priority
- TC0183: File path shown
- TC0184: Sync timestamp shown
- TC0185: 404 document shows error state
- TC0186: Loading state shown during fetch

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0179 | Document title | Pass | `DocumentView.test.tsx` |
| TC0180 | Markdown content | Pass | `DocumentView.test.tsx` |
| TC0181 | Status badge in sidebar | Pass | `DocumentView.test.tsx` |
| TC0182 | Owner and priority | Pass | `DocumentView.test.tsx` |
| TC0183 | File path | Pass | `DocumentView.test.tsx` |
| TC0184 | Sync timestamp | Pass | `DocumentView.test.tsx` |
| TC0185 | 404 error state | Pass | `DocumentView.test.tsx` |
| TC0186 | Loading state | Pass | `DocumentView.test.tsx` |

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec from US0015 story |
