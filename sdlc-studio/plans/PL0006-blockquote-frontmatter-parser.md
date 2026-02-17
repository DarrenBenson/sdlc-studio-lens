# PL0006: Blockquote Frontmatter Parser - Implementation Plan

> **Status:** Complete
> **Story:** [US0006: Blockquote Frontmatter Parser](../stories/US0006-blockquote-frontmatter-parser.md)
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Created:** 2026-02-17
> **Language:** Python

## Overview

Implement a pure function parser that extracts structured metadata from sdlc-studio markdown documents using the `> **Key:** Value` blockquote frontmatter format. Returns a typed ParseResult containing the document title, metadata dictionary, and body content. This parser is the first component in the EP0002 document processing pipeline and has no external dependencies.

## Acceptance Criteria Summary

| AC | Name | Description |
|----|------|-------------|
| AC1 | Parse standard fields | Blockquote `> **Key:** Value` lines extracted to metadata dict |
| AC2 | Extract title | First `#` heading returned as title |
| AC3 | Multi-line values | Continuation blockquote lines concatenated with space |
| AC4 | Empty metadata | No frontmatter returns empty dict and full body |
| AC5 | Skip malformed lines | Invalid blockquote lines skipped, valid ones parsed |

---

## Technical Context

### Language & Framework
- **Primary Language:** Python 3.12+
- **Framework:** None (pure function, no web framework)
- **Test Framework:** pytest >=8.0.0

### Relevant Best Practices
- Type hints on all public functions
- Specific exception handling (no bare except)
- Logging module (not print)
- Ruff for linting and formatting
- dataclass for ParseResult

### Library Documentation (Context7)

| Library | Context7 ID | Key Patterns |
|---------|-------------|--------------|
| Python re | stdlib | re.match, re.compile for `> **Key:** Value` pattern |
| Python dataclasses | stdlib | @dataclass for ParseResult |

### Existing Patterns

US0001 establishes the backend project structure under `backend/src/sdlc_lens/`. This story adds a new `services/parser.py` module following the same package layout.

---

## Recommended Approach

**Strategy:** TDD
**Rationale:** Pure function with clear input/output contract, 10 edge cases, and 15 test scenarios. Every AC has concrete Given/When/Then values. Ideal for test-first development.

### Test Priority
1. Standard field extraction unit tests (AC1 - core functionality)
2. Title extraction (AC2 - simple regex)
3. Multi-line value handling (AC3 - trickiest logic)
4. No frontmatter handling (AC4 - boundary case)
5. Malformed line skipping (AC5 - robustness)
6. Edge cases (colons in values, empty values, CRLF, etc.)

---

## Implementation Tasks

| # | Task | File | Depends On | Status |
|---|------|------|------------|--------|
| 1 | Define ParseResult dataclass | `backend/src/sdlc_lens/services/parser.py` | - | [ ] |
| 2 | Implement frontmatter block detection | `backend/src/sdlc_lens/services/parser.py` | 1 | [ ] |
| 3 | Implement key-value extraction regex | `backend/src/sdlc_lens/services/parser.py` | 2 | [ ] |
| 4 | Implement multi-line value continuation | `backend/src/sdlc_lens/services/parser.py` | 3 | [ ] |
| 5 | Implement title extraction from first heading | `backend/src/sdlc_lens/services/parser.py` | 1 | [ ] |
| 6 | Implement body separation logic | `backend/src/sdlc_lens/services/parser.py` | 2 | [ ] |
| 7 | Implement standard field mapping (story_points as int) | `backend/src/sdlc_lens/services/parser.py` | 3 | [ ] |
| 8 | Write unit tests for standard field parsing | `backend/tests/test_parser.py` | 3 | [ ] |
| 9 | Write unit tests for edge cases | `backend/tests/test_parser.py` | 4, 7 | [ ] |

### Parallel Execution Groups

| Group | Tasks | Prerequisite |
|-------|-------|--------------|
| Data Model | 1 | None |
| Core Parser | 2, 3, 4, 5, 6, 7 | Group: Data Model |
| Tests | 8, 9 | Group: Core Parser |

---

## Implementation Phases

### Phase 1: Data Model
**Goal:** Define the ParseResult return type

