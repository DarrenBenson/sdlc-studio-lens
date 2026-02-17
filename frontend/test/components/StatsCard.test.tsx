/**
 * StatsCard component tests.
 * Test cases: TC0207-TC0208 from TS0020.
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { StatsCard } from "../../src/components/StatsCard";

// TC0207: StatsCard renders count and label
describe("StatsCard display", () => {
  it("renders count and label", () => {
    render(<StatsCard count={120} label="Stories" />);
    expect(screen.getByText("120")).toBeInTheDocument();
    expect(screen.getByText("Stories")).toBeInTheDocument();
  });
});

// TC0208: StatsCard click handler fires
describe("StatsCard click", () => {
  it("fires onClick when clicked", async () => {
    const onClick = vi.fn();
    render(<StatsCard count={42} label="Epics" onClick={onClick} />);
    await userEvent.click(screen.getByText("42"));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
