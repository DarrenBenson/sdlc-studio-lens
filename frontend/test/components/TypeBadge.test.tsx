/**
 * TypeBadge tests.
 * CR-01KX8YD6: friendly labels for the v3 artefact types.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TypeBadge } from "../../src/components/TypeBadge.tsx";

describe("TypeBadge", () => {
  it.each([
    ["cr", "CR"],
    ["rfc", "RFC"],
    ["retro", "Retro"],
    ["review", "Review"],
    ["decision", "Decision"],
    ["pvd", "PVD"],
    ["persona", "Persona"],
    ["workflow", "Workflow"],
  ])("renders friendly label %s -> %s", (type, label) => {
    render(<TypeBadge type={type} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it("still renders existing labels", () => {
    render(<TypeBadge type="test-spec" />);
    expect(screen.getByText("Test Spec")).toBeInTheDocument();
  });

  it("renders Unknown for a missing type", () => {
    render(<TypeBadge type={null} />);
    expect(screen.getByText("Unknown")).toBeInTheDocument();
  });
});
