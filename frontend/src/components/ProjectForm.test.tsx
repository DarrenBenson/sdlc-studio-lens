/**
 * ProjectForm component tests.
 * Test cases: TC0331-TC0339 from TS0032, plus CR-01KXB377 (add-project rebuild).
 */
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  checkRepoHasSdlcStudio,
  fetchAllConnectionRepos,
  fetchGitHubRepos,
} from "../api/client.ts";
import type {
  AggregatedRepo,
  GitHubConnection,
  GitHubRepoItem,
} from "../types/index.ts";
import { ProjectForm } from "./ProjectForm.tsx";

vi.mock("../api/client.ts", () => ({
  fetchAllConnectionRepos: vi.fn(),
  fetchGitHubRepos: vi.fn(),
  checkRepoHasSdlcStudio: vi.fn(),
}));

const mockFetchAll = vi.mocked(fetchAllConnectionRepos);
const mockFetchRepos = vi.mocked(fetchGitHubRepos);
const mockCheckSdlc = vi.mocked(checkRepoHasSdlcStudio);

const mockOnSubmit = vi.fn().mockResolvedValue(undefined);

/** Repos as the aggregate endpoint returns them: each carries its connection. */
const AGGREGATED: AggregatedRepo[] = [
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
  {
    full_name: "acme/service",
    owner: "acme",
    name: "service",
    private: true,
    default_branch: "main",
    description: "svc",
    connection_id: 2,
    connection_label: "work",
  },
];

/** Repos as the one-off raw-token browse returns them: no connection. */
const TOKEN_REPOS: GitHubRepoItem[] = [
  {
    full_name: "alice/app",
    owner: "alice",
    name: "app",
    private: false,
    default_branch: "trunk",
    description: null,
  },
];

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

