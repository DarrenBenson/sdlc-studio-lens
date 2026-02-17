/**
 * Settings page component tests.
 * Test cases: TC0056-TC0068 from TS0004.
 */
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Project } from "../types/index.ts";
import { Settings } from "./Settings.tsx";

vi.mock("../api/client.ts", () => ({
  fetchProjects: vi.fn(),
  fetchProject: vi.fn(),
  createProject: vi.fn(),
  updateProject: vi.fn(),
  deleteProject: vi.fn(),
  triggerSync: vi.fn(),
}));

const {
  fetchProjects,
  createProject,
  updateProject,
  deleteProject,
  triggerSync,
} = await import("../api/client.ts");

const mockFetchProjects = vi.mocked(fetchProjects);
const mockCreateProject = vi.mocked(createProject);
const mockUpdateProject = vi.mocked(updateProject);
const mockDeleteProject = vi.mocked(deleteProject);
const mockTriggerSync = vi.mocked(triggerSync);

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
    sync_status: "never_synced",
    sync_error: null,
    last_synced_at: null,
    document_count: 0,
    created_at: "2026-02-17T09:30:00Z",
  },
  {
    slug: "personalblog",
    name: "PersonalBlog",
    sdlc_path: "/data/projects/PersonalBlog/sdlc-studio",
    sync_status: "error",
    sync_error: "Path not found",
    last_synced_at: null,
    document_count: 0,
    created_at: "2026-02-17T10:00:00Z",
  },
];

const newProjectResponse: Project = {
  slug: "homelabcmd",
  name: "HomelabCmd",
  sdlc_path: "/data/projects/HomelabCmd/sdlc-studio",
  sync_status: "never_synced",
  sync_error: null,
  last_synced_at: null,
  document_count: 0,
  created_at: "2026-02-17T11:00:00Z",
};

function renderSettings() {
  return render(
    <MemoryRouter initialEntries={["/settings"]}>
      <Settings />
    </MemoryRouter>,
  );
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// TC0056: Settings page renders add project form
describe("TC0056: Settings page renders add form", () => {
  it("displays name and path inputs and submit button", async () => {
    mockFetchProjects.mockResolvedValue([]);
    renderSettings();

    expect(screen.getByPlaceholderText("Project Name")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("SDLC Path")).toBeInTheDocument();
    expect(screen.getByText("Add Project")).toBeInTheDocument();
  });
});

// TC0057: Add project form submits successfully
describe("TC0057: Add project form submits", () => {
  it("creates project and shows it in list", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockCreateProject.mockResolvedValue(newProjectResponse);
    const user = userEvent.setup();
    renderSettings();

    await user.type(screen.getByPlaceholderText("Project Name"), "HomelabCmd");
    await user.type(
      screen.getByPlaceholderText("SDLC Path"),
      "/data/projects/HomelabCmd/sdlc-studio",
    );
    await user.click(screen.getByText("Add Project"));

    await waitFor(() => {
      expect(mockCreateProject).toHaveBeenCalledWith({
        name: "HomelabCmd",
        sdlc_path: "/data/projects/HomelabCmd/sdlc-studio",
      });
    });

    await waitFor(() => {
      expect(screen.getByText("HomelabCmd")).toBeInTheDocument();
    });
  });

  it("clears form fields after successful submit", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockCreateProject.mockResolvedValue(newProjectResponse);
    const user = userEvent.setup();
    renderSettings();

    await user.type(screen.getByPlaceholderText("Project Name"), "HomelabCmd");
    await user.type(
      screen.getByPlaceholderText("SDLC Path"),
      "/data/projects/HomelabCmd/sdlc-studio",
    );
    await user.click(screen.getByText("Add Project"));

    await waitFor(() => {
      expect(screen.getByPlaceholderText("Project Name")).toHaveValue("");
    });
  });
});

// TC0058: Add project shows server error for invalid path
describe("TC0058: Add project invalid path error", () => {
  it("displays error message", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockCreateProject.mockRejectedValue(
      new Error("Project sdlc-studio path does not exist on filesystem"),
    );
    const user = userEvent.setup();
    renderSettings();

    await user.type(screen.getByPlaceholderText("Project Name"), "Test");
    await user.type(screen.getByPlaceholderText("SDLC Path"), "/bad/path");
    await user.click(screen.getByText("Add Project"));

    await waitFor(() => {
      expect(screen.getByTestId("form-error")).toHaveTextContent(/path/i);
    });
  });
});

// TC0059: Add project shows server error for duplicate slug
describe("TC0059: Add project duplicate slug error", () => {
  it("displays already exists error", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockCreateProject.mockRejectedValue(
      new Error("Project slug already exists"),
    );
    const user = userEvent.setup();
    renderSettings();

    await user.type(screen.getByPlaceholderText("Project Name"), "Test");
    await user.type(screen.getByPlaceholderText("SDLC Path"), "/some/path");
    await user.click(screen.getByText("Add Project"));

    await waitFor(() => {
      expect(screen.getByTestId("form-error")).toHaveTextContent(
        /already exists/i,
      );
    });
  });
});

// TC0060: Project list displays all registered projects
describe("TC0060: Project list displays all projects", () => {
  it("renders all project cards", async () => {
    mockFetchProjects.mockResolvedValue(threeProjects);
    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("HomelabCmd")).toBeInTheDocument();
    });
    expect(screen.getByText("SDLCLens")).toBeInTheDocument();
    expect(screen.getByText("PersonalBlog")).toBeInTheDocument();
  });

  it("shows document count on cards", async () => {
    mockFetchProjects.mockResolvedValue(threeProjects);
    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("152 documents")).toBeInTheDocument();
    });
  });
});

