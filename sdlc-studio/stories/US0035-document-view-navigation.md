# US0035: Document View Navigation

> **Status:** Done
> **Epic:** [EP0008: Document Relationship Navigation](../epics/EP0008-document-relationship-navigation.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-18

## User Story

**As a** SDLC Developer (Darren)
**I want** breadcrumbs and a related documents panel on the document view page
**So that** I can navigate up to parent documents and down to child documents in one click

## Context

### Persona Reference
**Darren** - Frequently navigates between related SDLC documents and wants direct links instead of searching or manually filtering.
[Full persona details](../personas.md#darren)

### Background
The current DocumentView page shows a simple breadcrumb (Project / Documents) and a properties sidebar with raw metadata. It does not show navigable links to parent or child documents.

With the relationships API from US0034, the frontend can fetch a document's parents and children and render:
1. **Hierarchy breadcrumbs** - replacing the generic "Project / Documents" with "Project / EP0007 / US0028 / PL0028"
2. **Related documents panel** - a sidebar section listing parent and child documents as clickable links

Both use the `/related` endpoint to get structured relationship data.

---

## Inherited Constraints

> See Epic for full constraint chain. Key constraints for this story:

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Tech Stack | React 19.2 + react-router 7 | Use existing Link component and route patterns |
| TRD | Tech Stack | Tailwind CSS 4.1 | Style consistent with existing components |
| PRD | KPI | API response < 500ms | Fetch relationships in parallel with document data |

---

## Acceptance Criteria

### AC1: Hierarchy breadcrumbs show ancestor chain
- **Given** a plan document PL0028 with parent story US0028 and grandparent epic EP0007
- **When** I view the document
- **Then** the breadcrumbs show: Project > EP0007 > US0028 > PL0028, each ancestor being a clickable link

### AC2: Related documents panel shows parents
- **Given** a story document with a parent epic
- **When** I view the document
- **Then** a "Parent" section in the sidebar shows the epic with its title, type badge, and a link to its document view

### AC3: Related documents panel shows children
- **Given** an epic document with three child stories
- **When** I view the document
- **Then** a "Children" section in the sidebar lists all three stories with title, type badge, status, and links to their document views

### AC4: Leaf documents show no children section
- **Given** a plan document with no children
- **When** I view the document
- **Then** the children section is either hidden or shows "No child documents"

### AC5: Top-level documents show no parents section
- **Given** an epic document with no parent references
- **When** I view the document
- **Then** the parents section is either hidden or shows only the Project link

### AC6: Navigation links work correctly
- **Given** a breadcrumb or related document link
- **When** I click it
- **Then** I navigate to `/projects/{slug}/documents/{type}/{docId}` for the target document

### AC7: Loading and error states
- **Given** the relationships API is loading or fails
- **When** I view a document
- **Then** the breadcrumbs fall back to the generic "Project / Documents" path and the related panel shows a loading or error state without breaking the page

---

## Scope

### In Scope
- New API client function `fetchRelatedDocuments(slug, type, docId)`
- Enhanced breadcrumb nav in DocumentView with hierarchy path
- New "Relationships" panel in the sidebar (below Properties)
- Clickable links for all parent and child documents
- Type badges and status badges on related document items
- Loading state while relationships load
- Graceful fallback if relationships API fails
- TypeScript types for the relationships response

### Out of Scope
- Tree view page (US0036)
- Editing relationships
- Drag-and-drop reordering
- Relationship indicators in the document list page
- Cross-project navigation

---

## Technical Notes

### API Client Addition
```typescript
// api/client.ts
export async function fetchRelatedDocuments(
  slug: string,
  type: string,
  docId: string,
): Promise<DocumentRelationships> {
  const res = await fetch(`${BASE}/projects/${slug}/documents/${type}/${docId}/related`);
  if (!res.ok) throw new Error(`Failed to fetch relationships: ${res.status}`);
  return res.json();
}
```

### TypeScript Types
```typescript
// types/index.ts
export interface RelatedDocumentItem {
  doc_id: string;
  type: string;
  title: string;
  status: string | null;
}

export interface DocumentRelationships {
  doc_id: string;
  type: string;
  title: string;
  parents: RelatedDocumentItem[];
  children: RelatedDocumentItem[];
}
```

### Breadcrumb Enhancement
Replace the current static breadcrumb in DocumentView:
```tsx
{/* Current */}
<Link to={`/projects/${slug}`}>Project</Link> / <Link to={`/projects/${slug}/documents`}>Documents</Link>

{/* Enhanced */}
<Link to={`/projects/${slug}`}>Project</Link>
{parents.reverse().map(parent => (
  <>
    <span>/</span>
    <Link to={`/projects/${slug}/documents/${parent.type}/${parent.doc_id}`}>
      {parent.doc_id}
    </Link>
  </>
))}
<span>/</span>
<span>{doc.doc_id}</span>
```

### Related Documents Panel
New sidebar section below Properties:
```tsx
<div className="mt-4 rounded-lg border border-border-default bg-bg-surface p-4">
  <h3>Relationships</h3>
  {parents.length > 0 && (
    <div>
      <dt>Parent</dt>
      {parents.map(p => <RelatedDocLink key={p.doc_id} item={p} slug={slug} />)}
    </div>
  )}
  {children.length > 0 && (
    <div>
      <dt>Children</dt>
      {children.map(c => <RelatedDocLink key={c.doc_id} item={c} slug={slug} />)}
    </div>
  )}
</div>
```

### Parallel Fetch
Fetch document and relationships in parallel:
```typescript
const [doc, related] = await Promise.all([
  fetchDocument(slug, type, docId),
  fetchRelatedDocuments(slug, type, docId).catch(() => null),
]);
```

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Relationships API returns 404 | Breadcrumbs fall back to generic path; related panel hidden |
| Relationships API times out | Same fallback as 404; document content still renders |
| Parent document deleted between fetch and click | Standard 404 page shown when navigating |
| Document has no relationships (PRD/TRD/TSD) | Both sections empty; panel shows "No related documents" |
| Very long parent chain (unlikely, max 3 levels) | All levels shown in breadcrumbs |
| Child documents with long titles | Truncated with ellipsis in sidebar |
| Many children (e.g., epic with 10+ stories) | All shown; list scrolls within panel |

---

## Test Scenarios

- [ ] DocumentView renders hierarchy breadcrumbs for a plan (3 levels)
- [ ] DocumentView renders hierarchy breadcrumbs for a story (2 levels)
- [ ] DocumentView renders generic breadcrumbs when no parents
- [ ] Related panel shows parent documents with links
- [ ] Related panel shows child documents with links
- [ ] Related panel hidden when no relationships
- [ ] Clicking a parent breadcrumb navigates to correct route
- [ ] Clicking a child link navigates to correct route
- [ ] Type badges shown on related document items
- [ ] Status badges shown on related document items
- [ ] Loading state shown while relationships fetch
- [ ] Fallback breadcrumbs when relationships API fails
- [ ] fetchRelatedDocuments API client function works

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0034](US0034-relationships-api.md) | API | /related endpoint returning parents and children | Not Started |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

---

## Estimation

**Story Points:** 5
**Complexity:** Medium

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-18 | Claude | Initial story creation from EP0008 |
