import { expect, test } from "@playwright/test";

test.describe("Search", () => {
  test("search bar visible in header", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByPlaceholder("Search documents..."),
    ).toBeVisible();
  });

  test("search returns matching documents", async ({ page }) => {
    await page.goto("/");

    // Type a search query and press Enter
    const searchInput = page.getByPlaceholder("Search documents...");
    await searchInput.fill("widget");
    await searchInput.press("Enter");

    // Should navigate to search results
    await expect(page).toHaveURL(/\/search\?q=widget/);

    // Should show results
    await expect(page.getByText(/result.*for "widget"/i)).toBeVisible();
  });

  test("search highlights matching terms in results", async ({ page }) => {
    await page.goto("/search?q=widget");

    // Wait for results to load
    await expect(page.getByText(/result.*for "widget"/i)).toBeVisible();

    // Results should contain highlighted terms (rendered as <mark> elements)
    const marks = page.locator("mark");
    await expect(marks.first()).toBeVisible();
  });

  test("search with no results shows empty state", async ({ page }) => {
    await page.goto("/search?q=xyznonexistentterm123");

    await expect(
      page.getByText(/No results found for "xyznonexistentterm123"/),
    ).toBeVisible();
  });

  test("search navigates to results page", async ({ page }) => {
    await page.goto("/");

    const searchInput = page.getByPlaceholder("Search documents...");
    await searchInput.fill("alpha");
    await searchInput.press("Enter");

    await expect(page).toHaveURL(/\/search\?q=alpha/);
    await expect(page.getByText(/result.*for "alpha"/i)).toBeVisible();
  });

  test("search by document ID", async ({ page }) => {
    await page.goto("/search?q=US0001");

    // Should find the document by its ID
    await expect(page.getByText(/result.*for "US0001"/i)).toBeVisible();
    await expect(
      page.getByRole("link", { name: "US0001: Create Widget" }),
    ).toBeVisible();
  });
});
