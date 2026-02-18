/**
 * DocumentView page component tests.
 *
 * Test cases: TC0179-TC0186 from TS0015.
 */

import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import type { DocumentDetail } from "../types/index.ts";
import { DocumentView } from "./DocumentView.tsx";

vi.mock("../api/client.ts", () => ({
  fetchProjects: vi.fn(),
  fetchProject: vi.fn(),
  createProject: vi.fn(),
  updateProject: vi.fn(),
  deleteProject: vi.fn(),
  triggerSync: vi.fn(),
  fetchDocuments: vi.fn(),
  fetchDocument: vi.fn(),
  fetchRelatedDocuments: vi.fn(),
  fetchAggregateStats: vi.fn(),
  fetchProjectStats: vi.fn(),
  fetchSearchResults: vi.fn(),
}));

const { fetchDocument, fetchRelatedDocuments } = await import(
  "../api/client.ts"
);
const mockFetchDocument = vi.mocked(fetchDocument);
const mockFetchRelated = vi.mocked(fetchRelatedDocuments);

const sampleDocument: DocumentDetail = {
  doc_id: "US0001-register-project",
  type: "story",
  title: "Register a New Project",
  status: "Done",
  owner: "Darren",
  priority: "P0",
  story_points: 5,
  epic: "EP0001",
  story: null,
  metadata: { sprint: "Sprint 1", created: "2026-02-17" },
  content:
    "# US0001: Register a New Project\n\n> **Status:** Done\n\n## Description\n\nAs a developer, I want to register a project.\n\n- Item one\n- Item two\n",
  file_path: "stories/US0001-register-project.md",
  file_hash: "a1b2c3d4" + "0".repeat(56),
  synced_at: "2026-02-17T10:30:00Z",
};

/** Default: related documents returns empty to avoid breaking existing tests. */
function setupDefaultRelatedMock() {
  mockFetchRelated.mockResolvedValue({
    doc_id: "US0001-register-project",
    type: "story",
    title: "Register a New Project",
    parents: [],
    children: [],
  });
}

