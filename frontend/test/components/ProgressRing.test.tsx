/**
 * ProgressRing component tests.
 * Test cases: TC0200-TC0205 from TS0020.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProgressRing } from "../../src/components/ProgressRing";

// TC0200: ProgressRing renders percentage text
describe("ProgressRing percentage text", () => {
  it("renders percentage value", () => {
    render(<ProgressRing percentage={85.5} />);
    expect(screen.getByText("85.5%")).toBeInTheDocument();
  });
});

// TC0201: ProgressRing SVG arc present
describe("ProgressRing SVG structure", () => {
  it("contains SVG with circle elements", () => {
    const { container } = render(<ProgressRing percentage={50} />);
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
    // Track circle + progress circle
    const circles = container.querySelectorAll("circle");
    expect(circles.length).toBe(2);
  });
});

// TC0202: ProgressRing 0% shows empty ring
describe("ProgressRing 0%", () => {
  it("displays 0% text", () => {
    render(<ProgressRing percentage={0} />);
    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  it("progress arc has zero stroke-dashoffset equal to circumference", () => {
    const { container } = render(<ProgressRing percentage={0} />);
    const circles = container.querySelectorAll("circle");
    const progressCircle = circles[1];
    // strokeDashoffset should equal strokeDasharray (full offset = empty)
    const dashArray = progressCircle.getAttribute("stroke-dasharray");
    const dashOffset = progressCircle.getAttribute("stroke-dashoffset");
    expect(dashArray).toBe(dashOffset);
  });
});

// TC0203: ProgressRing 100% shows full ring
describe("ProgressRing 100%", () => {
  it("displays 100% text", () => {
    render(<ProgressRing percentage={100} />);
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("progress arc has zero dashoffset", () => {
    const { container } = render(<ProgressRing percentage={100} />);
    const circles = container.querySelectorAll("circle");
    const progressCircle = circles[1];
    const dashOffset = progressCircle.getAttribute("stroke-dashoffset");
    expect(dashOffset).toBe("0");
  });
});

// TC0204: ProgressRing clamps > 100
describe("ProgressRing clamp over 100", () => {
  it("displays 100% for percentage > 100", () => {
    render(<ProgressRing percentage={150} />);
    expect(screen.getByText("100%")).toBeInTheDocument();
  });
});

// TC0205: ProgressRing clamps negative
describe("ProgressRing clamp negative", () => {
  it("displays 0% for negative percentage", () => {
    render(<ProgressRing percentage={-10} />);
    expect(screen.getByText("0%")).toBeInTheDocument();
  });
});
