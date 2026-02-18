/** Sync status state machine values. */
export type SyncStatus = "never_synced" | "syncing" | "synced" | "error";

/** Source type for project document origin. */
export type SourceType = "local" | "github";

/** Project as returned by GET /api/v1/projects. */
export interface Project {
  slug: string;
  name: string;
  sdlc_path: string | null;
  source_type: SourceType;
  repo_url: string | null;
  repo_branch: string;
  repo_path: string;
  masked_token: string | null;
  sync_status: SyncStatus;
  sync_error: string | null;
  last_synced_at: string | null;
  document_count: number;
  created_at: string;
}

/** Request body for POST /api/v1/projects. */
export interface ProjectCreate {
  name: string;
  source_type: SourceType;
  sdlc_path?: string;
  repo_url?: string;
  repo_branch?: string;
  repo_path?: string;
  access_token?: string;
}

/** Request body for PUT /api/v1/projects/{slug}. */
export interface ProjectUpdate {
  name?: string;
  sdlc_path?: string;
  source_type?: SourceType;
  repo_url?: string;
  repo_branch?: string;
  repo_path?: string;
  access_token?: string;
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
  epic: string | null;
  story: string | null;
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
  story: string | null;
  metadata: Record<string, string> | null;
  content: string;
  file_path: string;
  file_hash: string;
  synced_at: string;
}

/** A related document item (parent or child). */
export interface RelatedDocumentItem {
  doc_id: string;
  type: string;
  title: string;
  status: string | null;
}

/** Response from GET /projects/{slug}/documents/{type}/{docId}/related. */
export interface DocumentRelationships {
  doc_id: string;
  type: string;
  title: string;
  parents: RelatedDocumentItem[];
  children: RelatedDocumentItem[];
}

/** A document affected by a health check finding. */
export interface AffectedDocument {
  doc_id: string;
  doc_type: string;
  title: string;
}

/** A single health check finding. */
export interface HealthFinding {
  rule_id: string;
  severity: "critical" | "high" | "medium" | "low";
  category: string;
  message: string;
  affected_documents: AffectedDocument[];
  suggested_fix: string;
}

/** Response from GET /api/v1/projects/{slug}/health-check. */
export interface HealthCheckResponse {
  project_slug: string;
  checked_at: string;
  total_documents: number;
  findings: HealthFinding[];
  summary: Record<string, number>;
  score: number;
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
