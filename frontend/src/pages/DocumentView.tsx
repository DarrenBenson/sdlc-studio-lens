import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import { Link, useLocation, useParams } from "react-router";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";

import { fetchDocument, fetchRelatedDocuments } from "../api/client.ts";
import { StatusBadge } from "../components/StatusBadge.tsx";
import { TypeBadge } from "../components/TypeBadge.tsx";
import type {
  DocumentDetail,
  DocumentRelationships,
  RelatedDocumentItem,
} from "../types/index.ts";

function RelatedDocLink({
  item,
  slug,
  fromTree,
}: {
  item: RelatedDocumentItem;
  slug: string;
  fromTree?: boolean;
}): React.JSX.Element {
  return (
    <Link
      to={`/projects/${slug}/documents/${item.type}/${item.doc_id}`}
      state={fromTree ? { from: "tree" } : undefined}
      className="flex items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-bg-elevated"
    >
      <TypeBadge type={item.type} />
      <span className="min-w-0 flex-1 truncate text-text-primary">
        {item.title}
      </span>
      {item.status && <StatusBadge status={item.status} />}
    </Link>
  );
}

export function DocumentView(): React.JSX.Element {
  const { slug, type, docId } = useParams<{
    slug: string;
    type: string;
    docId: string;
  }>();

  const location = useLocation();
  const fromTree = (location.state as { from?: string } | null)?.from === "tree";

  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [related, setRelated] = useState<DocumentRelationships | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug || !type || !docId) return;
    setLoading(true);
    setError(null);
    setRelated(null);

    Promise.all([
      fetchDocument(slug, type, docId),
      fetchRelatedDocuments(slug, type, docId).catch(() => null),
    ])
      .then(([docData, relData]) => {
        setDoc(docData);
        setRelated(relData);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Unknown error");
      })
      .finally(() => setLoading(false));
  }, [slug, type, docId]);

  if (loading) {
    return (
      <div className="text-text-secondary">
        <p>Loading document...</p>
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div className="text-text-secondary">
        <p className="text-status-blocked">Error: {error ?? "Not found"}</p>
        <Link
          to={`/projects/${slug}/documents`}
          className="mt-2 inline-block text-accent hover:text-accent-hover"
        >
          Back to documents
        </Link>
      </div>
    );
  }

  const syncDate = new Date(doc.synced_at);
  const formattedSync = syncDate.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

  // Build breadcrumb ancestors (furthest first for display)
  const ancestors = related?.parents ? [...related.parents].reverse() : [];

  const hasParents = related !== null && related.parents.length > 0;
  const hasChildren = related !== null && related.children.length > 0;
  const hasRelationships = hasParents || hasChildren;

  return (
    <div className="flex gap-6">
      {/* Main content */}
      <div className="min-w-0 flex-1">
        <nav className="mb-4 flex items-center gap-1 text-sm text-text-tertiary">
          <Link to={`/projects/${slug}`} className="hover:text-accent">
            Project
          </Link>
          <span>/</span>
          <Link
            to={fromTree ? `/projects/${slug}/tree` : `/projects/${slug}/documents`}
            className="hover:text-accent"
          >
            {fromTree ? "Tree View" : "Documents"}
          </Link>
          {ancestors.map((parent) => (
            <span key={parent.doc_id} className="flex items-center gap-1">
              <span>/</span>
              <Link
                to={`/projects/${slug}/documents/${parent.type}/${parent.doc_id}`}
                state={fromTree ? { from: "tree" } : undefined}
                className="hover:text-accent"
              >
                {parent.doc_id.split("-")[0]}
              </Link>
            </span>
          ))}
        </nav>

        <h1 className="font-display text-2xl font-bold text-text-primary">
          {doc.title}
        </h1>

        {/* Metadata bar */}
        <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-text-tertiary">
          <TypeBadge type={doc.type} />
          <span className="font-mono">{doc.file_path}</span>
          <span>Synced {formattedSync}</span>
        </div>

        {/* Markdown content */}
        <article className="prose prose-invert mt-6 max-w-none">
          <Markdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
          >
            {doc.content}
          </Markdown>
        </article>
      </div>

      {/* Sidebar */}
      <aside className="w-64 shrink-0">
        <div className="rounded-lg border border-border-default bg-bg-surface p-4">
          <h3 className="mb-3 font-display text-sm font-semibold text-text-primary">
            Properties
          </h3>

          <dl className="space-y-2 text-sm">
            <div>
              <dt className="text-text-tertiary">Status</dt>
              <dd className="mt-0.5">
                <StatusBadge status={doc.status} />
              </dd>
            </div>

            {doc.owner && (
              <div>
                <dt className="text-text-tertiary">Owner</dt>
                <dd className="text-text-primary">{doc.owner}</dd>
              </div>
            )}

            {doc.priority && (
              <div>
                <dt className="text-text-tertiary">Priority</dt>
                <dd className="text-text-primary">{doc.priority}</dd>
              </div>
            )}

            {doc.story_points != null && (
              <div>
                <dt className="text-text-tertiary">Story Points</dt>
                <dd className="text-text-primary">{doc.story_points}</dd>
              </div>
            )}

            {doc.epic && (
              <div>
                <dt className="text-text-tertiary">Epic</dt>
                <dd className="text-text-primary">{doc.epic}</dd>
              </div>
            )}

            {doc.story && (
              <div>
                <dt className="text-text-tertiary">Story</dt>
                <dd className="text-text-primary">{doc.story}</dd>
              </div>
            )}

            {doc.metadata &&
              Object.entries(doc.metadata).map(([key, value]) => (
                <div key={key}>
                  <dt className="text-text-tertiary capitalize">{key}</dt>
                  <dd className="text-text-primary">{value}</dd>
                </div>
              ))}
          </dl>
        </div>

        {/* Relationships panel */}
        {hasRelationships && (
          <div className="mt-4 rounded-lg border border-border-default bg-bg-surface p-4">
            <h3 className="mb-3 font-display text-sm font-semibold text-text-primary">
              Relationships
            </h3>

            {hasParents && (
              <div className="mb-3">
                <h4 className="mb-1 text-xs font-medium text-text-tertiary">
                  Parents
                </h4>
                <div className="-mx-2 space-y-0.5">
                  {related!.parents.map((p) => (
                    <RelatedDocLink key={p.doc_id} item={p} slug={slug!} fromTree={fromTree} />
                  ))}
                </div>
              </div>
            )}

            {hasChildren && (
              <div>
                <h4 className="mb-1 text-xs font-medium text-text-tertiary">
                  Children
                </h4>
                <div className="-mx-2 space-y-0.5">
                  {related!.children.map((c) => (
                    <RelatedDocLink key={c.doc_id} item={c} slug={slug!} fromTree={fromTree} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </aside>
    </div>
  );
}
