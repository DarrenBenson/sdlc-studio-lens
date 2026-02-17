const STATUS_CLASSES: Record<string, string> = {
  Done: "bg-badge-done/15 text-badge-done",
  "In Progress": "bg-badge-progress/15 text-badge-progress",
  Draft: "bg-badge-draft/15 text-badge-draft",
  Blocked: "bg-badge-blocked/15 text-badge-blocked",
  "Not Started": "bg-badge-draft/15 text-badge-draft",
  Review: "bg-badge-review/15 text-badge-review",
  Ready: "bg-badge-ready/15 text-badge-ready",
  Planned: "bg-badge-planned/15 text-badge-planned",
};

const DEFAULT_CLASS = "bg-badge-default/15 text-badge-default";

interface StatusBadgeProps {
  status?: string | null;
}

export function StatusBadge({ status }: StatusBadgeProps): React.JSX.Element {
  const trimmed = status?.trim() || "Unknown";
  const colourClass = STATUS_CLASSES[trimmed] ?? DEFAULT_CLASS;

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 font-mono text-xs font-medium ${colourClass}`}
    >
      {trimmed}
    </span>
  );
}
