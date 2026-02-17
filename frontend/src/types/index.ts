/** Sync status state machine values. */
export type SyncStatus = "never_synced" | "syncing" | "synced" | "error";

/** Project as returned by GET /api/v1/projects. */
export interface Project {
  slug: string;
  name: string;
  sdlc_path: string;
  sync_status: SyncStatus;
  sync_error: string | null;
  last_synced_at: string | null;
  document_count: number;
  created_at: string;
}

/** Request body for POST /api/v1/projects. */
export interface ProjectCreate {
  name: string;
  sdlc_path: string;
}

/** Request body for PUT /api/v1/projects/{slug}. */
export interface ProjectUpdate {
  name?: string;
  sdlc_path?: string;
}

/** Response from POST /api/v1/projects/{slug}/sync. */
export interface SyncTriggerResponse {
  slug: string;
  sync_status: string;
  message: string;
}

/** API error response shape. */
export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}

/** Document list item (excludes content). */
export interface DocumentListItem {
  doc_id: string;
  type: string;
  title: string;
  status: string | null;
  owner: string | null;
  priority: string | null;
  story_points: number | null;
  updated_at: string;
}

/** Paginated documents response. */
export interface PaginatedDocuments {
  items: DocumentListItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

/** Per-project summary in aggregate stats. */
export interface ProjectSummary {
  slug: string;
  name: string;
  total_documents: number;
  completion_percentage: number;
  last_synced_at: string | null;
}

/** Per-project stats response. */
export interface ProjectStats {
  slug: string;
  name: string;
  total_documents: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  completion_percentage: number;
  last_synced_at: string | null;
}

/** Aggregate stats response. */
export interface AggregateStats {
  total_projects: number;
  total_documents: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  completion_percentage: number;
  projects: ProjectSummary[];
}

/** Full document detail response. */
export interface DocumentDetail {
  doc_id: string;
  type: string;
  title: string;
  status: string | null;
  owner: string | null;
  priority: string | null;
  story_points: number | null;
  epic: string | null;
  metadata: Record<string, string> | null;
  content: string;
  file_path: string;
  file_hash: string;
  synced_at: string;
}

/** Single search result item. */
export interface SearchResultItem {
  doc_id: string;
  type: string;
  title: string;
  project_slug: string;
  project_name: string;
  status: string | null;
  snippet: string;
  score: number;
}

/** Search response from GET /api/v1/search. */
export interface SearchResponse {
  items: SearchResultItem[];
  total: number;
  query: string;
  page: number;
  per_page: number;
}
