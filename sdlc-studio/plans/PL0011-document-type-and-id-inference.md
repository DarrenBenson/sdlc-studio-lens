# PL0011: Document Type and ID Inference - Implementation Plan

> **Status:** Complete
> **Story:** [US0011: Document Type and ID Inference](../stories/US0011-document-type-and-id-inference.md)
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Created:** 2026-02-17
> **Language:** Python

## Overview

Implement a pure function that infers document type and ID from filename patterns and directory context. Uses a priority-ordered rule set: prefix patterns (EP, US, BG, PL, TS), singleton names (prd.md, trd.md, tsd.md, personas.md), directory fallback, and a default "other" type. Excludes `_index.md` files from import.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Prefix inference | EP, US, BG filename prefixes infer epic, story, bug |
| AC2 | Singleton inference | prd.md, trd.md, tsd.md infer prd, trd, tsd |
| AC3 | ID from prefixed filename | EP0001-project-management.md yields doc_id "EP0001" |
| AC4 | ID from singleton | prd.md yields doc_id "prd" |
| AC5 | Unknown defaults to other | brand-guide.md yields type "other", id "brand-guide" |

---

## Technical Context

### Language & Framework
- **Primary Language:** Python 3.12+
- **Framework:** None (pure function)
- **Test Framework:** pytest >=8.0.0

### Relevant Best Practices
- Type hints on all public functions
- Compiled regex patterns as module-level constants
- Ruff for linting and formatting

### Library Documentation (Context7)

| Library | Context7 ID | Key Patterns |
|---------|-------------|--------------|
| Python re | stdlib | re.match for prefix pattern matching |
| Python pathlib | stdlib | PurePosixPath for path decomposition |

### Existing Patterns

Backend project structure established by US0001. This story adds `utils/inference.py` alongside existing `utils/slug.py`.

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** Pure function with pattern matching rules, 7 edge cases, and 13 test scenarios. Each rule maps directly to a test case. Ideal for test-first with parametrised tests.

### Test Priority
1. Prefix pattern matching (EP, US, BG, PL, TS)
2. Singleton filenames (prd, trd, tsd, personas)
3. ID extraction from prefixed filenames
4. _index.md exclusion
5. Directory fallback
6. Default "other" type
7. Edge cases (case insensitivity, prefix without number)

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Define return type and SKIP sentinel | `backend/src/sdlc_lens/utils/inference.py` | - | [ ] |
| 2 | Implement prefix pattern rules (EP, US, BG, PL, TS) | `backend/src/sdlc_lens/utils/inference.py` | 1 | [ ] |
| 3 | Implement singleton name rules | `backend/src/sdlc_lens/utils/inference.py` | 1 | [ ] |
| 4 | Implement _index.md skip logic | `backend/src/sdlc_lens/utils/inference.py` | 1 | [ ] |
| 5 | Implement directory fallback logic | `backend/src/sdlc_lens/utils/inference.py` | 2 | [ ] |
| 6 | Implement default "other" fallback | `backend/src/sdlc_lens/utils/inference.py` | 2 | [ ] |
| 7 | Write parametrised unit tests | `backend/tests/test_inference.py` | 2, 3, 4, 5, 6 | [ ] |

### Parallel Execution Groups

| Group | Tasks | Prerequisite |
|-------|-------|--------------|
| Type Definition | 1 | None |
| Rules | 2, 3, 4, 5, 6 | Group: Type Definition |
| Tests | 7 | Group: Rules |

---

## Implementation Phases

### Phase 1: Core Inference Function
**Goal:** Implement the complete infer_type_and_id function

- [ ] Create `backend/src/sdlc_lens/utils/inference.py`
- [ ] Define return type: tuple[str, str] or NamedTuple(doc_type, doc_id)
- [ ] Define SKIP sentinel for _index.md files
- [ ] Compile prefix regex patterns as module constants
- [ ] Define singleton filename mapping dict
- [ ] Define directory-to-type mapping dict
- [ ] Implement priority-ordered rule chain:
  1. `_index.md` check returns SKIP
  2. Prefix patterns (EP\d{4}, US\d{4}, BG\d{4}, PL\d{4}, TS\d{4})
  3. Singleton names (prd.md, trd.md, tsd.md, personas.md)
  4. Directory fallback (epics/ to epic, stories/ to story, etc.)
  5. Default: type "other", id = filename stem

**Files:**
- `backend/src/sdlc_lens/utils/inference.py` - Inference function

### Phase 2: Testing
**Goal:** Verify all rules and edge cases

- [ ] Create `backend/tests/test_inference.py`
- [ ] Write parametrised tests for all prefix patterns
- [ ] Write tests for singleton filenames
- [ ] Write tests for _index.md exclusion
- [ ] Write tests for directory fallback
- [ ] Write tests for default "other" type
- [ ] Write tests for edge cases (case insensitivity, prefix without number)

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | Prefix patterns return correct types | `tests/test_inference.py` | Pending |
| AC2 | Singleton filenames return correct types | `tests/test_inference.py` | Pending |
| AC3 | doc_id extracted from prefixed filenames | `tests/test_inference.py` | Pending |
| AC4 | Singleton doc_id matches filename | `tests/test_inference.py` | Pending |
| AC5 | Unknown patterns default to "other" | `tests/test_inference.py` | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | _index.md in any directory | Return SKIP sentinel; caller excludes from import | Phase 1 |
| 2 | EP0001.md in wrong directory (stories/) | Filename prefix takes priority over directory | Phase 1 |
| 3 | Prefix without number (EP-overview.md) | No match on EP\d{4}; falls through to directory or "other" | Phase 1 |
| 4 | Nested subdirectory (epics/archive/EP0001.md) | Type from filename prefix; directory depth ignored | Phase 1 |
| 5 | Duplicate doc_id across types (EP0001, US0001) | Unique constraint (project_id, doc_type, doc_id) differentiates | Phase 1 |
| 6 | Uppercase extension .MD | Case-insensitive comparison on extension | Phase 1 |
| 7 | Unknown prefix (WF0001-workflow.md) | Falls through to directory or "other" | Phase 1 |

**Coverage:** 7/7 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| New document type prefixes added later | Low | Rule list is a simple dict; easy to extend |
| Path separator differences (Windows vs Unix) | Low | Use PurePosixPath for consistent path handling |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit tests written and passing
- [ ] Edge cases handled
- [ ] Code follows Python best practices (type hints, compiled regex)
- [ ] Ruff linting passes
- [ ] infer_type_and_id is importable from sdlc_lens.utils.inference

---

## Notes

- This is a pure function with no side effects - no database, no filesystem I/O.
- Called by the sync service (US0007) for each file during filesystem walk.
- The SKIP sentinel for _index.md allows the caller to decide how to handle exclusion.
- Filename prefix always takes priority over directory context.
