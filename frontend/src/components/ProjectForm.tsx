import { useCallback, useEffect, useRef, useState } from "react";

import type { GitHubCredential } from "../api/client.ts";
import {
  checkRepoHasSdlcStudio,
  fetchAllConnectionRepos,
  fetchGitHubRepos,
} from "../api/client.ts";
import type {
  DegradedConnection,
  GitHubConnection,
  ProjectCreate,
  ProjectUpdate,
  SourceType,
} from "../types/index.ts";

// Cap the rows whose sdlc-studio flag we resolve eagerly. Only these visible
// rows trigger a per-repo Contents call, so a large account (hundreds of repos)
// never fans out into hundreds of lazy checks and exhausts the rate limit -
// narrowing the filter surfaces more rows on demand.
const MAX_VISIBLE_REPOS = 30;

const DEFAULT_BRANCH = "main";
const DEFAULT_REPO_PATH = "sdlc-studio";

/**
 * A row in the repository list.
 *
 * Aggregated rows carry the connection that surfaced them. A one-off raw-token
 * browse has no stored connection, so those rows carry `null` and fall back to
 * the typed token for their lazy sdlc-studio check.
 */
interface RepoRow {
  full_name: string;
  owner: string;
  name: string;
  private: boolean;
  default_branch: string;
  description: string | null;
  connection_id: number | null;
  connection_label: string | null;
}

interface ProjectFormProps {
  mode: "add" | "edit";
  initialName?: string;
  initialPath?: string;
  initialSourceType?: SourceType;
  initialRepoUrl?: string;
  initialRepoBranch?: string;
  initialRepoPath?: string;
  initialConnectionId?: number | null;
  initialAutoSync?: boolean;
  /** Stored GitHub credentials - used only to decide whether to name them. */
  connections?: GitHubConnection[];
  onSubmit: (data: ProjectCreate | ProjectUpdate) => Promise<void>;
  onCancel?: () => void;
  error: string | null;
}

const inputClass =
  "w-full rounded-md border border-border-default bg-bg-elevated px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-border-strong focus:outline-none";

const secondaryButtonClass =
  "rounded-md bg-bg-elevated px-3 py-1.5 text-xs font-medium text-text-secondary hover:bg-bg-overlay disabled:opacity-50";

