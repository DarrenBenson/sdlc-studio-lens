# TS0006: Blockquote Frontmatter Parser

> **Status:** Complete
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Created:** 2026-02-17
> **Last Updated:** 2026-02-17

## Overview

Test specification for US0006 - Blockquote Frontmatter Parser. Covers the `parse_document()` pure function that extracts title, metadata, and body from sdlc-studio markdown documents using `> **Key:** Value` blockquote frontmatter format. Tests are entirely unit-level since this is a pure function with no database or filesystem dependencies.

## Scope

### Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| [US0006](../stories/US0006-blockquote-frontmatter-parser.md) | Blockquote Frontmatter Parser | High |

### AC Coverage Matrix

| Story | AC | Description | Test Cases | Status |
|-------|-----|-------------|------------|--------|
| US0006 | AC1 | Parse standard frontmatter fields | TC0069, TC0070, TC0071, TC0072, TC0073 | Covered |
| US0006 | AC2 | Extract title from first heading | TC0074 | Covered |
| US0006 | AC3 | Handle multi-line blockquote values | TC0075 | Covered |
| US0006 | AC4 | Return empty metadata for missing frontmatter | TC0076 | Covered |
| US0006 | AC5 | Skip malformed blockquote lines | TC0077 | Covered |

**Coverage:** 5/5 ACs covered

### Test Types Required

| Type | Required | Rationale |
|------|----------|-----------|
| Unit | Yes | Pure function with deterministic input/output |
| Integration | No | No database or external service dependencies |
| E2E | No | No frontend or API layer |

---

## Environment

| Requirement | Details |
|-------------|---------|
| Prerequisites | Python 3.12+, pytest |
| External Services | None |
| Test Data | Inline markdown strings |

---

## Test Cases

### TC0069: Parse status field from frontmatter

**Type:** Unit | **Priority:** Critical | **Story:** US0006 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Document with `> **Status:** Done` in frontmatter | Frontmatter present |
| When | parse_document(content) is called | Document parsed |
| Then | metadata["status"] equals "Done" | Field extracted |

**Assertions:**
- [ ] metadata["status"] equals "Done"

---

### TC0070: Parse owner field from frontmatter

**Type:** Unit | **Priority:** Critical | **Story:** US0006 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Document with `> **Owner:** Darren` in frontmatter | Frontmatter present |
| When | parse_document(content) is called | Document parsed |
| Then | metadata["owner"] equals "Darren" | Field extracted |

**Assertions:**
- [ ] metadata["owner"] equals "Darren"

---

### TC0071: Parse priority field from frontmatter

**Type:** Unit | **Priority:** High | **Story:** US0006 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Document with `> **Priority:** P0` in frontmatter | Frontmatter present |
| When | parse_document(content) is called | Document parsed |
| Then | metadata["priority"] equals "P0" | Field extracted |

**Assertions:**
- [ ] metadata["priority"] equals "P0"

---

### TC0072: Parse story_points as integer

**Type:** Unit | **Priority:** High | **Story:** US0006 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Document with `> **Story Points:** 5` in frontmatter | Numeric value |
| When | parse_document(content) is called | Document parsed |
| Then | metadata["story_points"] equals integer 5 | Parsed as int |

**Assertions:**
- [ ] metadata["story_points"] equals 5
- [ ] type(metadata["story_points"]) is int

---

### TC0073: Parse epic reference field

**Type:** Unit | **Priority:** High | **Story:** US0006 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Document with `> **Epic:** [EP0001: Project Management](...)` | Link value |
| When | parse_document(content) is called | Document parsed |
| Then | metadata["epic"] contains the full value string | Field extracted |

**Assertions:**
- [ ] metadata["epic"] contains "EP0001"

---

### TC0074: Extract title from first heading

**Type:** Unit | **Priority:** Critical | **Story:** US0006 AC2

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Document with `# EP0001: Project Management` as first heading | Title present |
| When | parse_document(content) is called | Document parsed |
| Then | title equals "EP0001: Project Management" | Title extracted |

**Assertions:**
- [ ] result.title equals "EP0001: Project Management"
- [ ] Title does not include the "# " prefix

---

### TC0075: Handle multi-line blockquote values

**Type:** Unit | **Priority:** High | **Story:** US0006 AC3

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Frontmatter with multi-line value: `> **Description:** Line one\n> that continues\n> and ends here` | Multi-line value |
| When | parse_document(content) is called | Document parsed |
| Then | metadata["description"] equals "Line one that continues and ends here" | Lines concatenated |

**Assertions:**
- [ ] metadata["description"] equals "Line one that continues and ends here"
- [ ] No leading/trailing whitespace in the value

---

### TC0076: Return empty metadata for no frontmatter

**Type:** Unit | **Priority:** Critical | **Story:** US0006 AC4

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Document with no blockquote frontmatter (just `# Title\n\nBody text`) | No frontmatter |
| When | parse_document(content) is called | Document parsed |
| Then | metadata is empty dict, body contains full content | Graceful handling |

**Assertions:**
- [ ] result.metadata equals {}
- [ ] result.body contains "Body text"
- [ ] result.title equals "Title"

---

### TC0077: Skip malformed blockquote lines

