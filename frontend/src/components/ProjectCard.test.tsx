/**
 * ProjectCard component tests.
 * Test cases: TC0340-TC0342 from TS0032.
 */
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Project } from "../types/index.ts";
import { ProjectCard } from "./ProjectCard.tsx";

afterEach(() => {
  cleanup();
});

const localProject: Project = {
  slug: "local-proj",
  name: "Local Project",
  sdlc_path: "/data/projects/test",
  source_type: "local",
  repo_url: null,
  repo_branch: "main",
  repo_path: "sdlc-studio",
  masked_token: null,
  sync_status: "synced",
  sync_error: null,
  last_synced_at: "2026-02-17T10:00:00Z",
  document_count: 42,
  created_at: "2026-02-17T09:00:00Z",
};

const githubProject: Project = {
  slug: "github-proj",
  name: "GitHub Project",
  sdlc_path: null,
  source_type: "github",
  repo_url: "https://github.com/owner/repo",
  repo_branch: "develop",
  repo_path: "docs",
  masked_token: "****1234",
  sync_status: "synced",
  sync_error: null,
  last_synced_at: "2026-02-17T10:00:00Z",
  document_count: 15,
  created_at: "2026-02-17T09:00:00Z",
};

const noop = () => {};

// TC0340: ProjectCard shows repo URL for github projects
describe("TC0340: GitHub card shows repo URL", () => {
  it("displays repository URL", () => {
    render(
      <ProjectCard
        project={githubProject}
        onEdit={noop}
        onDelete={noop}
        onSync={noop}
      />,
    );

    expect(
      screen.getByText("https://github.com/owner/repo"),
    ).toBeInTheDocument();
  });
});

// TC0341: ProjectCard shows sdlc_path for local projects
describe("TC0341: Local card shows sdlc_path", () => {
  it("displays local SDLC path", () => {
    render(
      <ProjectCard
        project={localProject}
        onEdit={noop}
        onDelete={noop}
        onSync={noop}
      />,
    );

    expect(screen.getByText("/data/projects/test")).toBeInTheDocument();
  });

  it("does not show repo URL for local project", () => {
    render(
      <ProjectCard
        project={localProject}
        onEdit={noop}
        onDelete={noop}
        onSync={noop}
      />,
    );

    expect(
      screen.queryByText("https://github.com/owner/repo"),
    ).not.toBeInTheDocument();
  });
});

// TC0342: ProjectCard shows source type badge
describe("TC0342: Source type badge", () => {
  it("shows GitHub badge for github project", () => {
    render(
      <ProjectCard
        project={githubProject}
        onEdit={noop}
        onDelete={noop}
        onSync={noop}
      />,
    );

    const badge = screen.getByTestId("source-badge");
    expect(badge).toHaveTextContent("GitHub");
  });

  it("shows Local badge for local project", () => {
    render(
      <ProjectCard
        project={localProject}
        onEdit={noop}
        onDelete={noop}
        onSync={noop}
      />,
    );

    const badge = screen.getByTestId("source-badge");
    expect(badge).toHaveTextContent("Local");
  });
});
