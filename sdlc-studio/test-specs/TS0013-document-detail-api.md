# TS0013: Document Detail API

> **Status:** Done
> **Epic:** [EP0003: Document Browsing](../epics/EP0003-document-browsing.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0013 - Document Detail API. Covers single document retrieval with full content, metadata, and error handling.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0013](../stories/US0013-document-detail-api.md) | Document Detail API | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0013 | AC1 | Full content retrieval | TC0159, TC0160, TC0166, TC0167 | Covered |
| US0013 | AC2 | 404 unknown document | TC0162, TC0164 | Covered |
| US0013 | AC3 | 404 unknown project | TC0163 | Covered |
| US0013 | AC4 | Metadata includes extras | TC0161, TC0168 | Covered |

**Coverage:** 4/4 ACs covered

---

## Test Cases

### TC0159: GET document returns full content
**Type:** Integration | **Priority:** Critical | **Story:** US0013 AC1

### TC0160: Response has all standard fields
**Type:** Integration | **Priority:** Critical | **Story:** US0013 AC1

### TC0161: Metadata JSON contains non-standard frontmatter
**Type:** Integration | **Priority:** High | **Story:** US0013 AC4

### TC0162: 404 for unknown doc_id
**Type:** Integration | **Priority:** Critical | **Story:** US0013 AC2

### TC0163: 404 for unknown project slug
**Type:** Integration | **Priority:** Critical | **Story:** US0013 AC3

### TC0164: 404 for type mismatch
**Type:** Integration | **Priority:** High | **Story:** US0013 AC2

### TC0165: Null optional fields returned correctly
**Type:** Integration | **Priority:** Medium | **Story:** US0013 AC1

### TC0166: file_path and file_hash present
**Type:** Integration | **Priority:** Medium | **Story:** US0013 AC1

### TC0167: synced_at timestamp present
**Type:** Integration | **Priority:** Medium | **Story:** US0013 AC1

### TC0168: Empty metadata returns null
**Type:** Integration | **Priority:** Medium | **Story:** US0013 AC4

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0159 | Full content | Pass | `test_api_document_detail.py` |
| TC0160 | All standard fields | Pass | `test_api_document_detail.py` |
| TC0161 | Metadata JSON | Pass | `test_api_document_detail.py` |
| TC0162 | 404 unknown doc_id | Pass | `test_api_document_detail.py` |
| TC0163 | 404 unknown project | Pass | `test_api_document_detail.py` |
| TC0164 | 404 type mismatch | Pass | `test_api_document_detail.py` |
| TC0165 | Null optional fields | Pass | `test_api_document_detail.py` |
| TC0166 | file_path and file_hash | Pass | `test_api_document_detail.py` |
| TC0167 | synced_at timestamp | Pass | `test_api_document_detail.py` |
| TC0168 | Empty metadata | Pass | `test_api_document_detail.py` |

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec from US0013 story |
