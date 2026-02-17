/**
 * StatusBadge and TypeBadge component tests.
 *
 * Test cases: TC0136-TC0144 from TS0016.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "./StatusBadge.tsx";
import { TypeBadge } from "./TypeBadge.tsx";

// ---------------------------------------------------------------------------
// TC0136: StatusBadge renders "Done" with green colour
// ---------------------------------------------------------------------------

describe("TC0136: StatusBadge done colour", () => {
  it("displays Done text", () => {
    render(<StatusBadge status="Done" />);
    expect(screen.getByText("Done")).toBeInTheDocument();
  });

  it("has green colour class", () => {
    render(<StatusBadge status="Done" />);
    const badge = screen.getByText("Done");
    expect(badge.className).toMatch(/done/i);
  });
});

// ---------------------------------------------------------------------------
// TC0137: All 8 status colours render correctly
// ---------------------------------------------------------------------------

describe("TC0137: All status colours", () => {
  const cases: [string, RegExp][] = [
    ["Done", /done/i],
    ["In Progress", /progress/i],
    ["Draft", /draft/i],
    ["Blocked", /blocked/i],
    ["Not Started", /draft/i],
    ["Review", /review/i],
    ["Ready", /ready/i],
    ["Planned", /planned/i],
  ];

  it.each(cases)("renders %s with correct colour class", (status, pattern) => {
    render(<StatusBadge status={status} />);
    const badge = screen.getByText(status);
    expect(badge.className).toMatch(pattern);
  });
});

// ---------------------------------------------------------------------------
// TC0138: Unknown status shows grey fallback
// ---------------------------------------------------------------------------

describe("TC0138: Unknown status fallback", () => {
  it("displays the unknown status text", () => {
    render(<StatusBadge status="Custom Status" />);
    expect(screen.getByText("Custom Status")).toBeInTheDocument();
  });

  it("uses default/fallback colour class", () => {
    render(<StatusBadge status="Custom Status" />);
    const badge = screen.getByText("Custom Status");
    expect(badge.className).toMatch(/default/i);
  });
});

// ---------------------------------------------------------------------------
// TC0139: Null status renders "Unknown"
// ---------------------------------------------------------------------------

describe("TC0139: Null status", () => {
  it("shows Unknown for null", () => {
    render(<StatusBadge status={null} />);
    expect(screen.getByText("Unknown")).toBeInTheDocument();
  });

  it("shows Unknown for undefined", () => {
    render(<StatusBadge />);
    expect(screen.getByText("Unknown")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0140: Status with whitespace is trimmed
// ---------------------------------------------------------------------------

describe("TC0140: Whitespace trimming", () => {
  it("trims whitespace from status", () => {
    render(<StatusBadge status="  Done  " />);
    expect(screen.getByText("Done")).toBeInTheDocument();
  });

  it("applies correct colour after trimming", () => {
    render(<StatusBadge status="  Done  " />);
    const badge = screen.getByText("Done");
    expect(badge.className).toMatch(/done/i);
  });
});

// ---------------------------------------------------------------------------
// TC0141: TypeBadge renders correct labels
// ---------------------------------------------------------------------------

describe("TC0141: TypeBadge labels", () => {
  const cases: [string, string][] = [
    ["epic", "Epic"],
    ["story", "Story"],
    ["bug", "Bug"],
    ["plan", "Plan"],
    ["test-spec", "Test Spec"],
    ["prd", "PRD"],
    ["trd", "TRD"],
    ["tsd", "TSD"],
    ["other", "Other"],
  ];

  it.each(cases)("renders %s as %s", (type, label) => {
    render(<TypeBadge type={type} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0142: TypeBadge unknown type capitalised
// ---------------------------------------------------------------------------

describe("TC0142: Unknown type capitalised", () => {
  it("capitalises unknown type", () => {
    render(<TypeBadge type="workflow" />);
    expect(screen.getByText("Workflow")).toBeInTheDocument();
  });

  it("capitalises multi-word unknown type", () => {
    render(<TypeBadge type="custom-doc" />);
    expect(screen.getByText("Custom-doc")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0143: TypeBadge null fallback
// ---------------------------------------------------------------------------

describe("TC0143: TypeBadge null", () => {
  it("shows Unknown for null type", () => {
    render(<TypeBadge type={null} />);
    expect(screen.getByText("Unknown")).toBeInTheDocument();
  });

  it("shows Unknown for undefined type", () => {
    render(<TypeBadge />);
    expect(screen.getByText("Unknown")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// TC0144: StatusBadge accessibility
// ---------------------------------------------------------------------------

describe("TC0144: Badge accessibility", () => {
  it("status text is visible and findable", () => {
    render(<StatusBadge status="Done" />);
    const badge = screen.getByText("Done");
    expect(badge).toBeVisible();
  });

  it("badge is not aria-hidden", () => {
    render(<StatusBadge status="In Progress" />);
    const badge = screen.getByText("In Progress");
    expect(badge).not.toHaveAttribute("aria-hidden", "true");
  });
});
