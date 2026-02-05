import { test, expect } from '@playwright/test';

test.describe('Chat Functionality', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:3000');
    });

    test('should create a new chat and switch between them', async ({ page }) => {
        // 1. Initial State: Should be on default "Research Assistant" view
        await expect(page.getByRole('heading', { name: 'Research Assistant' })).toBeVisible();

        // 2. Open Sidebar
        const menuButton = page.getByTitle('Open History');
        await menuButton.click();
        await expect(page.getByText('History')).toBeVisible();

        // 3. Create First Chat
        // Type a message to start a chat session (if logic allows) or click New Chat (which resets)
        // Actually, sending a message creates a chat if none selected? 
        // Wait, the current logic is: if currentChatId is null, send message -> create chat -> set ID.

        // Close sidebar to type
        await page.getByTitle('Close History').click();
        // Actually, on desktop sidebar pushes content? No, it's absolute/fixed overlay in my latest change?
        // Let's just click the overlay or close button if standard.
        // My sidebar implementation has a close button inside it.
        // But let's just type. The input is visible.

        await page.getByPlaceholder('Ask about research papers...').fill('Hello Chat 1');
        await page.getByRole('button', { name: 'Send message' }).click(); // ArrowUp button

        // API mock or wait for response? 
        // We are running against real backend.
        await expect(page.getByText('Hello Chat 1')).toBeVisible();
        // Wait for "Thinking..." to disappear
        await expect(page.getByText('Thinking...')).not.toBeVisible({ timeout: 10000 });

        // 4. Verify Chat 1 in Sidebar
        await menuButton.click();
        // Chat title might be "Hello Chat 1" or similar
        await expect(page.locator('.truncate').filter({ hasText: 'Hello Chat 1' })).toBeVisible();

        // 5. Create Second Chat
        await page.getByRole('button', { name: 'New Chat' }).click();
        await expect(page.getByText('Research Assistant')).toBeVisible(); // Welcome screen

        await page.getByPlaceholder('Ask about research papers...').fill('Hello Chat 2');
        await page.getByRole('button', { name: 'Send message' }).click();
        await expect(page.getByText('Thinking...')).not.toBeVisible({ timeout: 10000 });

        // 6. Switch back to Chat 1
        await menuButton.click();
        await page.locator('.truncate').filter({ hasText: 'Hello Chat 1' }).click();
        await expect(page.getByText('Hello Chat 1')).toBeVisible();
        await expect(page.getByText('Hello Chat 2')).not.toBeVisible();
    });

    test('should delete a chat', async ({ page }) => {
        // 1. Create a chat to delete
        await page.getByPlaceholder('Ask about research papers...').fill('Delete Me');
        await page.getByRole('button', { name: 'Send message' }).click();
        await expect(page.getByText('Thinking...')).not.toBeVisible({ timeout: 10000 });

        // 2. Open Sidebar
        await page.getByTitle('Open History').click();

        // 3. Find delete button for this chat
        const chatItem = page.locator('.group').filter({ hasText: 'Delete Me' });
        await expect(chatItem).toBeVisible();

        // Hover to show delete button
        await chatItem.hover();

        // Setup dialog handler
        page.on('dialog', dialog => dialog.accept());

        // Click delete
        await chatItem.getByTitle('Delete chat').click();

        // 4. Verify deletion
        await expect(chatItem).not.toBeVisible();
    });
});
