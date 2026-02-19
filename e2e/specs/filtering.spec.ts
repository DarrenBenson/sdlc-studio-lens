import { expect, test } from "@playwright/test";

test.describe("Document Filtering", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/projects/e2e-test-project/documents");
  });

  test("filters by document type", async ({ page }) => {
    // Select Epic type
    await page.getByLabel("Type").selectOption("Epic");

    // Should only show epics
    await expect(page.getByRole("link", { name: "EP0001: Alpha Feature" })).toBeVisible();
    await expect(page.getByRole("link", { name: "EP0002: Beta Feature" })).toBeVisible();

    // Stories should not be visible
    await expect(
      page.getByRole("link", { name: "US0001: Create Widget" }),
    ).not.toBeVisible();
  });

  test("filters by status", async ({ page }) => {
    // Select Done status
    await page.getByLabel("Status").selectOption("Done");

    // Done documents should be visible
    await expect(page.getByRole("link", { name: "EP0001: Alpha Feature" })).toBeVisible();

    // Draft documents should not be visible
    await expect(
      page.getByRole("link", { name: "US0004: Widget Tests" }),
    ).not.toBeVisible();
  });

  test("combines type and status filters", async ({ page }) => {
    // Filter by Story type and Done status
    await page.getByLabel("Type").selectOption("Story");
    await page.getByLabel("Status").selectOption("Done");

    // Should show done stories only
    await expect(page.getByRole("link", { name: "US0001: Create Widget" })).toBeVisible();
    await expect(page.getByRole("link", { name: "US0002: Update Widget" })).toBeVisible();

    // In Progress story should not appear
    await expect(
      page.getByRole("link", { name: "US0003: Widget API" }),
    ).not.toBeVisible();
  });

  test("filter persists in URL params", async ({ page }) => {
    // Select Story type
    await page.getByLabel("Type").selectOption("Story");

    // URL should contain the type param
    await expect(page).toHaveURL(/[?&]type=story/);

    // Select Done status
    await page.getByLabel("Status").selectOption("Done");
    await expect(page).toHaveURL(/[?&]status=Done/i);
  });

  test("clear filter shows all documents", async ({ page }) => {
    // Apply a filter
    await page.getByLabel("Type").selectOption("Epic");

    // Verify filter is active (only 2 epics)
    await expect(page.getByText(/2 documents?\)/)).toBeVisible();

    // Clear the filter
    await page.getByLabel("Type").selectOption("All Types");

    // Should show all documents again
    await expect(page.getByText(/\(10 documents?\)/)).toBeVisible();
  });

  test("filter counts match displayed results", async ({ page }) => {
    // Filter by Story type
    await page.getByLabel("Type").selectOption("Story");

    // Count displayed rows (excluding header)
    const rows = page.getByRole("row").filter({ hasNotText: "Title" });
    const count = await rows.count();

    // Should match the count shown in pagination
    await expect(page.getByText(new RegExp(`${count} documents?\\)`))).toBeVisible();
  });
});