beforeEach(() => {
  // Default: the aggregate browse succeeds with nothing to show, so a test that
  // does not care about repos never trips over an unmocked call.
  mockFetchAll.mockResolvedValue({ repos: [], degraded: [] });
  mockCheckSdlc.mockResolvedValue(false);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// TC0331: ProjectForm renders source type toggle
describe("TC0331: Source type toggle renders", () => {
  it("shows Local and GitHub buttons", () => {
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    const toggle = screen.getByTestId("source-type-toggle");
    expect(toggle).toBeInTheDocument();
    expect(screen.getByText("Local")).toBeInTheDocument();
    expect(screen.getByText("GitHub")).toBeInTheDocument();
  });
});

// TC0332: ProjectForm shows SDLC Path field when local selected
describe("TC0332: Local mode shows SDLC Path", () => {
  it("shows SDLC Path input in local mode", () => {
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    expect(screen.getByPlaceholderText("SDLC Path")).toBeInTheDocument();
    expect(screen.queryByTestId("repo-url-input")).not.toBeInTheDocument();
  });
});

// TC0333: ProjectForm shows the repository picker when github selected
describe("TC0333: GitHub mode shows the repository picker", () => {
  it("shows the repo URL field and the browse action", async () => {
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    await user.click(screen.getByText("GitHub"));

    expect(screen.getByTestId("repo-url-input")).toBeInTheDocument();
    expect(screen.getByTestId("browse-repos-button")).toBeInTheDocument();
  });

  it("asks no credential question in the default path", async () => {
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

    // No "which connection?" select and no token box before browsing.
    expect(screen.queryByTestId("connection-select")).not.toBeInTheDocument();
    expect(screen.queryByTestId("access-token-input")).not.toBeInTheDocument();
  });
});

// TC0334: ProjectForm hides SDLC Path field when github selected
describe("TC0334: GitHub mode hides SDLC Path", () => {
  it("hides SDLC Path after switching to GitHub", async () => {
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    expect(screen.getByPlaceholderText("SDLC Path")).toBeInTheDocument();

    await user.click(screen.getByText("GitHub"));

    expect(screen.queryByPlaceholderText("SDLC Path")).not.toBeInTheDocument();
  });
});

// TC0335: ProjectForm submits with source_type=local and sdlc_path
describe("TC0335: Local form submission", () => {
  it("submits correct payload for local source", async () => {
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

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
    // The local path never touches GitHub.
    expect(mockFetchAll).not.toHaveBeenCalled();
  });
});

// TC0336: ProjectForm submits with source_type=github and repo fields
describe("TC0336: GitHub form submission (manual URL)", () => {
  it("submits correct payload for a hand-typed repo URL", async () => {
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

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
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    expect(screen.getByPlaceholderText("SDLC Path")).toBeInTheDocument();
    expect(screen.queryByTestId("repo-url-input")).not.toBeInTheDocument();
  });
});

// TC0338: ProjectForm access token field is type=password
describe("TC0338: One-off access token is password type", () => {
  it("renders the token input with type=password under its disclosure", async () => {
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    await user.click(screen.getByText("GitHub"));
    await user.click(screen.getByTestId("use-token-toggle"));

    const tokenInput = screen.getByTestId("access-token-input");
    expect(tokenInput).toHaveAttribute("type", "password");
  });
});

// CR-01KXB377: pick a repository - the credential is not a question
describe("CR-01KXB377: Aggregate repository picker", () => {
  it("lists repositories with no credential chosen or typed", async () => {
    mockFetchAll.mockResolvedValue({ repos: AGGREGATED, degraded: [] });
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

    expect(await screen.findByText("alice/app")).toBeInTheDocument();
    expect(screen.getByText("acme/service")).toBeInTheDocument();
    expect(mockFetchAll).toHaveBeenCalledTimes(1);
    // Nothing was selected or typed to get here.
    expect(mockFetchRepos).not.toHaveBeenCalled();
  });

  it("lists a repo from a second connection and names the connection that surfaced it", async () => {
    mockFetchAll.mockResolvedValue({ repos: AGGREGATED, degraded: [] });
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

    expect(await screen.findByText("acme/service")).toBeInTheDocument();
    expect(screen.getByTestId("repo-connection-alice/app")).toHaveTextContent(
      "personal",
    );
    expect(
      screen.getByTestId("repo-connection-acme/service"),
    ).toHaveTextContent("work");
  });

  it("hides the connection label when only one connection is registered", async () => {
    mockFetchAll.mockResolvedValue({ repos: AGGREGATED, degraded: [] });
    const user = userEvent.setup();
    render(
      <ProjectForm
        mode="add"
        connections={[CONNECTIONS[0]]}
        onSubmit={mockOnSubmit}
        error={null}
      />,
    );

    await user.click(screen.getByText("GitHub"));

    expect(await screen.findByText("alice/app")).toBeInTheDocument();
    expect(
      screen.queryByTestId("repo-connection-alice/app"),
    ).not.toBeInTheDocument();
  });

  it("selecting a repo derives name, URL and branch, and submits connection_id with nothing typed", async () => {
    mockFetchAll.mockResolvedValue({ repos: AGGREGATED, degraded: [] });
    const user = userEvent.setup();
    render(
      <ProjectForm
        mode="add"
        connections={CONNECTIONS}
        onSubmit={mockOnSubmit}
        error={null}
      />,
    );

    // Open the card, click a repo, submit. Nothing is typed at any point.
    await user.click(screen.getByText("GitHub"));
    await user.click(await screen.findByTestId("repo-row-acme/service"));

    expect(screen.getByPlaceholderText("Project Name")).toHaveValue("service");
    expect(screen.getByTestId("repo-url-input")).toHaveValue(
      "https://github.com/acme/service",
    );

    await user.click(screen.getByText("Add Project"));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "service",
          source_type: "github",
          repo_url: "https://github.com/acme/service",
          repo_branch: "main",
          repo_path: "sdlc-studio",
          connection_id: 2,
        }),
      );
    });
    expect(mockOnSubmit.mock.calls[0][0]).not.toHaveProperty("access_token");
  });

  it("carries the repo's own default branch into the payload", async () => {
    mockFetchAll.mockResolvedValue({ repos: AGGREGATED, degraded: [] });
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
    await user.click(await screen.findByTestId("repo-row-alice/app"));
    await user.click(screen.getByText("Add Project"));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "app",
          repo_branch: "trunk",
          connection_id: 1,
        }),
      );
    });
  });

  it("filters the repository list", async () => {
    mockFetchAll.mockResolvedValue({ repos: AGGREGATED, degraded: [] });
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
    expect(await screen.findByText("alice/app")).toBeInTheDocument();

    await user.type(screen.getByTestId("repo-filter-input"), "service");

    expect(screen.queryByText("alice/app")).not.toBeInTheDocument();
    expect(screen.getByText("acme/service")).toBeInTheDocument();
  });
});

