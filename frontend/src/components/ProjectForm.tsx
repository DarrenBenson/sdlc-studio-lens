import { useEffect, useRef, useState } from "react";

import type { GitHubCredential } from "../api/client.ts";
import { checkRepoHasSdlcStudio, fetchGitHubRepos } from "../api/client.ts";
import type {
  GitHubConnection,
  GitHubRepoItem,
  ProjectCreate,
  ProjectUpdate,
  SourceType,
} from "../types/index.ts";

// Cap the rows whose sdlc-studio flag we resolve eagerly. Only these visible
// rows trigger a per-repo Contents call, so a large account (hundreds of repos)
// never fans out into hundreds of lazy checks and exhausts the rate limit -
// narrowing the filter surfaces more rows on demand.
const MAX_VISIBLE_REPOS = 30;

interface ProjectFormProps {
  mode: "add" | "edit";
  initialName?: string;
  initialPath?: string;
  initialSourceType?: SourceType;
  initialRepoUrl?: string;
  initialRepoBranch?: string;
  initialRepoPath?: string;
  initialConnectionId?: number | null;
  /** Stored GitHub credentials the operator can pick instead of pasting one. */
  connections?: GitHubConnection[];
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
  initialConnectionId = null,
  connections = [],
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
  const [connectionId, setConnectionId] = useState<number | null>(
    initialConnectionId,
  );
  const [loading, setLoading] = useState(false);

  // Repo selector state (GitHub source only).
  const [repos, setRepos] = useState<GitHubRepoItem[]>([]);
  const [repoFilter, setRepoFilter] = useState("");
  const [browsing, setBrowsing] = useState(false);
  const [browseError, setBrowseError] = useState<string | null>(null);
  const [sdlcFlags, setSdlcFlags] = useState<Record<string, boolean>>({});
  // Repos whose flag check has already been kicked off, so each is fetched once.
  const checkedRepos = useRef<Set<string>>(new Set());

  const matchesFilter = (repo: GitHubRepoItem): boolean => {
    const term = repoFilter.trim().toLowerCase();
    if (!term) return true;
    return (
      repo.full_name.toLowerCase().includes(term) ||
      (repo.description ?? "").toLowerCase().includes(term)
    );
  };

  const visibleRepos = repos
    .filter(matchesFilter)
    .slice(0, MAX_VISIBLE_REPOS);

  // A saved connection wins over a typed token: picking one means the operator
  // never has to paste a credential again.
  const credential: GitHubCredential | null =
    connectionId !== null
      ? { connectionId }
      : accessToken
        ? accessToken
        : null;

