import type { Project, SyncStatus } from "../types/index.ts";

const STATUS_LABELS: Record<SyncStatus, string> = {
  synced: "Synced",
  syncing: "Syncing",
  never_synced: "Never synced",
  error: "Error",
};

const STATUS_COLOURS: Record<SyncStatus, string> = {
  synced: "bg-status-done/15 text-status-done",
  syncing: "bg-status-progress/15 text-status-progress",
  never_synced: "bg-status-draft/15 text-status-draft",
  error: "bg-status-blocked/15 text-status-blocked",
};

const DOT_COLOURS: Record<SyncStatus, string> = {
  synced: "bg-status-done",
  syncing: "bg-status-progress",
  never_synced: "bg-status-draft",
  error: "bg-status-blocked",
};

interface ProjectCardProps {
  project: Project;
  onEdit: () => void;
  onDelete: () => void;
  onSync: () => void;
}

export function ProjectCard({
  project,
  onEdit,
  onDelete,
  onSync,
}: ProjectCardProps) {
  const isSyncing = project.sync_status === "syncing";

  return (
    <div
      className="rounded-lg border border-border-default bg-bg-surface p-4"
      data-testid={`project-card-${project.slug}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3
            className="truncate font-display text-sm font-semibold text-text-primary"
            title={project.name}
          >
            {project.name}
          </h3>
          <div className="mt-1 flex items-center gap-2">
            <span
              className="inline-flex rounded px-1.5 py-0.5 text-[10px] font-medium bg-bg-elevated text-text-tertiary"
              data-testid="source-badge"
            >
              {project.source_type === "github" ? "GitHub" : "Local"}
            </span>
            <p className="truncate font-mono text-xs text-text-tertiary">
              {project.source_type === "github"
                ? project.repo_url
                : project.sdlc_path}
            </p>
          </div>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs ${STATUS_COLOURS[project.sync_status]}`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${DOT_COLOURS[project.sync_status]}`}
          />
          {STATUS_LABELS[project.sync_status]}
        </span>
      </div>

      <div className="mt-3 flex items-center gap-4 text-xs text-text-tertiary">
        <span>
          {project.document_count}{" "}
          {project.document_count === 1 ? "document" : "documents"}
        </span>
        <span>
          {project.last_synced_at
            ? `Last synced: ${new Date(project.last_synced_at).toLocaleString()}`
            : "Never synced"}
        </span>
      </div>

      {project.sync_error && (
        <p className="mt-2 text-xs text-status-blocked">
          {project.sync_error}
        </p>
      )}

      <div className="mt-3 flex gap-2">
        <button
          onClick={onSync}
          disabled={isSyncing}
          className="rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-bg-base hover:bg-accent-hover disabled:opacity-50"
        >
          {isSyncing ? "Syncing..." : "Sync Now"}
        </button>
        <button
          onClick={onEdit}
          className="rounded-md bg-bg-elevated px-3 py-1.5 text-xs text-text-secondary hover:bg-bg-overlay"
        >
          Edit
        </button>
        <button
          onClick={onDelete}
          className="rounded-md bg-bg-elevated px-3 py-1.5 text-xs text-status-blocked hover:bg-bg-overlay"
        >
          Delete
        </button>
      </div>
    </div>
  );
}