describe("CR-01KXB377: Advanced disclosure", () => {
  it("hides branch and sdlc path by default", async () => {
    mockFetchAll.mockResolvedValue({ repos: AGGREGATED, degraded: [] });
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    await user.click(screen.getByText("GitHub"));

    expect(screen.queryByTestId("repo-branch-input")).not.toBeInTheDocument();
    expect(screen.queryByTestId("repo-path-input")).not.toBeInTheDocument();
    expect(screen.getByTestId("advanced-toggle")).toBeInTheDocument();
  });

  it("pre-fills the derived branch and path under Advanced", async () => {
    mockFetchAll.mockResolvedValue({ repos: AGGREGATED, degraded: [] });
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    await user.click(screen.getByText("GitHub"));
    await user.click(await screen.findByTestId("repo-row-alice/app"));
    await user.click(screen.getByTestId("advanced-toggle"));

    expect(screen.getByTestId("repo-branch-input")).toHaveValue("trunk");
    expect(screen.getByTestId("repo-path-input")).toHaveValue("sdlc-studio");
  });

  it("submits an overridden branch and sdlc path", async () => {
    mockFetchAll.mockResolvedValue({ repos: AGGREGATED, degraded: [] });
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    await user.click(screen.getByText("GitHub"));
    await user.click(await screen.findByTestId("repo-row-alice/app"));
    await user.click(screen.getByTestId("advanced-toggle"));

    await user.clear(screen.getByTestId("repo-branch-input"));
    await user.type(screen.getByTestId("repo-branch-input"), "develop");
    await user.clear(screen.getByTestId("repo-path-input"));
    await user.type(screen.getByTestId("repo-path-input"), "docs/sdlc");

    await user.click(screen.getByText("Add Project"));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          repo_branch: "develop",
          repo_path: "docs/sdlc",
          connection_id: 1,
        }),
      );
    });
  });
});

describe("CR-01KXB377: Degraded connections", () => {
  it("renders a non-fatal notice and still lists the repos that were reachable", async () => {
    mockFetchAll.mockResolvedValue({
      repos: [AGGREGATED[0]],
      degraded: [
        { connection_id: 2, label: "work", reason: "Rate limit exceeded" },
      ],
    });
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

    const notice = await screen.findByTestId("degraded-notice");
    expect(notice).toHaveTextContent("work");
    expect(notice).toHaveTextContent("Rate limit exceeded");
    // The list still renders - a failing connection is not a failed browse.
    expect(screen.getByText("alice/app")).toBeInTheDocument();
    expect(screen.queryByTestId("browse-error")).not.toBeInTheDocument();
  });
});

describe("CR-01KXB377: sdlc-studio badge", () => {
  it("checks each repo once, with the repo's own connection", async () => {
    mockFetchAll.mockResolvedValue({ repos: AGGREGATED, degraded: [] });
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

    expect(
      await screen.findByTestId("sdlc-badge-alice/app"),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("sdlc-badge-acme/service"),
    ).not.toBeInTheDocument();
    // One check per repo, no fan-out on re-render.
    expect(mockCheckSdlc).toHaveBeenCalledTimes(2);
    expect(mockCheckSdlc).toHaveBeenCalledWith(
      "alice",
      "app",
      { connectionId: 1 },
      "trunk",
    );
    expect(mockCheckSdlc).toHaveBeenCalledWith(
      "acme",
      "service",
      { connectionId: 2 },
      "main",
    );
  });

  it("does not re-check a repo when the filter changes", async () => {
    mockFetchAll.mockResolvedValue({ repos: AGGREGATED, degraded: [] });
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    await user.click(screen.getByText("GitHub"));
    expect(await screen.findByText("alice/app")).toBeInTheDocument();
    await waitFor(() => expect(mockCheckSdlc).toHaveBeenCalledTimes(2));

    await user.type(screen.getByTestId("repo-filter-input"), "app");

    expect(mockCheckSdlc).toHaveBeenCalledTimes(2);
  });
});

