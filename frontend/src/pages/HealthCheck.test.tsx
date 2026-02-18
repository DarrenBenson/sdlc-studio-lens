/**
 * HealthCheck page component tests.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import type { HealthCheckResponse } from "../types/index.ts";
import { HealthCheck } from "./HealthCheck.tsx";

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
  fetchHealthCheck: vi.fn(),
  fetchSearchResults: vi.fn(),
}));

const { fetchHealthCheck } = await import("../api/client.ts");
const mockFetchHealthCheck = vi.mocked(fetchHealthCheck);

const healthyResponse: HealthCheckResponse = {
  project_slug: "my-project",
  checked_at: "2026-02-18T12:00:00+00:00",
  total_documents: 6,
  findings: [],
  summary: { critical: 0, high: 0, medium: 0, low: 0 },
  score: 100,
};

const unhealthyResponse: HealthCheckResponse = {
  project_slug: "my-project",
  checked_at: "2026-02-18T12:00:00+00:00",
  total_documents: 3,
  findings: [
    {
      rule_id: "MISSING_PRD",
      severity: "critical",
      category: "completeness",
      message: "Project has no PRD document.",
      affected_documents: [],
      suggested_fix: "Create a PRD document defining the product requirements.",
    },
    {
      rule_id: "STORY_NO_EPIC",
      severity: "high",
      category: "consistency",
      message: "Story 'My Story' has no epic reference.",
      affected_documents: [
        { doc_id: "US0001", doc_type: "story", title: "My Story" },
      ],
      suggested_fix: "Add an epic reference to story US0001.",
    },
    {
      rule_id: "MISSING_PRIORITY",
      severity: "low",
      category: "quality",
      message: "Story 'My Story' has no priority set.",
      affected_documents: [
        { doc_id: "US0001", doc_type: "story", title: "My Story" },
      ],
      suggested_fix: "Add a priority field to US0001 frontmatter.",
    },
  ],
  summary: { critical: 1, high: 1, medium: 0, low: 1 },
  score: 74,
};

function renderPage(slug = "my-project") {
  return render(
    <MemoryRouter initialEntries={[`/projects/${slug}/health-check`]}>
      <Routes>
        <Route
          path="projects/:slug/health-check"
          element={<HealthCheck />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("HealthCheck", () => {
  it("shows loading state initially", () => {
    mockFetchHealthCheck.mockReturnValue(new Promise(() => {}));
    renderPage();
    expect(screen.getByText("Running health check...")).toBeInTheDocument();
  });

  it("renders score and no-issues message for healthy project", async () => {
    mockFetchHealthCheck.mockResolvedValue(healthyResponse);
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("100")).toBeInTheDocument();
    });

    expect(screen.getByText("No issues found")).toBeInTheDocument();
    expect(screen.getByText("6 documents analysed")).toBeInTheDocument();
    expect(screen.getByText("Health Score")).toBeInTheDocument();
  });

  it("renders findings grouped by category", async () => {
    mockFetchHealthCheck.mockResolvedValue(unhealthyResponse);
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("74")).toBeInTheDocument();
    });

    // Category headings
    expect(screen.getByText("Completeness")).toBeInTheDocument();
    expect(screen.getByText("Consistency")).toBeInTheDocument();
    expect(screen.getByText("Quality")).toBeInTheDocument();

    // Finding messages
    expect(
      screen.getByText("Project has no PRD document."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Story 'My Story' has no epic reference."),
    ).toBeInTheDocument();
  });

  it("renders severity badges", async () => {
    mockFetchHealthCheck.mockResolvedValue(unhealthyResponse);
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("critical")).toBeInTheDocument();
    });

    expect(screen.getByText("high")).toBeInTheDocument();
    expect(screen.getByText("low")).toBeInTheDocument();
  });

  it("renders summary counts as filter buttons", async () => {
    mockFetchHealthCheck.mockResolvedValue(unhealthyResponse);
    renderPage();

    await waitFor(() => {
      expect(screen.getByTitle("Filter by Critical")).toBeInTheDocument();
    });

    expect(screen.getByTitle("Filter by High")).toBeInTheDocument();
    expect(screen.getByTitle("Filter by Medium")).toBeInTheDocument();
    expect(screen.getByTitle("Filter by Low")).toBeInTheDocument();
  });

  it("filters findings by severity when clicking summary", async () => {
    mockFetchHealthCheck.mockResolvedValue(unhealthyResponse);
    renderPage();
    const user = userEvent.setup();

    await waitFor(() => {
      expect(screen.getByTitle("Filter by High")).toBeInTheDocument();
    });

    await user.click(screen.getByTitle("Filter by High"));

    // Should show only the high finding
    expect(
      screen.getByText("Story 'My Story' has no epic reference."),
    ).toBeInTheDocument();
    // Should hide the critical and low findings
    expect(
      screen.queryByText("Project has no PRD document."),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("Story 'My Story' has no priority set."),
    ).not.toBeInTheDocument();
    // Should show filter status
    expect(screen.getByText(/Showing 1 high finding/)).toBeInTheDocument();
    expect(screen.getByText("Clear filter")).toBeInTheDocument();
  });

  it("clears filter when clicking active severity or clear link", async () => {
    mockFetchHealthCheck.mockResolvedValue(unhealthyResponse);
    renderPage();
    const user = userEvent.setup();

    await waitFor(() => {
      expect(screen.getByTitle("Filter by High")).toBeInTheDocument();
    });

    // Activate filter
    await user.click(screen.getByTitle("Filter by High"));
    expect(
      screen.queryByText("Project has no PRD document."),
    ).not.toBeInTheDocument();

    // Clear via "Clear filter" link
    await user.click(screen.getByText("Clear filter"));

    // All findings visible again
    expect(
      screen.getByText("Project has no PRD document."),
    ).toBeInTheDocument();
  });

  it("renders affected document links", async () => {
    mockFetchHealthCheck.mockResolvedValue(unhealthyResponse);
    renderPage();

    await waitFor(() => {
      expect(screen.getAllByText("US0001").length).toBeGreaterThan(0);
    });

    const links = screen.getAllByText("US0001");
    expect(links[0].closest("a")).toHaveAttribute(
      "href",
      "/projects/my-project/documents/story/US0001",
    );
  });

  it("renders copy-all button", async () => {
    mockFetchHealthCheck.mockResolvedValue(unhealthyResponse);
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Copy all")).toBeInTheDocument();
    });
  });

  it("renders breadcrumb with project link", async () => {
    mockFetchHealthCheck.mockResolvedValue(healthyResponse);
    renderPage();

    await waitFor(() => {
      expect(
        screen.getByRole("navigation", { name: "Breadcrumb" }),
      ).toBeInTheDocument();
    });

    const projectLink = screen.getByText("my-project");
    expect(projectLink.closest("a")).toHaveAttribute(
      "href",
      "/projects/my-project",
    );
  });

  it("shows error state with retry", async () => {
    mockFetchHealthCheck.mockRejectedValue(new Error("Network error"));
    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });

    expect(screen.getByText("Retry")).toBeInTheDocument();
  });

  it("retries on button click", async () => {
    mockFetchHealthCheck
      .mockRejectedValueOnce(new Error("fail"))
      .mockResolvedValueOnce(healthyResponse);

    renderPage();
    const user = userEvent.setup();

    await waitFor(() => {
      expect(screen.getByText("Retry")).toBeInTheDocument();
    });

    await user.click(screen.getByText("Retry"));

    await waitFor(() => {
      expect(screen.getByText("100")).toBeInTheDocument();
    });
  });
});
