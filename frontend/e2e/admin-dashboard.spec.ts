import { test, expect } from '@playwright/test';

test.describe('Admin Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // For now, we'll test the dashboard route directly
    // In a real test, we'd authenticate first
    await page.goto('/admin');
  });

  test('should display dashboard layout', async ({ page }) => {
    // Test that the dashboard layout is rendered
    await expect(page.getByRole('navigation', { name: 'sidebar' })).toBeVisible();
    await expect(page.getByRole('banner', { name: 'topbar' })).toBeVisible();
    await expect(page.getByRole('main')).toBeVisible();
  });

  test('should have navigation links', async ({ page }) => {
    // Test that navigation links are present
    const sidebar = page.getByRole('navigation', { name: 'sidebar' });
    await expect(sidebar.getByRole('link', { name: 'Dashboard' })).toBeVisible();
    await expect(sidebar.getByRole('link', { name: 'Customers' })).toBeVisible();
    await expect(sidebar.getByRole('link', { name: 'Billing' })).toBeVisible();
    await expect(sidebar.getByRole('link', { name: 'Tickets' })).toBeVisible();
  });

  test('should navigate between pages', async ({ page }) => {
    // Test navigation between dashboard pages
    const sidebar = page.getByRole('navigation', { name: 'sidebar' });
    
    await sidebar.getByRole('link', { name: 'Customers' }).click();
    await expect(page).toHaveURL(/.*admin\/customers/);
    
    await sidebar.getByRole('link', { name: 'Billing' }).click();
    await expect(page).toHaveURL(/.*admin\/billing/);
  });
});
