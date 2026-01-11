import { test, expect, type Page } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { StrategyPage } from '../pages/StrategyPage';
import { NotificationPage } from '../pages/NotificationPage';

// Test data
const testUser = {
  username: 'testuser',
  password: 'Test@123456',
  email: 'test@example.com'
};

const testStrategy = {
  name: 'E2E Test Strategy',
  type: 'momentum',
  initialCapital: 100000,
  description: 'Strategy created for E2E testing'
};

/**
 * Helper function to login as test user
 */
async function loginAsTestUser(page: Page) {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login(testUser.username, testUser.password);
  await expect(page).toHaveURL(/dashboard/);
}

test.describe('Dashboard Core User Flows', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    // Grant notification permissions
    await page.context().grantPermissions(['notifications']);
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('should login and view dashboard', async () => {
    await loginAsTestUser(page);

    // Verify dashboard elements
    const dashboard = new DashboardPage(page);
    await expect(dashboard.header).toBeVisible();
    await expect(dashboard.sidebar).toBeVisible();
    await expect(dashboard.mainContent).toBeVisible();

    // Check for widgets
    await expect(dashboard.strategyStatusWidget).toBeVisible();
    await expect(dashboard.performanceWidget).toBeVisible();
    await expect(dashboard.portfolioWidget).toBeVisible();

    // Verify real-time updates are working
    await dashboard.waitForRealTimeUpdates();
  });

  test('should navigate to strategy management page', async () => {
    await loginAsTestUser(page);

    const dashboard = new DashboardPage(page);

    // Click on strategies in sidebar
    await dashboard.navigateToStrategies();

    // Verify strategy page
    const strategyPage = new StrategyPage(page);
    await expect(strategyPage.pageHeader).toBeVisible();
    await expect(strategyPage.strategyList).toBeVisible();
    await expect(strategyPage.createStrategyButton).toBeVisible();
  });

  test('should create a new strategy', async () => {
    await loginAsTestUser(page);

    const dashboard = new DashboardPage(page);
    await dashboard.navigateToStrategies();

    const strategyPage = new StrategyPage(page);

    // Click create strategy button
    await strategyPage.clickCreateStrategy();

    // Fill strategy form
    await strategyPage.fillStrategyForm(testStrategy);

    // Save strategy
    await strategyPage.saveStrategy();

    // Verify strategy was created
    await expect(strategyPage.successMessage).toBeVisible();
    await expect(strategyPage.strategyList).toContainText(testStrategy.name);
  });

  test('should view strategy performance metrics', async () => {
    await loginAsTestUser(page);

    const dashboard = new DashboardPage(page);

    // Find and click on a strategy in the widget
    await dashboard.clickFirstStrategy();

    // Verify performance metrics page
    await expect(page.locator('[data-testid=performance-metrics]')).toBeVisible();
    await expect(page.locator('[data-testid=total-return]')).toBeVisible();
    await expect(page.locator('[data-testid=sharpe-ratio]')).toBeVisible();
    await expect(page.locator('[data-testid=max-drawdown]')).toBeVisible();
  });

  test('should configure and trigger alerts', async () => {
    await loginAsTestUser(page);

    // Navigate to notification center
    const notificationPage = new NotificationPage(page);
    await notificationPage.openNotificationCenter();

    // Switch to alert rules tab
    await notificationPage.switchToAlertRules();

    // Create a new alert rule
    await notificationPage.createAlertRule({
      name: 'High Drawdown Alert',
      description: 'Alert when drawdown exceeds 10%',
      type: 'threshold',
      severity: 'high',
      conditions: [{
        metric: 'drawdown',
        operator: 'lt',
        threshold: -0.1
      }],
      channels: ['email', 'browser_push']
    });

    // Verify alert rule was created
    await expect(notificationPage.alertRulesList).toContainText('High Drawdown Alert');

    // Test the alert rule
    await notificationPage.testAlertRule('High Drawdown Alert');

    // Verify test notification
    await expect(notificationPage.testNotification).toBeVisible();
  });

  test('should handle real-time updates', async () => {
    await loginAsTestUser(page);

    const dashboard = new DashboardPage(page);

    // Wait for WebSocket connection
    await dashboard.waitForWebSocketConnection();

    // Get initial portfolio value
    const initialValue = await dashboard.getPortfolioValue();

    // Simulate a market update (in real scenario, this would come from backend)
    await page.evaluate(() => {
      // Simulate WebSocket message
      window.postMessage({
        type: 'strategy_update',
        data: {
          strategy_id: 'test',
          total_return: 0.05,
          daily_pnl: 500
        }
      }, '*');
    });

    // Wait for UI to update
    await dashboard.waitForValueChange();

    // Verify the value changed
    const newValue = await dashboard.getPortfolioValue();
    expect(newValue).not.toBe(initialValue);
  });

  test('should be responsive on different viewports', async () => {
    // Test desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });
    await loginAsTestUser(page);

    const dashboard = new DashboardPage(page);
    await expect(dashboard.sidebar).toBeVisible();
    await expect(dashboard.header).toBeVisible();

    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(dashboard.mobileMenuButton).toBeVisible();

    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(dashboard.mobileMenuButton).toBeVisible();
    await expect(dashboard.sidebar).not.toBeVisible();

    // Open mobile menu
    await dashboard.openMobileMenu();
    await expect(dashboard.mobileSidebar).toBeVisible();
  });

  test('should handle errors gracefully', async () => {
    // Simulate network error
    await page.route('**/api/v1/strategies', route => route.abort());

    await loginAsTestUser(page);

    const dashboard = new DashboardPage(page);

    // Try to load strategies
    await dashboard.navigateToStrategies();

    // Should show error message
    await expect(dashboard.errorMessage).toBeVisible();
    await expect(dashboard.errorMessage).toContainText('Failed to load strategies');

    // Should have retry button
    await expect(dashboard.retryButton).toBeVisible();
  });

  test('should export data', async () => {
    await loginAsTestUser(page);

    const dashboard = new DashboardPage(page);

    // Go to strategy performance
    await dashboard.clickFirstStrategy();

    // Click export button
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid=export-button]');

    // Wait for download
    const download = await downloadPromise;

    // Verify file name
    expect(download.suggestedFilename()).toMatch(/\.(csv|xlsx)$/);
  });

  test('should validate form inputs', async () => {
    await loginAsTestUser(page);

    const dashboard = new DashboardPage(page);
    await dashboard.navigateToStrategies();

    const strategyPage = new StrategyPage(page);
    await strategyPage.clickCreateStrategy();

    // Try to save without required fields
    await strategyPage.saveStrategy();

    // Should show validation errors
    await expect(strategyPage.validationErrors).toBeVisible();
    await expect(strategyPage.validationErrors).toContainText('Strategy name is required');

    // Fill invalid initial capital
    await strategyPage.fillStrategyForm({
      ...testStrategy,
      initialCapital: -1000
    });

    await strategyPage.saveStrategy();

    // Should show validation error for capital
    await expect(strategyPage.validationErrors).toContainText('Initial capital must be positive');
  });
});

