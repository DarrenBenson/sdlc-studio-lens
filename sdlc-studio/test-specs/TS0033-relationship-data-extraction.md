# TS0033: Relationship Data Extraction - Test Specification

> **Status:** Complete
> **Story:** [US0033: Relationship Data Extraction](../stories/US0033-relationship-data-extraction.md)
> **Epic:** [EP0008: Document Relationship Navigation](../epics/EP0008-document-relationship-navigation.md)
> **Created:** 2026-02-18

## Test Cases

| TC ID | Description | Type | Status |
|-------|-------------|------|--------|
| TC0343 | extract_doc_id extracts ID from markdown link with title | Unit | Automated |
| TC0344 | extract_doc_id returns plain ID unchanged | Unit | Automated |
| TC0345 | extract_doc_id returns None for None input | Unit | Automated |
| TC0346 | extract_doc_id returns None for empty string | Unit | Automated |
| TC0347 | extract_doc_id handles link without colon-title | Unit | Automated |
| TC0348 | extract_doc_id returns raw value for non-matching format | Unit | Automated |
| TC0349 | _STANDARD_FIELDS includes "story" | Unit | Automated |
| TC0350 | _build_doc_attrs cleans epic markdown link to plain ID | Unit | Automated |
| TC0351 | _build_doc_attrs populates story from metadata | Unit | Automated |
| TC0352 | _build_doc_attrs null epic and story for docs without them | Unit | Automated |
| TC0353 | _build_doc_attrs preserves plain ID unchanged | Unit | Automated |
| TC0354 | Document model has story column | Unit | Automated |
| TC0355 | story column is in the table definition | Unit | Automated |
| TC0356 | Parser extracts story field from blockquote frontmatter | Unit | Automated |
| TC0357 | Parser extracts epic field from blockquote frontmatter | Unit | Automated |

## Test File

- `backend/tests/test_relationship_extraction.py` - 28 tests (15 extract_doc_id + 3 standard fields + 5 build_doc_attrs + 3 model + 2 parser)

## Summary

| Metric | Value |
|--------|-------|
| Total Test Cases | 15 |
| Total Test Functions | 28 |
| All Passing | Yes |
