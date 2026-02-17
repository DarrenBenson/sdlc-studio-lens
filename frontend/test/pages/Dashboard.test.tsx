/**
 * Dashboard page component tests.
 * Test cases: TC0210-TC0217 from TS0018.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";

import type { AggregateStats } from "../../src/types/index.ts";

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
}));

const { fetchAggregateStats } = await import("../../src/api/client.ts");
const mockFetchStats = vi.mocked(fetchAggregateStats);

const sampleStats: AggregateStats = {
  total_projects: 2,
  total_documents: 182,
  by_type: { story: 140, epic: 22, plan: 10, prd: 2 },
  by_status: { Done: 160, Draft: 12, "In Progress": 10 },
  completion_percentage: 90.0,
  projects: [
    {
      slug: "project-alpha",
      name: "Project Alpha",
      total_documents: 152,
      completion_percentage: 95.8,
      last_synced_at: "2026-02-17T10:30:00Z",
    },
    {
      slug: "project-beta",
      name: "Project Beta",
      total_documents: 30,
      completion_percentage: 66.7,
      last_synced_at: "2026-02-17T12:00:00Z",
    },
  ],
};

// Helper to import and render Dashboard
async function renderDashboard() {
  const { Dashboard } = await import("../../src/pages/Dashboard.tsx");
  return render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>,
  );
}

// TC0210: Dashboard renders project cards
describe("Dashboard project cards", () => {
  it("renders project names", async () => {
    mockFetchStats.mockResolvedValue(sampleStats);
    await renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("Project Alpha")).toBeInTheDocument();
    });
    expect(screen.getByText("Project Beta")).toBeInTheDocument();
  });
});

// TC0211: Project card shows document count and completion
describe("Dashboard card details", () => {
  it("shows document count", async () => {
    mockFetchStats.mockResolvedValue(sampleStats);
    await renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("152")).toBeInTheDocument();
    });
  });
});

// TC0212: Progress ring on cards
describe("Dashboard progress ring", () => {
  it("renders percentage text", async () => {
    mockFetchStats.mockResolvedValue(sampleStats);
    await renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("95.8%")).toBeInTheDocument();
    });
    expect(screen.getByText("66.7%")).toBeInTheDocument();
  });
});

// TC0213: Click card navigates to project detail
describe("Dashboard card navigation", () => {
  it("card links to project detail", async () => {
    mockFetchStats.mockResolvedValue(sampleStats);
    await renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("Project Alpha")).toBeInTheDocument();
    });
    const link = screen.getByText("Project Alpha").closest("a");
    expect(link).toHaveAttribute("href", "/projects/project-alpha");
  });
});

// TC0214: Empty state when no projects
describe("Dashboard empty state", () => {
  it("shows empty message and settings link", async () => {
    mockFetchStats.mockResolvedValue({
      total_projects: 0,
      total_documents: 0,
      by_type: {},
      by_status: {},
      completion_percentage: 0.0,
      projects: [],
    });
    await renderDashboard();
    await waitFor(() => {
      expect(screen.getByText(/no projects registered/i)).toBeInTheDocument();
    });
    const link = screen.getByRole("link", { name: /settings/i });
    expect(link).toHaveAttribute("href", "/settings");
  });
});

// TC0215: Aggregate stats header
describe("Dashboard aggregate stats", () => {
  it("shows totals in header", async () => {
    mockFetchStats.mockResolvedValue(sampleStats);
    await renderDashboard();
    await waitFor(() => {
      expect(screen.getByText("182")).toBeInTheDocument();
    });
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("Documents")).toBeInTheDocument();
    expect(screen.getAllByText("90%").length).toBeGreaterThan(0);
  });
});

// TC0216: Loading state
describe("Dashboard loading", () => {
  it("shows loading indicator", async () => {
    mockFetchStats.mockReturnValue(new Promise(() => {})); // never resolves
    await renderDashboard();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});

// TC0217: Error state
describe("Dashboard error", () => {
  it("shows error with retry button", async () => {
    mockFetchStats.mockRejectedValue(new Error("Network error"));
    await renderDashboard();
    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });
});
