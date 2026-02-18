/** Project health check page. */
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";

import { fetchHealthCheck } from "../api/client.ts";
import { SeverityBadge } from "../components/SeverityBadge.tsx";
import type { HealthCheckResponse, HealthFinding } from "../types/index.ts";

type Severity = "critical" | "high" | "medium" | "low";

function scoreColour(score: number): string {
  if (score >= 80) return "#a3e635"; // green
  if (score >= 50) return "#f59e0b"; // amber
  return "#ef4444"; // red
}

function ScoreRing({ score }: { score: number }) {
  const size = 120;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const colour = scoreColour(score);

  return (
    <div className="flex flex-col items-center gap-1">
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        aria-label={`Health score: ${score}`}
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#1C2520"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colour}
          strokeWidth={strokeWidth}
          strokeDasharray={String(circumference)}
          strokeDashoffset={String(offset)}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
        <text
          x="50%"
          y="50%"
          dominantBaseline="central"
          textAnchor="middle"
          fill="#F0F6F0"
          fontFamily="'JetBrains Mono', monospace"
          fontWeight={700}
          fontSize={size * 0.22}
        >
          {score}
        </text>
      </svg>
      <span className="text-xs text-text-tertiary">Health Score</span>
    </div>
  );
}

function SummaryBar({
  summary,
  filter,
  onFilterChange,
}: {
  summary: Record<string, number>;
  filter: Severity | null;
  onFilterChange: (severity: Severity | null) => void;
}) {
  const items: Array<{ key: Severity; label: string; colour: string }> = [
    { key: "critical", label: "Critical", colour: "text-severity-critical" },
    { key: "high", label: "High", colour: "text-severity-high" },
    { key: "medium", label: "Medium", colour: "text-severity-medium" },
    { key: "low", label: "Low", colour: "text-severity-low" },
  ];

  return (
    <div className="flex items-center gap-6">
      {items.map((item) => {
        const isActive = filter === item.key;
        return (
          <button
            key={item.key}
            onClick={() => onFilterChange(isActive ? null : item.key)}
            className={`text-center px-3 py-2 rounded-lg transition-colors ${
              isActive
                ? "bg-bg-elevated border border-border-strong"
                : "hover:bg-bg-elevated border border-transparent"
            }`}
            aria-pressed={isActive}
            title={`Filter by ${item.label}`}
          >
            <span className={`font-mono text-2xl font-bold ${item.colour}`}>
              {summary[item.key] ?? 0}
            </span>
            <p className="text-xs text-text-tertiary mt-1">{item.label}</p>
          </button>
        );
      })}
    </div>
  );
}