describe("CR-01KXB377: Fallbacks", () => {
  it("browses with a one-off raw token for an unregistered credential", async () => {
    mockFetchRepos.mockResolvedValue(TOKEN_REPOS);
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    await user.click(screen.getByText("GitHub"));
    await user.click(screen.getByTestId("use-token-toggle"));
    await user.type(screen.getByTestId("access-token-input"), "ghp_token");
    await user.click(screen.getByTestId("token-browse-button"));

    expect(await screen.findByText("alice/app")).toBeInTheDocument();
    expect(mockFetchRepos).toHaveBeenCalledWith("ghp_token", undefined);

    await user.click(screen.getByTestId("repo-row-alice/app"));
    await user.click(screen.getByText("Add Project"));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "app",
          source_type: "github",
          repo_url: "https://github.com/alice/app",
          repo_branch: "trunk",
          access_token: "ghp_token",
        }),
      );
    });
    expect(mockOnSubmit.mock.calls[0][0]).not.toHaveProperty("connection_id");
  });

  it("checks the sdlc-studio flag with the raw token for a one-off browse", async () => {
    mockFetchRepos.mockResolvedValue(TOKEN_REPOS);
    mockCheckSdlc.mockResolvedValue(true);
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    await user.click(screen.getByText("GitHub"));
    await user.click(screen.getByTestId("use-token-toggle"));
    await user.type(screen.getByTestId("access-token-input"), "ghp_token");
    await user.click(screen.getByTestId("token-browse-button"));

    expect(
      await screen.findByTestId("sdlc-badge-alice/app"),
    ).toBeInTheDocument();
    expect(mockCheckSdlc).toHaveBeenCalledWith(
      "alice",
      "app",
      "ghp_token",
      "trunk",
    );
  });

  it("surfaces a browse failure without breaking the card", async () => {
    mockFetchAll.mockRejectedValue(new Error("Connections unavailable"));
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    await user.click(screen.getByText("GitHub"));

    expect(await screen.findByTestId("browse-error")).toHaveTextContent(
      "Connections unavailable",
    );
    // Manual entry still works.
    expect(screen.getByTestId("repo-url-input")).toBeInTheDocument();
  });

  it("prompts to register a connection when none are stored", async () => {
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    await user.click(screen.getByText("GitHub"));

    expect(await screen.findByTestId("no-repos-hint")).toBeInTheDocument();
    expect(screen.queryByTestId("browse-error")).not.toBeInTheDocument();
  });
});

describe("A hand-typed URL inherits no credential", () => {
  it("drops the clicked repo's connection and derived branch when the URL is typed away", async () => {
    mockFetchAll.mockResolvedValue({ repos: AGGREGATED, degraded: [] });
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
    // alice/app is surfaced by connection 1 and derives the branch "trunk".
    await user.click(await screen.findByTestId("repo-row-alice/app"));

    // Now change your mind and hand-type an entirely different repository.
    const urlInput = screen.getByTestId("repo-url-input");
    await user.clear(urlInput);
    await user.type(urlInput, "https://github.com/other/private");
    await user.click(screen.getByText("Add Project"));

    await waitFor(() => expect(mockOnSubmit).toHaveBeenCalled());
    const payload = mockOnSubmit.mock.calls[0][0];
    // The typed URL must not inherit the discarded repo's credential...
    expect(payload).not.toHaveProperty("connection_id");
    // ...nor its derived branch.
    expect(payload).toMatchObject({
      repo_url: "https://github.com/other/private",
      repo_branch: "main",
    });
  });

  it("keeps an explicit branch override when the URL is edited", async () => {
    mockFetchAll.mockResolvedValue({ repos: AGGREGATED, degraded: [] });
    const user = userEvent.setup();
    render(<ProjectForm mode="add" onSubmit={mockOnSubmit} error={null} />);

    await user.click(screen.getByText("GitHub"));
    await user.click(await screen.findByTestId("repo-row-alice/app"));
    await user.click(screen.getByTestId("advanced-toggle"));
    await user.clear(screen.getByTestId("repo-branch-input"));
    await user.type(screen.getByTestId("repo-branch-input"), "develop");

    const urlInput = screen.getByTestId("repo-url-input");
    await user.clear(urlInput);
    await user.type(urlInput, "https://github.com/other/private");
    await user.click(screen.getByText("Add Project"));

    await waitFor(() => expect(mockOnSubmit).toHaveBeenCalled());
    // A branch the operator typed is theirs, not a derived value to discard.
    expect(mockOnSubmit.mock.calls[0][0]).toMatchObject({
      repo_branch: "develop",
    });
  });
});

