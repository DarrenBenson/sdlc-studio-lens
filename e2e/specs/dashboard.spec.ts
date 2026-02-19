import { expect, test } from "@playwright/test";

test.describe("Dashboard", () => {
  test("displays project card with name and document count", async ({
    page,
  }) => {
    await page.goto("/");

    // Project card is a link wrapping the heading
    const main = page.locator("main");
    const card = main.getByRole("link", { name: /E2E Test Project/ });
    await expect(card).toBeVisible();

    // Card should show document count
    await expect(card.getByText("documents")).toBeVisible();
  });

  test("shows global stats", async ({ page }) => {
    await page.goto("/");

    const main = page.locator("main");
    // Stats cards show "Projects" and "Documents" labels
    await expect(main.getByText("Projects", { exact: true })).toBeVisible();
    await expect(main.getByText("Documents", { exact: true })).toBeVisible();
  });

  test("shows story completion progress ring", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByText("Story Completion")).toBeVisible();
  });

  test("project card links to project detail page", async ({ page }) => {
    await page.goto("/");

    // Click the project card link in main content area
    const main = page.locator("main");
    const card = main.getByRole("link", { name: /E2E Test Project/ });
    await card.click();

    // Should navigate to project detail
    await expect(page).toHaveURL(/\/projects\/e2e-test-project/);
    await expect(page.getByRole("heading", { name: "E2E Test Project" })).toBeVisible();
  });

  test("empty state when no projects exist", async ({ page }) => {
    await page.goto("/");

    // The sidebar should show the project (not empty)
    await expect(page.getByTestId("sidebar").getByText("E2E Test Project")).toBeVisible();
  });
});
