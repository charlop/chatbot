import { test, expect } from '@playwright/test';

test.describe('Smoke Tests', () => {
  test('should load the home page', async ({ page }) => {
    await page.goto('/');

    // Check that the page title is correct
    await expect(page).toHaveTitle(/Contract Refund Eligibility System/);

    // Check that the main heading is visible
    await expect(page.getByRole('heading', { name: /Contract Refund Eligibility System/i })).toBeVisible();
  });

  test('should have no console errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/');

    // Allow time for any errors to appear
    await page.waitForTimeout(1000);

    expect(errors).toHaveLength(0);
  });
});
