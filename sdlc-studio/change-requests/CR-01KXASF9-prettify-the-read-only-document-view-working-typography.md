# CR-01KXASF9: Prettify the read-only document view: working typography plus sdlc-studio-aware presentation

> **Status:** Proposed
> **Triaged-by:** Darren; human; v3
> **Created:** 2026-07-12
> **Created-by:** sdlc-studio new
> **Raised-by:** Elena Foss; persona; v3
> **Priority:** Medium
> **Type:** Improvement

## Summary

`DocumentView` renders markdown (react-markdown + `remark-gfm` + `rehype-highlight`) inside
`<article className="prose prose-invert max-w-none">` - but **`@tailwindcss/typography` is not
installed**, so the `prose` classes are inert, and Tailwind's reset strips native heading/list/
paragraph styling. The result is an undifferentiated, dense wall of text (no heading hierarchy, no
paragraph/list spacing, unbounded line length). Because the lens is a **read-only viewer**, it can
reshape the raw markdown purely for reading - a presentation transform, with no round-trip to source
to preserve. This CR does both: restore real typography, and add an sdlc-studio-aware presentation
layer that makes the structured artefacts scannable.

## Impact

Readability is the core of a viewer, and it is currently poor. The fix is high-leverage: turning on
typography alone converts the wall of text into a properly-spaced document, and the sdlc-studio-aware
transforms (metadata card, clickable id references, TOC) make the artefacts genuinely navigable -
directly improving the primary use of the tool.

**Effort:** M

## Acceptance Criteria

- [ ] **Typography works** - enable `@tailwindcss/typography` (Tailwind 4 `@plugin`) or equivalent custom prose CSS, tuned to the dark design tokens: heading hierarchy, paragraph/list/blockquote spacing, comfortable line-height, and a reading **measure** (bounded max-width ~70-80ch) instead of `max-w-none`. Legible in both light and dark themes.
- [ ] **Wide content scrolls, the page never does** - tables and code blocks scroll horizontally within their own container; code keeps `rehype-highlight` syntax colours on a readable theme.
- [ ] **Metadata header as a card** - the leading `> **Field:** value` blockquote block renders as a structured header/info panel (Status badge, Owner, dates, etc.), not raw blockquotes.
- [ ] **Clickable id references** - artefact ids in the body (`US0001`, `CR-01KX8B82`, `[[CR-0496]]`) render as links to the referenced document (reuse the existing id resolver), consistent with the breadcrumb/relationship links.
- [ ] **Navigable long docs** - a heading-derived table of contents (side/sticky) for longer documents; acceptance-criteria checklists render as styled checkboxes.
- [ ] Purely presentational - the stored/source content is not mutated; tests cover prose rendering, the metadata card, an id-link, and the TOC.

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-07-12 | Elena Foss | Raised |
