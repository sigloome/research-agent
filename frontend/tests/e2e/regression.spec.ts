import { test, expect } from '@playwright/test';

test.describe('Regression Tests', () => {

    test('Bug: Page title should be "Velvet Research"', async ({ page }) => {
        await page.goto('/');
        await expect(page).toHaveTitle('Velvet Research');
    });

    test('Bug: Main header should be accessible via unique role', async ({ page }) => {
        await page.goto('/');
        // Ensures accessibility and uniqueness of the main heading
        // Previous bug: Test failed because locator('h1') found multiple elements or was ambiguous
        await expect(page.getByRole('heading', { name: 'Velvet Research' })).toBeVisible();
    });

    test('Bug: Frontend should connect to backend (No Connection Error)', async ({ page }) => {
        // Enable console logging
        page.on('console', msg => console.log(`PAGE LOG: ${msg.text()}`));
        page.on('pageerror', exception => console.log(`PAGE ERROR: ${exception}`));

        await page.goto('/');
        // Bug: "Failed to load library" appeared when backend port was not proxied correctly

        // 1. Negative Check: Ensure the error toast/message is NOT present
        await expect(page.getByText('Failed to load library')).not.toBeVisible();

        // 2. Positive Check: Ensure data is loaded
        // If DB is empty, we see "Library Empty" or "Add Source"
        // If DB has papers, we see filters.
        // We accept either to confirm connection.
        await expect(page.locator('text=Library Empty').or(page.getByRole('button', { name: 'All' }))).toBeVisible({ timeout: 30000 });
    });

});
