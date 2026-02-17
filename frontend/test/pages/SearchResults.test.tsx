/**
 * Search results page component tests.
 * Test cases: TC0245-TC0252 from TS0022.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { SearchResponse } from "../../src/types/index.ts";

vi.mock("../../src/api/client.ts", () => ({
  fetchAggregateStats: vi.fn(),
  fetchProjects: vi.fn(),
  fetchProject: vi.fn(),
  createProject: vi.fn(),
  updateProject: vi.fn(),
  deleteProject: vi.fn(),
  triggerSync: vi.fn(),
  fetchDocuments: vi.fn(),
  fetchDocument: vi.fn(),
  fetchProjectStats: vi.fn(),
  fetchSearchResults: vi.fn(),
}));

const { fetchSearchResults } = await import("../../src/api/client.ts");
const mockFetch = vi.mocked(fetchSearchResults);

/** Helper that renders the current pathname + search string. */
function LocationDisplay() {
  const location = useLocation();
  return (
    <div data-testid="location">
      {location.pathname}
      {location.search}
    </div>
  );
}

async function renderSearchResults(initialUrl = "/search?q=test") {
  const { SearchResults } = await import(
    "../../src/pages/SearchResults.tsx"
  );
  return render(
    <MemoryRouter initialEntries={[initialUrl]}>
      <Routes>
        <Route path="/search" element={<SearchResults />} />
        <Route path="*" element={<LocationDisplay />} />
      </Routes>
    </MemoryRouter>,
  );
}

const threeResults: SearchResponse = {
  items: [
    {
      doc_id: "US0001",
      type: "story",
      title: "User Authentication",
      project_slug: "homelabcmd",
      project_name: "HomelabCmd",
      status: "Done",
      snippet: "Implement <mark>authentication</mark> via API key",
      score: 1.5,
    },
    {
      doc_id: "US0002",
      type: "epic",
      title: "Project Setup",
      project_slug: "homelabcmd",
      project_name: "HomelabCmd",
      status: "In Progress",
      snippet: "Set up <mark>test</mark> infrastructure",
      score: 1.2,
    },
    {
      doc_id: "US0003",
      type: "bug",
      title: "Login Failure",
      project_slug: "sdlc-lens",
      project_name: "SDLC Lens",
      status: null,
      snippet: "Fix <mark>test</mark> login flow",
      score: 0.9,
    },
  ],
  total: 3,
  query: "test",
  page: 1,
  per_page: 20,
};

// ---------------------------------------------------------------------------
// TC0245: Renders result cards
// ---------------------------------------------------------------------------

