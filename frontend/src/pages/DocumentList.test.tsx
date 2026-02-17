/**
 * DocumentList page component tests.
 *
 * Test cases: TC0169-TC0178 from TS0014.
 */

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import type { PaginatedDocuments } from "../types/index.ts";
import { DocumentList } from "./DocumentList.tsx";

vi.mock("../api/client.ts", () => ({
  fetchProjects: vi.fn(),
  fetchProject: vi.fn(),
  createProject: vi.fn(),
  updateProject: vi.fn(),
  deleteProject: vi.fn(),
  triggerSync: vi.fn(),
  fetchDocuments: vi.fn(),
}));

const { fetchDocuments } = await import("../api/client.ts");
const mockFetchDocuments = vi.mocked(fetchDocuments);

const sampleResponse: PaginatedDocuments = {
  items: [
    {
      doc_id: "EP0001-alpha-epic",
      type: "epic",
      title: "Alpha Epic",
      status: "Done",
      owner: "Darren",
      priority: "P0",
      story_points: 8,
      updated_at: "2026-02-17T10:00:00Z",
    },
    {
      doc_id: "US0001-register-project",
      type: "story",
      title: "Register a New Project",
      status: "In Progress",
      owner: "Darren",
      priority: "P0",
      story_points: 5,
      updated_at: "2026-02-17T11:00:00Z",
    },
    {
      doc_id: "BG0001-login-bug",
      type: "bug",
      title: "Login Bug Fix",
      status: "Draft",
      owner: null,
      priority: null,
      story_points: null,
      updated_at: "2026-02-17T09:00:00Z",
    },
  ],
  total: 3,
  page: 1,
  per_page: 50,
  pages: 1,
};

const emptyResponse: PaginatedDocuments = {
  items: [],
  total: 0,
  page: 1,
  per_page: 50,
  pages: 0,
};

function renderDocumentList() {
  return render(
    <MemoryRouter initialEntries={["/projects/testproject/documents"]}>
      <Routes>
        <Route path="projects/:slug/documents" element={<DocumentList />} />
        <Route
          path="projects/:slug/documents/:type/:docId"
          element={<div data-testid="detail-page">Detail</div>}
        />
      </Routes>
    </MemoryRouter>,
  );
}

// ---------------------------------------------------------------------------
// TC0169: Document list renders document titles
// ---------------------------------------------------------------------------

describe("TC0169: Document titles rendered", () => {
  it("displays document titles after loading", async () => {
    mockFetchDocuments.mockResolvedValueOnce(sampleResponse);
    renderDocumentList();
    await waitFor(() => {
      expect(screen.getByText("Alpha Epic")).toBeInTheDocument();
    });
    expect(screen.getByText("Register a New Project")).toBeInTheDocument();
    expect(screen.getByText("Login Bug Fix")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0170: Type badges shown for documents
// ---------------------------------------------------------------------------

describe("TC0170: Type badges shown", () => {
  it("displays type badges for each document", async () => {
    mockFetchDocuments.mockResolvedValueOnce(sampleResponse);
    renderDocumentList();
    await waitFor(() => {
      expect(screen.getByText("Alpha Epic")).toBeInTheDocument();
    });
    const table = screen.getByRole("table");
    const tableScope = within(table);
    expect(tableScope.getByText("Epic")).toBeInTheDocument();
    expect(tableScope.getByText("Story")).toBeInTheDocument();
    expect(tableScope.getByText("Bug")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0171: Status badges shown for documents
// ---------------------------------------------------------------------------

describe("TC0171: Status badges shown", () => {
  it("displays status badges for each document", async () => {
    mockFetchDocuments.mockResolvedValueOnce(sampleResponse);
    renderDocumentList();
    await waitFor(() => {
      expect(screen.getByText("Alpha Epic")).toBeInTheDocument();
    });
    const table = screen.getByRole("table");
    const tableScope = within(table);
    expect(tableScope.getByText("Done")).toBeInTheDocument();
    expect(tableScope.getByText("In Progress")).toBeInTheDocument();
    expect(tableScope.getByText("Draft")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0172: Type filter calls API with type param
// ---------------------------------------------------------------------------

describe("TC0172: Type filter", () => {
  it("calls fetchDocuments with type param on filter change", async () => {
    mockFetchDocuments.mockResolvedValue(sampleResponse);
    const user = userEvent.setup();
    renderDocumentList();

    await waitFor(() => {
      expect(screen.getByText("Alpha Epic")).toBeInTheDocument();
    });

    const typeSelect = screen.getByLabelText("Type");
    await user.selectOptions(typeSelect, "epic");

    await waitFor(() => {
      expect(mockFetchDocuments).toHaveBeenCalledWith(
        "testproject",
        expect.objectContaining({ type: "epic" }),
      );
    });
  });
});

// ---------------------------------------------------------------------------
// TC0173: Status filter calls API with status param
// ---------------------------------------------------------------------------

describe("TC0173: Status filter", () => {
  it("calls fetchDocuments with status param on filter change", async () => {
    mockFetchDocuments.mockResolvedValue(sampleResponse);
    const user = userEvent.setup();
    renderDocumentList();

    await waitFor(() => {
      expect(screen.getByText("Alpha Epic")).toBeInTheDocument();
    });

    const statusSelect = screen.getByLabelText("Status");
    await user.selectOptions(statusSelect, "Done");

    await waitFor(() => {
      expect(mockFetchDocuments).toHaveBeenCalledWith(
        "testproject",
        expect.objectContaining({ status: "Done" }),
      );
    });
  });
});

// ---------------------------------------------------------------------------
// TC0174: Click navigates to document view route
// ---------------------------------------------------------------------------

describe("TC0174: Click navigation", () => {
  it("navigates to document detail on click", async () => {
    mockFetchDocuments.mockResolvedValueOnce(sampleResponse);
    const user = userEvent.setup();
    renderDocumentList();

    await waitFor(() => {
      expect(screen.getByText("Alpha Epic")).toBeInTheDocument();
    });

    await user.click(screen.getByText("Alpha Epic"));

    await waitFor(() => {
      expect(screen.getByTestId("detail-page")).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// TC0175: Empty state shown when no documents
// ---------------------------------------------------------------------------

describe("TC0175: Empty state", () => {
  it("shows empty message when no documents", async () => {
    mockFetchDocuments.mockResolvedValueOnce(emptyResponse);
    renderDocumentList();

    await waitFor(() => {
      expect(screen.getByText(/no documents/i)).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// TC0176: Loading state shown during fetch
// ---------------------------------------------------------------------------

describe("TC0176: Loading state", () => {
  it("shows loading indicator initially", () => {
    mockFetchDocuments.mockReturnValue(new Promise(() => {})); // never resolves
    renderDocumentList();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0177: Pagination info displayed
// ---------------------------------------------------------------------------

describe("TC0177: Pagination info", () => {
  it("shows pagination info when documents exist", async () => {
    const paginatedResponse: PaginatedDocuments = {
      ...sampleResponse,
      total: 120,
      page: 1,
      per_page: 50,
      pages: 3,
    };
    mockFetchDocuments.mockResolvedValueOnce(paginatedResponse);
    renderDocumentList();

    await waitFor(() => {
      expect(screen.getByText(/page 1/i)).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// TC0178: Error state on API failure
// ---------------------------------------------------------------------------

describe("TC0178: Error state", () => {
  it("shows error message on fetch failure", async () => {
    mockFetchDocuments.mockRejectedValueOnce(new Error("Network error"));
    renderDocumentList();

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});
