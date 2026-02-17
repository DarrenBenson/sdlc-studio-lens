# US0006: Blockquote Frontmatter Parser

> **Status:** Done
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** the system to extract structured metadata from sdlc-studio markdown documents
**So that** I can filter and search documents by status, type, owner, and other fields

## Context

### Persona Reference
**Darren** - Uses sdlc-studio CLI to generate SDLC artefacts in blockquote frontmatter format.
[Full persona details](../personas.md#darren)

### Background
sdlc-studio documents use a blockquote-style metadata format (`> **Key:** Value`) rather than YAML frontmatter. A custom parser must extract this metadata into structured fields. The parser is a pure function with no side effects - it takes markdown text and returns extracted metadata plus the remaining content.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Parser | Blockquote format: `> **Key:** Value` | Regex-based extraction |
| TRD | Data Model | Standard fields: status, owner, priority, story_points, epic | Must map to document table columns |
| Epic | Performance | Sync 100 docs < 10s | Parser must be efficient (< 10ms per document) |

---

## Acceptance Criteria

### AC1: Parse standard frontmatter fields
- **Given** a markdown document containing `> **Status:** Done\n> **Owner:** Darren\n> **Priority:** P0`
- **When** the parser processes the document
- **Then** it returns metadata dict `{"status": "Done", "owner": "Darren", "priority": "P0"}`

### AC2: Extract title from first heading
- **Given** a document with `# EP0001: Project Management` as the first line (before or after frontmatter)
- **When** the parser processes the document
- **Then** it returns title "EP0001: Project Management"

### AC3: Handle multi-line blockquote values
- **Given** a frontmatter block containing:
  ```
  > **Description:** This is a long description
  > that spans multiple lines
  > and continues here
  ```
- **When** the parser processes the document
- **Then** it returns description as "This is a long description that spans multiple lines and continues here"

### AC4: Return empty metadata for missing frontmatter
- **Given** a markdown document with no blockquote frontmatter (just regular content)
- **When** the parser processes the document
- **Then** it returns an empty metadata dict `{}` and the full content as body

### AC5: Skip malformed lines, parse valid ones
- **Given** a frontmatter block with both valid and invalid lines:
  ```
  > **Status:** Done
  > This is not a key-value pair
  > **Owner:** Darren
  ```
- **When** the parser processes the document
- **Then** it returns `{"status": "Done", "owner": "Darren"}`, skipping the non-key-value line

---

## Scope

### In Scope
- Parse `> **Key:** Value` format from document start
- Extract standard fields: status, owner, priority, story_points (as integer), epic, created, type
- Store additional fields as JSON metadata dict
- Extract title from first `#` heading
- Handle multi-line blockquote values (continuation lines starting with `>`)
- Return (title, metadata_dict, body_content) tuple
- Handle documents with no frontmatter gracefully
- Skip malformed blockquote lines

### Out of Scope
- YAML frontmatter parsing (not used by sdlc-studio)
- Document type inference from filename (US0011)
- Document ID extraction from filename (US0011)
- Database storage (US0007-US0009)

---

## Technical Notes

### API Contract (Internal)
```python
def parse_document(content: str) -> ParseResult:
    """Parse sdlc-studio markdown document.

    Returns:
        ParseResult with title, metadata dict, and body content.
    """
```

### Data Requirements
- Standard fields to extract to dedicated columns: status, owner, priority, story_points, epic
- story_points parsed as integer (None if not present or not numeric)
- All other `> **Key:** Value` pairs stored in metadata JSON column
- Body content: everything after the frontmatter blockquote block

### Parser Logic
```
1. Split content into lines
2. Identify frontmatter block (consecutive lines starting with "> ")
3. For each frontmatter line matching "> **Key:** Value" pattern:
   a. Extract key (normalise to lowercase/snake_case)
   b. Extract value (strip whitespace)
   c. If next line starts with "> " but NOT "> **": append as continuation
4. Find first line matching "# " for title extraction
5. Body = everything after frontmatter block
```

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Document with only frontmatter, no body | Returns metadata and empty body string |
| Document with only body, no frontmatter | Returns empty metadata and full body |
| Nested blockquotes (`>> **Key:** Value`) | Not parsed as frontmatter; treated as body content |
| Key with colon in value (`> **URL:** http://example.com`) | Value correctly captured as "http://example.com" |
| Empty value (`> **Owner:**`) | Key mapped with empty string value |
| story_points with non-numeric value (`> **Story Points:** Large`) | story_points returns None; value preserved in metadata JSON |
| Very large document (>100KB) | Parser completes without significant delay |
| Document with Windows line endings (CRLF) | Handles both LF and CRLF line endings |
| Frontmatter block not at start of document (preceded by blank lines) | Still parsed if blockquote block is contiguous |
| Multiple blockquote blocks in document | Only first contiguous blockquote block treated as frontmatter |

---

## Test Scenarios

- [ ] Parse status field from frontmatter
- [ ] Parse owner field from frontmatter
- [ ] Parse priority field from frontmatter
- [ ] Parse story_points as integer
- [ ] Parse epic reference field
- [ ] Extract title from first heading
- [ ] Handle multi-line blockquote values
- [ ] Return empty metadata for no frontmatter
- [ ] Skip malformed blockquote lines
- [ ] Handle colons in values
- [ ] Handle empty values
- [ ] Non-numeric story_points returns None
- [ ] Additional fields stored in metadata dict
- [ ] Body content correctly separated from frontmatter
- [ ] Windows line endings handled

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| None | - | Pure function, no dependencies | - |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

---

## Estimation

**Story Points:** {{TBD}}
**Complexity:** Medium

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial story creation from EP0002 |
