/**
 * ProjectForm component tests.
 * Test cases: TC0331-TC0339 from TS0032.
 */
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { checkRepoHasSdlcStudio, fetchGitHubRepos } from "../api/client.ts";
import type { GitHubConnection, GitHubRepoItem } from "../types/index.ts";
import { ProjectForm } from "./ProjectForm.tsx";

vi.mock("../api/client.ts", () => ({
  fetchGitHubRepos: vi.fn(),
  checkRepoHasSdlcStudio: vi.fn(),
}));

const mockFetchRepos = vi.mocked(fetchGitHubRepos);
const mockCheckSdlc = vi.mocked(checkRepoHasSdlcStudio);

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const mockOnSubmit = vi.fn().mockResolvedValue(undefined);

const REPOS: GitHubRepoItem[] = [
  {
    full_name: "alice/app",
    owner: "alice",
    name: "app",
    private: false,
    default_branch: "trunk",
    description: null,
  },
  {
    full_name: "acme/service",
    owner: "acme",
    name: "service",
    private: true,
    default_branch: "main",
    description: "svc",
  },
];

// TC0331: ProjectForm renders source type toggle
describe("TC0331: Source type toggle renders", () => {
  it("shows Local and GitHub buttons", () => {
    render(
      <ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />,
    );

    const toggle = screen.getByTestId("source-type-toggle");
    expect(toggle).toBeInTheDocument();
    expect(screen.getByText("Local")).toBeInTheDocument();
    expect(screen.getByText("GitHub")).toBeInTheDocument();
  });
});

// TC0332: ProjectForm shows SDLC Path field when local selected
describe("TC0332: Local mode shows SDLC Path", () => {
  it("shows SDLC Path input in local mode", () => {
    render(
      <ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />,
    );

    expect(screen.getByPlaceholderText("SDLC Path")).toBeInTheDocument();
    expect(screen.queryByTestId("repo-url-input")).not.toBeInTheDocument();
  });
});

// TC0333: ProjectForm shows GitHub fields when github selected
describe("TC0333: GitHub mode shows repo fields", () => {
  it("shows GitHub fields after clicking GitHub button", async () => {
    const user = userEvent.setup();
    render(
      <ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />,
    );

    await user.click(screen.getByText("GitHub"));

    expect(screen.getByTestId("repo-url-input")).toBeInTheDocument();
    expect(screen.getByTestId("repo-branch-input")).toBeInTheDocument();
    expect(screen.getByTestId("repo-path-input")).toBeInTheDocument();
    expect(screen.getByTestId("access-token-input")).toBeInTheDocument();
  });

  it("shows default values for branch and path", async () => {
    const user = userEvent.setup();
    render(
      <ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />,
    );

    await user.click(screen.getByText("GitHub"));

    expect(screen.getByTestId("repo-branch-input")).toHaveValue("main");
    expect(screen.getByTestId("repo-path-input")).toHaveValue("sdlc-studio");
  });
});

// TC0334: ProjectForm hides SDLC Path field when github selected
describe("TC0334: GitHub mode hides SDLC Path", () => {
  it("hides SDLC Path after switching to GitHub", async () => {
    const user = userEvent.setup();
    render(
      <ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />,
    );

    expect(screen.getByPlaceholderText("SDLC Path")).toBeInTheDocument();

    await user.click(screen.getByText("GitHub"));

    expect(screen.queryByPlaceholderText("SDLC Path")).not.toBeInTheDocument();
  });
});

// TC0335: ProjectForm submits with source_type=local and sdlc_path
describe("TC0335: Local form submission", () => {
  it("submits correct payload for local source", async () => {
    const user = userEvent.setup();
    render(
      <ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />,
    );

    await user.type(screen.getByPlaceholderText("Project Name"), "MyProject");
    await user.type(screen.getByPlaceholderText("SDLC Path"), "/data/test");
    await user.click(screen.getByText("Add Project"));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "MyProject",
          source_type: "local",
          sdlc_path: "/data/test",
        }),
      );
    });
  });
});

// TC0336: ProjectForm submits with source_type=github and repo fields
describe("TC0336: GitHub form submission", () => {
  it("submits correct payload for GitHub source", async () => {
    const user = userEvent.setup();
    render(
      <ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />,
    );

    await user.type(screen.getByPlaceholderText("Project Name"), "GHProject");
    await user.click(screen.getByText("GitHub"));
    await user.type(
      screen.getByTestId("repo-url-input"),
      "https://github.com/owner/repo",
    );
    await user.click(screen.getByText("Add Project"));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "GHProject",
          source_type: "github",
          repo_url: "https://github.com/owner/repo",
        }),
      );
    });
  });
});

