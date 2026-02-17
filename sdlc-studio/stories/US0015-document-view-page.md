# US0015: Document View Page

> **Status:** Done
> **Epic:** [EP0003: Document Browsing](../epics/EP0003-document-browsing.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** to view a rendered markdown document with its metadata in a sidebar
**So that** I can read documents in a clean interface without opening a text editor

## Context

### Persona Reference
**Darren** - Views rendered documents for review; prefers clean, dark-themed interfaces.
[Full persona details](../personas.md#darren)

### Background
The document view page renders the raw markdown content with proper formatting, syntax highlighting for code blocks, and correct table rendering. A sidebar panel displays extracted frontmatter fields (status, owner, priority, etc.) in a structured format. This is the read-only document viewer.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Design | Dark theme with lime green accents (Brand Guide) | Markdown rendering styled for dark theme |
| TRD | Tech Stack | react-markdown + rehype-highlight | Markdown rendering libraries |
| PRD | Architecture | Read-only | No edit controls |

---

## Acceptance Criteria

### AC1: Render markdown content
- **Given** I navigate to `/projects/homelabcmd/documents/story/US0001`
- **When** the page loads
- **Then** the document markdown body renders with headings, lists, bold/italic, links, and blockquotes correctly formatted

### AC2: Syntax highlighting for code blocks
- **Given** a document contains fenced code blocks with language tags (```python, ```json)
- **When** the document renders
- **Then** code blocks display with syntax highlighting appropriate to the language

### AC3: Frontmatter sidebar
- **Given** a document has frontmatter fields: Status, Owner, Priority, Epic, Story Points
- **When** I view the document
- **Then** a sidebar panel displays these fields as labelled values with the status shown as a coloured badge

### AC4: Table rendering
- **Given** a document contains markdown tables
- **When** the document renders
- **Then** tables display with proper column alignment, borders, and header styling

### AC5: Document metadata bar
- **Given** a document with file_path "stories/US0001.md" synced at "2026-02-17 10:30"
- **When** I view the document
- **Then** a metadata bar shows the document type badge, file path, and sync timestamp

---

## Scope

### In Scope
- Document view page at `/projects/:slug/documents/:type/:docId`
- react-markdown rendering with dark theme styling
- rehype-highlight for syntax highlighting
- Frontmatter metadata sidebar panel
- Document type badge and status badge
- File path and sync timestamp display
- Back navigation to document list
- Loading state while fetching document

### Out of Scope
- Document editing
- Table of contents generation
- Document relationship navigation (epic → stories links)
- Print-friendly layout
- Search term highlighting in viewed document

---

## Technical Notes

### API Integration
- GET /api/v1/projects/{slug}/documents/{type}/{doc_id}
- Response includes content (markdown), metadata (JSON), and sync metadata

### Data Requirements
- react-markdown for rendering
- rehype-highlight for code block highlighting
- remark-gfm for GitHub-Flavoured Markdown (tables, task lists, strikethrough)

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Document not found (404 from API) | "Document not found" message with back link |
| Very large document (>100KB) | Renders correctly; may take slightly longer |
| Document with no frontmatter | Sidebar shows "No metadata" or minimal fields |
| Code block with unknown language tag | Renders as plain code (no highlighting) |
| Document with nested blockquotes | Renders with indentation levels |
| Document with raw HTML in markdown | Sanitised; potentially dangerous tags stripped |
| Document with image references | Images not rendered (no image hosting); shown as alt text |
| Loading state | Skeleton placeholder for content and sidebar |

---

## Test Scenarios

- [ ] Document content renders as formatted markdown
- [ ] Headings render at correct levels
- [ ] Code blocks have syntax highlighting
- [ ] Tables render with proper formatting
- [ ] Frontmatter sidebar shows extracted fields
- [ ] Status badge displays with correct colour
- [ ] Type badge displays correctly
- [ ] File path shown in metadata bar
- [ ] Sync timestamp shown in metadata bar
- [ ] 404 document shows error state
- [ ] Loading state displayed during fetch
- [ ] Back navigation returns to document list

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0013](US0013-document-detail-api.md) | API | Document detail endpoint | Draft |
| [US0016](US0016-status-and-type-badge-components.md) | Component | Badge components | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| react-markdown (>=9.0.0) | Package | Not Installed |
| rehype-highlight (>=7.0.0) | Package | Not Installed |
| remark-gfm | Package | Not Installed |

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
| 2026-02-17 | Claude | Initial story creation from EP0003 |
