import { useCallback, useEffect, useRef, useState } from "react";

import {
  createConnection,
  createProject,
  deleteConnection,
  deleteProject,
  fetchConnections,
  fetchProject,
  fetchProjects,
  rotateConnection,
  triggerSync,
  updateProject,
  validateConnection,
} from "../api/client.ts";
import { ConfirmDialog } from "../components/ConfirmDialog.tsx";
import { ProjectCard } from "../components/ProjectCard.tsx";
import { ProjectForm } from "../components/ProjectForm.tsx";
import type {
  GitHubConnection,
  Project,
  ProjectCreate,
  ProjectUpdate,
} from "../types/index.ts";

const POLL_INTERVAL = 2000;

const inputClass =
  "w-full rounded-md border border-border-default bg-bg-elevated px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-border-strong focus:outline-none";

/** Render an ISO timestamp as "12 Jul 2026", or null when absent. */
function formatDate(iso: string | null): string | null {
  if (!iso) return null;
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function Settings() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [formError, setFormError] = useState<string | null>(null);
  const [editingSlug, setEditingSlug] = useState<string | null>(null);
  const [deleteSlug, setDeleteSlug] = useState<string | null>(null);
  const [notification, setNotification] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // GitHub connections: named credentials, registered once and reused.
  const [connections, setConnections] = useState<GitHubConnection[]>([]);
  const [connectionLabel, setConnectionLabel] = useState("");
  const [connectionToken, setConnectionToken] = useState("");
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [connectionBusy, setConnectionBusy] = useState(false);
  // Rotation: the id of the connection whose token is being replaced, and the
  // replacement itself. Both are dropped the moment the token is exchanged.
  const [rotatingId, setRotatingId] = useState<number | null>(null);
  const [rotateToken, setRotateToken] = useState("");

  const loadProjects = useCallback(async () => {
    try {
      const data = await fetchProjects();
      setProjects(data);
    } catch {
      // Sidebar handles errors; settings page just shows what it can
    }
  }, []);

  const loadConnections = useCallback(async () => {
    try {
      const data = await fetchConnections();
      setConnections(data);
    } catch {
      // A connections failure must not take the whole settings page down
    }
  }, []);

  useEffect(() => {
    void loadProjects();
  }, [loadProjects]);

  useEffect(() => {
    void loadConnections();
  }, [loadConnections]);

  // Poll for syncing projects
  useEffect(() => {
    const syncingSlugs = projects
      .filter((p) => p.sync_status === "syncing")
      .map((p) => p.slug);

    if (syncingSlugs.length === 0) {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
      return;
    }

    pollRef.current = setInterval(() => {
      void (async () => {
        for (const slug of syncingSlugs) {
          try {
            const updated = await fetchProject(slug);
            setProjects((prev) =>
              prev.map((p) => (p.slug === slug ? updated : p)),
            );
          } catch {
            // Ignore poll errors
          }
        }
      })();
    }, POLL_INTERVAL);

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [projects]);

  const showNotification = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 3000);
  };

  const handleAdd = async (data: ProjectCreate | ProjectUpdate) => {
    setFormError(null);
    try {
      const created = await createProject(data as ProjectCreate);
      setProjects((prev) => [...prev, created]);
      showNotification(`Project "${created.name}" added.`);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to add project");
      throw err; // Re-throw so form knows it failed
    }
  };

  const handleEdit = async (data: ProjectCreate | ProjectUpdate) => {
    if (!editingSlug) return;
    setFormError(null);
    try {
      const updated = await updateProject(editingSlug, data as ProjectUpdate);
      setProjects((prev) =>
        prev.map((p) => (p.slug === editingSlug ? updated : p)),
      );
      setEditingSlug(null);
      showNotification(`Project "${updated.name}" updated.`);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to update project");
      throw err;
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteSlug) return;
    const name = projects.find((p) => p.slug === deleteSlug)?.name;
    // Optimistic removal
    setProjects((prev) => prev.filter((p) => p.slug !== deleteSlug));
    setDeleteSlug(null);
    try {
      await deleteProject(deleteSlug);
      showNotification(`Project "${name}" deleted.`);
    } catch {
      // Revert on failure
      void loadProjects();
      showNotification("Failed to delete project.");
    }
  };

  const handleSync = async (slug: string) => {
    try {
      await triggerSync(slug);
      setProjects((prev) =>
        prev.map((p) =>
          p.slug === slug ? { ...p, sync_status: "syncing" as const } : p,
        ),
      );
    } catch {
      showNotification("Failed to trigger sync.");
    }
  };

  const handleAddConnection = async (e: React.FormEvent) => {
    e.preventDefault();
    setConnectionError(null);
    setConnectionBusy(true);
    try {
      const created = await createConnection(connectionLabel, connectionToken);
      setConnections((prev) => [...prev, created]);
      // Drop the raw token the moment it has been exchanged for a connection.
      setConnectionLabel("");
      setConnectionToken("");
      showNotification(
        `Connection "${created.label}" added for ${created.login}.`,
      );
    } catch (err) {
      setConnectionError(
        err instanceof Error ? err.message : "Failed to add connection",
      );
    } finally {
      setConnectionBusy(false);
    }
  };

  const handleValidateConnection = async (id: number) => {
    setConnectionError(null);
    try {
      const updated = await validateConnection(id);
      setConnections((prev) => prev.map((c) => (c.id === id ? updated : c)));
      showNotification(`Connection "${updated.label}" is valid.`);
    } catch (err) {
      setConnectionError(
        err instanceof Error ? err.message : "Failed to validate connection",
      );
    }
  };

  const handleRotateConnection = async (e: React.FormEvent, id: number) => {
    e.preventDefault();
    setConnectionError(null);
    setConnectionBusy(true);
    try {
      const updated = await rotateConnection(id, rotateToken);
      setConnections((prev) => prev.map((c) => (c.id === id ? updated : c)));
      // Drop the raw token the moment the server has taken it.
      setRotateToken("");
      setRotatingId(null);
      showNotification(`Connection "${updated.label}" token replaced.`);
    } catch (err) {
      // A rejected token changes nothing server-side; keep the form open.
      setConnectionError(
        err instanceof Error ? err.message : "Failed to rotate connection",
      );
    } finally {
      setConnectionBusy(false);
    }
  };

  const toggleRotate = (id: number) => {
    setConnectionError(null);
    setRotateToken("");
    setRotatingId((current) => (current === id ? null : id));
  };

  const handleDeleteConnection = async (id: number) => {
    setConnectionError(null);
    try {
      await deleteConnection(id);
      setConnections((prev) => prev.filter((c) => c.id !== id));
      showNotification("Connection removed.");
    } catch (err) {
      // A refusal (the connection is still in use) leaves the row in place.
      setConnectionError(
        err instanceof Error ? err.message : "Failed to remove connection",
      );
    }
  };

  const editingProject = projects.find((p) => p.slug === editingSlug);
  const deletingProject = projects.find((p) => p.slug === deleteSlug);

  return (
    <div className="mx-auto max-w-2xl">
      <h2 className="font-display text-xl font-semibold text-text-primary">
        Settings
      </h2>
      <p className="mt-1 text-sm text-text-secondary">
        Manage your registered projects.
      </p>

      {/* Notification */}
      {notification && (
        <div className="mt-4 rounded-md bg-accent-muted border border-accent px-4 py-2 text-sm text-accent">
          {notification}
        </div>
      )}

      {/* GitHub connections */}
      <div className="mt-6 rounded-lg border border-border-default bg-bg-surface p-4">
        <h3 className="text-sm font-medium text-text-secondary">
          GitHub connections
        </h3>
        <p className="mt-1 text-xs text-text-tertiary">
          Register a personal access token once, then pick it when adding a
          repository. Tokens are stored server-side and never shown again.
        </p>

        <form
          onSubmit={(e) => void handleAddConnection(e)}
          className="mt-3 space-y-2"
        >
          <div className="grid grid-cols-2 gap-2">
            <input
              type="text"
              placeholder="Label (e.g. personal)"
              value={connectionLabel}
              onChange={(e) => setConnectionLabel(e.target.value)}
              required
              className={inputClass}
              data-testid="connection-label-input"
            />
            <input
              type="password"
              placeholder="Personal access token"
              value={connectionToken}
              onChange={(e) => setConnectionToken(e.target.value)}
              required
              className={inputClass}
              data-testid="connection-token-input"
            />
          </div>
          <button
            type="submit"
            disabled={connectionBusy}
            className="rounded-md bg-bg-elevated px-3 py-1.5 text-xs font-medium text-text-secondary hover:bg-bg-overlay disabled:opacity-50"
          >
            {connectionBusy ? "Checking..." : "Add connection"}
          </button>
        </form>

        {/* One error region for every connection action: add, rotate, validate,
            remove. Each failure leaves the server state untouched. */}
        {connectionError && (
          <p
            className="mt-2 text-xs text-status-blocked"
            data-testid="connection-error"
          >
            {connectionError}
          </p>
        )}

        <div className="mt-3 space-y-2">
          {connections.length === 0 ? (
            <p className="text-xs text-text-tertiary">
              No GitHub connections saved yet.
            </p>
          ) : (
            connections.map((conn) => {
              const validated = formatDate(conn.last_validated_at);
              return (
                <div
                  key={conn.id}
                  className="rounded-md border border-border-subtle bg-bg-elevated px-3 py-2"
                  data-testid={`connection-row-${conn.id}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm text-text-primary">
                        {conn.label}
                        <span className="ml-2 text-xs text-text-tertiary">
                          {conn.login}
                        </span>
                      </p>
                      <p className="mt-0.5 font-mono text-xs text-text-muted">
                        {conn.masked_token ?? "token stored"}
                        <span className="ml-2 font-sans">
                          {validated
                            ? `Validated ${validated}`
                            : "Never validated"}
                        </span>
                      </p>
                    </div>
                    <div className="flex shrink-0 gap-2">
                      <button
                        type="button"
                        onClick={() => void handleValidateConnection(conn.id)}
                        className="rounded-md bg-bg-surface px-2.5 py-1 text-xs text-text-secondary hover:bg-bg-overlay"
                        data-testid={`validate-connection-${conn.id}`}
                      >
                        Validate
                      </button>
                      <button
                        type="button"
                        onClick={() => toggleRotate(conn.id)}
                        className="rounded-md bg-bg-surface px-2.5 py-1 text-xs text-text-secondary hover:bg-bg-overlay"
                        data-testid={`rotate-connection-${conn.id}`}
                      >
                        Rotate
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleDeleteConnection(conn.id)}
                        className="rounded-md bg-bg-surface px-2.5 py-1 text-xs text-status-blocked hover:bg-bg-overlay"
                        data-testid={`delete-connection-${conn.id}`}
                      >
                        Remove
                      </button>
                    </div>
                  </div>

                  {/* Rotation: replace an expired PAT in one edit. The projects
                      using this connection pick the new token up automatically. */}
                  {rotatingId === conn.id && (
                    <form
                      onSubmit={(e) => void handleRotateConnection(e, conn.id)}
                      className="mt-2 flex gap-2 border-t border-border-subtle pt-2"
                    >
                      <input
                        type="password"
                        placeholder="New personal access token"
                        value={rotateToken}
                        onChange={(e) => setRotateToken(e.target.value)}
                        required
                        className={inputClass}
                        data-testid={`rotate-token-input-${conn.id}`}
                      />
                      <button
                        type="submit"
                        disabled={connectionBusy}
                        className="shrink-0 rounded-md bg-bg-surface px-2.5 py-1 text-xs text-text-secondary hover:bg-bg-overlay disabled:opacity-50"
                        data-testid={`rotate-submit-${conn.id}`}
                      >
                        {connectionBusy ? "Checking..." : "Replace token"}
                      </button>
                    </form>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Add / Edit form */}
      <div className="mt-6 rounded-lg border border-border-default bg-bg-surface p-4">
        <h3 className="mb-3 text-sm font-medium text-text-secondary">
          {editingSlug ? `Editing: ${editingProject?.name}` : "Add a project"}
        </h3>
        <ProjectForm
          key={editingSlug ?? "add"}
          mode={editingSlug ? "edit" : "add"}
          initialName={editingProject?.name}
          initialPath={editingProject?.sdlc_path ?? ""}
          initialSourceType={editingProject?.source_type}
          initialRepoUrl={editingProject?.repo_url ?? ""}
          initialRepoBranch={editingProject?.repo_branch}
          initialRepoPath={editingProject?.repo_path}
          initialConnectionId={editingProject?.connection_id ?? null}
          connections={connections}
          onSubmit={editingSlug ? handleEdit : handleAdd}
          onCancel={editingSlug ? () => { setEditingSlug(null); setFormError(null); } : undefined}
          error={formError}
        />
      </div>

      {/* Project list */}
      <div className="mt-6 space-y-3">
        {projects.length === 0 && (
          <p className="text-sm text-text-tertiary">
            No projects registered. Add your first project above.
          </p>
        )}
        {projects.map((project) => (
          <ProjectCard
            key={project.slug}
            project={project}
            onEdit={() => { setEditingSlug(project.slug); setFormError(null); }}
            onDelete={() => setDeleteSlug(project.slug)}
            onSync={() => void handleSync(project.slug)}
          />
        ))}
      </div>

      {/* Delete confirmation */}
      {deleteSlug && deletingProject && (
        <ConfirmDialog
          message={
            deletingProject.sync_status === "syncing"
              ? `"${deletingProject.name}" is currently syncing. Delete anyway?`
              : `Delete "${deletingProject.name}"? This will remove all synced documents.`
          }
          onConfirm={() => void handleDeleteConfirm()}
          onCancel={() => setDeleteSlug(null)}
        />
      )}
    </div>
  );
}
