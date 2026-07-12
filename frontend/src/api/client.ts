import type {
  AggregateStats,
  ApiError,
  DocumentDetail,
  DocumentListItem,
  DocumentRelationships,
  GitHubRepoItem,
  HealthCheckResponse,
  PaginatedDocuments,
  Project,
  ProjectCreate,
  ProjectStats,
  ProjectUpdate,
  SearchResponse,
  SyncTriggerResponse,
} from "../types/index.ts";

const BASE = "/api/v1";

/** Fetch all registered projects. */
export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${BASE}/projects`);
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res));
  }
  return res.json() as Promise<Project[]>;
}

/** Fetch a single project by slug. */
export async function fetchProject(slug: string): Promise<Project> {
  const res = await fetch(`${BASE}/projects/${slug}`);
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res));
  }
  return res.json() as Promise<Project>;
}

async function extractErrorMessage(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as ApiError;
    return body.error.message;
  } catch {
    return `Request failed (${res.status})`;
  }
}

/** Register a new project. */
export async function createProject(data: ProjectCreate): Promise<Project> {
  const res = await fetch(`${BASE}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res));
  }
  return res.json() as Promise<Project>;
}

/** Update a project by slug. */
export async function updateProject(
  slug: string,
  data: ProjectUpdate,
): Promise<Project> {
  const res = await fetch(`${BASE}/projects/${slug}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res));
  }
  return res.json() as Promise<Project>;
}

/** Delete a project by slug. */
export async function deleteProject(slug: string): Promise<void> {
  const res = await fetch(`${BASE}/projects/${slug}`, { method: "DELETE" });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res));
  }
}

/** Fetch paginated documents for a project. */
export async function fetchDocuments(
  slug: string,
  params?: Record<string, string>,
): Promise<PaginatedDocuments> {
  const query = params ? `?${new URLSearchParams(params).toString()}` : "";
  const res = await fetch(`${BASE}/projects/${slug}/documents${query}`);
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res));
  }
  return res.json() as Promise<PaginatedDocuments>;
}

/** Fetch ALL documents for a project (paginating automatically). */
export async function fetchAllDocuments(
  slug: string,
): Promise<DocumentListItem[]> {
  const allItems: DocumentListItem[] = [];
  let page = 1;
  let pages = 1;
  do {
    const data = await fetchDocuments(slug, {
      per_page: "100",
      page: String(page),
    });
    allItems.push(...data.items);
    pages = data.pages;
    page++;
  } while (page <= pages);
  return allItems;
}

/** Fetch a single document detail by type and doc_id. */
export async function fetchDocument(
  slug: string,
  type: string,
  docId: string,
): Promise<DocumentDetail> {
  const res = await fetch(`${BASE}/projects/${slug}/documents/${type}/${docId}`);
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res));
  }
  return res.json() as Promise<DocumentDetail>;
}

/** Fetch related documents (parents and children) for a document. */
export async function fetchRelatedDocuments(
  slug: string,
  type: string,
  docId: string,
): Promise<DocumentRelationships> {
  const res = await fetch(
    `${BASE}/projects/${slug}/documents/${type}/${docId}/related`,
  );
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res));
  }
  return res.json() as Promise<DocumentRelationships>;
}

/** Fetch aggregate stats across all projects. */
export async function fetchAggregateStats(): Promise<AggregateStats> {
  const res = await fetch(`${BASE}/stats`);
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res));
  }
  return res.json() as Promise<AggregateStats>;
}

/** Fetch stats for a single project. */
export async function fetchProjectStats(
  slug: string,
): Promise<ProjectStats> {
  const res = await fetch(`${BASE}/projects/${slug}/stats`);
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res));
  }
  return res.json() as Promise<ProjectStats>;
}

/** Trigger a sync for a project. */
export async function triggerSync(
  slug: string,
): Promise<SyncTriggerResponse> {
  const res = await fetch(`${BASE}/projects/${slug}/sync`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res));
  }
  return res.json() as Promise<SyncTriggerResponse>;
}

/** Fetch health check for a project. */
export async function fetchHealthCheck(
  slug: string,
): Promise<HealthCheckResponse> {
  const res = await fetch(`${BASE}/projects/${slug}/health-check`);
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res));
  }
  return res.json() as Promise<HealthCheckResponse>;
}

/**
 * List the GitHub repositories the supplied token can see.
 *
 * The token travels in the POST body, never in the URL. Returns ALL visible
 * repos; the sdlc-studio flag per repo is fetched lazily via
 * {@link checkRepoHasSdlcStudio}.
 */
export async function fetchGitHubRepos(
  accessToken: string,
  search?: string,
): Promise<GitHubRepoItem[]> {
  const res = await fetch(`${BASE}/projects/github/repos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ access_token: accessToken, search }),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res));
  }
  const data = (await res.json()) as { repositories: GitHubRepoItem[] };
  return data.repositories;
}

/**
 * Lazy per-repo flag: does this repo already contain an sdlc-studio/ workspace?
 *
 * Call this only for the rows the operator is actually viewing, not for every
 * repo in the list - that would exhaust the GitHub rate limit.
 */
export async function checkRepoHasSdlcStudio(
  owner: string,
  repo: string,
  accessToken: string,
  branch?: string,
): Promise<boolean> {
  const res = await fetch(
    `${BASE}/projects/github/repos/${owner}/${repo}/has-sdlc-studio`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ access_token: accessToken, branch }),
    },
  );
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res));
  }
  const data = (await res.json()) as { has_sdlc_studio: boolean };
  return data.has_sdlc_studio;
}

/** Search documents by query. */
export async function fetchSearchResults(
  params: Record<string, string>,
): Promise<SearchResponse> {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE}/search?${query}`);
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res));
  }
  return res.json() as Promise<SearchResponse>;
}
