# PL0036: Document Tree View - Implementation Plan

> **Status:** Complete
> **Story:** [US0036: Document Tree View](../stories/US0036-document-tree-view.md)
> **Epic:** [EP0008: Document Relationship Navigation](../epics/EP0008-document-relationship-navigation.md)
> **Created:** 2026-02-18
> **Language:** TypeScript (React)

## Overview

New tree view page at `/projects/:slug/tree` showing the full document hierarchy built client-side from the document list API. Expand/collapse toggles, type/status badges, and navigation links on every node.

## Implementation Summary

### New Page (pages/DocumentTree.tsx)
- [x] `buildTree()` function: builds tree from flat DocumentListItem array
- [x] Matching: doc.epic → epic doc_id prefix, doc.story → story doc_id prefix
- [x] Orphan handling: unresolved parents placed at root
- [x] Sorting: TYPE_PRIORITY (prd < trd < tsd < epic < story < plan < test-spec < bug), then doc_id
- [x] `TreeNodeRow` recursive component with expand/collapse, TypeBadge, StatusBadge, Link
- [x] Default expand: root nodes with children
- [x] Empty state: "No documents synced yet" with link to project
- [x] Loading and error states

### Route (App.tsx)
- [x] `<Route path="projects/:slug/tree" element={<DocumentTree />} />`

### Navigation Link (ProjectDetail.tsx)
- [x] "Document List" and "Tree View" links in project header

### Tests (DocumentTree.test.tsx)
- [x] TC0379-TC0389: 14 tests (4 unit + 10 integration)

## Definition of Done

- [x] All acceptance criteria implemented
- [x] Frontend tests passing (157 total)
- [x] TypeScript compilation clean
- [x] Backend tests still passing (361 total)