function FindingCard({
  finding,
  slug,
}: {
  finding: HealthFinding;
  slug: string;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    void navigator.clipboard.writeText(finding.suggested_fix).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="rounded-lg bg-bg-surface border border-border-default p-4">
      <div className="flex items-start gap-3">
        <SeverityBadge severity={finding.severity} />
        <div className="flex-1 min-w-0">
          <p className="text-text-primary text-sm">{finding.message}</p>
          {finding.affected_documents.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {finding.affected_documents.map((doc) => (
                <Link
                  key={`${doc.doc_type}-${doc.doc_id}`}
                  to={`/projects/${slug}/documents/${doc.doc_type}/${doc.doc_id}`}
                  className="text-xs text-accent hover:text-accent-hover font-mono"
                >
                  {doc.doc_id}
                </Link>
              ))}
            </div>
          )}
          <div className="mt-3 rounded bg-bg-elevated border border-border-subtle p-3">
            <div className="flex items-start justify-between gap-2">
              <p className="text-xs text-text-secondary font-mono leading-relaxed">
                {finding.suggested_fix}
              </p>
              <button
                onClick={handleCopy}
                className="shrink-0 text-xs text-text-tertiary hover:text-accent px-2 py-1 rounded border border-border-subtle hover:border-accent/30"
                title="Copy suggested fix"
              >
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const CATEGORY_LABELS: Record<string, string> = {
  completeness: "Completeness",
  consistency: "Consistency",
  quality: "Quality",
  integrity: "Integrity",
};

const CATEGORY_ORDER = ["completeness", "consistency", "quality", "integrity"];

function groupByCategory(
  findings: HealthFinding[],
): Record<string, HealthFinding[]> {
  const grouped: Record<string, HealthFinding[]> = {};
  for (const finding of findings) {
    const cat = finding.category;
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(finding);
  }
  return grouped;
}

function buildCopyText(findings: HealthFinding[]): string {
  return findings
    .map(
      (f) =>
        `[${f.severity.toUpperCase()}] ${f.message}\n  Fix: ${f.suggested_fix}`,
    )
    .join("\n\n");
}

export function HealthCheck() {
  const { slug } = useParams<{ slug: string }>();
  const [data, setData] = useState<HealthCheckResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Severity | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);

  const load = () => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    fetchHealthCheck(slug)
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, [slug]);

  if (loading) {
    return (
      <p className="p-6 text-text-secondary">Running health check...</p>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <p className="text-red-400 mb-4">
          Failed to load health check: {error}
        </p>
        <button
          onClick={load}
          className="px-4 py-2 rounded-md bg-accent text-bg-base font-semibold"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const filtered = filter
    ? data.findings.filter((f) => f.severity === filter)
    : data.findings;
  const grouped = groupByCategory(filtered);
  const visibleCount = filtered.length;

  const handleCopyAll = () => {
    const text = buildCopyText(filtered);
    void navigator.clipboard.writeText(text).then(() => {
      setCopiedAll(true);
      setTimeout(() => setCopiedAll(false), 2000);
    });
  };

  return (
    <div className="p-6 space-y-8">
      {/* Breadcrumb */}
      <nav className="text-sm text-text-tertiary" aria-label="Breadcrumb">
        <Link to={`/projects/${slug}`} className="hover:text-accent">
          {slug}
        </Link>
        <span className="mx-2">/</span>
        <span className="text-text-primary">Health Check</span>
      </nav>

      {/* Score banner */}
      <div className="flex items-center gap-6">
        <ScoreRing score={data.score} />
        <div>
          <h1 className="font-display text-2xl font-bold text-text-primary">
            Health Check
          </h1>
          <p className="text-sm text-text-tertiary mt-1">
            {data.total_documents} documents analysed
          </p>
          <p className="text-sm text-text-tertiary">
            {new Date(data.checked_at).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Summary bar (clickable filters) */}
      <div className="rounded-lg bg-bg-surface border border-border-default p-5">
        <div className="flex items-center justify-between">
          <SummaryBar
            summary={data.summary}
            filter={filter}
            onFilterChange={setFilter}
          />
          {visibleCount > 0 && (
            <button
              onClick={handleCopyAll}
              className="text-sm text-text-tertiary hover:text-accent px-3 py-2 rounded border border-border-subtle hover:border-accent/30"
              title={`Copy all ${visibleCount} visible findings as text`}
            >
              {copiedAll
                ? "Copied!"
                : `Copy all${filter ? ` ${visibleCount}` : ""}`}
            </button>
          )}
        </div>
        {filter && (
          <p className="text-xs text-text-tertiary mt-3">
            Showing {visibleCount} {filter} finding
            {visibleCount !== 1 ? "s" : ""}.{" "}
            <button
              onClick={() => setFilter(null)}
              className="text-accent hover:text-accent-hover"
            >
              Clear filter
            </button>
          </p>
        )}
      </div>

      {/* Findings */}
      {filtered.length === 0 ? (
        <div className="rounded-lg bg-bg-surface border border-border-default p-8 text-center">
          <p className="text-text-primary text-lg font-display">
            {filter ? `No ${filter} issues` : "No issues found"}
          </p>
          <p className="text-text-tertiary text-sm mt-2">
            {filter
              ? "Try a different severity filter."
              : "All documentation checks passed."}
          </p>
        </div>
      ) : (
        CATEGORY_ORDER.filter((cat) => grouped[cat]?.length).map((cat) => (
          <div key={cat}>
            <h2 className="font-display text-lg text-text-primary mb-3">
              {CATEGORY_LABELS[cat] ?? cat}
            </h2>
            <div className="space-y-3">
              {grouped[cat].map((finding, idx) => (
                <FindingCard
                  key={`${finding.rule_id}-${idx}`}
                  finding={finding}
                  slug={slug!}
                />
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
