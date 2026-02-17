/**
 * Project detail statistics page component tests.
 * Test cases: TC0218-TC0227 from TS0019.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import type { ProjectStats } from "../../src/types/index.ts";

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

// Mock recharts to avoid canvas/SVG rendering issues in jsdom
vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  BarChart: ({ children, data }: { children: React.ReactNode; data: unknown[] }) => (
    <div data-testid="bar-chart" data-count={data.length}>
      {children}
    </div>
  ),
  Bar: ({ dataKey, name }: { dataKey: string; name?: string }) => (
    <div data-testid={`bar-${dataKey}`} data-name={name} />
  ),
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Cell: () => <div data-testid="cell" />,
}));

const { fetchProjectStats } = await import("../../src/api/client.ts");
const mockFetchStats = vi.mocked(fetchProjectStats);

const sampleStats: ProjectStats = {
  slug: "project-alpha",
  name: "Project Alpha",
  total_documents: 152,
  by_type: { story: 120, epic: 18, bug: 5, plan: 9 },
  by_status: { Done: 145, Draft: 2, "In Progress": 4, Review: 1 },
  completion_percentage: 95.8,
  last_synced_at: "2026-02-17T10:30:00Z",
};

async function renderProjectDetail(slug = "project-alpha") {
  const { ProjectDetail } = await import(
    "../../src/pages/ProjectDetail.tsx"
  );
  return render(
    <MemoryRouter initialEntries={[`/projects/${slug}`]}>
      <Routes>
        <Route path="projects/:slug" element={<ProjectDetail />} />
        <Route
          path="projects/:slug/documents"
          element={<div>DocumentList</div>}
        />
      </Routes>
    </MemoryRouter>,
  );
}

// TC0218: Project header renders name and progress ring
describe("ProjectDetail header", () => {
  it("renders project name and progress ring", async () => {
    mockFetchStats.mockResolvedValue(sampleStats);
    await renderProjectDetail();
    await waitFor(() => {
      expect(screen.getByText("Project Alpha")).toBeInTheDocument();
    });
    expect(screen.getByText("95.8%")).toBeInTheDocument();
  });
});

// TC0219: Last synced timestamp displayed
describe("ProjectDetail last synced", () => {
  it("shows last synced timestamp", async () => {
    mockFetchStats.mockResolvedValue(sampleStats);
    await renderProjectDetail();
    await waitFor(() => {
      expect(screen.getByText(/synced/i)).toBeInTheDocument();
    });
  });
});

// TC0220: Type distribution chart renders
describe("ProjectDetail type chart", () => {
  it("renders bar chart for type distribution", async () => {
    mockFetchStats.mockResolvedValue(sampleStats);
    await renderProjectDetail();
    await waitFor(() => {
      expect(screen.getByText("Project Alpha")).toBeInTheDocument();
    });
    const charts = screen.getAllByTestId("bar-chart");
    expect(charts.length).toBeGreaterThanOrEqual(1);
  });
});

// TC0221: Status breakdown chart renders
describe("ProjectDetail status chart", () => {
  it("renders bar chart for status breakdown", async () => {
    mockFetchStats.mockResolvedValue(sampleStats);
    await renderProjectDetail();
    await waitFor(() => {
      expect(screen.getByText("Project Alpha")).toBeInTheDocument();
    });
    const charts = screen.getAllByTestId("bar-chart");
    expect(charts.length).toBeGreaterThanOrEqual(2);
  });
});

// TC0222: Per-type stat cards show counts
describe("ProjectDetail stat cards", () => {
  it("shows stat cards with per-type counts", async () => {
    mockFetchStats.mockResolvedValue(sampleStats);
    await renderProjectDetail();
    await waitFor(() => {
      expect(screen.getByText("120")).toBeInTheDocument();
    });
    expect(screen.getByText("18")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });
});

// TC0223: Click stat card navigates to filtered documents
describe("ProjectDetail stat card navigation", () => {
  it("navigates to filtered document list on card click", async () => {
    mockFetchStats.mockResolvedValue(sampleStats);
    await renderProjectDetail();
    await waitFor(() => {
      expect(screen.getByText("120")).toBeInTheDocument();
    });
    const storyCard = screen.getByText("120").closest("a");
    expect(storyCard).toHaveAttribute(
      "href",
      "/projects/project-alpha/documents?type=story",
    );
  });
});

// TC0224: Loading state
describe("ProjectDetail loading", () => {
  it("shows loading indicator", async () => {
    mockFetchStats.mockReturnValue(new Promise(() => {}));
    await renderProjectDetail();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});

// TC0225: Error state with retry
describe("ProjectDetail error", () => {
  it("shows error with retry button", async () => {
    mockFetchStats.mockRejectedValue(new Error("Network error"));
    await renderProjectDetail();
    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
    expect(
      screen.getByRole("button", { name: /retry/i }),
    ).toBeInTheDocument();
  });
});

// TC0226: Zero-document project
describe("ProjectDetail zero documents", () => {
  it("renders with empty data", async () => {
    mockFetchStats.mockResolvedValue({
      ...sampleStats,
      total_documents: 0,
      by_type: {},
      by_status: {},
      completion_percentage: 0,
    });
    await renderProjectDetail();
    await waitFor(() => {
      expect(screen.getByText("Project Alpha")).toBeInTheDocument();
    });
    expect(screen.getByText("0%")).toBeInTheDocument();
  });
});

// TC0227: Not found / error state
describe("ProjectDetail not found", () => {
  it("shows error for unknown project", async () => {
    mockFetchStats.mockRejectedValue(new Error("Not found"));
    await renderProjectDetail("unknown-slug");
    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
  });
});