- [ ] Create `backend/src/sdlc_lens/services/parser.py`
- [ ] Define `ParseResult` dataclass with fields: title (str | None), metadata (dict[str, str]), body (str)
- [ ] Define standard field constants: STATUS, OWNER, PRIORITY, STORY_POINTS, EPIC, CREATED, TYPE

**Files:**
- `backend/src/sdlc_lens/services/parser.py` - Parser module

### Phase 2: Core Parser Logic
**Goal:** Implement the parse_document function

- [ ] Compile regex pattern for `> **Key:** Value` extraction
- [ ] Implement frontmatter block detection (contiguous blockquote lines from start)
- [ ] Implement key normalisation (Title Case to snake_case)
- [ ] Implement multi-line value continuation (lines starting with `> ` but not `> **`)
- [ ] Implement title extraction from first `# ` heading
- [ ] Implement body extraction (content after frontmatter block)
- [ ] Implement story_points integer conversion (None for non-numeric)
- [ ] Handle CRLF line endings (normalise to LF before parsing)

**Files:**
- `backend/src/sdlc_lens/services/parser.py` - All parser logic

### Phase 3: Testing
**Goal:** Verify all acceptance criteria and edge cases

- [ ] Create `backend/tests/test_parser.py`
- [ ] Write tests for standard field extraction (status, owner, priority)
- [ ] Write tests for story_points integer parsing
- [ ] Write tests for title extraction
- [ ] Write tests for multi-line values
- [ ] Write tests for empty/no frontmatter
- [ ] Write tests for malformed line skipping
- [ ] Write tests for all 10 edge cases

| AC | Verification Method | File Evidence | Status |
|----|---------------------|---------------|--------|
| AC1 | parse_document returns correct metadata dict | `tests/test_parser.py` | Pending |
| AC2 | parse_document returns correct title | `tests/test_parser.py` | Pending |
| AC3 | Multi-line values concatenated correctly | `tests/test_parser.py` | Pending |
| AC4 | Empty metadata for missing frontmatter | `tests/test_parser.py` | Pending |
| AC5 | Malformed lines skipped | `tests/test_parser.py` | Pending |

---

## Edge Case Handling

| # | Edge Case (from Story) | Handling Strategy | Phase |
|---|------------------------|-------------------|-------|
| 1 | Document with only frontmatter, no body | Return metadata and empty body string | Phase 2 |
| 2 | Document with only body, no frontmatter | Return empty metadata dict and full body | Phase 2 |
| 3 | Nested blockquotes (`>> **Key:** Value`) | Only match single `> ` prefix; nested quotes treated as body | Phase 2 |
| 4 | Colon in value (`> **URL:** http://example.com`) | Split on first `: ` after key; rest is value | Phase 2 |
| 5 | Empty value (`> **Owner:**`) | Map key with empty string value | Phase 2 |
| 6 | Non-numeric story_points (`> **Story Points:** Large`) | story_points returns None; raw value in metadata | Phase 2 |
| 7 | Very large document (>100KB) | No special handling; parser is line-based, efficient | Phase 2 |
| 8 | Windows CRLF line endings | Normalise to LF before splitting | Phase 2 |
| 9 | Frontmatter not at document start (preceded by blank lines) | Still parse if blockquote block is contiguous | Phase 2 |
| 10 | Multiple blockquote blocks | Only first contiguous blockquote block is frontmatter | Phase 2 |

**Coverage:** 10/10 edge cases handled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Regex too greedy (captures body blockquotes) | Medium | Only parse contiguous blockquote block from document start |
| Key normalisation edge cases | Low | Use explicit mapping for standard fields; snake_case for extras |
| Performance on large documents | Low | Line-based parsing; no full-content regex |

---

## Definition of Done

- [ ] All acceptance criteria implemented
- [ ] Unit tests written and passing
- [ ] Edge cases handled
- [ ] Code follows Python best practices (type hints, dataclasses)
- [ ] Ruff linting passes
- [ ] ParseResult is importable from sdlc_lens.services.parser

---

## Notes

- This is a pure function with no side effects - no database, no filesystem I/O.
- The parser will be called by the sync service (US0007) for each document.
- Standard fields (status, owner, priority, story_points, epic) are extracted to dedicated dict keys. All other key-value pairs go into the same metadata dict for JSON storage.
- Key normalisation: "Story Points" to "story_points", "Status" to "status".
