import type {
  AggregateStats,
  ApiError,
  DocumentDetail,
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
    throw new Error(`Failed to fetch projects: ${res.status}`);
  }
  return res.json() as Promise<Project[]>;
}

/** Fetch a single project by slug. */
export async function fetchProject(slug: string): Promise<Project> {
  const res = await fetch(`${BASE}/projects/${slug}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch project: ${res.status}`);
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

/** Fetch aggregate stats across all projects. */
export async function fetchAggregateStats(): Promise<AggregateStats> {
  const res = await fetch(`${BASE}/stats`);
  if (!res.ok) {
    throw new Error(`Failed to fetch stats: ${res.status}`);
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