  // Lazily resolve the sdlc-studio flag for the currently-visible rows only.
  useEffect(() => {
    if (repos.length === 0 || !credential) return;
    for (const repo of visibleRepos) {
      if (checkedRepos.current.has(repo.full_name)) continue;
      checkedRepos.current.add(repo.full_name);
      void checkRepoHasSdlcStudio(
        repo.owner,
        repo.name,
        credential,
        repo.default_branch,
      )
        .then((has) => {
          setSdlcFlags((prev) => ({ ...prev, [repo.full_name]: has }));
        })
        .catch(() => {
          // A failed flag check is non-fatal; allow a later retry.
          checkedRepos.current.delete(repo.full_name);
        });
    }
    // visibleRepos is derived from repos + repoFilter, and credential from
    // accessToken + connectionId; those are the real deps.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [repos, repoFilter, accessToken, connectionId]);

  /** Drop any browsed repos - they belong to whichever credential fetched them. */
  const resetBrowse = () => {
    checkedRepos.current = new Set();
    setSdlcFlags({});
    setRepos([]);
    setRepoFilter("");
    setBrowseError(null);
  };

  const handleConnectionChange = (value: string) => {
    resetBrowse();
    if (value === "") {
      setConnectionId(null);
      return;
    }
    setConnectionId(Number(value));
    // A stored connection replaces any one-off token that was typed.
    setAccessToken("");
  };

  const handleBrowse = async () => {
    if (!credential) return;
    setBrowsing(true);
    setBrowseError(null);
    checkedRepos.current = new Set();
    setSdlcFlags({});
    try {
      const found = await fetchGitHubRepos(credential, undefined);
      setRepos(found);
    } catch (err) {
      setBrowseError(err instanceof Error ? err.message : "Failed to load repositories");
      setRepos([]);
    } finally {
      setBrowsing(false);
    }
  };

  const handleSelectRepo = (repo: GitHubRepoItem) => {
    setRepoUrl(`https://github.com/${repo.full_name}`);
    setRepoBranch(repo.default_branch);
    // Leave repo_path at its default/current value.
  };

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
          if (connectionId !== null) {
            data.connection_id = connectionId;
          } else if (accessToken) {
            data.access_token = accessToken;
          }
        }
        await onSubmit(data);
        setName("");
        setSdlcPath("");
        setRepoUrl("");
        setRepoBranch("main");
        setRepoPath("sdlc-studio");
        setAccessToken("");
        setConnectionId(null);
        resetBrowse();
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
          if (connectionId !== initialConnectionId) {
            update.connection_id = connectionId;
          }
          if (connectionId === null && accessToken) {
            update.access_token = accessToken;
          }
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
          {/* Saved credential picker - choosing one means no token to paste. */}
          {connections.length > 0 && (
            <div>
              <label
                htmlFor="connection-select"
                className="mb-1.5 block text-xs text-text-tertiary"
              >
                GitHub connection
              </label>
              <select
                id="connection-select"
                value={connectionId === null ? "" : String(connectionId)}
                onChange={(e) => handleConnectionChange(e.target.value)}
                className={inputClass}
                data-testid="connection-select"
              >
                <option value="">Enter a token manually</option>
                {connections.map((conn) => (
                  <option key={conn.id} value={String(conn.id)}>
                    {conn.label} ({conn.login})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* One-off token entry, the fallback when no connection is chosen. */}
          {connectionId === null && (
            <input
              type="password"
              placeholder="Access token (optional, for private repos)"
              value={accessToken}
              onChange={(e) => setAccessToken(e.target.value)}
              className={inputClass}
              data-testid="access-token-input"
            />
          )}

          {/* Repo selector - browse the repos a credential can see. Manual URL
              entry above remains available as a fallback. */}
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => void handleBrowse()}
              disabled={!credential || browsing}
              className="rounded-md bg-bg-elevated px-3 py-1.5 text-xs font-medium text-text-secondary hover:bg-bg-overlay disabled:opacity-50"
              data-testid="browse-repos-button"
            >
              {browsing ? "Loading repositories..." : "Browse repositories"}
            </button>

            {browseError && (
              <p
                className="text-xs text-status-blocked"
                data-testid="browse-error"
              >
                {browseError}
              </p>
            )}

            {repos.length > 0 && (
              <div className="space-y-2" data-testid="repo-selector">
                <input
                  type="text"
                  placeholder="Filter repositories"
                  value={repoFilter}
                  onChange={(e) => setRepoFilter(e.target.value)}
                  className={inputClass}
                  data-testid="repo-filter-input"
                />
                <ul className="max-h-56 divide-y divide-border-default overflow-y-auto rounded-md border border-border-default">
                  {visibleRepos.map((repo) => (
                    <li key={repo.full_name}>
                      <button
                        type="button"
                        onClick={() => handleSelectRepo(repo)}
                        className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm text-text-primary hover:bg-bg-overlay"
                        data-testid={`repo-row-${repo.full_name}`}
                      >
                        <span className="flex min-w-0 items-center gap-2">
                          <span className="truncate">{repo.full_name}</span>
                          {repo.private && (
                            <span className="shrink-0 text-xs text-text-muted">
                              private
                            </span>
                          )}
                        </span>
                        {sdlcFlags[repo.full_name] && (
                          <span
                            className="shrink-0 rounded bg-status-done/15 px-1.5 py-0.5 text-xs text-status-done"
                            data-testid={`sdlc-badge-${repo.full_name}`}
                          >
                            sdlc-studio
                          </span>
                        )}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
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