// TC0061: Empty state shown when no projects
describe("TC0061: Empty state", () => {
  it("shows no projects message", async () => {
    mockFetchProjects.mockResolvedValue([]);
    renderSettings();

    await waitFor(() => {
      expect(screen.getByText(/no projects registered/i)).toBeInTheDocument();
    });
  });
});

// TC0062: Edit button opens pre-populated form
describe("TC0062: Edit opens pre-populated form", () => {
  it("populates form with current values", async () => {
    mockFetchProjects.mockResolvedValue(threeProjects);
    const user = userEvent.setup();
    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("HomelabCmd")).toBeInTheDocument();
    });

    const editButtons = screen.getAllByText("Edit");
    await user.click(editButtons[0]);

    expect(screen.getByPlaceholderText("Project Name")).toHaveValue(
      "HomelabCmd",
    );
    expect(screen.getByPlaceholderText("SDLC Path")).toHaveValue(
      "/data/projects/HomelabCmd/sdlc-studio",
    );
    expect(screen.getByText("Save")).toBeInTheDocument();
  });
});

// TC0063: Edit saves changes and updates list
describe("TC0063: Edit saves changes", () => {
  it("calls updateProject and updates list", async () => {
    mockFetchProjects.mockResolvedValue(threeProjects);
    const updated = { ...threeProjects[0], name: "HomelabCmd v2" };
    mockUpdateProject.mockResolvedValue(updated);
    const user = userEvent.setup();
    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("HomelabCmd")).toBeInTheDocument();
    });

    const editButtons = screen.getAllByText("Edit");
    await user.click(editButtons[0]);

    const nameInput = screen.getByPlaceholderText("Project Name");
    await user.clear(nameInput);
    await user.type(nameInput, "HomelabCmd v2");
    await user.click(screen.getByText("Save"));

    await waitFor(() => {
      expect(mockUpdateProject).toHaveBeenCalledWith("homelabcmd", {
        name: "HomelabCmd v2",
      });
    });

    await waitFor(() => {
      expect(screen.getByText("HomelabCmd v2")).toBeInTheDocument();
    });
  });
});

// TC0064: Delete button shows confirmation dialog
describe("TC0064: Delete shows confirmation dialog", () => {
  it("opens confirm dialog with project name", async () => {
    mockFetchProjects.mockResolvedValue(threeProjects);
    const user = userEvent.setup();
    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("HomelabCmd")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByText("Delete");
    await user.click(deleteButtons[0]);

    const dialog = screen.getByTestId("confirm-dialog");
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveTextContent(/HomelabCmd/);
    expect(screen.getByText("Confirm")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });
});

// TC0065: Delete confirmation removes project from list
describe("TC0065: Delete confirmation removes project", () => {
  it("removes project on confirm", async () => {
    mockFetchProjects.mockResolvedValue(threeProjects);
    mockDeleteProject.mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("HomelabCmd")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByText("Delete");
    await user.click(deleteButtons[0]);
    await user.click(screen.getByText("Confirm"));

    await waitFor(() => {
      expect(mockDeleteProject).toHaveBeenCalledWith("homelabcmd");
    });

    await waitFor(() => {
      expect(
        screen.queryByTestId("project-card-homelabcmd"),
      ).not.toBeInTheDocument();
    });
  });
});

// TC0066: Delete cancel keeps project in list
describe("TC0066: Delete cancel keeps project", () => {
  it("keeps project on cancel", async () => {
    mockFetchProjects.mockResolvedValue(threeProjects);
    const user = userEvent.setup();
    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("HomelabCmd")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByText("Delete");
    await user.click(deleteButtons[0]);
    await user.click(screen.getByText("Cancel"));

    expect(mockDeleteProject).not.toHaveBeenCalled();
    expect(screen.getByText("HomelabCmd")).toBeInTheDocument();
  });
});

// TC0067: Sync button triggers sync and shows syncing state
describe("TC0067: Sync button triggers sync", () => {
  it("calls triggerSync and shows syncing state", async () => {
    mockFetchProjects.mockResolvedValue(threeProjects);
    mockTriggerSync.mockResolvedValue({
      slug: "homelabcmd",
      sync_status: "syncing",
      message: "Sync started",
    });
    const user = userEvent.setup();
    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("HomelabCmd")).toBeInTheDocument();
    });

    const syncButtons = screen.getAllByText("Sync Now");
    await user.click(syncButtons[0]);

    await waitFor(() => {
      expect(mockTriggerSync).toHaveBeenCalledWith("homelabcmd");
    });

    // Card should show syncing state
    await waitFor(() => {
      expect(
        screen.getByTestId("project-card-homelabcmd"),
      ).toHaveTextContent(/syncing/i);
    });
  });
});

// TC0068: Sync completion updates status indicator
describe("TC0068: Sync completion updates status", () => {
  it("sync button disabled while syncing", async () => {
    const syncingProjects = threeProjects.map((p) =>
      p.slug === "homelabcmd"
        ? { ...p, sync_status: "syncing" as const }
        : p,
    );
    mockFetchProjects.mockResolvedValue(syncingProjects);
    renderSettings();

    await waitFor(() => {
      expect(screen.getByText("HomelabCmd")).toBeInTheDocument();
    });

    // The first card should have a disabled "Syncing..." button
    const card = screen.getByTestId("project-card-homelabcmd");
    const syncButton = card.querySelector("button");
    expect(syncButton).toHaveTextContent("Syncing...");
    expect(syncButton).toBeDisabled();
  });
});
