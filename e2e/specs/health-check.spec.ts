import { expect, test } from "@playwright/test";

test.describe("Health Check", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/projects/e2e-test-project/health-check");
    // Wait for health check data to load
    await expect(page.getByText("Health Score")).toBeVisible();
  });

  test("health check page shows score ring", async ({ page }) => {
    // Score ring should be visible with an aria-label containing the score
    const scoreRing = page.locator("[aria-label^='Health score:']");
    await expect(scoreRing).toBeVisible();
  });

  test("score ring displays numeric score", async ({ page }) => {
    // The score ring should show a numeric value
    const scoreRing = page.locator("[aria-label^='Health score:']");
    const label = await scoreRing.getAttribute("aria-label");
    expect(label).toMatch(/Health score: \d+/);

    // "Health Score" label text should be visible
    await expect(page.getByText("Health Score")).toBeVisible();
  });

  test("findings grouped by category", async ({ page }) => {
    // The fixture data produces "Completeness" findings (missing plans/test-specs)
    await expect(
      page.getByRole("heading", { name: "Completeness" }),
    ).toBeVisible();
  });

  test("severity summary bar shows counts", async ({ page }) => {
    // Severity filter buttons should be visible
    const severities = ["Critical", "High", "Medium", "Low"];

    for (const severity of severities) {
      const button = page.getByTitle(`Filter by ${severity}`);
      await expect(button).toBeVisible();
    }

    // Clicking a severity button should filter findings
    await page.getByTitle("Filter by Medium").click();

    // Should show the active filter indicator or filtered text
    const clearButton = page.getByRole("button", { name: "Clear filter" });
    const filterText = page.getByText(/Showing \d+ Medium finding/);
    const noIssuesText = page.getByText("No Medium issues");

    // One of these should be visible after filtering
    await expect(filterText.or(noIssuesText).or(clearButton)).toBeVisible();
  });
});
