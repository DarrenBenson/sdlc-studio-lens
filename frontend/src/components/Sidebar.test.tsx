/**
 * Sidebar component tests.
 * Test cases: TC0048-TC0055 from TS0005.
 */
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Project } from "../types/index.ts";
import { Sidebar } from "./Sidebar.tsx";

// Mock the API client module
vi.mock("../api/client.ts", () => ({
  fetchProjects: vi.fn(),
}));

// Import the mocked function for test control
const { fetchProjects } = await import("../api/client.ts");
const mockFetchProjects = vi.mocked(fetchProjects);

function renderSidebar(initialPath = "/") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Sidebar />
    </MemoryRouter>,
  );
}

const threeProjects: Project[] = [
  {
    slug: "homelabcmd",
    name: "HomelabCmd",
    sdlc_path: "/data/projects/HomelabCmd/sdlc-studio",
    sync_status: "synced",
    sync_error: null,
    last_synced_at: "2026-02-17T10:00:00Z",
    document_count: 152,
    created_at: "2026-02-17T09:00:00Z",
  },
  {
    slug: "sdlclens",
    name: "SDLCLens",
    sdlc_path: "/data/projects/SDLCLens/sdlc-studio",
    sync_status: "syncing",
    sync_error: null,
    last_synced_at: null,
    document_count: 0,
    created_at: "2026-02-17T09:30:00Z",
  },
  {
    slug: "personalblog",
    name: "PersonalBlog",
    sdlc_path: "/data/projects/PersonalBlog/sdlc-studio",
    sync_status: "never_synced",
    sync_error: null,
    last_synced_at: null,
    document_count: 0,
    created_at: "2026-02-17T10:00:00Z",
  },
];

const mixedStatusProjects: Project[] = [
  { ...threeProjects[0], slug: "proj-synced", name: "Synced Project", sync_status: "synced" },
  { ...threeProjects[0], slug: "proj-syncing", name: "Syncing Project", sync_status: "syncing" },
  { ...threeProjects[0], slug: "proj-never", name: "Never Synced", sync_status: "never_synced" },
  { ...threeProjects[0], slug: "proj-error", name: "Error Project", sync_status: "error" },
];

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// TC0048: Sidebar renders project list from API data
describe("TC0048: Sidebar renders project list", () => {
  it("displays all project names", async () => {
    mockFetchProjects.mockResolvedValue(threeProjects);
    renderSidebar();

    await waitFor(() => {
      expect(screen.getByText("HomelabCmd")).toBeInTheDocument();
    });
    expect(screen.getByText("SDLCLens")).toBeInTheDocument();
    expect(screen.getByText("PersonalBlog")).toBeInTheDocument();
  });
});

// TC0049: Sidebar shows empty state when no projects
describe("TC0049: Sidebar empty state", () => {
  it("shows no projects message", async () => {
    mockFetchProjects.mockResolvedValue([]);
    renderSidebar();

    await waitFor(() => {
      expect(screen.getByText(/no projects/i)).toBeInTheDocument();
    });
  });

  it("has link to settings", async () => {
    mockFetchProjects.mockResolvedValue([]);
    renderSidebar();

    await waitFor(() => {
      const link = screen.getByText(/add a project/i);
      expect(link).toBeInTheDocument();
      expect(link.closest("a")).toHaveAttribute("href", "/settings");
    });
  });
});

// TC0050: Sync status indicators show correct colours
describe("TC0050: Sync status indicators", () => {
  it("renders correct status colour classes", async () => {
    mockFetchProjects.mockResolvedValue(mixedStatusProjects);
    renderSidebar();

    await waitFor(() => {
      expect(screen.getByText("Synced Project")).toBeInTheDocument();
    });

    const synced = screen.getByTestId("status-proj-synced");
    const syncing = screen.getByTestId("status-proj-syncing");
    const never = screen.getByTestId("status-proj-never");
    const error = screen.getByTestId("status-proj-error");

    expect(synced.className).toContain("bg-status-done");
    expect(syncing.className).toContain("bg-status-progress");
    expect(never.className).toContain("bg-status-draft");
    expect(error.className).toContain("bg-status-blocked");
  });
});

// TC0051: Clicking project navigates to document list
describe("TC0051: Project navigation links", () => {
  it("links to correct document path", async () => {
    mockFetchProjects.mockResolvedValue(threeProjects);
    renderSidebar();

    await waitFor(() => {
      expect(screen.getByText("HomelabCmd")).toBeInTheDocument();
    });

    const link = screen.getByText("HomelabCmd").closest("a");
    expect(link).toHaveAttribute("href", "/projects/homelabcmd");
  });
});

// TC0052: Active project is highlighted
describe("TC0052: Active project highlighted", () => {
  it("applies active styling to current project", async () => {
    mockFetchProjects.mockResolvedValue(threeProjects);
    renderSidebar("/projects/homelabcmd");

    await waitFor(() => {
      expect(screen.getByText("HomelabCmd")).toBeInTheDocument();
    });

    const activeLink = screen.getByText("HomelabCmd").closest("a");
    expect(activeLink?.className).toContain("text-accent");

    const inactiveLink = screen.getByText("SDLCLens").closest("a");
    expect(inactiveLink?.className).not.toContain("text-accent");
  });
});

// TC0053: Settings link navigates to /settings
describe("TC0053: Settings link", () => {
  it("has settings link pointing to /settings", async () => {
    mockFetchProjects.mockResolvedValue(threeProjects);
    renderSidebar();

    await waitFor(() => {
      expect(screen.getByText("HomelabCmd")).toBeInTheDocument();
    });

    // The Settings link in the footer
    const settingsLinks = screen.getAllByText("Settings");
    const footerLink = settingsLinks.find(
      (el) => el.closest("[class*='border-t']") !== null,
    );
    expect(footerLink?.closest("a")).toHaveAttribute("href", "/settings");
  });
});

// TC0054: Application title displays at top of sidebar
describe("TC0054: Application title", () => {
  it("shows Studio Lens title", async () => {
    mockFetchProjects.mockResolvedValue([]);
    renderSidebar();

    expect(screen.getByText("Studio Lens")).toBeInTheDocument();
  });
});

// TC0055: Sidebar handles API error gracefully
describe("TC0055: API error handling", () => {
  it("shows error message on fetch failure", async () => {
    mockFetchProjects.mockRejectedValue(new Error("Network error"));
    renderSidebar();

    await waitFor(() => {
      expect(screen.getByText(/failed to load projects/i)).toBeInTheDocument();
    });
  });

  it("has retry button", async () => {
    mockFetchProjects.mockRejectedValue(new Error("Network error"));
    renderSidebar();

    await waitFor(() => {
      expect(screen.getByText(/retry/i)).toBeInTheDocument();
    });
  });

  it("retries on button click", async () => {
    mockFetchProjects.mockRejectedValueOnce(new Error("Network error"));
    mockFetchProjects.mockResolvedValueOnce(threeProjects);
    renderSidebar();

    await waitFor(() => {
      expect(screen.getByText(/retry/i)).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText(/retry/i));

    await waitFor(() => {
      expect(screen.getByText("HomelabCmd")).toBeInTheDocument();
    });
    expect(mockFetchProjects).toHaveBeenCalledTimes(2);
  });
});
