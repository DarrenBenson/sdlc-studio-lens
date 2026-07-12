import { expect, test } from "@playwright/test";

test.describe("Settings - Project Management", () => {
  test("adds a new project via form", async ({ page }) => {
    await page.goto("/settings");

    // Fill in project form - use /tmp which always exists
    await page.getByPlaceholder("Project Name").fill("Temp Project");
    await page.getByTestId("sdlc-path-input").fill("/tmp");
    await page.getByRole("button", { name: "Add Project" }).click();

    // Should show success notification
    await expect(page.getByText('Project "Temp Project" added.')).toBeVisible();

    // Card should appear
    await expect(page.getByTestId("project-card-temp-project")).toBeVisible();

    // Clean up: delete the project
    await page
      .getByTestId("project-card-temp-project")
      .getByRole("button", { name: "Delete" })
      .click();
    await page.getByTestId("confirm-dialog").getByRole("button", { name: "Confirm" }).click();
    await expect(page.getByText('Project "Temp Project" deleted.')).toBeVisible();
  });

  test("edits existing project name", async ({ page }) => {
    await page.goto("/settings");

    // Click Edit on the fixture project
    await page
      .getByTestId("project-card-e2e-test-project")
      .getByRole("button", { name: "Edit" })
      .click();

    // Form should show "Editing:" heading
    await expect(page.getByText("Editing:")).toBeVisible();

    // Change the name
    const nameInput = page.getByPlaceholder("Project Name");
    await nameInput.clear();
    await nameInput.fill("E2E Test Project Renamed");
    await page.getByRole("button", { name: "Save" }).click();

    // Should show success notification
    await expect(
      page.getByText('Project "E2E Test Project Renamed" updated.'),
    ).toBeVisible();

    // Slug doesn't change on rename - card still has original testid
    await expect(page.getByTestId("project-card-e2e-test-project")).toBeVisible();

    // Revert the name back
    await page
      .getByTestId("project-card-e2e-test-project")
      .getByRole("button", { name: "Edit" })
      .click();
    await nameInput.clear();
    await nameInput.fill("E2E Test Project");
    await page.getByRole("button", { name: "Save" }).click();
    await expect(
      page.getByText('Project "E2E Test Project" updated.'),
    ).toBeVisible();
  });

  test("deletes project with confirmation dialog", async ({ page }) => {
    await page.goto("/settings");

    // First, create a throwaway project to delete - use /tmp which exists
    await page.getByPlaceholder("Project Name").fill("Delete Me");
    await page.getByTestId("sdlc-path-input").fill("/tmp");
    await page.getByRole("button", { name: "Add Project" }).click();
    await expect(page.getByTestId("project-card-delete-me")).toBeVisible();

    // Click Delete
    await page
      .getByTestId("project-card-delete-me")
      .getByRole("button", { name: "Delete" })
      .click();

    // Confirm dialog should appear
    const dialog = page.getByTestId("confirm-dialog");
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText('Delete "Delete Me"?')).toBeVisible();

    // Confirm deletion
    await dialog.getByRole("button", { name: "Confirm" }).click();
    await expect(page.getByText('Project "Delete Me" deleted.')).toBeVisible();
    await expect(page.getByTestId("project-card-delete-me")).not.toBeVisible();
  });

  test("form validation rejects empty name", async ({ page }) => {
    await page.goto("/settings");

    // Try to submit with empty name
    await page.getByTestId("sdlc-path-input").fill("/tmp");
    await page.getByRole("button", { name: "Add Project" }).click();

    // The name input should be marked as invalid (HTML5 required)
    const nameInput = page.getByPlaceholder("Project Name");
    await expect(nameInput).toHaveAttribute("required", "");
  });

  test("source type toggle shows conditional fields", async ({ page }) => {
    await page.goto("/settings");

    // Default is Local - should show SDLC path input
    await expect(page.getByTestId("sdlc-path-input")).toBeVisible();
    await expect(page.getByTestId("repo-url-input")).not.toBeVisible();

    // Switch to GitHub. Branch and sdlc path are derived from the chosen repo
    // (CR-01KXB377), so they live behind Advanced rather than the default flow.
    await page.getByTestId("source-type-toggle").getByText("GitHub").click();
    await expect(page.getByTestId("repo-url-input")).toBeVisible();
    await expect(page.getByTestId("repo-branch-input")).not.toBeVisible();
    await expect(page.getByTestId("sdlc-path-input")).not.toBeVisible();

    // The override is still reachable under Advanced.
    await page.getByTestId("advanced-toggle").click();
    await expect(page.getByTestId("repo-branch-input")).toBeVisible();
    await expect(page.getByTestId("repo-path-input")).toBeVisible();

    // Switch back to Local
    await page.getByTestId("source-type-toggle").getByText("Local").click();
    await expect(page.getByTestId("sdlc-path-input")).toBeVisible();
    await expect(page.getByTestId("repo-url-input")).not.toBeVisible();
  });
});
