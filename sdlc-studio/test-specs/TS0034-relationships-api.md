# TS0034: Relationships API - Test Specification

> **Status:** Complete
> **Story:** [US0034: Relationships API](../stories/US0034-relationships-api.md)
> **Epic:** [EP0008: Document Relationship Navigation](../epics/EP0008-document-relationship-navigation.md)
> **Created:** 2026-02-18

## Test Cases

| TC ID | Description | Type | Status |
|-------|-------------|------|--------|
| TC0358 | GET /related returns 200 with correct response fields | Integration | Automated |
| TC0359 | Story's parents include its epic | Integration | Automated |
| TC0360 | Plan's parents include story and grandparent epic | Integration | Automated |
| TC0361 | Epic's children include its stories (direct only) | Integration | Automated |
| TC0362 | Story's children include plans and test-specs | Integration | Automated |
| TC0363 | Leaf document (plan) has empty children | Integration | Automated |
| TC0364 | Top-level document (epic) has empty parents | Integration | Automated |
| TC0365 | PRD has empty parents and children | Integration | Automated |
| TC0366 | Missing parent reference returns partial chain | Integration | Automated |
| TC0367 | Non-existent document returns 404 | Integration | Automated |
| TC0368 | Non-existent project returns 404 | Integration | Automated |
| TC0369 | Children sorted by type then doc_id | Integration | Automated |
| TC0370 | DocumentDetail response includes story field (AC7) | Integration | Automated |
| TC0371 | DocumentListItem includes epic and story fields (AC8) | Integration | Automated |

## Test File

- `backend/tests/test_api_relationships.py` - 18 test functions

## Summary

| Metric | Value |
|--------|-------|
| Total Test Cases | 14 |
| Total Test Functions | 18 |
| All Passing | Yes |
