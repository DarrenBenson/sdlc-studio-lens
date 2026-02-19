import { expect, test } from "@playwright/test";

test.describe("Document View", () => {
  test("renders markdown content", async ({ page }) => {
    await page.goto(
      "/projects/e2e-test-project/documents/story/US0001-create-widget",
    );

    // Should render the document heading
    await expect(
      page.getByRole("heading", { name: "US0001: Create Widget" }),
    ).toBeVisible();

    // Should render markdown body content
    await expect(page.getByRole("heading", { name: "User Story" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Acceptance Criteria" })).toBeVisible();
  });

  test("shows frontmatter metadata", async ({ page }) => {
    await page.goto(
      "/projects/e2e-test-project/documents/story/US0001-create-widget",
    );

    // Properties panel in the sidebar (complementary role)
    const sidebar = page.getByRole("complementary").last();
    await expect(sidebar.getByRole("heading", { name: "Properties" })).toBeVisible();

    // Status shown as definition term/value
    await expect(sidebar.getByRole("term").filter({ hasText: "Status" })).toBeVisible();
    await expect(sidebar.getByText("Alice")).toBeVisible();
  });

  test("breadcrumb shows hierarchy", async ({ page }) => {
    await page.goto(
      "/projects/e2e-test-project/documents/story/US0001-create-widget",
    );

    // Breadcrumb navigation in the main content (not sidebar)
    const main = page.locator("main");
    await expect(main.getByRole("link", { name: "Project", exact: true })).toBeVisible();
    await expect(main.getByRole("link", { name: "Documents", exact: true })).toBeVisible();
  });

  test("related documents panel shows parent", async ({ page }) => {
    await page.goto(
      "/projects/e2e-test-project/documents/story/US0001-create-widget",
    );

    // Relationships section in the sidebar
    const sidebar = page.getByRole("complementary").last();
    await expect(sidebar.getByRole("heading", { name: "Relationships" })).toBeVisible();
    await expect(sidebar.getByRole("heading", { name: "Parents" })).toBeVisible();
    await expect(
      sidebar.getByRole("link", { name: /EP0001: Alpha Feature/ }),
    ).toBeVisible();
  });

  test("navigation links work - click parent epic from story", async ({
    page,
  }) => {
    await page.goto(
      "/projects/e2e-test-project/documents/story/US0001-create-widget",
    );

    // Click on the parent epic link in relationships sidebar
    const sidebar = page.getByRole("complementary").last();
    await sidebar.getByRole("link", { name: /EP0001: Alpha Feature/ }).click();

    // Should navigate to the epic's detail view
    await expect(page).toHaveURL(
      /\/projects\/e2e-test-project\/documents\/epic\/EP0001-alpha-feature/,
    );
    await expect(
      page.getByRole("heading", { name: "EP0001: Alpha Feature" }),
    ).toBeVisible();
  });
});
