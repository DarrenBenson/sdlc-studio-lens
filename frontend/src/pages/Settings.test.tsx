/**
 * Settings page component tests.
 * Test cases: TC0056-TC0068 from TS0004.
 */
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { GitHubConnection, Project } from "../types/index.ts";
import { Settings } from "./Settings.tsx";

vi.mock("../api/client.ts", () => ({
  fetchProjects: vi.fn(),
  fetchProject: vi.fn(),
  createProject: vi.fn(),
  updateProject: vi.fn(),
  deleteProject: vi.fn(),
  triggerSync: vi.fn(),
  fetchConnections: vi.fn(),
  createConnection: vi.fn(),
  deleteConnection: vi.fn(),
  validateConnection: vi.fn(),
  rotateConnection: vi.fn(),
  fetchAllConnectionRepos: vi.fn(),
  fetchGitHubRepos: vi.fn(),
  checkRepoHasSdlcStudio: vi.fn(),
}));

const {
  fetchProjects,
  createProject,
  updateProject,
  deleteProject,
  triggerSync,
  fetchConnections,
  createConnection,
  deleteConnection,
  validateConnection,
  rotateConnection,
  fetchAllConnectionRepos,
  checkRepoHasSdlcStudio,
} = await import("../api/client.ts");

const mockFetchProjects = vi.mocked(fetchProjects);
const mockCreateProject = vi.mocked(createProject);
const mockUpdateProject = vi.mocked(updateProject);
const mockDeleteProject = vi.mocked(deleteProject);
const mockTriggerSync = vi.mocked(triggerSync);
const mockFetchConnections = vi.mocked(fetchConnections);
const mockCreateConnection = vi.mocked(createConnection);
const mockDeleteConnection = vi.mocked(deleteConnection);
const mockValidateConnection = vi.mocked(validateConnection);
const mockRotateConnection = vi.mocked(rotateConnection);
const mockFetchAllRepos = vi.mocked(fetchAllConnectionRepos);
const mockCheckSdlc = vi.mocked(checkRepoHasSdlcStudio);

const savedConnections: GitHubConnection[] = [
  {
    id: 1,
    label: "personal",
    login: "alice",
    masked_token: "****cdef",
    created_at: "2026-07-10T09:00:00Z",
    last_validated_at: "2026-07-11T09:00:00Z",
  },
];