export function ProjectForm({
  mode,
  initialName = "",
  initialPath = "",
  initialSourceType = "local",
  initialRepoUrl = "",
  initialRepoBranch = DEFAULT_BRANCH,
  initialRepoPath = DEFAULT_REPO_PATH,
  initialConnectionId = null,
  initialAutoSync = false,
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
  // Opt-in, default off (CR-01KXCAZJ): an existing project must keep behaving exactly as
  // it does today until the operator asks for something different.
  const [autoSync, setAutoSync] = useState(initialAutoSync);
  const [connectionId, setConnectionId] = useState<number | null>(
    initialConnectionId,
  );
  const [loading, setLoading] = useState(false);

  // The name is derived from the picked repo until the operator types one.
  const [nameTouched, setNameTouched] = useState(initialName !== "");
  // Likewise the branch: a value the operator typed is theirs and survives a
  // change of repository; a value we derived from a pick does not.
  const [branchTouched, setBranchTouched] = useState(false);

  // Branch and sdlc path are derived, so they live behind Advanced. An existing
  // override is never hidden: editing a project that has one opens it.
  const [showAdvanced, setShowAdvanced] = useState(
    mode === "edit" &&
      initialSourceType === "github" &&
      (initialRepoBranch !== DEFAULT_BRANCH ||
        initialRepoPath !== DEFAULT_REPO_PATH),
  );
  // The one-off raw token is a fallback for an unregistered credential.
  const [showToken, setShowToken] = useState(false);

  // Repository picker state (GitHub source only).
  const [repos, setRepos] = useState<RepoRow[]>([]);
  const [degraded, setDegraded] = useState<DegradedConnection[]>([]);
  const [repoFilter, setRepoFilter] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [browsing, setBrowsing] = useState(false);
  const [browsed, setBrowsed] = useState(false);
  const [browseError, setBrowseError] = useState<string | null>(null);
  const [sdlcFlags, setSdlcFlags] = useState<Record<string, boolean>>({});
  // Repos whose flag check has already been kicked off, so each is fetched once.
  const checkedRepos = useRef<Set<string>>(new Set());

  const matchesFilter = (repo: RepoRow): boolean => {
    const term = repoFilter.trim().toLowerCase();
    if (!term) return true;
    return (
      repo.full_name.toLowerCase().includes(term) ||
      (repo.description ?? "").toLowerCase().includes(term)
    );
  };

  const visibleRepos = repos.filter(matchesFilter).slice(0, MAX_VISIBLE_REPOS);

  // The repo the operator actually picked, or null once the URL has been typed
  // away from it. Everything the pick derives - above all the credential - is
  // read from HERE at submit time rather than copied into its own state, so a
  // hand-typed URL cannot inherit a stale binding from a discarded pick.
  const selectedRepo = repos.find((repo) => repo.full_name === selected) ?? null;

  // Which connection surfaced a repo only matters when there is more than one.
  const showConnectionLabels = connections.length > 1;

  /** The credential that can answer for this repo: its connection, or the token. */
  const credentialFor = (repo: RepoRow): GitHubCredential | null => {
    if (repo.connection_id !== null) return { connectionId: repo.connection_id };
    return accessToken ? accessToken : null;
  };

  /** Clear whatever a previous browse left behind, whichever browse it was. */
  const startBrowse = () => {
    setBrowsing(true);
    setBrowsed(true);
    setBrowseError(null);
    setDegraded([]);
    checkedRepos.current = new Set();
    setSdlcFlags({});
  };

  /** Browse every stored connection at once. No credential is chosen or sent. */
  const browseAll = useCallback(async () => {
    setBrowsing(true);
    setBrowsed(true);
    setBrowseError(null);
    setDegraded([]);
    checkedRepos.current = new Set();
    setSdlcFlags({});
    try {
      const data = await fetchAllConnectionRepos();
      setRepos(data.repos.map((repo) => ({ ...repo })));
      setDegraded(data.degraded);
    } catch (err) {
      setBrowseError(
        err instanceof Error ? err.message : "Failed to load repositories",
      );
      setRepos([]);
    } finally {
      setBrowsing(false);
    }
  }, []);

  // Opening the GitHub flow IS the request to see your repositories.
  useEffect(() => {
    if (mode !== "add" || sourceType !== "github" || browsed) return;
    void browseAll();
  }, [mode, sourceType, browsed, browseAll]);

  /** Fallback browse with a one-off token for a credential nobody registered. */
  const browseWithToken = async () => {
    if (!accessToken) return;
    startBrowse();
    try {
      const found = await fetchGitHubRepos(accessToken, undefined);
      setRepos(
        found.map((repo) => ({
          ...repo,
          connection_id: null,
          connection_label: null,
        })),
      );
    } catch (err) {
      setBrowseError(
        err instanceof Error ? err.message : "Failed to load repositories",
      );
      setRepos([]);
    } finally {
      setBrowsing(false);
    }
  };

  // Lazily resolve the sdlc-studio flag for the currently-visible rows only,
  // each with the credential that surfaced that row.
  useEffect(() => {
    for (const repo of visibleRepos) {
      if (checkedRepos.current.has(repo.full_name)) continue;
      const credential = credentialFor(repo);
      if (!credential) continue;
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
    // visibleRepos is derived from repos + repoFilter, and the fallback
    // credential from accessToken; those are the real deps.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [repos, repoFilter, accessToken]);

  /** Picking a repo derives everything the project needs. */
  const handleSelectRepo = (repo: RepoRow) => {
    setSelected(repo.full_name);
    setRepoUrl(`https://github.com/${repo.full_name}`);
    setRepoBranch(repo.default_branch);
    setBranchTouched(false);
    // Edit mode submits `connectionId`, so a pick rebinds the project's
    // credential. Add mode reads the credential off `selectedRepo` instead.
    setConnectionId(repo.connection_id);
    // The name is almost always the repo's own; it stays editable.
    if (!nameTouched) setName(repo.name);
  };

  /** Typing over the URL discards the pick, and everything it derived. */
  const handleRepoUrlChange = (value: string) => {
    setRepoUrl(value);
    if (selected === null) return;
    setSelected(null);
    // In add mode the pick is the ONLY source of a credential, so dropping it
    // is what stops a hand-typed URL binding to a connection that cannot see
    // the repo. Its derived branch goes with it, unless the operator typed one.
    if (mode === "add" && !branchTouched) setRepoBranch(DEFAULT_BRANCH);
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
          data.repo_branch = repoBranch;
          data.repo_path = repoPath;
          // Derived, not stored: only a repo still selected carries a
          // connection. A URL typed by hand sends none.
          if (selectedRepo?.connection_id != null) {
            data.connection_id = selectedRepo.connection_id;
          } else if (accessToken) {
            data.access_token = accessToken;
          }
        }
        await onSubmit(data);
        setName("");
        setNameTouched(false);
        setSdlcPath("");
        setRepoUrl("");
        setRepoBranch(DEFAULT_BRANCH);
        setBranchTouched(false);
        setRepoPath(DEFAULT_REPO_PATH);
        setAccessToken("");
        setConnectionId(null);
        setSelected(null);
        setShowAdvanced(false);
        setShowToken(false);
      } else {
        const update: ProjectUpdate = {};
        if (name !== initialName) update.name = name;
        if (autoSync !== initialAutoSync) update.auto_sync = autoSync;
        if (sourceType !== initialSourceType) update.source_type = sourceType;
        if (sourceType === "local" && sdlcPath !== initialPath) {
          update.sdlc_path = sdlcPath;
        }
        if (sourceType === "github") {
          if (repoUrl !== initialRepoUrl) update.repo_url = repoUrl;
          if (repoBranch !== initialRepoBranch) update.repo_branch = repoBranch;
          if (repoPath !== initialRepoPath) update.repo_path = repoPath;
          // The credential picker below is what makes these reachable: it can
          // rebind the project to another connection, or detach it (an explicit
          // null) so a one-off token takes effect - a connection's token always
          // wins over a per-project one, so a raw token only means anything
          // once no connection is bound.
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
          onChange={(e) => {
            setName(e.target.value);
            setNameTouched(e.target.value !== "");
          }}
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
        <div className="space-y-3">
          {/* Repository: pick one, or paste a URL. Nothing asks for a token. */}
          <div className="space-y-2">
            <div className="flex items-center justify-between gap-2">
              <label className="text-xs text-text-tertiary">Repository</label>
              <button
                type="button"
                onClick={() => void browseAll()}
                disabled={browsing}
                className={secondaryButtonClass}
                data-testid="browse-repos-button"
              >
                {browsing ? "Loading..." : "Browse my repositories"}
              </button>
            </div>

            {browseError && (
              <p
                className="text-xs text-status-blocked"
                data-testid="browse-error"
              >
                {browseError}
              </p>
            )}

            {degraded.length > 0 && (
              <p
                className="rounded-md bg-status-blocked/15 px-2.5 py-1.5 text-xs text-text-secondary"
                data-testid="degraded-notice"
              >
                Some connections could not be listed in full:{" "}
                {degraded
                  .map((d) => `${d.label} (${d.reason})`)
                  .join("; ")}
              </p>
            )}

            {repos.length > 0 && (
              <div className="space-y-2" data-testid="repo-selector">
                <input
                  type="text"
                  placeholder="Search repositories"
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
                        aria-pressed={selected === repo.full_name}
                        className={`flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm text-text-primary hover:bg-bg-overlay ${
                          selected === repo.full_name ? "bg-accent-muted" : ""
                        }`}
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
                        <span className="flex shrink-0 items-center gap-2">
                          {showConnectionLabels && repo.connection_label && (
                            <span
                              className="text-xs text-text-tertiary"
                              data-testid={`repo-connection-${repo.full_name}`}
                            >
                              {repo.connection_label}
                            </span>
                          )}
                          {sdlcFlags[repo.full_name] && (
                            <span
                              className="rounded bg-status-done/15 px-1.5 py-0.5 text-xs text-status-done"
                              data-testid={`sdlc-badge-${repo.full_name}`}
                            >
                              sdlc-studio
                            </span>
                          )}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {browsed && !browsing && !browseError && repos.length === 0 && (
              <p
                className="text-xs text-text-tertiary"
                data-testid="no-repos-hint"
              >
                No repositories to show. Register a GitHub connection above, or
                paste a repository URL below.
              </p>
            )}

            <input
              type="text"
              placeholder="Repository URL (e.g. https://github.com/owner/repo)"
              value={repoUrl}
              onChange={(e) => handleRepoUrlChange(e.target.value)}
              required
              className={inputClass}
              data-testid="repo-url-input"
            />
          </div>

          {/* Advanced: derived values, editable for the rare override. */}
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => setShowAdvanced((open) => !open)}
              aria-expanded={showAdvanced}
              className="text-xs text-text-tertiary hover:text-text-secondary"
              data-testid="advanced-toggle"
            >
              {showAdvanced ? "Advanced -" : "Advanced +"}
            </button>
            {showAdvanced && (
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="text"
                  placeholder="Branch"
                  value={repoBranch}
                  onChange={(e) => {
                    setRepoBranch(e.target.value);
                    setBranchTouched(true);
                  }}
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
                <label className="col-span-2 flex items-center gap-2 text-sm text-slate-300">
                  <input
                    type="checkbox"
                    checked={autoSync}
                    onChange={(e) => setAutoSync(e.target.checked)}
                    data-testid="auto-sync-toggle"
                    className="h-4 w-4 rounded border-slate-600 bg-slate-800"
                  />
                  <span>
                    Keep in sync automatically
                    <span className="block text-xs text-slate-500">
                      Checks the branch for new commits and re-syncs only what changed.
                    </span>
                  </span>
                </label>
              </div>
            )}
          </div>

          {/* The credential.
              Adding: the pick carries it, so the only control here is the
              fallback for a credential nobody registered.
              Editing: it is an explicit choice, and the ONLY way to rebind a
              project to another connection, detach it, or replace a revoked
              token - which is why a saved connection must be selectable, not
              merely inherited. */}
          {mode === "edit" ? (
            <div className="space-y-2">
              <label
                htmlFor="project-credential"
                className="block text-xs text-text-tertiary"
              >
                Credential
              </label>
              <select
                id="project-credential"
                value={connectionId === null ? "" : String(connectionId)}
                onChange={(e) =>
                  setConnectionId(
                    e.target.value === "" ? null : Number(e.target.value),
                  )
                }
                className={inputClass}
                data-testid="connection-select"
              >
                <option value="">Use a one-off token instead</option>
                {connections.map((connection) => (
                  <option key={connection.id} value={connection.id}>
                    {connection.label} ({connection.login})
                  </option>
                ))}
              </select>
              {/* A raw token only takes effect with no connection bound, so it
                  is offered only there rather than rendered inert. */}
              {connectionId === null && (
                <div className="flex gap-2">
                  <input
                    type="password"
                    placeholder="Access token (blank keeps the stored one)"
                    value={accessToken}
                    onChange={(e) => setAccessToken(e.target.value)}
                    className={inputClass}
                    data-testid="access-token-input"
                  />
                  <button
                    type="button"
                    onClick={() => void browseWithToken()}
                    disabled={!accessToken || browsing}
                    className={`shrink-0 ${secondaryButtonClass}`}
                    data-testid="token-browse-button"
                  >
                    Browse
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => setShowToken((open) => !open)}
                aria-expanded={showToken}
                className="text-xs text-text-tertiary hover:text-text-secondary"
                data-testid="use-token-toggle"
              >
                {showToken ? "Use a one-off token -" : "Use a one-off token +"}
              </button>
              {showToken && (
                <div className="flex gap-2">
                  <input
                    type="password"
                    placeholder="Access token (for a credential you have not saved)"
                    value={accessToken}
                    onChange={(e) => setAccessToken(e.target.value)}
                    className={inputClass}
                    data-testid="access-token-input"
                  />
                  <button
                    type="button"
                    onClick={() => void browseWithToken()}
                    disabled={!accessToken || browsing}
                    className={`shrink-0 ${secondaryButtonClass}`}
                    data-testid="token-browse-button"
                  >
                    Browse
                  </button>
                </div>
              )}
            </div>
          )}
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