test.describe('Authentication Flows', () => {
  test('should show error with invalid credentials', async () => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();

    // Try to login with invalid credentials
    await loginPage.login('invalid', 'invalid');

    // Should show error message
    await expect(loginPage.errorMessage).toBeVisible();
    await expect(loginPage.errorMessage).toContainText('Invalid username or password');
  });

  test('should redirect to dashboard after successful login', async () => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(testUser.username, testUser.password);

    // Should redirect to dashboard
    await expect(page).toHaveURL(/dashboard/);
  });

  test('should remember login session', async () => {
    await loginAsTestUser(page);

    // Close browser and reopen
    await page.context().close();
    page = await page.browser()!.newPage();

    // Go to dashboard - should not require login
    await page.goto('/dashboard');

    // Should be logged in
    await expect(page.locator('[data-testid=user-menu]')).toBeVisible();
  });

  test('should logout successfully', async () => {
    await loginAsTestUser(page);

    // Click logout
    await page.click('[data-testid=user-menu]');
    await page.click('[data-testid=logout-button]');

    // Should redirect to login
    await expect(page).toHaveURL(/login/);
  });
});

test.describe('Notification System', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
  });

  test('should receive browser push notifications', async () => {
    // Grant notification permissions
    await page.context().grantPermissions(['notifications']);

    const notificationPage = new NotificationPage(page);

    // Create a test notification
    await notificationPage.createTestNotification('browser_push');

    // Listen for notification
    const notification = await page.waitForEvent('notification');

    // Verify notification content
    expect(notification.title).toContain('Test Notification');
    expect(notification.body).toContain('This is a test notification');
  });

  test('should show in-app notifications', async () => {
    const notificationPage = new NotificationPage(page);

    // Open notification center
    await notificationPage.openNotificationCenter();

    // Should show unread count badge
    await expect(notificationPage.unreadBadge).toBeVisible();

    // Should list notifications
    await expect(notificationPage.notificationList).toBeVisible();
  });

  test('should mark notifications as read', async () => {
    const notificationPage = new NotificationPage(page);

    // Get initial unread count
    const initialCount = await notificationPage.getUnreadCount();

    // Mark all as read
    await notificationPage.markAllAsRead();

    // Verify count decreased
    const newCount = await notificationPage.getUnreadCount();
    expect(newCount).toBeLessThan(initialCount);
  });
});

test.describe('Performance Tests', () => {
  test('should load dashboard within 3 seconds', async () => {
    const startTime = Date.now();

    await loginAsTestUser(page);

    // Wait for dashboard to fully load
    await page.waitForSelector('[data-testid=dashboard-loaded]');

    const loadTime = Date.now() - startTime;

    // Should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should handle large data sets without crashing', async () => {
    await loginAsTestUser(page);

    // Navigate to strategies with large dataset
    await page.goto('/strategies?limit=1000');

    // Should not crash
    await expect(page.locator('[data-testid=strategy-list]')).toBeVisible();

    // Should load content progressively
    await page.waitForSelector('[data-testid=loading]', { state: 'hidden' });
  });
});

// Performance metrics collection
test.afterAll(async () => {
  // Collect performance metrics
  const metrics = {
    timestamp: new Date().toISOString(),
    browser: 'chromium',
    tests: {
      total: test.info().parallelTests.length,
      passed: test.info().passed,
      failed: test.info().failed,
      skipped: test.info().skipped
    }
  };

  // Save metrics to file
  await require('fs').writeFileSync(
    'test-results/performance-metrics.json',
    JSON.stringify(metrics, null, 2)
  );
});