describe("Edit mode: the credential is changeable", () => {
  const renderEdit = (connectionId: number | null) =>
    render(
      <ProjectForm
        mode="edit"
        initialName="Bound Project"
        initialSourceType="github"
        initialRepoUrl="https://github.com/acme/service"
        initialConnectionId={connectionId}
        connections={CONNECTIONS}
        onSubmit={mockOnSubmit}
        onCancel={() => {}}
        error={null}
      />,
    );

  it("rebinds a project to a different stored connection", async () => {
    const user = userEvent.setup();
    renderEdit(2);

    const select = screen.getByTestId("connection-select");
    expect(select).toHaveValue("2");
    await user.selectOptions(select, "1");
    await user.click(screen.getByText("Save"));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({ connection_id: 1 });
    });
  });

  it("detaches the connection with an explicit null", async () => {
    const user = userEvent.setup();
    renderEdit(2);

    await user.selectOptions(screen.getByTestId("connection-select"), "");
    await user.click(screen.getByText("Save"));

    await waitFor(() => expect(mockOnSubmit).toHaveBeenCalled());
    const payload = mockOnSubmit.mock.calls[0][0];
    expect(payload).toHaveProperty("connection_id", null);
    expect(payload).not.toHaveProperty("access_token");
  });

  it("replaces a revoked credential with a one-off token", async () => {
    const user = userEvent.setup();
    renderEdit(2);

    // Detaching the connection is what makes a raw token take effect: the
    // connection's token wins over a per-project one in the sync engine.
    await user.selectOptions(screen.getByTestId("connection-select"), "");
    await user.type(screen.getByTestId("access-token-input"), "ghp_fresh");
    await user.click(screen.getByText("Save"));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        connection_id: null,
        access_token: "ghp_fresh",
      });
    });
  });

  it("replaces the token of a project that has no connection", async () => {
    const user = userEvent.setup();
    renderEdit(null);

    await user.type(screen.getByTestId("access-token-input"), "ghp_fresh");
    await user.click(screen.getByText("Save"));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({ access_token: "ghp_fresh" });
    });
  });

  it("submits only the name on a pure rename, and browses nothing", async () => {
    const user = userEvent.setup();
    renderEdit(2);

    await user.clear(screen.getByPlaceholderText("Project Name"));
    await user.type(screen.getByPlaceholderText("Project Name"), "Renamed");
    await user.click(screen.getByText("Save"));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({ name: "Renamed" });
    });
    expect(mockFetchAll).not.toHaveBeenCalled();
  });
});

// TC0339: ProjectForm edit mode pre-fills source type and fields
describe("TC0339: Edit mode pre-fills GitHub fields", () => {
  it("pre-fills GitHub fields in edit mode", async () => {
    const user = userEvent.setup();
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
    expect(screen.queryByPlaceholderText("SDLC Path")).not.toBeInTheDocument();

    // Non-default branch/path are already open under Advanced, so an existing
    // override is never hidden from the operator editing it.
    expect(screen.getByTestId("repo-branch-input")).toHaveValue("develop");
    expect(screen.getByTestId("repo-path-input")).toHaveValue("docs");

    // Editing does not browse until asked.
    expect(mockFetchAll).not.toHaveBeenCalled();
    await user.click(screen.getByTestId("browse-repos-button"));
    await waitFor(() => expect(mockFetchAll).toHaveBeenCalledTimes(1));
  });
});
