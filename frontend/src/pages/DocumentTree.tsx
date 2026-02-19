import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";

import { fetchAllDocuments } from "../api/client.ts";
import { StatusBadge } from "../components/StatusBadge.tsx";
import { TypeBadge } from "../components/TypeBadge.tsx";
import type { TreeNode } from "../lib/buildTree.ts";
import { buildTree } from "../lib/buildTree.ts";

// ---------------------------------------------------------------------------
// Tree node component
// ---------------------------------------------------------------------------

function TreeNodeRow({
  node,
  slug,
  depth,
  expanded,
  onToggle,
}: {
  node: TreeNode;
  slug: string;
  depth: number;
  expanded: Set<string>;
  onToggle: (docId: string) => void;
}): React.JSX.Element {
  const hasChildren = node.children.length > 0;
  const isExpanded = expanded.has(node.doc_id);

  return (
    <div>
      <div
        className="flex items-center gap-2 rounded px-2 py-1 hover:bg-bg-elevated"
        style={{ paddingLeft: `${depth * 20 + 8}px` }}
      >
        {hasChildren ? (
          <button
            onClick={() => onToggle(node.doc_id)}
            className="flex h-5 w-5 shrink-0 items-center justify-center rounded text-text-tertiary hover:text-text-primary"
            aria-label={isExpanded ? "Collapse" : "Expand"}
          >
            <svg
              className={`h-3 w-3 transition-transform ${isExpanded ? "rotate-90" : ""}`}
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        ) : (
          <span className="w-5 shrink-0" />
        )}

        <TypeBadge type={node.type} />

        <Link
          to={`/projects/${slug}/documents/${node.type}/${node.doc_id}`}
          state={{ from: "tree" }}
          className="min-w-0 flex-1 truncate text-sm text-text-primary hover:text-accent"
        >
          {node.title}
        </Link>

        <StatusBadge status={node.status} />

        {hasChildren && (
          <span className="shrink-0 text-xs text-text-tertiary">
            {node.children.length}
          </span>
        )}
      </div>

      {hasChildren && isExpanded && (
        <div>
          {node.children.map((child) => (
            <TreeNodeRow
              key={child.doc_id}
              node={child}
              slug={slug}
              depth={depth + 1}
              expanded={expanded}
              onToggle={onToggle}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export function DocumentTree(): React.JSX.Element {
  const { slug } = useParams<{ slug: string }>();
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    fetchAllDocuments(slug)
      .then((items) => {
        const roots = buildTree(items);
        setTree(roots);
        // Start fully collapsed
        setExpanded(new Set());
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Unknown error");
      })
      .finally(() => setLoading(false));
  }, [slug]);

  const handleToggle = (docId: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(docId)) {
        next.delete(docId);
      } else {
        next.add(docId);
      }
      return next;
    });
  };

  if (loading) {
    return (
      <div className="text-text-secondary">
        <p>Loading document tree...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-text-secondary">
        <p className="text-status-blocked">Error: {error}</p>
        <Link
          to={`/projects/${slug}`}
          className="mt-2 inline-block text-accent hover:text-accent-hover"
        >
          Back to project
        </Link>
      </div>
    );
  }

  return (
    <div>
      <nav className="mb-4 flex items-center gap-1 text-sm text-text-tertiary">
        <Link to={`/projects/${slug}`} className="hover:text-accent">
          Project
        </Link>
        <span>/</span>
        <span className="text-text-primary">Tree View</span>
      </nav>

      <div className="mb-4 flex items-center justify-between">
        <h1 className="font-display text-2xl font-bold text-text-primary">
          Document Hierarchy
        </h1>
        {tree.length > 0 && (
          <div className="flex gap-2">
            <button
              onClick={() => {
                const all = new Set<string>();
                const collect = (nodes: TreeNode[]) => {
                  for (const n of nodes) {
                    if (n.children.length > 0) {
                      all.add(n.doc_id);
                      collect(n.children);
                    }
                  }
                };
                collect(tree);
                setExpanded(all);
              }}
              className="rounded border border-border-default px-3 py-1 text-sm text-text-secondary hover:bg-bg-elevated hover:text-text-primary"
            >
              Expand all
            </button>
            <button
              onClick={() => setExpanded(new Set())}
              className="rounded border border-border-default px-3 py-1 text-sm text-text-secondary hover:bg-bg-elevated hover:text-text-primary"
            >
              Collapse all
            </button>
          </div>
        )}
      </div>

      {tree.length === 0 ? (
        <div className="rounded-lg border border-border-default bg-bg-surface p-6 text-center text-text-secondary">
          <p>No documents synced yet.</p>
          <Link
            to={`/projects/${slug}`}
            className="mt-2 inline-block text-accent hover:text-accent-hover"
          >
            Go to project to trigger sync
          </Link>
        </div>
      ) : (
        <div className="rounded-lg border border-border-default bg-bg-surface py-2">
          {tree.map((node) => (
            <TreeNodeRow
              key={node.doc_id}
              node={node}
              slug={slug!}
              depth={0}
              expanded={expanded}
              onToggle={handleToggle}
            />
          ))}
        </div>
      )}
    </div>
  );
}
