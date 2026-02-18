# PL0035: Document View Navigation - Implementation Plan

> **Status:** Complete
> **Story:** [US0035: Document View Navigation](../stories/US0035-document-view-navigation.md)
> **Epic:** [EP0008: Document Relationship Navigation](../epics/EP0008-document-relationship-navigation.md)
> **Created:** 2026-02-18
> **Language:** TypeScript (React)

## Overview

Add hierarchy breadcrumbs and a relationships sidebar panel to the DocumentView page. Fetch related documents in parallel with the document itself using the `/related` endpoint from US0034.

## Implementation Summary

### Types (types/index.ts)
- [x] Add `epic` and `story` to `DocumentListItem`
- [x] Add `story` to `DocumentDetail`
- [x] Add `RelatedDocumentItem` and `DocumentRelationships` interfaces

### API Client (api/client.ts)
- [x] Add `fetchRelatedDocuments(slug, type, docId)` function
- [x] Import `DocumentRelationships` type

### DocumentView Page (pages/DocumentView.tsx)
- [x] Parallel fetch: `Promise.all([fetchDocument, fetchRelatedDocuments.catch(() => null)])`
- [x] Hierarchy breadcrumbs: Project / Documents / EP0007 / US0028 (ancestors, furthest first)
- [x] Breadcrumb links use clean doc_id prefix (split on `-`)
- [x] Related documents panel below Properties sidebar
- [x] Parents section with TypeBadge, title, StatusBadge
- [x] Children section with same layout
- [x] Panel hidden when no relationships
- [x] Graceful fallback when relationships API fails
- [x] Story field shown in Properties sidebar

### Tests (DocumentView.test.tsx)
- [x] TC0372-TC0378: 7 new tests for relationship navigation
- [x] Updated mock to include `fetchRelatedDocuments`
- [x] All 16 tests pass (9 existing + 7 new)

## Definition of Done

- [x] All acceptance criteria implemented
- [x] Frontend tests passing (143 total)
- [x] TypeScript compilation clean
- [x] No regressions
