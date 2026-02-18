/** Multi-project dashboard page. */
import { useEffect, useState } from "react";
import { Link } from "react-router";

import { fetchAggregateStats } from "../api/client.ts";
import { ProgressRing } from "../components/ProgressRing.tsx";
import { StatsCard } from "../components/StatsCard.tsx";
import type { AggregateStats } from "../types/index.ts";

export function Dashboard() {
  const [stats, setStats] = useState<AggregateStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    setError(null);
    fetchAggregateStats()
      .then(setStats)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  if (loading) {
    return <p className="p-6 text-text-secondary">Loading dashboard...</p>;
  }

  if (error) {
    return (
      <div className="p-6">
        <p className="text-red-400 mb-4">Failed to load dashboard: {error}</p>
        <button
          onClick={load}
          className="px-4 py-2 rounded-md bg-accent text-bg-base font-semibold"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!stats || stats.total_projects === 0) {
    return (
      <div className="p-6 text-center">
        <p className="text-text-secondary text-lg mb-4">
          No projects registered
        </p>
        <Link
          to="/settings"
          className="text-accent hover:text-accent-hover underline"
        >
          Go to Settings to add a project
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-8">
      {/* Aggregate summary */}
      <div className="flex gap-6 items-center">
        <StatsCard count={stats.total_projects} label="Projects" />
        <StatsCard count={stats.total_documents} label="Documents" />
        <ProgressRing
          percentage={stats.completion_percentage}
          size={64}
          label="Story Completion"
        />
      </div>

      {/* Project cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {stats.projects.map((proj) => (
          <Link
            key={proj.slug}
            to={`/projects/${proj.slug}`}
            className="rounded-lg bg-bg-surface border border-border-default p-5 hover:border-accent transition-colors block"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display text-lg text-text-primary">
                {proj.name}
              </h3>
              <ProgressRing
                percentage={proj.completion_percentage}
                size={48}
                strokeWidth={6}
                label="Stories"
              />
            </div>
            <div className="flex gap-4 text-sm text-text-secondary">
              <span className="font-mono">{proj.total_documents}</span>
              <span>documents</span>
            </div>
            <div className="mt-2 text-xs text-text-tertiary">
              {proj.last_synced_at
                ? `Synced ${new Date(proj.last_synced_at).toLocaleString()}`
                : "Never synced"}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
