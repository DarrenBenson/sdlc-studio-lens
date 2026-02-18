# US0036: Document Tree View

> **Status:** Done
> **Epic:** [EP0008: Document Relationship Navigation](../epics/EP0008-document-relationship-navigation.md)
> **Owner:** Darren
> **Reviewer:** -
> **Created:** 2026-02-18

## User Story

**As a** SDLC Developer (Darren)
**I want** a tree view page showing the full document hierarchy for a project
**So that** I can see the entire SDLC structure at a glance and navigate to any document

## Context

### Persona Reference
**Darren** - Manages SDLC projects and wants a visual overview of how all documents fit together in the hierarchy.
[Full persona details](../personas.md#darren)

### Background
The existing document list page shows a flat, filterable table of documents. While useful for searching and sorting, it doesn't reveal the hierarchical structure: which stories belong to which epics, which plans relate to which stories, etc.

A tree view page shows the project's documents organised as an expandable tree:
```
Project Name
├── PRD
├── TRD
├── TSD
├── EP0001: Project Management
│   ├── US0001: Register Project
│   │   ├── PL0001: Register Project Plan
│   │   └── TS0001: Register Project Tests
│   ├── US0002: Trigger Sync
│   └── ...
├── EP0002: Document Sync & Parsing
│   └── ...
└── ...
```

The tree is built client-side from the existing document list API (which now includes `epic` and `story` fields from US0034). Each node is clickable, navigating to the document view page.

---

## Inherited Constraints

> See Epic for full constraint chain. Key constraints for this story:

| Source | Type | Constraint | AC Implication |
|--------|------|------------|----------------|
| TRD | Tech Stack | React 19.2 + react-router 7 | New route and page component |
| TRD | Tech Stack | Tailwind CSS 4.1 | Consistent styling; no new CSS dependencies |
| PRD | KPI | Page loads < 500ms | Build tree client-side from existing API data |

---

## Acceptance Criteria

### AC1: Tree view page accessible via route
- **Given** a synced project
- **When** I navigate to `/projects/{slug}/tree`
- **Then** a tree view page loads showing the project's document hierarchy

### AC2: Tree shows correct hierarchy
- **Given** a project with epics, stories, plans, test-specs, and bugs
- **When** the tree renders
- **Then** top-level documents (PRD, TRD, TSD, epics) appear at the root, stories nested under their parent epic, and plans/test-specs/bugs nested under their parent story

### AC3: Nodes are expandable/collapsible
- **Given** the tree view with nested documents
- **When** I click an expand/collapse toggle on a parent node
- **Then** its children are shown or hidden

### AC4: Clicking a node navigates to document view
- **Given** a tree node
- **When** I click the document title
- **Then** I navigate to `/projects/{slug}/documents/{type}/{docId}`

### AC5: Nodes show type badge, status, and child count
- **Given** a tree node that has children
- **When** I inspect it
- **Then** it shows the document title, a type badge, a status badge, and the number of direct children

### AC9: Tree starts fully collapsed
- **Given** a synced project with documents
- **When** I navigate to the tree view
- **Then** only root-level nodes are visible; all are collapsed

### AC10: Expand all and collapse all controls
- **Given** the tree view page
- **When** I click "Expand all"
- **Then** all parent nodes expand showing the full hierarchy
- **When** I click "Collapse all"
- **Then** only root-level nodes are visible

### AC11: All documents fetched across pages
- **Given** a project with more documents than the API page size (100)
- **When** the tree view loads
- **Then** all documents are fetched by paginating automatically, and the full hierarchy is built

### AC6: Navigation link from project detail
- **Given** the project detail page
- **When** I look for navigation options
- **Then** there is a link/button to the tree view page

### AC7: Empty project shows message
- **Given** a project with no synced documents
- **When** I navigate to the tree view
- **Then** a message like "No documents synced yet" is shown with a link to trigger sync

### AC8: Orphan documents shown at root
- **Given** documents that have an `epic` or `story` reference that doesn't match any document in the project
- **When** the tree renders
- **Then** orphan documents are placed at the root level (not hidden)

---

## Scope

### In Scope
- New route: `/projects/:slug/tree`
- New page component: `DocumentTree.tsx`
- Tree-building logic from flat document list using `epic` and `story` fields
- Expand/collapse state management (React state)
- Type badges and status badges on nodes
- Navigation link from ProjectDetail page
- Empty state for projects with no documents
- Orphan document handling (documents with unresolved parent references)

### Out of Scope
- Drag-and-drop reordering
- Inline editing of documents in the tree
- Search/filter within the tree
- Persist expand/collapse state across page navigations
- Lazy-loading children (all data fetched upfront)
- Tree view for cross-project hierarchies

---

## Technical Notes

### Route Addition
```tsx
// App.tsx
<Route path="projects/:slug/tree" element={<DocumentTree />} />
```

### Tree Building Algorithm
```typescript
interface TreeNode {
  doc_id: string;
  type: string;
  title: string;
  status: string | null;
  children: TreeNode[];
}

function buildTree(docs: DocumentListItem[]): TreeNode[] {
  // 1. Create a map of doc_id -> node
  // 2. Top-level: PRD, TRD, TSD, and epics (no epic/story parent)
  // 3. Stories: find parent epic by matching doc.epic to an epic's doc_id
  // 4. Plans/test-specs/bugs: find parent story by matching doc.story
  // 5. Orphans (unresolved parent): place at root
  // 6. Sort children by type priority then doc_id
}
```

### Type Sort Priority
Documents within each level should be sorted by type, then by ID:
1. prd, trd, tsd (singletons)
2. epic
3. story
4. plan
5. test-spec
6. bug

### Data Source
Reuses the existing document list API (`GET /projects/{slug}/documents`) with the `epic` and `story` fields added by US0034. The backend caps `per_page` at 100, so the tree must paginate to fetch all documents.

### API Client
Uses `fetchAllDocuments(slug)` which auto-paginates through all pages of the document list API (`per_page=100`, incrementing `page` until all pages fetched). Returns a flat `DocumentListItem[]` array for tree building.

### Component Structure
```
DocumentTree (page)
├── TreeBreadcrumb (Project / Tree View)
├── Toolbar (Expand All / Collapse All buttons)
├── TreeNode (recursive component)
│   ├── ExpandToggle (chevron, only on parents)
│   ├── TypeBadge
│   ├── DocumentTitle (Link)
│   ├── StatusBadge
│   └── ChildCount (only on parents)
└── EmptyState
```

### Expand/Collapse State
```typescript
const [expanded, setExpanded] = useState<Set<string>>(new Set());
// Default: starts fully collapsed (empty set)
// Toggle: add/remove doc_id from the set
// Expand all: collect all parent doc_ids into the set
// Collapse all: clear the set
```

---

## Edge Cases & Error Handling

| Scenario | Expected Behaviour |
|----------|-------------------|
| Project has no documents | Shows "No documents synced yet" with sync link |
| Document list API fails | Shows error message with retry option |
| Orphan documents (parent not found) | Placed at root level |
| Single top-level document (just a PRD) | Tree shows one node, no expand toggle |
| Large project (100+ documents) | All fetched via auto-pagination; tree compact when collapsed |
| Project with more than 100 documents | fetchAllDocuments paginates through all pages |
| Document without a type (edge case) | Rendered at root with "unknown" type badge |
| Clicking expand on leaf node | No toggle shown for leaf nodes |
| Deep nesting (plan under story under epic) | 3 levels of indentation; consistent styling |

---

## Test Scenarios

- [ ] DocumentTree page renders at /projects/:slug/tree
- [ ] Tree shows epics at root level
- [ ] Stories nested under their parent epic
- [ ] Plans nested under their parent story
- [ ] Test-specs nested under their parent story
- [ ] Bugs nested under their parent story
- [ ] PRD/TRD/TSD shown at root level
- [ ] Orphan documents shown at root level
- [ ] Expand/collapse toggles work
- [ ] Clicking document title navigates to document view
- [ ] Type badges shown on each node
- [ ] Status badges shown on each node
- [ ] Child count shown on parent nodes
- [ ] Tree starts fully collapsed
- [ ] Expand all button expands entire tree
- [ ] Collapse all button collapses entire tree
- [ ] All documents fetched across multiple pages for large projects
- [ ] Empty project shows appropriate message
- [ ] Loading state shown while fetching documents
- [ ] Error state shown when API fails
- [ ] ProjectDetail page has link to tree view
- [ ] Route registered in App.tsx

---

## Dependencies

### Story Dependencies

| Story | Type | What's Needed | Status |
|-------|------|---------------|--------|
| [US0034](US0034-relationships-api.md) | API | Document list includes epic and story fields | Not Started |

### External Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| None | - | - |

---

## Estimation

**Story Points:** 3
**Complexity:** Medium

---

## Open Questions

None.

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-18 | Claude | Initial story creation from EP0008 |
| 2026-02-18 | Claude | Added AC9-AC11: collapsed default, expand/collapse all, auto-pagination, child count |