const threeProjects: Project[] = [
  {
    slug: "homelabcmd",
    name: "HomelabCmd",
    sdlc_path: "/data/projects/HomelabCmd/sdlc-studio",
    source_type: "local",
    repo_url: null,
    repo_branch: "main",
    repo_path: "sdlc-studio",
    masked_token: null,
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
    source_type: "local",
    repo_url: null,
    repo_branch: "main",
    repo_path: "sdlc-studio",
    masked_token: null,
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
    source_type: "local",
    repo_url: null,
    repo_branch: "main",
    repo_path: "sdlc-studio",
    masked_token: null,
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
  source_type: "local",
  repo_url: null,
  repo_branch: "main",
  repo_path: "sdlc-studio",
  masked_token: null,
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

beforeEach(() => {
  // Most tests are about projects; connections default to none.
  mockFetchConnections.mockResolvedValue([]);
});

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
        source_type: "local",
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

// CR-01KXAZX9: Stored GitHub connections
describe("CR-01KXAZX9: GitHub connections section", () => {
  it("lists the saved connections with login, masked token and last validated", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockFetchConnections.mockResolvedValue(savedConnections);
    renderSettings();

    const row = await screen.findByTestId("connection-row-1");
    expect(row).toHaveTextContent("personal");
    expect(row).toHaveTextContent("alice");
    expect(row).toHaveTextContent("****cdef");
    expect(row).toHaveTextContent(/validated/i);
  });

  it("shows an empty state when no connections are saved", async () => {
    mockFetchProjects.mockResolvedValue([]);
    renderSettings();

    await waitFor(() => {
      expect(
        screen.getByText(/no github connections/i),
      ).toBeInTheDocument();
    });
  });

  it("adding a connection shows the resolved login", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockCreateConnection.mockResolvedValue({
      id: 7,
      label: "work",
      login: "octocat",
      masked_token: "****beef",
      created_at: "2026-07-12T09:00:00Z",
      last_validated_at: "2026-07-12T09:00:00Z",
    });
    const user = userEvent.setup();
    renderSettings();

    await user.type(screen.getByTestId("connection-label-input"), "work");
    await user.type(
      screen.getByTestId("connection-token-input"),
      "ghp_supersecret123",
    );
    await user.click(screen.getByText("Add connection"));

    await waitFor(() => {
      expect(mockCreateConnection).toHaveBeenCalledWith(
        "work",
        "ghp_supersecret123",
      );
    });

    const row = await screen.findByTestId("connection-row-7");
    expect(row).toHaveTextContent("octocat");
  });

  it("never renders the raw token back into the DOM after a successful add", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockCreateConnection.mockResolvedValue({
      id: 7,
      label: "work",
      login: "octocat",
      masked_token: "****beef",
      created_at: "2026-07-12T09:00:00Z",
      last_validated_at: "2026-07-12T09:00:00Z",
    });
    const user = userEvent.setup();
    renderSettings();

    await user.type(screen.getByTestId("connection-label-input"), "work");
    await user.type(
      screen.getByTestId("connection-token-input"),
      "ghp_supersecret123",
    );
    await user.click(screen.getByText("Add connection"));

    await screen.findByTestId("connection-row-7");

    expect(screen.getByTestId("connection-token-input")).toHaveValue("");
    expect(document.body.innerHTML).not.toContain("ghp_supersecret123");
  });

  it("surfaces an INVALID_TOKEN error inline and adds nothing", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockCreateConnection.mockRejectedValue(
      new Error("GitHub rejected the access token"),
    );
    const user = userEvent.setup();
    renderSettings();

    await user.type(screen.getByTestId("connection-label-input"), "bad");
    await user.type(screen.getByTestId("connection-token-input"), "ghp_bad");
    await user.click(screen.getByText("Add connection"));

    await waitFor(() => {
      expect(screen.getByTestId("connection-error")).toHaveTextContent(
        /rejected the access token/i,
      );
    });
    expect(screen.queryByTestId("connection-row-7")).not.toBeInTheDocument();
    expect(screen.getByText(/no github connections/i)).toBeInTheDocument();
  });

  it("surfaces a LABEL_EXISTS error inline", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockFetchConnections.mockResolvedValue(savedConnections);
    mockCreateConnection.mockRejectedValue(
      new Error("A connection named 'personal' already exists"),
    );
    const user = userEvent.setup();
    renderSettings();

    await screen.findByTestId("connection-row-1");
    await user.type(screen.getByTestId("connection-label-input"), "personal");
    await user.type(screen.getByTestId("connection-token-input"), "ghp_dup");
    await user.click(screen.getByText("Add connection"));

    await waitFor(() => {
      expect(screen.getByTestId("connection-error")).toHaveTextContent(
        /already exists/i,
      );
    });
  });

  it("re-validates a connection and refreshes last validated", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockFetchConnections.mockResolvedValue(savedConnections);
    mockValidateConnection.mockResolvedValue({
      ...savedConnections[0],
      last_validated_at: "2026-07-12T12:00:00Z",
    });
    const user = userEvent.setup();
    renderSettings();

    await screen.findByTestId("connection-row-1");
    await user.click(screen.getByTestId("validate-connection-1"));

    await waitFor(() => {
      expect(mockValidateConnection).toHaveBeenCalledWith(1);
    });
    await waitFor(() => {
      expect(screen.getByTestId("connection-row-1")).toHaveTextContent(
        /12 Jul 2026/,
      );
    });
  });

  it("deletes a connection", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockFetchConnections.mockResolvedValue(savedConnections);
    mockDeleteConnection.mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderSettings();

    await screen.findByTestId("connection-row-1");
    await user.click(screen.getByTestId("delete-connection-1"));

    await waitFor(() => {
      expect(mockDeleteConnection).toHaveBeenCalledWith(1);
    });
    await waitFor(() => {
      expect(screen.queryByTestId("connection-row-1")).not.toBeInTheDocument();
    });
  });

  it("surfaces CONNECTION_IN_USE when deleting a connection still in use", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockFetchConnections.mockResolvedValue(savedConnections);
    mockDeleteConnection.mockRejectedValue(
      new Error("Connection is in use by projects: HomelabCmd, SDLCLens"),
    );
    const user = userEvent.setup();
    renderSettings();

    await screen.findByTestId("connection-row-1");
    await user.click(screen.getByTestId("delete-connection-1"));

    await waitFor(() => {
      expect(screen.getByTestId("connection-error")).toHaveTextContent(
        /in use by projects: HomelabCmd, SDLCLens/,
      );
    });
    // The connection is still listed - the refusal did not remove it.
    expect(screen.getByTestId("connection-row-1")).toBeInTheDocument();
  });

  // Review of CR-01KXAZX9: an expired PAT must be a one-field edit, not a
  // detach-delete-re-add dance across every project that uses the connection.
  it("rotates a connection's token and shows the refreshed masked token", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockFetchConnections.mockResolvedValue(savedConnections);
    mockRotateConnection.mockResolvedValue({
      ...savedConnections[0],
      masked_token: "****9999",
      last_validated_at: "2026-07-12T12:00:00Z",
    });
    const user = userEvent.setup();
    renderSettings();

    await screen.findByTestId("connection-row-1");
    await user.click(screen.getByTestId("rotate-connection-1"));
    await user.type(
      screen.getByTestId("rotate-token-input-1"),
      "ghp_rotated9999",
    );
    await user.click(screen.getByTestId("rotate-submit-1"));

    await waitFor(() => {
      expect(mockRotateConnection).toHaveBeenCalledWith(1, "ghp_rotated9999");
    });
    await waitFor(() => {
      const row = screen.getByTestId("connection-row-1");
      expect(row).toHaveTextContent("****9999");
      expect(row).toHaveTextContent(/12 Jul 2026/);
    });
  });

  it("drops the rotated token from state once it has been exchanged", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockFetchConnections.mockResolvedValue(savedConnections);
    mockRotateConnection.mockResolvedValue({
      ...savedConnections[0],
      masked_token: "****9999",
    });
    const user = userEvent.setup();
    renderSettings();

    await screen.findByTestId("connection-row-1");
    await user.click(screen.getByTestId("rotate-connection-1"));
    await user.type(
      screen.getByTestId("rotate-token-input-1"),
      "ghp_rotated9999",
    );
    await user.click(screen.getByTestId("rotate-submit-1"));

    await waitFor(() => {
      expect(
        screen.queryByTestId("rotate-token-input-1"),
      ).not.toBeInTheDocument();
    });
    expect(document.body.innerHTML).not.toContain("ghp_rotated9999");
  });

  it("surfaces an INVALID_TOKEN rotation failure inline and changes nothing", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockFetchConnections.mockResolvedValue(savedConnections);
    mockRotateConnection.mockRejectedValue(
      new Error("GitHub rejected the access token"),
    );
    const user = userEvent.setup();
    renderSettings();

    await screen.findByTestId("connection-row-1");
    await user.click(screen.getByTestId("rotate-connection-1"));
    await user.type(screen.getByTestId("rotate-token-input-1"), "ghp_bad");
    await user.click(screen.getByTestId("rotate-submit-1"));

    await waitFor(() => {
      expect(screen.getByTestId("connection-error")).toHaveTextContent(
        /rejected the access token/i,
      );
    });
    // The old credential is still the one on show.
    expect(screen.getByTestId("connection-row-1")).toHaveTextContent("****cdef");
  });

  // CR-01KXB377: the card no longer asks which connection to browse with - it
  // browses every stored connection at once and lists the repos it finds.
  it("browses every saved connection from the project form, asking for no credential", async () => {
    mockFetchProjects.mockResolvedValue([]);
    mockFetchConnections.mockResolvedValue(savedConnections);
    mockCheckSdlc.mockResolvedValue(false);
    mockFetchAllRepos.mockResolvedValue({
      repos: [
        {
          full_name: "alice/app",
          owner: "alice",
          name: "app",
          private: false,
          default_branch: "trunk",
          description: null,
          connection_id: 1,
          connection_label: "personal",
        },
      ],
      degraded: [],
    });
    const user = userEvent.setup();
    renderSettings();

    await screen.findByTestId("connection-row-1");
    await user.click(screen.getByText("GitHub"));

    expect(await screen.findByText("alice/app")).toBeInTheDocument();
    expect(mockFetchAllRepos).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId("connection-select")).not.toBeInTheDocument();
    expect(screen.queryByTestId("access-token-input")).not.toBeInTheDocument();
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
