/** Project detail statistics page. */
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { fetchProjectStats } from "../api/client.ts";
import { ProgressRing } from "../components/ProgressRing.tsx";
import { StatsCard } from "../components/StatsCard.tsx";
import { ChartTooltip } from "../components/ChartTooltip.tsx";
import { CHART_THEME, STATUS_COLOURS } from "../lib/chartTheme.ts";
import type { ProjectStats } from "../types/index.ts";

export function ProjectDetail() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    fetchProjectStats(slug)
      .then(setStats)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, [slug]);

  if (loading) {
    return <p className="p-6 text-text-secondary">Loading project stats...</p>;
  }

  if (error) {
    return (
      <div className="p-6">
        <p className="text-red-400 mb-4">Failed to load project: {error}</p>
        <button
          onClick={load}
          className="px-4 py-2 rounded-md bg-accent text-bg-base font-semibold"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!stats) return null;

  const TYPE_ORDER = [
    "prd", "trd", "tsd", "personas", "epic", "story",
    "plan", "test-spec", "workflow", "bug", "other",
  ];
  const TYPE_LABELS: Record<string, string> = {
    prd: "PRD", trd: "TRD", tsd: "TSD",
    personas: "Personas", epic: "Epics", story: "Stories",
    plan: "Plans", "test-spec": "Test Specs", workflow: "Workflows",
    bug: "Bugs", other: "Other",
  };
  const typeData = Object.entries(stats.by_type)
    .map(([name, value]) => ({
      name,
      label: TYPE_LABELS[name] ?? name.charAt(0).toUpperCase() + name.slice(1),
      value,
    }))
    .sort((a, b) => {
      const ai = TYPE_ORDER.indexOf(a.name);
      const bi = TYPE_ORDER.indexOf(b.name);
      return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
    });

  // Normalise verbose statuses and merge terminal states into "Done"
  const mergedStatus: Record<string, number> = {};
  for (const [key, count] of Object.entries(stats.by_status)) {
    // Strip parenthesised detail, e.g. "Complete (81/88 ...)" → "Complete"
    const base = key.replace(/\s*\(.*\)$/, "");
    const normalised = base === "Complete" || base === "Done" ? "Done" : base;
    mergedStatus[normalised] = (mergedStatus[normalised] ?? 0) + count;
  }

  const STATUS_ORDER = [
    "null", "Draft", "Ready", "Planned", "In Progress",
    "Review", "Active", "Done", "Won't Implement",
  ];
  const statusData = Object.entries(mergedStatus)
    .map(([name, value]) => ({
      name,
      label: name === "null" ? "No Status" : name,
      value,
      fill: STATUS_COLOURS[name] ?? (name === "Done" ? STATUS_COLOURS["Done"] : CHART_THEME.text),
    }))
    .sort((a, b) => {
      const ai = STATUS_ORDER.indexOf(a.name);
      const bi = STATUS_ORDER.indexOf(b.name);
      return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
    });

  return (
    <div className="p-6 space-y-8">
      {/* Project header */}
      <div className="flex items-center gap-6">
        <ProgressRing
          percentage={stats.completion_percentage}
          size={120}
          strokeWidth={10}
        />
        <div>
          <h1 className="font-display text-2xl font-bold text-text-primary">
            {stats.name}
          </h1>
          <p className="text-sm text-text-tertiary mt-1">
            {stats.last_synced_at
              ? `Synced ${new Date(stats.last_synced_at).toLocaleString()}`
              : "Never synced"}
          </p>
          <p className="text-sm text-text-secondary mt-1">
            {stats.total_documents} documents
          </p>
        </div>
      </div>

      {/* Per-type stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {typeData.map((entry) => (
          <Link
            key={entry.name}
            to={`/projects/${slug}/documents?type=${entry.name}`}
            className="block"
          >
            <StatsCard
              count={entry.value}
              label={entry.label}
            />
          </Link>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Type distribution chart */}
        <div className="rounded-lg bg-bg-surface border border-border-default p-5">
          <h2 className="font-display text-lg text-text-primary mb-4">
            Document Types
          </h2>
          <ResponsiveContainer width="100%" height={250} className="cursor-pointer">
            <BarChart
              data={typeData}
              onClick={(state) => {
                if (state?.activeTooltipIndex != null) {
                  const entry = typeData[Number(state.activeTooltipIndex)];
                  if (entry) void navigate(`/projects/${slug}/documents?type=${entry.name}`);
                }
              }}
            >
              <CartesianGrid stroke={CHART_THEME.grid} />
              <XAxis dataKey="label" stroke={CHART_THEME.text} />
              <YAxis stroke={CHART_THEME.text} />
              <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(163, 230, 53, 0.08)" }} />
              <Bar dataKey="value" fill={CHART_THEME.primary} name="Documents" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Status breakdown chart */}
        <div className="rounded-lg bg-bg-surface border border-border-default p-5">
          <h2 className="font-display text-lg text-text-primary mb-4">
            Status Breakdown
          </h2>
          <ResponsiveContainer width="100%" height={250} className="cursor-pointer">
            <BarChart
              data={statusData}
              onClick={(state) => {
                if (state?.activeTooltipIndex != null) {
                  const entry = statusData[Number(state.activeTooltipIndex)];
                  if (entry)
                    void navigate(`/projects/${slug}/documents?status=${entry.name === "null" ? "none" : entry.name}`);
                }
              }}
            >
              <CartesianGrid stroke={CHART_THEME.grid} />
              <XAxis dataKey="label" stroke={CHART_THEME.text} />
              <YAxis stroke={CHART_THEME.text} />
              <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(163, 230, 53, 0.08)" }} />
              <Bar dataKey="value" name="Documents">
                {statusData.map((entry) => (
                  <Cell key={entry.name} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
