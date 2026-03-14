import { expect, test } from '@playwright/test';

test('paper route canonicalizes versioned arxiv id', async ({ page }) => {
    await page.route('**/api/**', async route => {
        const url = route.request().url();
        if (url.includes('/api/paper/2602.04879')) {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    id: '2602.04879',
                    title: 'Canonical Paper',
                    authors: '["A"]',
                    published_date: '2026-01-01',
                    abstract: 'x',
                    url: 'https://arxiv.org/abs/2602.04879',
                }),
            });
            return;
        }
        if (url.includes('/api/notes?paper_id=2602.04879')) {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify([]),
            });
            return;
        }
        if (url.includes('/api/chats')) {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify([]),
            });
            return;
        }
        if (url.includes('/api/preferences')) {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ preferences: [], suggestions: [] }),
            });
            return;
        }
        if (url.includes('/api/papers?')) {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify([]),
            });
            return;
        }
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({}),
        });
    });

    await page.goto('http://127.0.0.1:18001/paper/2602.04879v1');

    await expect(page).toHaveURL('http://127.0.0.1:18001/paper/2602.04879');
    await expect(page.getByRole('heading', { name: 'Canonical Paper' })).toBeVisible();
});