// TC0337: ProjectForm defaults to local source type
describe("TC0337: Defaults to local", () => {
  it("shows SDLC Path field by default (local mode)", () => {
    render(
      <ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />,
    );

    expect(screen.getByPlaceholderText("SDLC Path")).toBeInTheDocument();
    expect(screen.queryByTestId("repo-url-input")).not.toBeInTheDocument();
  });
});

// TC0338: ProjectForm access token field is type=password
describe("TC0338: Access token is password type", () => {
  it("renders access token input with type=password", async () => {
    const user = userEvent.setup();
    render(
      <ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />,
    );

    await user.click(screen.getByText("GitHub"));

    const tokenInput = screen.getByTestId("access-token-input");
    expect(tokenInput).toHaveAttribute("type", "password");
  });
});

// CR-01KXAS75: Repo selector - browse the repos a token can see
describe("CR-01KXAS75: GitHub repo selector", () => {
  it("browsing lists the repositories the token can see", async () => {
    mockFetchRepos.mockResolvedValue(REPOS);
    mockCheckSdlc.mockResolvedValue(false);
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    await user.click(screen.getByText("GitHub"));
    await user.type(screen.getByTestId("access-token-input"), "ghp_token");
    await user.click(screen.getByTestId("browse-repos-button"));

    expect(await screen.findByText("alice/app")).toBeInTheDocument();
    expect(screen.getByText("acme/service")).toBeInTheDocument();
    expect(mockFetchRepos).toHaveBeenCalledWith("ghp_token", undefined);
  });

  it("shows an sdlc-studio badge only for a flagged repo", async () => {
    mockFetchRepos.mockResolvedValue(REPOS);
    mockCheckSdlc.mockImplementation((_owner, repo) =>
      Promise.resolve(repo === "app"),
    );
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    await user.click(screen.getByText("GitHub"));
    await user.type(screen.getByTestId("access-token-input"), "ghp_token");
    await user.click(screen.getByTestId("browse-repos-button"));

    expect(
      await screen.findByTestId("sdlc-badge-alice/app"),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("sdlc-badge-acme/service"),
    ).not.toBeInTheDocument();
  });

  it("selecting a repo fills repo_url and repo_branch", async () => {
    mockFetchRepos.mockResolvedValue(REPOS);
    mockCheckSdlc.mockResolvedValue(false);
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    await user.click(screen.getByText("GitHub"));
    await user.type(screen.getByTestId("access-token-input"), "ghp_token");
    await user.click(screen.getByTestId("browse-repos-button"));

    await user.click(await screen.findByTestId("repo-row-alice/app"));

    expect(screen.getByTestId("repo-url-input")).toHaveValue(
      "https://github.com/alice/app",
    );
    expect(screen.getByTestId("repo-branch-input")).toHaveValue("trunk");
  });

  it("keeps manual repo URL entry available", async () => {
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    await user.click(screen.getByText("GitHub"));
    // The manual URL field is present without browsing.
    expect(screen.getByTestId("repo-url-input")).toBeInTheDocument();
    expect(screen.getByTestId("browse-repos-button")).toBeInTheDocument();
  });
});

// CR-01KXAZX9: Stored connections - browse and submit without pasting a token
const CONNECTIONS: GitHubConnection[] = [
  {
    id: 1,
    label: "personal",
    login: "alice",
    masked_token: "****cdef",
    created_at: "2026-07-10T09:00:00Z",
    last_validated_at: "2026-07-11T09:00:00Z",
  },
  {
    id: 2,
    label: "work",
    login: "acme-bot",
    masked_token: "****9876",
    created_at: "2026-07-10T10:00:00Z",
    last_validated_at: null,
  },
];

