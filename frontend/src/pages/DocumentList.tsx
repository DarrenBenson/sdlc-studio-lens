import { useCallback, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router";

import { fetchDocuments } from "../api/client.ts";
import { StatusBadge } from "../components/StatusBadge.tsx";
import { TypeBadge } from "../components/TypeBadge.tsx";
import type { DocumentListItem, PaginatedDocuments } from "../types/index.ts";

const TYPE_OPTIONS = [
  { value: "", label: "All Types" },
  { value: "epic", label: "Epic" },
  { value: "story", label: "Story" },
  { value: "bug", label: "Bug" },
  { value: "plan", label: "Plan" },
  { value: "test-spec", label: "Test Spec" },
  { value: "prd", label: "PRD" },
  { value: "trd", label: "TRD" },
  { value: "tsd", label: "TSD" },
  { value: "other", label: "Other" },
];

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "Done", label: "Done" },
  { value: "In Progress", label: "In Progress" },
  { value: "Draft", label: "Draft" },
  { value: "Blocked", label: "Blocked" },
  { value: "Not Started", label: "Not Started" },
  { value: "Review", label: "Review" },
  { value: "Ready", label: "Ready" },
  { value: "Planned", label: "Planned" },
];

export function DocumentList(): React.JSX.Element {
  const { slug } = useParams<{ slug: string }>();
  const [searchParams, setSearchParams] = useSearchParams();

  const [data, setData] = useState<PaginatedDocuments | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const typeFilter = searchParams.get("type") ?? "";
  const statusFilter = searchParams.get("status") ?? "";
  const page = searchParams.get("page") ?? "1";

  const load = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (typeFilter) params.type = typeFilter;
      if (statusFilter) params.status = statusFilter;
      if (page !== "1") params.page = page;
      const result = await fetchDocuments(slug, params);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [slug, typeFilter, statusFilter, page]);

  useEffect(() => {
    void load();
  }, [load]);

  function handleTypeChange(value: string) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set("type", value);
      } else {
        next.delete("type");
      }
      next.delete("page");
      return next;
    });
  }

  function handleStatusChange(value: string) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set("status", value);
      } else {
        next.delete("status");
      }
      next.delete("page");
      return next;
    });
  }

  function handlePageChange(newPage: number) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (newPage > 1) {
        next.set("page", String(newPage));
      } else {
        next.delete("page");
      }
      return next;
    });
  }

  if (loading) {
    return (
      <div className="text-text-secondary">
        <p>Loading documents...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-text-secondary">
        <p className="text-status-blocked">Error: {error}</p>
        <button
          onClick={() => void load()}
          className="mt-2 rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-bg-base"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4">
        <Link
          to={`/projects/${slug}`}
          className="text-sm text-text-tertiary hover:text-accent"
        >
          &larr; Project Dashboard
        </Link>
      </div>

      <h2 className="font-display text-xl font-semibold text-text-primary">
        Documents
      </h2>

      {/* Filters */}
      <div className="mt-4 flex gap-4">
        <label className="flex flex-col gap-1">
          <span className="text-xs text-text-tertiary">Type</span>
          <select
            aria-label="Type"
            value={typeFilter}
            onChange={(e) => handleTypeChange(e.target.value)}
            className="rounded-md border border-border-default bg-bg-surface px-3 py-1.5 text-sm text-text-primary"
          >
            {TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-xs text-text-tertiary">Status</span>
          <select
            aria-label="Status"
            value={statusFilter}
            onChange={(e) => handleStatusChange(e.target.value)}
            className="rounded-md border border-border-default bg-bg-surface px-3 py-1.5 text-sm text-text-primary"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {/* Document list */}
      {data && data.items.length === 0 ? (
        <p className="mt-6 text-text-tertiary">
          No documents match your filters.
        </p>
      ) : (
        <>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-default text-left text-text-tertiary">
                  <th className="pb-2 font-medium">Title</th>
                  <th className="pb-2 font-medium">Type</th>
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium">Owner</th>
                  <th className="pb-2 font-medium">Updated</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((doc) => (
                  <DocumentRow key={doc.doc_id} doc={doc} slug={slug!} />
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data && data.pages > 0 && (
            <div className="mt-4 flex items-center gap-4 text-sm text-text-secondary">
              <button
                disabled={data.page <= 1}
                onClick={() => handlePageChange(data.page - 1)}
                className="rounded border border-border-default px-2 py-1 disabled:opacity-40"
              >
                Prev
              </button>
              <span>
                Page {data.page} of {data.pages} ({data.total} documents)
              </span>
              <button
                disabled={data.page >= data.pages}
                onClick={() => handlePageChange(data.page + 1)}
                className="rounded border border-border-default px-2 py-1 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function DocumentRow({
  doc,
  slug,
}: {
  doc: DocumentListItem;
  slug: string;
}): React.JSX.Element {
  const date = new Date(doc.updated_at);
  const formatted = date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

  return (
    <tr className="border-b border-border-subtle hover:bg-bg-surface">
      <td className="py-2 pr-4">
        <Link
          to={`/projects/${slug}/documents/${doc.type}/${doc.doc_id}`}
          className="text-text-primary hover:text-accent"
        >
          {doc.title}
        </Link>
      </td>
      <td className="py-2 pr-4">
        <TypeBadge type={doc.type} />
      </td>
      <td className="py-2 pr-4">
        <StatusBadge status={doc.status} />
      </td>
      <td className="py-2 pr-4 text-text-secondary">{doc.owner ?? "—"}</td>
      <td className="py-2 text-text-tertiary">{formatted}</td>
    </tr>
  );
}
