import { StatusBadge } from "./StatusBadge.tsx";
import type { DocMetaField } from "../lib/docMetadata.ts";

interface DocumentMetaCardProps {
  fields: DocMetaField[];
}

/**
 * Renders the leading artefact metadata (parsed from the `> **Field:** value`
 * blockquote) as a compact structured panel above the prose. The Status field
 * is shown via the shared StatusBadge; everything else is a labelled value.
 */
export function DocumentMetaCard({
  fields,
}: DocumentMetaCardProps): React.JSX.Element | null {
  if (fields.length === 0) return null;

  return (
    <dl
      data-testid="doc-metadata-card"
      className="mt-6 grid grid-cols-2 gap-x-6 gap-y-3 rounded-lg border border-border-default bg-bg-surface p-4 sm:grid-cols-3"
    >
      {fields.map((field) => (
        <div key={field.key} className="min-w-0">
          <dt className="text-xs font-medium uppercase tracking-wide text-text-tertiary">
            {field.label}
          </dt>
          <dd className="mt-1 text-sm text-text-primary">
            {field.label.toLowerCase() === "status" ? (
              <StatusBadge status={field.value} />
            ) : (
              <span className="break-words">{field.value}</span>
            )}
          </dd>
        </div>
      ))}
    </dl>
  );
}