describe("CR-01KXAZX9: Saved connection picker", () => {
  it("lists the saved connections in the picker", async () => {
    const user = userEvent.setup();
    render(
      <ProjectForm
        mode="add"
        connections={CONNECTIONS}
        onSubmit={mockOnSubmit}
        error={null}
      />,
    );

    await user.click(screen.getByText("GitHub"));

    const select = screen.getByTestId("connection-select");
    expect(select).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /personal \(alice\)/ })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /work \(acme-bot\)/ })).toBeInTheDocument();
  });

  it("browses repositories with a saved connection and no token typed", async () => {
    mockFetchRepos.mockResolvedValue(REPOS);
    mockCheckSdlc.mockResolvedValue(false);
    const user = userEvent.setup();
    render(
      <ProjectForm
        mode="add"
        connections={CONNECTIONS}
        onSubmit={mockOnSubmit}
        error={null}
      />,
    );

    await user.click(screen.getByText("GitHub"));
    await user.selectOptions(screen.getByTestId("connection-select"), "1");
    await user.click(screen.getByTestId("browse-repos-button"));

    expect(await screen.findByText("alice/app")).toBeInTheDocument();
    expect(mockFetchRepos).toHaveBeenCalledWith({ connectionId: 1 }, undefined);
    // No raw token field is on screen once a saved connection is chosen.
    expect(screen.queryByTestId("access-token-input")).not.toBeInTheDocument();
  });

  it("still shows the sdlc-studio badge when browsing via a connection", async () => {
    mockFetchRepos.mockResolvedValue(REPOS);
    mockCheckSdlc.mockImplementation((_owner, repo) =>
      Promise.resolve(repo === "app"),
    );
    const user = userEvent.setup();
    render(
      <ProjectForm
        mode="add"
        connections={CONNECTIONS}
        onSubmit={mockOnSubmit}
        error={null}
      />,
    );

    await user.click(screen.getByText("GitHub"));
    await user.selectOptions(screen.getByTestId("connection-select"), "1");
    await user.click(screen.getByTestId("browse-repos-button"));

    expect(
      await screen.findByTestId("sdlc-badge-alice/app"),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("sdlc-badge-acme/service"),
    ).not.toBeInTheDocument();
    // One flag check per repo, no fan-out on re-render.
    expect(mockCheckSdlc).toHaveBeenCalledTimes(2);
  });

  it("selects a repo and submits connection_id with the project", async () => {
    mockFetchRepos.mockResolvedValue(REPOS);
    mockCheckSdlc.mockResolvedValue(false);
    const user = userEvent.setup();
    render(
      <ProjectForm
        mode="add"
        connections={CONNECTIONS}
        onSubmit={mockOnSubmit}
        error={null}
      />,
    );

    await user.type(screen.getByPlaceholderText("Project Name"), "GHProject");
    await user.click(screen.getByText("GitHub"));
    await user.selectOptions(screen.getByTestId("connection-select"), "1");
    await user.click(screen.getByTestId("browse-repos-button"));
    await user.click(await screen.findByTestId("repo-row-alice/app"));

    expect(screen.getByTestId("repo-url-input")).toHaveValue(
      "https://github.com/alice/app",
    );
    expect(screen.getByTestId("repo-branch-input")).toHaveValue("trunk");

    await user.click(screen.getByText("Add Project"));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "GHProject",
          source_type: "github",
          repo_url: "https://github.com/alice/app",
          repo_branch: "trunk",
          connection_id: 1,
        }),
      );
    });
    // The raw token field is never used, so no token is submitted.
    expect(mockOnSubmit.mock.calls[0][0]).not.toHaveProperty("access_token");
  });

  it("keeps the manual token fallback working when no connection is chosen", async () => {
    mockFetchRepos.mockResolvedValue(REPOS);
    mockCheckSdlc.mockResolvedValue(false);
    const user = userEvent.setup();
    render(
      <ProjectForm
        mode="add"
        connections={CONNECTIONS}
        onSubmit={mockOnSubmit}
        error={null}
      />,
    );

    await user.type(screen.getByPlaceholderText("Project Name"), "OneOff");
    await user.click(screen.getByText("GitHub"));
    await user.type(screen.getByTestId("access-token-input"), "ghp_token");
    await user.click(screen.getByTestId("browse-repos-button"));

    expect(await screen.findByText("alice/app")).toBeInTheDocument();
    expect(mockFetchRepos).toHaveBeenCalledWith("ghp_token", undefined);

    await user.click(await screen.findByTestId("repo-row-alice/app"));
    await user.click(screen.getByText("Add Project"));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          source_type: "github",
          access_token: "ghp_token",
        }),
      );
    });
    expect(mockOnSubmit.mock.calls[0][0]).not.toHaveProperty("connection_id");
  });
});

// TC0339: ProjectForm edit mode pre-fills source type and fields
describe("TC0339: Edit mode pre-fills GitHub fields", () => {
  it("pre-fills GitHub fields in edit mode", () => {
    render(
      <ProjectForm
        mode="edit"
        initialName="My GH Project"
        initialSourceType="github"
        initialRepoUrl="https://github.com/owner/repo"
        initialRepoBranch="develop"
        initialRepoPath="docs"
        onSubmit={mockOnSubmit}
        onCancel={() => {}}
        error={null}
      />,
    );

    expect(screen.getByPlaceholderText("Project Name")).toHaveValue(
      "My GH Project",
    );
    expect(screen.getByTestId("repo-url-input")).toHaveValue(
      "https://github.com/owner/repo",
    );
    expect(screen.getByTestId("repo-branch-input")).toHaveValue("develop");
    expect(screen.getByTestId("repo-path-input")).toHaveValue("docs");
    expect(screen.queryByPlaceholderText("SDLC Path")).not.toBeInTheDocument();
  });
});