function renderDocumentView(path = "/projects/testproject/documents/story/US0001-register-project") {
  setupDefaultRelatedMock();
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="projects/:slug/documents/:type/:docId"
          element={<DocumentView />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

// ---------------------------------------------------------------------------
// TC0179: Document title rendered
// ---------------------------------------------------------------------------

describe("TC0179: Document title", () => {
  it("displays the document title", async () => {
    mockFetchDocument.mockResolvedValueOnce(sampleDocument);
    renderDocumentView();
    await waitFor(() => {
      expect(
        screen.getByText("Register a New Project"),
      ).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// TC0180: Markdown content rendered
// ---------------------------------------------------------------------------

describe("TC0180: Markdown content", () => {
  it("renders markdown content as HTML", async () => {
    mockFetchDocument.mockResolvedValueOnce(sampleDocument);
    renderDocumentView();
    await waitFor(() => {
      expect(screen.getByText("Description")).toBeInTheDocument();
    });
    expect(screen.getByText("Item one")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0181: Frontmatter sidebar shows status badge
// ---------------------------------------------------------------------------

describe("TC0181: Status badge in sidebar", () => {
  it("displays status badge in sidebar", async () => {
    mockFetchDocument.mockResolvedValueOnce(sampleDocument);
    renderDocumentView();
    await waitFor(() => {
      expect(screen.getByText("Properties")).toBeInTheDocument();
    });
    // The sidebar contains a StatusBadge with "Done"
    const sidebar = screen.getByText("Properties").closest("aside")!;
    expect(within(sidebar).getByText("Done")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0182: Frontmatter sidebar shows owner and priority
// ---------------------------------------------------------------------------

describe("TC0182: Owner and priority in sidebar", () => {
  it("displays owner in sidebar", async () => {
    mockFetchDocument.mockResolvedValueOnce(sampleDocument);
    renderDocumentView();
    await waitFor(() => {
      expect(screen.getByText("Darren")).toBeInTheDocument();
    });
  });

  it("displays priority in sidebar", async () => {
    mockFetchDocument.mockResolvedValueOnce(sampleDocument);
    renderDocumentView();
    await waitFor(() => {
      expect(screen.getByText("P0")).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// TC0183: File path shown
// ---------------------------------------------------------------------------

describe("TC0183: File path", () => {
  it("displays file path", async () => {
    mockFetchDocument.mockResolvedValueOnce(sampleDocument);
    renderDocumentView();
    await waitFor(() => {
      expect(
        screen.getByText("stories/US0001-register-project.md"),
      ).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// TC0184: Sync timestamp shown
// ---------------------------------------------------------------------------

describe("TC0184: Sync timestamp", () => {
  it("displays synced at timestamp", async () => {
    mockFetchDocument.mockResolvedValueOnce(sampleDocument);
    renderDocumentView();
    await waitFor(() => {
      expect(screen.getByText(/17 Feb 2026/)).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// TC0185: 404 document shows error state
// ---------------------------------------------------------------------------

describe("TC0185: Error state", () => {
  it("shows error message on fetch failure", async () => {
    mockFetchDocument.mockRejectedValueOnce(new Error("Document not found"));
    renderDocumentView();
    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// TC0186: Loading state shown during fetch
// ---------------------------------------------------------------------------

describe("TC0186: Loading state", () => {
  it("shows loading indicator initially", () => {
    mockFetchDocument.mockReturnValue(new Promise(() => {})); // never resolves
    renderDocumentView();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0372-TC0378: Relationship navigation (US0035)
// ---------------------------------------------------------------------------

const planDocument: DocumentDetail = {
  doc_id: "PL0028-database-plan",
  type: "plan",
  title: "Database Plan",
  status: "Done",
  owner: "Darren",
  priority: null,
  story_points: null,
  epic: "EP0007",
  story: "US0028",
  metadata: null,
  content: "# PL0028: Database Plan\n\nPlan content.",
  file_path: "plans/PL0028-database-plan.md",
  file_hash: "f".repeat(64),
  synced_at: "2026-02-18T12:00:00Z",
};

const planRelated = {
  doc_id: "PL0028-database-plan",
  type: "plan",
  title: "Database Plan",
  parents: [
    { doc_id: "US0028-database-schema", type: "story", title: "Database Schema", status: "Done" },
    { doc_id: "EP0007-git-repo-sync", type: "epic", title: "Git Repository Sync", status: "Done" },
  ],
  children: [],
};

const epicDocument: DocumentDetail = {
  doc_id: "EP0007-git-repo-sync",
  type: "epic",
  title: "Git Repository Sync",
  status: "Done",
  owner: "Darren",
  priority: null,
  story_points: null,
  epic: null,
  story: null,
  metadata: null,
  content: "# EP0007\n\nEpic content.",
  file_path: "epics/EP0007-git-repo-sync.md",
  file_hash: "e".repeat(64),
  synced_at: "2026-02-18T12:00:00Z",
};

const epicRelated = {
  doc_id: "EP0007-git-repo-sync",
  type: "epic",
  title: "Git Repository Sync",
  parents: [],
  children: [
    { doc_id: "US0028-database-schema", type: "story", title: "Database Schema", status: "Done" },
    { doc_id: "US0029-github-api", type: "story", title: "GitHub API Source", status: "Done" },
  ],
};

describe("TC0372: Hierarchy breadcrumbs for plan (3 levels)", () => {
  it("shows ancestor chain in breadcrumbs", async () => {
    mockFetchDocument.mockResolvedValueOnce(planDocument);
    mockFetchRelated.mockResolvedValueOnce(planRelated);
    renderDocumentView("/projects/testproject/documents/plan/PL0028-database-plan");
    await waitFor(() => {
      expect(screen.getByText("Database Plan")).toBeInTheDocument();
    });
    // Breadcrumbs should contain EP0007 and US0028
    const nav = screen.getByRole("navigation");
    expect(within(nav).getByText("EP0007")).toBeInTheDocument();
    expect(within(nav).getByText("US0028")).toBeInTheDocument();
  });
});

describe("TC0373: Breadcrumbs link to correct routes", () => {
  it("ancestor links have correct href", async () => {
    mockFetchDocument.mockResolvedValueOnce(planDocument);
    mockFetchRelated.mockResolvedValueOnce(planRelated);
    renderDocumentView("/projects/testproject/documents/plan/PL0028-database-plan");
    await waitFor(() => {
      expect(screen.getByText("Database Plan")).toBeInTheDocument();
    });
    const nav = screen.getByRole("navigation");
    const epicLink = within(nav).getByText("EP0007").closest("a");
    expect(epicLink).toHaveAttribute(
      "href",
      "/projects/testproject/documents/epic/EP0007-git-repo-sync",
    );
  });
});

describe("TC0374: Related panel shows parents", () => {
  it("displays parent documents in sidebar", async () => {
    mockFetchDocument.mockResolvedValueOnce(planDocument);
    mockFetchRelated.mockResolvedValueOnce(planRelated);
    renderDocumentView("/projects/testproject/documents/plan/PL0028-database-plan");
    await waitFor(() => {
      expect(screen.getByText("Relationships")).toBeInTheDocument();
    });
    expect(screen.getByText("Parents")).toBeInTheDocument();
    expect(screen.getByText("Database Schema")).toBeInTheDocument();
    expect(screen.getByText("Git Repository Sync")).toBeInTheDocument();
  });
});

describe("TC0375: Related panel shows children", () => {
  it("displays child documents in sidebar", async () => {
    mockFetchDocument.mockResolvedValueOnce(epicDocument);
    mockFetchRelated.mockResolvedValueOnce(epicRelated);
    renderDocumentView("/projects/testproject/documents/epic/EP0007-git-repo-sync");
    await waitFor(() => {
      expect(screen.getByText("Relationships")).toBeInTheDocument();
    });
    expect(screen.getByText("Children")).toBeInTheDocument();
    expect(screen.getByText("Database Schema")).toBeInTheDocument();
    expect(screen.getByText("GitHub API Source")).toBeInTheDocument();
  });
});

describe("TC0376: No relationships panel when empty", () => {
  it("hides relationships panel when no parents or children", async () => {
    mockFetchDocument.mockResolvedValueOnce(sampleDocument);
    // Default mock returns empty parents/children
    renderDocumentView();
    await waitFor(() => {
      expect(screen.getByText("Register a New Project")).toBeInTheDocument();
    });
    expect(screen.queryByText("Relationships")).not.toBeInTheDocument();
  });
});

describe("TC0377: Fallback when relationships API fails", () => {
  it("still renders document when related API fails", async () => {
    mockFetchDocument.mockResolvedValueOnce(sampleDocument);
    mockFetchRelated.mockRejectedValueOnce(new Error("Network error"));
    renderDocumentView();
    await waitFor(() => {
      expect(screen.getByText("Register a New Project")).toBeInTheDocument();
    });
    // Generic breadcrumbs shown (no ancestors)
    const nav = screen.getByRole("navigation");
    expect(within(nav).getByText("Project")).toBeInTheDocument();
    expect(within(nav).getByText("Documents")).toBeInTheDocument();
  });
});

describe("TC0378: Story field shown in properties sidebar", () => {
  it("displays story value in sidebar when present", async () => {
    mockFetchDocument.mockResolvedValueOnce(planDocument);
    mockFetchRelated.mockResolvedValueOnce(planRelated);
    renderDocumentView("/projects/testproject/documents/plan/PL0028-database-plan");
    await waitFor(() => {
      expect(screen.getByText("Database Plan")).toBeInTheDocument();
    });
    const sidebar = screen.getByText("Properties").closest("div")!;
    expect(within(sidebar).getByText("Story")).toBeInTheDocument();
    expect(within(sidebar).getByText("US0028")).toBeInTheDocument();
  });
});
