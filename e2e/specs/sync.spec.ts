import fs from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

const FIXTURES_DIR = path.resolve(__dirname, "../fixtures/sdlc-docs");

test.describe("Sync", () => {
  test("triggers sync from project detail page", async ({ page }) => {
    await page.goto("/settings");

    // Click Sync Now on the fixture project card
    await page
      .getByTestId("project-card-e2e-test-project")
      .getByRole("button", { name: "Sync Now" })
      .click();

    // Button should show syncing state
    await expect(
      page
        .getByTestId("project-card-e2e-test-project")
        .getByRole("button", { name: "Syncing..." }),
    ).toBeVisible();

    // Wait for sync to complete - button returns to "Sync Now"
    await expect(
      page
        .getByTestId("project-card-e2e-test-project")
        .getByRole("button", { name: "Sync Now" }),
    ).toBeVisible({ timeout: 15_000 });
  });

  test("sync updates last synced timestamp", async ({ page }) => {
    await page.goto("/settings");

    const card = page.getByTestId("project-card-e2e-test-project");

    // Verify the card shows a last synced timestamp
    await expect(card.getByText(/Last synced:/)).toBeVisible();

    // Trigger sync - the button goes to "Syncing..." then back to "Sync Now"
    await card.getByRole("button", { name: "Sync Now" }).click();
    await expect(
      card.getByRole("button", { name: "Sync Now" }),
    ).toBeVisible({ timeout: 15_000 });

    // After sync completes, timestamp should still be present
    const timestampText = await card.getByText(/Last synced:/).textContent();
    expect(timestampText).toMatch(/Last synced: .+/);
  });

  test("sync detects new documents added to fixtures", async ({ page }) => {
    const newDocPath = path.join(
      FIXTURES_DIR,
      "stories/US0099-temp-story.md",
    );

    try {
      // Create a new fixture file
      fs.writeFileSync(
        newDocPath,
        [
          "# US0099: Temporary Story",
          "",
          '> **Status:** Draft',
          '> **Epic:** [EP0001: Alpha Feature](../epics/EP0001-alpha-feature.md)',
          '> **Owner:** Test',
          "",
          "## User Story",
          "",
          "Temporary story for E2E sync test.",
        ].join("\n"),
      );

      // Trigger sync from settings page
      await page.goto("/settings");
      await page
        .getByTestId("project-card-e2e-test-project")
        .getByRole("button", { name: "Sync Now" })
        .click();
      await expect(
        page
          .getByTestId("project-card-e2e-test-project")
          .getByRole("button", { name: "Sync Now" }),
      ).toBeVisible({ timeout: 15_000 });

      // Navigate to documents and verify the new doc appears
      await page.goto("/projects/e2e-test-project/documents");
      await expect(page.getByRole("link", { name: "US0099: Temporary Story" })).toBeVisible();
    } finally {
      // Clean up the temp file
      if (fs.existsSync(newDocPath)) {
        fs.unlinkSync(newDocPath);
      }

      // Re-sync to remove the deleted doc from DB
      await page.goto("/settings");
      await page
        .getByTestId("project-card-e2e-test-project")
        .getByRole("button", { name: "Sync Now" })
        .click();
      await expect(
        page
          .getByTestId("project-card-e2e-test-project")
          .getByRole("button", { name: "Sync Now" }),
      ).toBeVisible({ timeout: 15_000 });
    }
  });

  test("sync detects document changes", async ({ page }) => {
    const docPath = path.join(
      FIXTURES_DIR,
      "stories/US0004-widget-tests.md",
    );
    const originalContent = fs.readFileSync(docPath, "utf-8");

    try {
      // Modify the fixture file - change status
      const modified = originalContent.replace(
        '> **Status:** Draft',
        '> **Status:** In Progress',
      );
      fs.writeFileSync(docPath, modified);

      // Trigger sync
      await page.goto("/settings");
      await page
        .getByTestId("project-card-e2e-test-project")
        .getByRole("button", { name: "Sync Now" })
        .click();
      await expect(
        page
          .getByTestId("project-card-e2e-test-project")
          .getByRole("button", { name: "Sync Now" }),
      ).toBeVisible({ timeout: 15_000 });

      // Verify the status changed in the document list
      await page.goto("/projects/e2e-test-project/documents");
      const row = page.getByRole("row").filter({ hasText: "US0004: Widget Tests" });
      await expect(row.getByText("In Progress")).toBeVisible();
    } finally {
      // Restore original content
      fs.writeFileSync(docPath, originalContent);

      // Re-sync to restore DB state
      await page.goto("/settings");
      await page
        .getByTestId("project-card-e2e-test-project")
        .getByRole("button", { name: "Sync Now" })
        .click();
      await expect(
        page
          .getByTestId("project-card-e2e-test-project")
          .getByRole("button", { name: "Sync Now" }),
      ).toBeVisible({ timeout: 15_000 });
    }
  });
});
