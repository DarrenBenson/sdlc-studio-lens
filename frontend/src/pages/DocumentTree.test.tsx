/**
 * DocumentTree page component tests.
 *
 * Test cases: TC0379-TC0390 from US0036.
 */

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import type { DocumentListItem } from "../types/index.ts";
import { buildTree, DocumentTree } from "./DocumentTree.tsx";

vi.mock("../api/client.ts", () => ({
  fetchProjects: vi.fn(),
  fetchProject: vi.fn(),
  createProject: vi.fn(),
  updateProject: vi.fn(),
  deleteProject: vi.fn(),
  triggerSync: vi.fn(),
  fetchDocuments: vi.fn(),
  fetchAllDocuments: vi.fn(),
  fetchDocument: vi.fn(),
  fetchRelatedDocuments: vi.fn(),
  fetchAggregateStats: vi.fn(),
  fetchProjectStats: vi.fn(),
  fetchSearchResults: vi.fn(),
}));

const { fetchAllDocuments } = await import("../api/client.ts");
const mockFetchAllDocuments = vi.mocked(fetchAllDocuments);

const now = "2026-02-18T12:00:00Z";

function makeDoc(overrides: Partial<DocumentListItem> & { doc_id: string; type: string; title: string }): DocumentListItem {
  return {
    status: "Done",
    owner: "Darren",
    priority: null,
    story_points: null,
    epic: null,
    story: null,
    updated_at: now,
    ...overrides,
  };
}

const hierarchyDocs: DocumentListItem[] = [
  makeDoc({ doc_id: "prd", type: "prd", title: "Product Requirements" }),
  makeDoc({ doc_id: "trd", type: "trd", title: "Technical Requirements" }),
  makeDoc({ doc_id: "EP0001-project-mgmt", type: "epic", title: "Project Management" }),
  makeDoc({ doc_id: "EP0002-sync", type: "epic", title: "Document Sync" }),
  makeDoc({ doc_id: "US0001-register", type: "story", title: "Register Project", epic: "EP0001" }),
  makeDoc({ doc_id: "US0002-list", type: "story", title: "List Projects", epic: "EP0001" }),
  makeDoc({ doc_id: "PL0001-register-plan", type: "plan", title: "Register Plan", story: "US0001", epic: "EP0001" }),
  makeDoc({ doc_id: "TS0001-register-tests", type: "test-spec", title: "Register Tests", story: "US0001", epic: "EP0001" }),
  makeDoc({ doc_id: "US0003-sync-story", type: "story", title: "Sync Story", epic: "EP0002" }),
];

function renderTree(path = "/projects/testproject/tree") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="projects/:slug/tree" element={<DocumentTree />} />
      </Routes>
    </MemoryRouter>,
  );
}

// ---------------------------------------------------------------------------
// TC0379: buildTree produces correct hierarchy (unit test)
// ---------------------------------------------------------------------------

describe("TC0379: buildTree unit test", () => {
  it("places epics at root level", () => {
    const roots = buildTree(hierarchyDocs);
    const rootTypes = roots.map((n) => n.type);
    expect(rootTypes).toContain("epic");
    expect(rootTypes).toContain("prd");
    expect(rootTypes).toContain("trd");
  });

  it("nests stories under their parent epic", () => {
    const roots = buildTree(hierarchyDocs);
    const ep1 = roots.find((n) => n.doc_id === "EP0001-project-mgmt");
    expect(ep1).toBeDefined();
    const childIds = ep1!.children.map((c) => c.doc_id);
    expect(childIds).toContain("US0001-register");
    expect(childIds).toContain("US0002-list");
  });

  it("nests plans under their parent story", () => {
    const roots = buildTree(hierarchyDocs);
    const ep1 = roots.find((n) => n.doc_id === "EP0001-project-mgmt")!;
    const us1 = ep1.children.find((c) => c.doc_id === "US0001-register")!;
    const childIds = us1.children.map((c) => c.doc_id);
    expect(childIds).toContain("PL0001-register-plan");
    expect(childIds).toContain("TS0001-register-tests");
  });

  it("sorts by type priority then doc_id", () => {
    const roots = buildTree(hierarchyDocs);
    const rootTypes = roots.map((n) => n.type);
    // PRD/TRD come before epics
    expect(rootTypes.indexOf("prd")).toBeLessThan(rootTypes.indexOf("epic"));
  });
});

// ---------------------------------------------------------------------------
// TC0380: Orphan documents at root
// ---------------------------------------------------------------------------

