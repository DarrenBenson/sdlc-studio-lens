import { useEffect, useState } from "react";
import { NavLink } from "react-router";

import { fetchProjects } from "../api/client.ts";
import type { Project, SyncStatus } from "../types/index.ts";

const STATUS_COLOURS: Record<SyncStatus, string> = {
  synced: "bg-status-done",
  syncing: "bg-status-progress",
  never_synced: "bg-status-draft",
  error: "bg-status-blocked",
};

export function Sidebar() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProjects();
      setProjects(data);
    } catch {
      setError("Failed to load projects");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadProjects();
  }, []);

  return (
    <aside
      className="flex h-screen w-60 flex-col bg-bg-surface border-r border-border-default"
      data-testid="sidebar"
    >
      {/* Header */}
      <div className="px-4 py-5 border-b border-border-subtle">
        <h1 className="font-display text-lg font-semibold text-accent">
          Studio Lens
        </h1>
      </div>

      {/* Project list */}
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {loading && (
          <p className="px-2 text-sm text-text-tertiary">Loading...</p>
        )}

        {error && (
          <div className="px-2 text-sm">
            <p className="text-status-blocked">{error}</p>
            <button
              onClick={() => void loadProjects()}
              className="mt-2 text-accent hover:text-accent-hover underline"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && projects.length === 0 && (
          <div className="px-2 text-sm text-text-tertiary">
            <p>No projects registered.</p>
            <NavLink to="/settings" className="text-accent hover:text-accent-hover underline">
              Add a project
            </NavLink>
          </div>
        )}

        {projects.map((project) => (
          <NavLink
            key={project.slug}
            to={`/projects/${project.slug}`}
            className={({ isActive }) =>
              `flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${
                isActive
                  ? "bg-accent-muted text-accent font-medium"
                  : "text-text-secondary hover:bg-bg-elevated hover:text-text-primary"
              }`
            }
            title={project.name}
          >
            <span
              className={`h-2 w-2 shrink-0 rounded-full ${STATUS_COLOURS[project.sync_status]}`}
              data-testid={`status-${project.slug}`}
            />
            <span className="truncate">{project.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-border-subtle px-2 py-3">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${
              isActive
                ? "bg-accent-muted text-accent font-medium"
                : "text-text-secondary hover:bg-bg-elevated hover:text-text-primary"
            }`
          }
        >
          Settings
        </NavLink>
      </div>
    </aside>
  );
}
