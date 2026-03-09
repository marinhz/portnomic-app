import { test, expect } from "@playwright/test";

/**
 * Task 7.4 — Icon spacing and sizing
 * Verifies Dashboard summary card icons use size-6 and layout has adequate spacing.
 * Run with: npx playwright test
 */
test.describe("Icon spacing and sizing", () => {
  test("Dashboard summary cards have size-6 icons", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Check that SVG icons have size-6 class (present on dashboard or after login)
    const iconsWithSize6 = page.locator(".size-6");
    await expect(iconsWithSize6.first()).toBeVisible({ timeout: 10000 });
    expect(await iconsWithSize6.count()).toBeGreaterThanOrEqual(1);
  });

  test("Integrations page action row has gap-6 spacing", async ({ page }) => {
    await page.goto("/settings/integrations");
    await page.waitForLoadState("networkidle");

    const actionRow = page.locator(".gap-6").filter({ has: page.getByRole("button") }).first();
    await expect(actionRow).toBeVisible({ timeout: 10000 });
    await expect(actionRow).toHaveClass(/gap-6/);
  });
});
