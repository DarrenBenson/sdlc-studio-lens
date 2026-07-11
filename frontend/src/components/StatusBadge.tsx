const DONE = "bg-badge-done/15 text-badge-done";
const PROGRESS = "bg-badge-progress/15 text-badge-progress";
const DRAFT = "bg-badge-draft/15 text-badge-draft";
const BLOCKED = "bg-badge-blocked/15 text-badge-blocked";
const REVIEW = "bg-badge-review/15 text-badge-review";
const READY = "bg-badge-ready/15 text-badge-ready";
const PLANNED = "bg-badge-planned/15 text-badge-planned";
const INBOX = "bg-badge-inbox/15 text-badge-inbox";

// Full schema-v3 vocabulary across all artefact types, grouped by lifecycle stage.
const STATUS_CLASSES: Record<string, string> = {
  // Terminal / complete
  Done: DONE,
  Complete: DONE,
  Fixed: DONE,
  Verified: DONE,
  Closed: DONE,
  Accepted: DONE,
  // In-flight
  "In Progress": PROGRESS,
  Planning: PROGRESS,
  Implementing: PROGRESS,
  Testing: PROGRESS,
  Verifying: PROGRESS,
  Reviewing: PROGRESS,
  Checking: PROGRESS,
  "In Review": PROGRESS,
  // Review / awaiting
  Review: REVIEW,
  // Ready / approved
  Ready: READY,
  Approved: READY,
  // Planned / created
  Planned: PLANNED,
  Created: PLANNED,
  // Draft / proposed (not started)
  Draft: DRAFT,
  Proposed: DRAFT,
  "Not Started": DRAFT,
  // Triage lane
  inbox: INBOX,
  // Blocked / rejected / abandoned
  Blocked: BLOCKED,
  Rejected: BLOCKED,
  "Won't Fix": BLOCKED,
  "Won't Implement": BLOCKED,
  Withdrawn: BLOCKED,
  // Inactive (deferred/paused/superseded) - muted grey
  Deferred: DRAFT,
  Paused: DRAFT,
  Superseded: DRAFT,
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
