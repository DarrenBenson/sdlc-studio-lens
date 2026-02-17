import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";

import { fetchSearchResults } from "../api/client.ts";
import { StatusBadge } from "../components/StatusBadge.tsx";
import { TypeBadge } from "../components/TypeBadge.tsx";
import type { SearchResponse, SearchResultItem } from "../types/index.ts";

export function SearchResults(): React.JSX.Element {
  const [searchParams, setSearchParams] = useSearchParams();

  const [data, setData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const query = searchParams.get("q") ?? "";
  const projectFilter = searchParams.get("project") ?? "";
  const typeFilter = searchParams.get("type") ?? "";

  const load = useCallback(async () => {
    if (!query) {
      setData(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = { q: query };
      if (projectFilter) params.project = projectFilter;
      if (typeFilter) params.type = typeFilter;
      const result = await fetchSearchResults(params);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [query, projectFilter, typeFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  function handleProjectChange(value: string) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set("project", value);
      } else {
        next.delete("project");
      }
      return next;
    });
  }

  // Extract unique projects from result items for filter options
  const uniqueProjects: { slug: string; name: string }[] = [];
  if (data) {
    const seen = new Set<string>();
    for (const item of data.items) {
      if (!seen.has(item.project_slug)) {
        seen.add(item.project_slug);
        uniqueProjects.push({
          slug: item.project_slug,
          name: item.project_name,
        });
      }
    }
  }

  if (loading) {
    return (
      <div className="text-text-secondary">
        <p>Loading search results...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-text-secondary">
        <p className="text-status-blocked">
          Failed to load search results: {error}
        </p>
        <button
          onClick={() => void load()}
          className="mt-2 rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-bg-base"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!query) {
    return (
      <div className="text-text-secondary">
        <h2 className="font-display text-xl font-semibold text-text-primary">
          Search
        </h2>
        <p className="mt-2">Enter a query to search documents.</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="font-display text-xl font-semibold text-text-primary">
        {data && data.total > 0
          ? `${data.total} result${data.total !== 1 ? "s" : ""} for "${query}"`
          : `Results for "${query}"`}
      </h2>

      {/* Project filter */}
      {uniqueProjects.length > 1 && (
        <div className="mt-4 flex gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-xs text-text-tertiary">Project</span>
            <select
              aria-label="Project"
              value={projectFilter}
              onChange={(e) => handleProjectChange(e.target.value)}
              className="rounded-md border border-border-default bg-bg-surface px-3 py-1.5 text-sm text-text-primary"
            >
              <option value="">All Projects</option>
              {uniqueProjects.map((p) => (
                <option key={p.slug} value={p.slug}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}

      {/* Results */}
      {data && data.items.length === 0 ? (
        <p className="mt-6 text-text-tertiary">
          No results found for "{query}".
        </p>
      ) : (
        <div className="mt-4 flex flex-col gap-3">
          {data?.items.map((item) => (
            <ResultCard key={`${item.project_slug}-${item.type}-${item.doc_id}`} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}

function ResultCard({ item }: { item: SearchResultItem }): React.JSX.Element {
  return (
    <div className="rounded-lg border border-border-default bg-bg-surface p-4">
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <Link
              to={`/projects/${item.project_slug}/documents/${item.type}/${item.doc_id}`}
              className="font-medium text-text-primary hover:text-accent"
            >
              {item.title}
            </Link>
          </div>

          <div className="mt-1 flex items-center gap-2 text-sm">
            <TypeBadge type={item.type} />
            <span className="text-text-tertiary">{item.project_name}</span>
            {item.status && <StatusBadge status={item.status} />}
          </div>

          <p
            className="mt-2 text-sm text-text-secondary"
            dangerouslySetInnerHTML={{ __html: item.snippet }}
          />
        </div>
      </div>
    </div>
  );
}
