import { useCallback, useEffect, useRef, useState } from "react";

import {
  createProject,
  deleteProject,
  fetchProject,
  fetchProjects,
  triggerSync,
  updateProject,
} from "../api/client.ts";
import { ConfirmDialog } from "../components/ConfirmDialog.tsx";
import { ProjectCard } from "../components/ProjectCard.tsx";
import { ProjectForm } from "../components/ProjectForm.tsx";
import type { Project, ProjectCreate, ProjectUpdate } from "../types/index.ts";

const POLL_INTERVAL = 2000;

export function Settings() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [formError, setFormError] = useState<string | null>(null);
  const [editingSlug, setEditingSlug] = useState<string | null>(null);
  const [deleteSlug, setDeleteSlug] = useState<string | null>(null);
  const [notification, setNotification] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadProjects = useCallback(async () => {
    try {
      const data = await fetchProjects();
      setProjects(data);
    } catch {
      // Sidebar handles errors; settings page just shows what it can
    }
  }, []);

  useEffect(() => {
    void loadProjects();
  }, [loadProjects]);

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

      {/* Add / Edit form */}
      <div className="mt-6 rounded-lg border border-border-default bg-bg-surface p-4">
        <h3 className="mb-3 text-sm font-medium text-text-secondary">
          {editingSlug ? `Editing: ${editingProject?.name}` : "Add a project"}
        </h3>
        <ProjectForm
          key={editingSlug ?? "add"}
          mode={editingSlug ? "edit" : "add"}
          initialName={editingProject?.name}
          initialPath={editingProject?.sdlc_path}
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
