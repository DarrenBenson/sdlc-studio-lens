# US0011: Document Type and ID Inference

> **Status:** Done
> **Epic:** [EP0002: Document Sync & Parsing](../epics/EP0002-document-sync-and-parsing.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** the system to infer document type and ID from filename patterns
**So that** documents are automatically categorised for filtering and navigation

## Context

### Persona Reference
**Darren** - Expects documents to be categorised correctly without manual tagging.
[Full persona details](../personas.md#darren)

### Background
sdlc-studio uses consistent naming conventions: epics are `EP0001.md`, stories are `US0045.md`, bugs are `BG0001.md`, and singleton documents are `prd.md`, `trd.md`, `tsd.md`. The system must infer document type and extract the document ID from these patterns. Files that do not match any pattern are assigned type "other".

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Business Logic | Document type inferred from filename | No manual type assignment |
| TRD | Data Model | doc_type and doc_id columns on documents table | Must populate both fields |
| Epic | Assumption | Filename patterns: EP*, US*, BG*, PL*, TS*, prd, trd, tsd | Defined pattern set |

---

## Acceptance Criteria

### AC1: Infer type from filename prefix
- **Given** files with names: `EP0001-project-management.md`, `US0045-login-form.md`, `BG0003-timeout-error.md`
- **When** the type inference function processes each filename
- **Then** types are inferred as "epic", "story", "bug" respectively

### AC2: Infer type from singleton filenames
- **Given** files named `prd.md`, `trd.md`, `tsd.md`
- **When** the type inference function processes each filename
- **Then** types are inferred as "prd", "trd", "tsd" respectively

### AC3: Extract document ID from filename
- **Given** a file named `EP0001-project-management.md`
- **When** the ID extraction function processes the filename
- **Then** doc_id is "EP0001"

### AC4: Singleton document IDs
- **Given** a file named `prd.md`
- **When** the ID extraction function processes the filename
- **Then** doc_id is "prd"

### AC5: Unknown filename pattern defaults to "other"
- **Given** a file named `brand-guide.md` that does not match any known pattern
- **When** the type inference function processes the filename
- **Then** doc_type is "other" and doc_id is "brand-guide"

---

## Scope

### In Scope
- Type inference from filename prefix: EP→epic, US→story, BG→bug, PL→plan, TS→test-spec
- Type inference from singleton names: prd.md, trd.md, tsd.md
- Type inference from directory context: files in epics/ → epic, stories/ → story, bugs/ → bug
- Document ID extraction from filename
- Fallback type "other" for unrecognised patterns
- Index file exclusion: `_index.md` files not imported as documents

### Out of Scope
- Frontmatter-based type override (type always from filename)
- Custom type registration
- File content-based type detection

---

## Technical Notes

### Inference Rules (Priority Order)
```
1. If filename == "_index.md" → SKIP (not a document)
2. If filename matches "EP\d{4}" → type: "epic", id: "EP{NNNN}"
3. If filename matches "US\d{4}" → type: "story", id: "US{NNNN}"
4. If filename matches "BG\d{4}" → type: "bug", id: "BG{NNNN}"
5. If filename matches "PL\d{4}" → type: "plan", id: "PL{NNNN}"
6. If filename matches "TS\d{4}" → type: "test-spec", id: "TS{NNNN}"
7. If filename == "prd.md" → type: "prd", id: "prd"
8. If filename == "trd.md" → type: "trd", id: "trd"
9. If filename == "tsd.md" → type: "tsd", id: "tsd"
10. If filename == "personas.md" → type: "personas", id: "personas"
11. Fallback from directory: epics/ → "epic", stories/ → "story", etc.
12. Default: type: "other", id: stem of filename
```

### Data Requirements
- Pure function: takes filename (str) and relative path (str), returns (doc_type, doc_id)
- No database access needed

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| File `_index.md` in any directory | Skipped entirely (not imported) |
| File `EP0001.md` in wrong directory (e.g., stories/) | Filename prefix takes priority; type is "epic" |
| File with prefix but no number (e.g., `EP-overview.md`) | Does not match EP\d{4} pattern; fallback to directory or "other" |
| Nested subdirectory (e.g., `epics/archive/EP0001.md`) | Type inferred from filename prefix; directory depth ignored |
| Duplicate doc_id across types (EP0001 and US0001) | Unique constraint: (project_id, doc_type, doc_id) differentiates |
| File named `readme.md` | type: "other", id: "readme" |
| File with uppercase extension `.MD` | Matched case-insensitively |
| File named `WF0001-workflow.md` | type: "workflow", id: "WF0001" |

---

## Test Scenarios

- [ ] EP prefix infers type "epic"
- [ ] US prefix infers type "story"
- [ ] BG prefix infers type "bug"
- [ ] PL prefix infers type "plan"
- [ ] TS prefix infers type "test-spec"
- [ ] prd.md infers type "prd"
- [ ] trd.md infers type "trd"
- [ ] tsd.md infers type "tsd"
- [ ] Unknown pattern defaults to type "other"
- [ ] Document ID extracted correctly from prefixed filenames
- [ ] Singleton document IDs extracted correctly
- [ ] _index.md files excluded from import
- [ ] Directory context used as fallback for type inference

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
**Complexity:** Low

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-17 | Claude | Initial story creation from EP0002 |
