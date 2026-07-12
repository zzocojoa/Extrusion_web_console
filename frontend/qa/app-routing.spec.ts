import { expect, test } from "@playwright/test";

test("keeps page state synchronized with navigation history", async ({ page }) => {
  await page.goto("/upload");
  await expect(page.locator(".page--upload")).toBeVisible();
  await expect(page.locator(".dashboard-page")).toHaveCount(0);

  await page.locator("aside").getByRole("button", { name: /대시보드|Dashboard/ }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.locator(".dashboard-page")).toBeVisible();

  await page.goBack();
  await expect(page).toHaveURL(/\/upload$/);
  await expect(page.locator(".page--upload")).toBeVisible();

  await page.goForward();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.locator(".dashboard-page")).toBeVisible();

  await page.locator("aside").getByRole("button", { name: /설정|Settings/ }).click();
  await expect(page).toHaveURL(/\/settings$/);
  await page.reload();
  await expect(page.locator(".settings-page")).toBeVisible();
});
