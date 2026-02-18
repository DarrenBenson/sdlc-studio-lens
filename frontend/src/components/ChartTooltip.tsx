/** Custom Recharts tooltip matching the dark brand theme. */

interface ChartTooltipProps {
  active?: boolean;
  payload?: Array<{ value?: number; name?: string }>;
  label?: string | number;
}

export function ChartTooltip({ active, payload, label }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;

  const value = payload[0].value ?? 0;
  const displayLabel =
    label === "null" ? "No Status" : String(label ?? payload[0].name ?? "");

  return (
    <div className="rounded-md border border-border-default bg-bg-surface px-3 py-2 shadow-lg">
      <p className="font-display text-sm font-semibold text-text-primary capitalize">
        {displayLabel}
      </p>
      <p className="font-mono text-sm text-accent">
        {value.toLocaleString()}
        <span className="ml-1.5 text-text-tertiary font-sans font-normal">
          documents
        </span>
      </p>
    </div>
  );
}