**Type:** Unit | **Priority:** High | **Story:** US0006 AC5

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Frontmatter with mix of valid and invalid lines | Mixed lines |
| When | parse_document(content) is called with `> **Status:** Done\n> Not a key-value\n> **Owner:** Darren` | Document parsed |
| Then | metadata contains status and owner, malformed line skipped | Valid lines parsed |

**Assertions:**
- [ ] metadata["status"] equals "Done"
- [ ] metadata["owner"] equals "Darren"
- [ ] "Not a key-value" not in metadata values

---

### TC0078: Handle colons in values

**Type:** Unit | **Priority:** High | **Story:** US0006 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Frontmatter with `> **URL:** http://example.com:8080/path` | Colon in value |
| When | parse_document(content) is called | Document parsed |
| Then | Value correctly captured as "http://example.com:8080/path" | Split on first colon only |

**Assertions:**
- [ ] metadata["url"] equals "http://example.com:8080/path"

---

### TC0079: Handle empty values

**Type:** Unit | **Priority:** Medium | **Story:** US0006 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Frontmatter with `> **Owner:**` (no value after colon) | Empty value |
| When | parse_document(content) is called | Document parsed |
| Then | Key mapped with empty string value | Graceful handling |

**Assertions:**
- [ ] metadata["owner"] equals ""

---

### TC0080: Non-numeric story_points returns None

**Type:** Unit | **Priority:** High | **Story:** US0006 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Frontmatter with `> **Story Points:** Large` | Non-numeric |
| When | parse_document(content) is called | Document parsed |
| Then | story_points is None; raw value preserved in metadata | Handled gracefully |

**Assertions:**
- [ ] metadata["story_points"] is None
- [ ] Raw value "Large" preserved in metadata

---

### TC0081: Additional fields stored in metadata dict

**Type:** Unit | **Priority:** Medium | **Story:** US0006 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Frontmatter with non-standard field `> **Reviewer:** Alice` | Extra field |
| When | parse_document(content) is called | Document parsed |
| Then | metadata["reviewer"] equals "Alice" | Stored in metadata dict |

**Assertions:**
- [ ] metadata["reviewer"] equals "Alice"

---

### TC0082: Body content correctly separated from frontmatter

**Type:** Unit | **Priority:** Critical | **Story:** US0006 AC1

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Document with frontmatter block followed by body content | Full document |
| When | parse_document(content) is called | Document parsed |
| Then | body contains only content after frontmatter block | Clean separation |

**Assertions:**
- [ ] result.body does not contain any `> **Key:**` frontmatter lines
- [ ] result.body starts with the first non-frontmatter content
- [ ] result.body is not empty

---

### TC0083: Windows line endings handled

**Type:** Unit | **Priority:** Medium | **Story:** US0006 (edge case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| Given | Document with CRLF line endings (`\r\n`) | Windows format |
| When | parse_document(content) is called | Document parsed |
| Then | Metadata and body extracted correctly despite CRLF | Line endings normalised |

**Assertions:**
- [ ] metadata fields extracted correctly
- [ ] No `\r` characters in extracted values
- [ ] Body content parsed correctly

---

## Fixtures

```yaml
standard_frontmatter:
  content: |
    > **Status:** Done
    > **Owner:** Darren
    > **Priority:** P0
    > **Story Points:** 5
    > **Epic:** [EP0001](../epics/EP0001-project-management.md)

    # US0001: Register a New Project

    Body content here.

no_frontmatter:
  content: |
    # Just a Title

    Body content with no metadata.

multi_line_value:
  content: |
    > **Description:** This is a long description
    > that spans multiple lines
    > and continues here
    > **Status:** Draft

    # Title

    Body.

malformed_lines:
  content: |
    > **Status:** Done
    > This is not a key-value pair
    > **Owner:** Darren

    Body.

colon_in_value:
  content: |
    > **URL:** http://example.com:8080/path

    Body.

crlf_document:
  content: "> **Status:** Done\r\n> **Owner:** Darren\r\n\r\n# Title\r\n\r\nBody."
```

---

## Automation Status

| TC | Title | Status | Implementation |
|----|-------|--------|----------------|
| TC0069 | Parse status field from frontmatter | Pending | - |
| TC0070 | Parse owner field from frontmatter | Pending | - |
| TC0071 | Parse priority field from frontmatter | Pending | - |
| TC0072 | Parse story_points as integer | Pending | - |
| TC0073 | Parse epic reference field | Pending | - |
| TC0074 | Extract title from first heading | Pending | - |
| TC0075 | Handle multi-line blockquote values | Pending | - |
| TC0076 | Return empty metadata for no frontmatter | Pending | - |
| TC0077 | Skip malformed blockquote lines | Pending | - |
| TC0078 | Handle colons in values | Pending | - |
| TC0079 | Handle empty values | Pending | - |
| TC0080 | Non-numeric story_points returns None | Pending | - |
| TC0081 | Additional fields stored in metadata dict | Pending | - |
| TC0082 | Body content correctly separated from frontmatter | Pending | - |
| TC0083 | Windows line endings handled | Pending | - |

---

## Traceability

| Artefact | Reference |
|----------|-----------|
| PRD | [sdlc-studio/prd.md](../prd.md) |
| Epic | [EP0002](../epics/EP0002-document-sync-and-parsing.md) |
| TSD | [sdlc-studio/tsd.md](../tsd.md) |

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial spec from US0006 story plan |
