/**
 * ProjectForm component tests.
 * Test cases: TC0331-TC0339 from TS0032.
 */
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ProjectForm } from "./ProjectForm.tsx";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const mockOnSubmit = vi.fn().mockResolvedValue(undefined);

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
