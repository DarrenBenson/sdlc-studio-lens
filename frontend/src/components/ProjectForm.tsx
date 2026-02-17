import { useState } from "react";

import type { ProjectCreate, ProjectUpdate } from "../types/index.ts";

interface ProjectFormProps {
  mode: "add" | "edit";
  initialName?: string;
  initialPath?: string;
  onSubmit: (data: ProjectCreate | ProjectUpdate) => Promise<void>;
  onCancel?: () => void;
  error: string | null;
}

export function ProjectForm({
  mode,
  initialName = "",
  initialPath = "",
  onSubmit,
  onCancel,
  error,
}: ProjectFormProps) {
  const [name, setName] = useState(initialName);
  const [sdlcPath, setSdlcPath] = useState(initialPath);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === "add") {
        await onSubmit({ name, sdlc_path: sdlcPath });
        setName("");
        setSdlcPath("");
      } else {
        const update: ProjectUpdate = {};
        if (name !== initialName) update.name = name;
        if (sdlcPath !== initialPath) update.sdlc_path = sdlcPath;
        await onSubmit(update);
      }
    } catch {
      // Error is handled by parent via error prop
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={(e) => void handleSubmit(e)} className="space-y-3">
      <div>
        <input
          type="text"
          placeholder="Project Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          className="w-full rounded-md border border-border-default bg-bg-elevated px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-border-strong focus:outline-none"
        />
      </div>
      <div>
        <input
          type="text"
          placeholder="SDLC Path"
          value={sdlcPath}
          onChange={(e) => setSdlcPath(e.target.value)}
          required
          className="w-full rounded-md border border-border-default bg-bg-elevated px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-border-strong focus:outline-none"
        />
      </div>
      {error && (
        <p className="text-sm text-status-blocked" data-testid="form-error">
          {error}
        </p>
      )}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg-base hover:bg-accent-hover disabled:opacity-50"
        >
          {loading ? "Saving..." : mode === "add" ? "Add Project" : "Save"}
        </button>
        {mode === "edit" && onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md bg-bg-elevated px-4 py-2 text-sm text-text-secondary hover:bg-bg-overlay"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