describe("TC0380: Orphan documents at root", () => {
  it("places orphan documents at root when parent not found", () => {
    const docs = [
      makeDoc({ doc_id: "PL9999-orphan", type: "plan", title: "Orphan Plan", story: "US9999" }),
      makeDoc({ doc_id: "EP0001-epic", type: "epic", title: "An Epic" }),
    ];
    const roots = buildTree(docs);
    const rootIds = roots.map((n) => n.doc_id);
    expect(rootIds).toContain("PL9999-orphan");
  });
});

// ---------------------------------------------------------------------------
// TC0381: Page renders at /projects/:slug/tree
// ---------------------------------------------------------------------------

describe("TC0381: Page renders at correct route", () => {
  it("renders tree view page", async () => {
    mockFetchAllDocuments.mockResolvedValueOnce(hierarchyDocs);
    renderTree();
    await waitFor(() => {
      expect(screen.getByText("Document Hierarchy")).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// TC0382: Tree shows type badges
// ---------------------------------------------------------------------------

describe("TC0382: Type badges on nodes", () => {
  it("shows type badges for each node", async () => {
    mockFetchAllDocuments.mockResolvedValueOnce(hierarchyDocs);
    renderTree();
    await waitFor(() => {
      expect(screen.getByText("Document Hierarchy")).toBeInTheDocument();
    });
    // PRD type badge should be visible
    expect(screen.getByText("PRD")).toBeInTheDocument();
    expect(screen.getByText("TRD")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0383: Tree shows status badges
// ---------------------------------------------------------------------------

describe("TC0383: Status badges on nodes", () => {
  it("shows status badges", async () => {
    mockFetchAllDocuments.mockResolvedValueOnce(hierarchyDocs);
    renderTree();
    await waitFor(() => {
      expect(screen.getByText("Document Hierarchy")).toBeInTheDocument();
    });
    // All docs have "Done" status
    const doneBadges = screen.getAllByText("Done");
    expect(doneBadges.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// TC0384: Clicking document title links to document view
// ---------------------------------------------------------------------------

describe("TC0384: Document title links", () => {
  it("links to document view page", async () => {
    mockFetchAllDocuments.mockResolvedValueOnce(hierarchyDocs);
    renderTree();
    await waitFor(() => {
      expect(screen.getByText("Product Requirements")).toBeInTheDocument();
    });
    const link = screen.getByText("Product Requirements").closest("a");
    expect(link).toHaveAttribute(
      "href",
      "/projects/testproject/documents/prd/prd",
    );
  });
});

// ---------------------------------------------------------------------------
// TC0385: Expand/collapse toggles work
// ---------------------------------------------------------------------------

describe("TC0385: Expand/collapse", () => {
  it("collapses an expanded node on click", async () => {
    mockFetchAllDocuments.mockResolvedValueOnce(hierarchyDocs);
    renderTree();
    await waitFor(() => {
      expect(screen.getByText("Project Management")).toBeInTheDocument();
    });
    // EP0001 should be auto-expanded - stories visible
    expect(screen.getByText("Register Project")).toBeInTheDocument();

    // Click collapse on EP0001
    const collapseBtn = screen
      .getByText("Project Management")
      .closest("div")!
      .querySelector("button")!;
    await userEvent.click(collapseBtn);

    // Stories should now be hidden
    expect(screen.queryByText("Register Project")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0386: Empty project shows message
// ---------------------------------------------------------------------------

describe("TC0386: Empty project", () => {
  it("shows empty state message", async () => {
    mockFetchAllDocuments.mockResolvedValueOnce([]);
    renderTree();
    await waitFor(() => {
      expect(screen.getByText("No documents synced yet.")).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// TC0387: Loading state
// ---------------------------------------------------------------------------

describe("TC0387: Loading state", () => {
  it("shows loading indicator initially", () => {
    mockFetchAllDocuments.mockReturnValue(new Promise(() => {}));
    renderTree();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0388: Error state
// ---------------------------------------------------------------------------

describe("TC0388: Error state", () => {
  it("shows error message on fetch failure", async () => {
    mockFetchAllDocuments.mockRejectedValueOnce(new Error("Network error"));
    renderTree();
    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// TC0389: Breadcrumb navigation
// ---------------------------------------------------------------------------

describe("TC0389: Breadcrumb navigation", () => {
  it("shows Project / Tree View breadcrumb", async () => {
    mockFetchAllDocuments.mockResolvedValueOnce(hierarchyDocs);
    renderTree();
    await waitFor(() => {
      expect(screen.getByText("Document Hierarchy")).toBeInTheDocument();
    });
    const nav = screen.getByRole("navigation");
    expect(within(nav).getByText("Project")).toBeInTheDocument();
    expect(within(nav).getByText("Tree View")).toBeInTheDocument();
  });
});
