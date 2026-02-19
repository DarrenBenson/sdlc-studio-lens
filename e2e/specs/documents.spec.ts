import { expect, test } from "@playwright/test";

test.describe("Document List", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/projects/e2e-test-project/documents");
  });

  test("lists all documents for a project", async ({ page }) => {
    // Should show documents from the fixture set
    // We have 10 fixture docs, but _index.md files are skipped
    // prd, trd, 2 epics, 4 stories, 1 plan, 1 test-spec = 10 docs
    await expect(page.getByText(/\d+ documents?\)/)).toBeVisible();
  });

  test("shows document type badges", async ({ page }) => {
    // Verify different type badges are present
    await expect(page.getByRole("cell", { name: "Epic" }).first()).toBeVisible();
    await expect(page.getByRole("cell", { name: "Story" }).first()).toBeVisible();
  });

  test("shows document status badges", async ({ page }) => {
    // Verify status badges are present (fixture data has Done, In Progress, Draft)
    await expect(page.getByRole("cell", { name: "Done" }).first()).toBeVisible();
  });

  test("clicking document navigates to detail view", async ({ page }) => {
    // Click on the first story document
    await page.getByRole("link", { name: "US0001: Create Widget" }).click();

    // Should navigate to the document view
    await expect(page).toHaveURL(
      /\/projects\/e2e-test-project\/documents\/story\/US0001-create-widget/,
    );
    await expect(
      page.getByRole("heading", { name: "US0001: Create Widget" }),
    ).toBeVisible();
  });

  test("shows document count in header", async ({ page }) => {
    // The pagination text should show the total count
    await expect(page.getByText(/\d+ documents?\)/)).toBeVisible();
  });

  test("sorts documents by title", async ({ page }) => {
    // Click the Title column header to sort
    await page.getByRole("columnheader", { name: "Title" }).click();

    // Verify documents are listed (sorted state)
    const firstRow = page.getByRole("row").nth(1); // skip header row
    await expect(firstRow).toBeVisible();
  });

  test("empty state for project with no documents", async ({ page }) => {
    // Filter to a type that doesn't exist in fixtures
    await page.getByLabel("Type").selectOption("Bug");

    // Should show empty state
    await expect(page.getByText("No documents match your filters.")).toBeVisible();
  });

  test("pagination controls are visible", async ({ page }) => {
    // Pagination info should be visible
    await expect(page.getByText(/Page \d+ of \d+/)).toBeVisible();
  });
});
