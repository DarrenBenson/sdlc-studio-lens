/** Stats card component displaying a count and label. */

interface StatsCardProps {
  count: number;
  label: string;
  onClick?: () => void;
}

export function StatsCard({ count, label, onClick }: StatsCardProps) {
  const Tag = onClick ? "button" : "div";

  return (
    <Tag
      className="rounded-lg bg-bg-surface p-4 text-center cursor-pointer hover:bg-bg-elevated transition-colors"
      onClick={onClick}
    >
      <div className="font-mono text-2xl font-bold text-text-primary">
        {count}
      </div>
      <div className="text-sm text-text-secondary mt-1">{label}</div>
    </Tag>
  );
}
