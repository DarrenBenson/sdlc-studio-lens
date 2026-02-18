/** Circular progress ring SVG component. */

interface ProgressRingProps {
  percentage: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}

export function ProgressRing({
  percentage,
  size = 80,
  strokeWidth = 8,
  label,
}: ProgressRingProps) {
  const clamped = Math.min(100, Math.max(0, percentage));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;

  const displayText =
    clamped === Math.floor(clamped)
      ? `${clamped}%`
      : `${Number(clamped.toFixed(1))}%`;

  const ariaText = label ? `${label}: ${displayText}` : `${displayText} complete`;

  return (
    <div className="flex flex-col items-center gap-1">
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      aria-label={ariaText}
    >
      {/* Track */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="#1C2520"
        strokeWidth={strokeWidth}
      />
      {/* Progress arc */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="#A3E635"
        strokeWidth={strokeWidth}
        strokeDasharray={String(circumference)}
        strokeDashoffset={String(offset)}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      {/* Percentage text */}
      <text
        x="50%"
        y="50%"
        dominantBaseline="central"
        textAnchor="middle"
        fill="#F0F6F0"
        fontFamily="'JetBrains Mono', monospace"
        fontWeight={700}
        fontSize={size * 0.2}
      >
        {displayText}
      </text>
    </svg>
    {label && (
      <span className="text-xs text-text-tertiary">{label}</span>
    )}
    </div>
  );
}
