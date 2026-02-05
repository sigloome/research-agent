import { test, expect } from '@playwright/test';

test('basic smoke test', async ({ page }) => {
    // Wait for the application to load
    await page.goto('/');

    // Verify title
    await expect(page).toHaveTitle(/Velvet Research/);

    // Check if main layout elements are present
    await expect(page.getByRole('heading', { name: 'Velvet Research' })).toBeVisible();

    // Check if chat input is visible
    const chatInput = page.locator('textarea[placeholder*="Ask"]');
    await expect(chatInput).toBeVisible();

    // Verify that we can type in the chat
    await chatInput.fill('Test Message');
    await expect(chatInput).toHaveValue('Test Message');
});