describe("TC0245: Renders result cards", () => {
  it("displays 3 result cards with titles visible", async () => {
    mockFetch.mockResolvedValue(threeResults);
    await renderSearchResults();

    await waitFor(() => {
      expect(screen.getByText("User Authentication")).toBeInTheDocument();
    });
    expect(screen.getByText("Project Setup")).toBeInTheDocument();
    expect(screen.getByText("Login Failure")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0246: Result card shows type badge, project, snippet
// ---------------------------------------------------------------------------

describe("TC0246: Result card shows type badge, project, snippet", () => {
  it("displays type badge, project name, and snippet with mark tag", async () => {
    mockFetch.mockResolvedValue({
      items: [
        {
          doc_id: "US0001",
          type: "story",
          title: "User Authentication",
          project_slug: "homelabcmd",
          project_name: "HomelabCmd",
          status: "Done",
          snippet: "Implement <mark>authentication</mark> via API key",
          score: 1.5,
        },
      ],
      total: 1,
      query: "authentication",
      page: 1,
      per_page: 20,
    });
    await renderSearchResults("/search?q=authentication");

    await waitFor(() => {
      expect(screen.getByText("User Authentication")).toBeInTheDocument();
    });

    // Type badge should display "Story"
    expect(screen.getByText("Story")).toBeInTheDocument();

    // Project name visible
    expect(screen.getByText("HomelabCmd")).toBeInTheDocument();

    // Snippet rendered with dangerouslySetInnerHTML - the <mark> tag should be in the DOM
    const markElement = document.querySelector("mark");
    expect(markElement).toBeInTheDocument();
    expect(markElement).toHaveTextContent("authentication");
  });
});

// ---------------------------------------------------------------------------
// TC0247: Click result navigates to document
// ---------------------------------------------------------------------------

describe("TC0247: Click result navigates to document", () => {
  it("navigates to /projects/homelabcmd/documents/story/US0045 on click", async () => {
    mockFetch.mockResolvedValue({
      items: [
        {
          doc_id: "US0045",
          type: "story",
          title: "Feature X",
          project_slug: "homelabcmd",
          project_name: "HomelabCmd",
          status: "Done",
          snippet: "Some <mark>test</mark> snippet",
          score: 1.0,
        },
      ],
      total: 1,
      query: "test",
      page: 1,
      per_page: 20,
    });
    await renderSearchResults();

    await waitFor(() => {
      expect(screen.getByText("Feature X")).toBeInTheDocument();
    });

    const link = screen.getByText("Feature X").closest("a");
    expect(link).toHaveAttribute(
      "href",
      "/projects/homelabcmd/documents/story/US0045",
    );
  });
});

// ---------------------------------------------------------------------------
// TC0248: Project filter updates results
// ---------------------------------------------------------------------------

describe("TC0248: Project filter updates results", () => {
  it("updates URL with project parameter when filter selected", async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValue(threeResults);
    await renderSearchResults("/search?q=test");

    await waitFor(() => {
      expect(screen.getByText("User Authentication")).toBeInTheDocument();
    });

    // Find the project filter select element
    const projectSelect = screen.getByRole("combobox", {
      name: /project/i,
    });
    expect(projectSelect).toBeInTheDocument();

    // Select a project filter
    await user.selectOptions(projectSelect, "homelabcmd");

    // The mock should have been called again with the project parameter
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.objectContaining({ q: "test", project: "homelabcmd" }),
      );
    });
  });
});

// ---------------------------------------------------------------------------
// TC0249: No results shows empty state
// ---------------------------------------------------------------------------

describe("TC0249: No results shows empty state", () => {
  it("displays 'No results found' when search returns 0 items", async () => {
    mockFetch.mockResolvedValue({
      items: [],
      total: 0,
      query: "nonexistent",
      page: 1,
      per_page: 20,
    });
    await renderSearchResults("/search?q=nonexistent");

    await waitFor(() => {
      expect(screen.getByText(/no results found/i)).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// TC0250: Search query shown in heading
// ---------------------------------------------------------------------------

describe("TC0250: Search query shown in heading", () => {
  it("displays the result count for the query", async () => {
    mockFetch.mockResolvedValue({
      ...threeResults,
      query: "authentication",
    });
    await renderSearchResults("/search?q=authentication");

    await waitFor(() => {
      expect(screen.getByText(/3/)).toBeInTheDocument();
    });
    // The heading should include the result count
    expect(screen.getByText(/result/i)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0251: Loading state
// ---------------------------------------------------------------------------

describe("TC0251: Loading state", () => {
  it("shows loading indicator while fetching", async () => {
    mockFetch.mockReturnValue(new Promise(() => {})); // never resolves
    await renderSearchResults();

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0252: Error state with retry
// ---------------------------------------------------------------------------

describe("TC0252: Error state with retry", () => {
  it("shows error message with retry button on API failure", async () => {
    mockFetch.mockRejectedValue(new Error("Network error"));
    await renderSearchResults();

    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
    expect(
      screen.getByRole("button", { name: /retry/i }),
    ).toBeInTheDocument();
  });

  it("re-fetches when retry button is clicked", async () => {
    const user = userEvent.setup();
    mockFetch.mockRejectedValueOnce(new Error("Network error"));
    await renderSearchResults();

    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });

    // Now set up a successful response for the retry
    mockFetch.mockResolvedValue(threeResults);

    const retryButton = screen.getByRole("button", { name: /retry/i });
    await user.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText("User Authentication")).toBeInTheDocument();
    });
  });
});
