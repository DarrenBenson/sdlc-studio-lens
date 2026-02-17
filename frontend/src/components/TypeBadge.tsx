const TYPE_LABELS: Record<string, string> = {
  epic: "Epic",
  story: "Story",
  bug: "Bug",
  plan: "Plan",
  "test-spec": "Test Spec",
  prd: "PRD",
  trd: "TRD",
  tsd: "TSD",
  other: "Other",
};

interface TypeBadgeProps {
  type?: string | null;
}

export function TypeBadge({ type }: TypeBadgeProps): React.JSX.Element {
  let label: string;
  if (!type) {
    label = "Unknown";
  } else if (type in TYPE_LABELS) {
    label = TYPE_LABELS[type];
  } else {
    label = type.charAt(0).toUpperCase() + type.slice(1);
  }

  return (
    <span className="inline-flex items-center rounded-md border border-border-default bg-bg-elevated px-2 py-0.5 font-mono text-xs text-text-secondary">
      {label}
    </span>
  );
}
