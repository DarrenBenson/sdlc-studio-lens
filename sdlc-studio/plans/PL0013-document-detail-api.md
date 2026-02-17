# PL0013: Document Detail API - Implementation Plan

> **Status:** Done
> **Story:** [US0013: Document Detail API](../stories/US0013-document-detail-api.md)
> **Epic:** [EP0003: Document Browsing](../epics/EP0003-document-browsing.md)
> **Created:** 2026-02-17
> **Language:** Python (FastAPI)

## Overview

Add a single document retrieval endpoint at `GET /api/v1/projects/{slug}/documents/{type}/{doc_id}`. Returns full content, metadata, and sync information for rendering in the frontend markdown viewer.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Full content retrieval | Returns all fields including raw markdown content |
| AC2 | 404 unknown document | Returns NOT_FOUND for missing doc_id |
| AC3 | 404 unknown project | Returns NOT_FOUND for missing slug |
| AC4 | Metadata includes extras | Non-standard frontmatter in metadata JSON |

---

## Technical Context

### Language & Framework
- **Primary Language:** Python 3.13
- **Framework:** FastAPI + SQLAlchemy async
- **Test Framework:** pytest + httpx AsyncClient

### Existing Patterns
- Document list endpoint already in `api/routes/projects.py`
- Document schemas in `api/schemas/documents.py`
- Service functions in `services/documents.py`

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** Simple query with well-defined response shape.

---

## Implementation Phases

### Phase 1: Schema
- [ ] Add `DocumentDetail` Pydantic schema with all fields

### Phase 2: Service
- [ ] Add `get_document()` service function

### Phase 3: Route
- [ ] Add `GET /projects/{slug}/documents/{type}/{doc_id}` handler

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Tests written and passing
- [ ] Edge cases handled
- [ ] No linting errors
