import { useState } from "react";

import type {
  ProjectCreate,
  ProjectUpdate,
  SourceType,
} from "../types/index.ts";

interface ProjectFormProps {
  mode: "add" | "edit";
  initialName?: string;
  initialPath?: string;
  initialSourceType?: SourceType;
  initialRepoUrl?: string;
  initialRepoBranch?: string;
  initialRepoPath?: string;
  onSubmit: (data: ProjectCreate | ProjectUpdate) => Promise<void>;
  onCancel?: () => void;
  error: string | null;
}

const inputClass =
  "w-full rounded-md border border-border-default bg-bg-elevated px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-border-strong focus:outline-none";

export function ProjectForm({
  mode,
  initialName = "",
  initialPath = "",
  initialSourceType = "local",
  initialRepoUrl = "",
  initialRepoBranch = "main",
  initialRepoPath = "sdlc-studio",
  onSubmit,
  onCancel,
  error,
}: ProjectFormProps) {
  const [name, setName] = useState(initialName);
  const [sourceType, setSourceType] = useState<SourceType>(initialSourceType);
  const [sdlcPath, setSdlcPath] = useState(initialPath);
  const [repoUrl, setRepoUrl] = useState(initialRepoUrl);
  const [repoBranch, setRepoBranch] = useState(initialRepoBranch);
  const [repoPath, setRepoPath] = useState(initialRepoPath);
  const [accessToken, setAccessToken] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === "add") {
        const data: ProjectCreate = {
          name,
          source_type: sourceType,
        };
        if (sourceType === "local") {
          data.sdlc_path = sdlcPath;
        } else {
          data.repo_url = repoUrl;
          if (repoBranch !== "main") data.repo_branch = repoBranch;
          if (repoPath !== "sdlc-studio") data.repo_path = repoPath;
          if (accessToken) data.access_token = accessToken;
        }
        await onSubmit(data);
        setName("");
        setSdlcPath("");
        setRepoUrl("");
        setRepoBranch("main");
        setRepoPath("sdlc-studio");
        setAccessToken("");
      } else {
        const update: ProjectUpdate = {};
        if (name !== initialName) update.name = name;
        if (sourceType !== initialSourceType) update.source_type = sourceType;
        if (sourceType === "local" && sdlcPath !== initialPath) {
          update.sdlc_path = sdlcPath;
        }
        if (sourceType === "github") {
          if (repoUrl !== initialRepoUrl) update.repo_url = repoUrl;
          if (repoBranch !== initialRepoBranch)
            update.repo_branch = repoBranch;
          if (repoPath !== initialRepoPath) update.repo_path = repoPath;
          if (accessToken) update.access_token = accessToken;
        }
        await onSubmit(update);
      }
    } catch {
      // Error is handled by parent via error prop
    } finally {
      setLoading(false);
    }
  };

  const toggleClass = (active: boolean) =>
    `rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
      active
        ? "bg-accent text-bg-base"
        : "bg-bg-elevated text-text-secondary hover:bg-bg-overlay"
    }`;

  return (
    <form onSubmit={(e) => void handleSubmit(e)} className="space-y-3">
      <div>
        <input
          type="text"
          placeholder="Project Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          className={inputClass}
        />
      </div>

      {/* Source type toggle */}
      <div>
        <label className="mb-1.5 block text-xs text-text-tertiary">
          Source
        </label>
        <div className="flex gap-1" data-testid="source-type-toggle">
          <button
            type="button"
            onClick={() => setSourceType("local")}
            className={toggleClass(sourceType === "local")}
          >
            Local
          </button>
          <button
            type="button"
            onClick={() => setSourceType("github")}
            className={toggleClass(sourceType === "github")}
          >
            GitHub
          </button>
        </div>
      </div>

      {/* Conditional fields */}
      {sourceType === "local" ? (
        <div>
          <input
            type="text"
            placeholder="SDLC Path"
            value={sdlcPath}
            onChange={(e) => setSdlcPath(e.target.value)}
            required
            className={inputClass}
            data-testid="sdlc-path-input"
          />
        </div>
      ) : (
        <div className="space-y-2">
          <input
            type="text"
            placeholder="Repository URL (e.g. https://github.com/owner/repo)"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            required
            className={inputClass}
            data-testid="repo-url-input"
          />
          <div className="grid grid-cols-2 gap-2">
            <input
              type="text"
              placeholder="Branch"
              value={repoBranch}
              onChange={(e) => setRepoBranch(e.target.value)}
              className={inputClass}
              data-testid="repo-branch-input"
            />
            <input
              type="text"
              placeholder="Subdirectory path"
              value={repoPath}
              onChange={(e) => setRepoPath(e.target.value)}
              className={inputClass}
              data-testid="repo-path-input"
            />
          </div>
          <input
            type="password"
            placeholder="Access token (optional, for private repos)"
            value={accessToken}
            onChange={(e) => setAccessToken(e.target.value)}
            className={inputClass}
            data-testid="access-token-input"
          />
        </div>
      )}

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
