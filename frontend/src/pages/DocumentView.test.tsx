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
}));

const { fetchDocument } = await import("../api/client.ts");
const mockFetchDocument = vi.mocked(fetchDocument);

const sampleDocument: DocumentDetail = {
  doc_id: "US0001-register-project",
  type: "story",
  title: "Register a New Project",
  status: "Done",
  owner: "Darren",
  priority: "P0",
  story_points: 5,
  epic: "EP0001",
  metadata: { sprint: "Sprint 1", created: "2026-02-17" },
  content:
    "# US0001: Register a New Project\n\n> **Status:** Done\n\n## Description\n\nAs a developer, I want to register a project.\n\n- Item one\n- Item two\n",
  file_path: "stories/US0001-register-project.md",
  file_hash: "a1b2c3d4" + "0".repeat(56),
  synced_at: "2026-02-17T10:30:00Z",
};

function renderDocumentView(path = "/projects/testproject/documents/story/US0001-register-project") {
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
