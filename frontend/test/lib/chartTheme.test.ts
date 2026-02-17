/**
 * Chart theme tests.
 * Test cases: TC0206, TC0209 from TS0020.
 */
import { describe, expect, it } from "vitest";
import { CHART_THEME, STATUS_COLOURS } from "../../src/lib/chartTheme";

// TC0206: Chart theme exports correct keys
describe("CHART_THEME", () => {
  it("has required keys", () => {
    expect(CHART_THEME).toHaveProperty("background");
    expect(CHART_THEME).toHaveProperty("text");
    expect(CHART_THEME).toHaveProperty("grid");
    expect(CHART_THEME).toHaveProperty("primary");
  });
});

// TC0209: STATUS_COLOURS match brand guide
describe("STATUS_COLOURS", () => {
  it("matches brand guide values", () => {
    expect(STATUS_COLOURS["Done"]).toBe("#A3E635");
    expect(STATUS_COLOURS["In Progress"]).toBe("#3B82F6");
    expect(STATUS_COLOURS["Draft"]).toBe("#78909C");
    expect(STATUS_COLOURS["Blocked"]).toBe("#EF4444");
  });
});
