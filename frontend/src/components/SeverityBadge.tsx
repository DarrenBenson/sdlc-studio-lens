const SEVERITY_CLASSES: Record<string, string> = {
  critical: "bg-severity-critical/15 text-severity-critical",
  high: "bg-severity-high/15 text-severity-high",
  medium: "bg-severity-medium/15 text-severity-medium",
  low: "bg-severity-low/15 text-severity-low",
};

const DEFAULT_CLASS = "bg-badge-default/15 text-badge-default";

interface SeverityBadgeProps {
  severity: string;
}

export function SeverityBadge({ severity }: SeverityBadgeProps): React.JSX.Element {
  const colourClass = SEVERITY_CLASSES[severity] ?? DEFAULT_CLASS;

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 font-mono text-xs font-medium uppercase ${colourClass}`}
    >
      {severity}
    </span>
  );
}
