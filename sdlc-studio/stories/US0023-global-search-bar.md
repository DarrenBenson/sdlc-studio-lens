# US0023: Global Search Bar Component

> **Status:** Done
> **Epic:** [EP0005: Search](../epics/EP0005-search.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-17

## User Story

**As a** SDLC Developer (Darren)
**I want** a search bar in the header that I can use from any page
**So that** I can search documents without navigating to a dedicated search page first

## Context

### Persona Reference
**Darren** - Searches for specific stories when planning next tasks; wants quick access from anywhere.
[Full persona details](../personas.md#darren)

### Background
The search bar is a persistent element in the application header (or top navigation). Typing a query and pressing Enter navigates to the search results page with the query. The search bar is visible on every page via the layout shell.

---

## Inherited Constraints

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| PRD | Design | Brand Guide colour system | Input uses bg-elevated (#1C2520) with text-secondary |
| TRD | Architecture | React SPA layout shell | Search bar in header, part of Layout.tsx |

---

## Acceptance Criteria

### AC1: Search bar visible on all pages
- **Given** I am on any page (dashboard, document list, settings)
- **When** I look at the header
- **Then** I see a search input with a search icon and placeholder "Search documents..."

### AC2: Submit navigates to results
- **Given** I type "authentication" in the search bar
- **When** I press Enter or click the search icon
- **Then** I navigate to `/search?q=authentication`

### AC3: Preserves query on results page
- **Given** I am on `/search?q=authentication`
- **When** I look at the search bar
- **Then** it shows "authentication" as the current value

### AC4: Keyboard shortcut
- **Given** I am on any page
- **When** I press `/` (slash key, when not focused on an input)
- **Then** the search bar receives focus

### AC5: Empty submit prevented
- **Given** the search bar is empty
- **When** I press Enter
- **Then** nothing happens (no navigation to empty search)

---

## Scope

### In Scope
- SearchBar component in header/Layout
- Text input with search icon
- Enter key submits search
- Navigation to /search?q=...
- Keyboard shortcut `/` to focus
- Input styling per brand guide

### Out of Scope
- Autocomplete or search suggestions
- Recent searches dropdown
- Search-as-you-type (results page handles search)

---

## Technical Notes

### Integration
- Part of Layout.tsx header section
- Uses React Router useNavigate() for navigation
- Reads query from URL params on search results page to sync input value

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Empty search submission | Prevented; no navigation |
| Whitespace-only search | Trimmed; treated as empty |
| Very long search query (>200 chars) | Submitted as-is; API validates length |
| Special characters in query | URL-encoded on navigation |
| `/` shortcut while in another input | Does not steal focus (only when no input focused) |
| Search bar on mobile/narrow viewport | Full width; search icon only when collapsed |

---

## Test Scenarios

- [ ] Search bar renders in header
- [ ] Typing and pressing Enter navigates to /search
- [ ] Empty submit does not navigate
- [ ] Query preserved in search bar on results page
- [ ] Search icon click triggers search
- [ ] Keyboard shortcut `/` focuses search bar
- [ ] Placeholder text "Search documents..." visible
- [ ] Search bar visible on all page routes

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0005](US0005-sidebar-project-navigation.md) | Component | Layout shell | Draft |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| React Router | Infrastructure | Not Started |

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
| 2026-02-17 | Claude | Initial story creation from EP0005 |
