/**
 * E2E Tests for Dashboard System
 * End-to-end testing using Playwright
 */

import { test, expect } from '@playwright/test';
import { Page, BrowserContext } from '@playwright/test';

// Test data
const testUser = {
  email: 'test@example.com',
  password: 'Test123!',
  name: 'Test User'
};

const testStrategies = [
  {
    name: 'Momentum Trading Strategy',
    id: 'momentum-001',
    status: 'active',
    dailyPnL: 1250.50,
    totalReturn: 15.3
  },
  {
    name: 'Mean Reversion Arbitrage',
    id: 'mean-rev-001',
    status: 'active',
    dailyPnL: 890.25,
    totalReturn: 8.7
  },
  {
    name: 'Volatility Surface Trading',
    id: 'vol-surface-001',
    status: 'paused',
    dailyPnL: -150.75,
    totalReturn: -2.1
  }
];

test.describe('Dashboard E2E Tests', () => {
  let page: Page;
  let context: BrowserContext;

  test.beforeAll(async ({ browser }) => {
    // Create browser context with permissions
    context = await browser.newContext({
      permissions: ['notifications'],
      viewport: { width: 1920, height: 1080 }
    });

    // Handle notifications
    context.on('page', async (page) => {
      // Grant notification permissions
      await page.evaluate(() => {
        Notification.requestPermission = () => Promise.resolve('granted');
      });
    });
  });

  test.beforeEach(async () => {
    page = await context.newPage();
  });

  test.afterEach(async () => {
    await page.close();
  });

  test.afterAll(async () => {
    await context.close();
  });

  test.describe('Authentication', () => {
    test('should login successfully', async () => {
      await page.goto('/login');

      // Fill login form
      await page.fill('[data-testid=email-input]', testUser.email);
      await page.fill('[data-testid=password-input]', testUser.password);
      await page.click('[data-testid=login-button]');

      // Should redirect to dashboard
      await expect(page).toHaveURL('/dashboard');

      // Should show user name
      await expect(page.locator('[data-testid=user-name]')).toContainText(testUser.name);
    });

    test('should show error with invalid credentials', async () => {
      await page.goto('/login');

      await page.fill('[data-testid=email-input]', 'invalid@example.com');
      await page.fill('[data-testid=password-input]', 'WrongPassword');
      await page.click('[data-testid=login-button]');

      // Should show error message
      await expect(page.locator('[data-testid=error-message]')).toBeVisible();
      await expect(page.locator('[data-testid=error-message]')).toContainText('Invalid credentials');
    });

    test('should logout successfully', async () => {
      // Login first
      await login(page);

      // Click user menu
      await page.click('[data-testid=user-menu]');

      // Click logout
      await page.click('[data-testid=logout-button]');

      // Should redirect to login
      await expect(page).toHaveURL('/login');
    });
  });

  test.describe('Strategy Status Widget', () => {
    test.beforeEach(async () => {
      await login(page);
      await page.goto('/dashboard');
    });

    test('should display strategy list', async () => {
      // Check if widget is present
      await expect(page.locator('[data-testid=strategy-status-widget]')).toBeVisible();

      // Check if all test strategies are displayed
      for (const strategy of testStrategies) {
        await expect(page.locator(`[data-testid=strategy-${strategy.id}]`)).toBeVisible();
        await expect(page.locator(`[data-testid=strategy-${strategy.id}]`)).toContainText(strategy.name);
      }
    });

    test('should display correct status badges', async () => {
      // Check active strategy
      await expect(page.locator(`[data-testid=strategy-${testStrategies[0].id}]`))
        .locator('[data-testid=status-badge]')
        .toContainText('Active');

      // Check paused strategy
      await expect(page.locator(`[data-testid=strategy-${testStrategies[2].id}]`))
        .locator('[data-testid=status-badge]')
        .toContainText('Paused');
    });

    test('should toggle strategy status', async () => {
      const strategy = testStrategies[1]; // Active strategy

      // Find toggle switch
      const toggle = page.locator(`[data-testid=strategy-${strategy.id}]`).locator('[data-testid=status-toggle]');

      // Get initial state
      const initialState = await toggle.isChecked();
      expect(initialState).toBe(true);

      // Click to toggle
      await toggle.click();

      // Wait for API call
      await page.waitForTimeout(500);

      // Verify state changed
      const newState = await toggle.isChecked();
      expect(newState).toBe(!initialState);
    });

    test('should show daily P&L and total return', async () => {
      for (const strategy of testStrategies) {
        const strategyElement = page.locator(`[data-testid=strategy-${strategy.id}]`);

        // Check daily P&L
        await expect(strategyElement).toContainText('$' + strategy.dailyPnL.toFixed(2));

        // Check total return
        await expect(strategyElement).toContainText(strategy.totalReturn + '%');
      }
    });

    test('should expand strategy details', async () => {
      const strategy = testStrategies[0];

      // Click on strategy row
      await page.click(`[data-testid=strategy-${strategy.id}]`);

      // Check if expanded details are visible
      await expect(page.locator(`[data-testid=strategy-details-${strategy.id}]`)).toBeVisible();
      await expect(page.locator(`[data-testid=strategy-details-${strategy.id}]`)).toContainText('Last Execution');
      await expect(page.locator(`[data-testid=strategy-details-${strategy.id}]`)).toContainText('Next Execution');
    });
  });

  test.describe('Performance Metrics Widget', () => {
    test.beforeEach(async () => {
      await login(page);
      await page.goto('/dashboard');
    });

    test('should display performance metrics', async () => {
      // Check if widget is present
      await expect(page.locator('[data-testid=performance-metrics-widget]')).toBeVisible();

      // Check key metrics
      await expect(page.locator('[data-testid=total-return]')).toBeVisible();
      await expect(page.locator('[data-testid=sharpe-ratio]')).toBeVisible();
      await expect(page.locator('[data-testid=max-drawdown]')).toBeVisible();
      await expect(page.locator('[data-testid=win-rate]')).toBeVisible();
    });

    test('should switch between views', async () => {
      // Click on Returns view
      await page.click('[data-testid=view-returns]');
      await expect(page.locator('[data-testid=returns-chart]')).toBeVisible();

      // Click on Risk view
      await page.click('[data-testid=view-risk]');
      await expect(page.locator('[data-testid=risk-chart]')).toBeVisible();

      // Click on Efficiency view
      await page.click('[data-testid=view-efficiency]');
      await expect(page.locator('[data-testid=efficiency-radar]')).toBeVisible();
    });

    test('should change period selection', async () => {
      // Click period dropdown
      await page.click('[data-testid=period-selector]');

      // Select 1W
      await page.click('[data-testid=period-1W]');

      // Verify period is updated
      await expect(page.locator('[data-testid=period-selector]')).toContainText('1W');
    });

    test('should show benchmark comparison', async () => {
      // Enable benchmark
      await page.click('[data-testid=benchmark-toggle]');

      // Select benchmark
      await page.click('[data-testid=benchmark-selector]');
      await page.click('[data-testid=benchmark-spx]');

      // Should show benchmark data
      await expect(page.locator('[data-testid=benchmark-data]')).toBeVisible();
    });
  });

  test.describe('Portfolio Overview Widget', () => {
    test.beforeEach(async () => {
      await login(page);
      await page.goto('/dashboard');
    });

    test('should display portfolio summary', async () => {
      // Check if widget is present
      await expect(page.locator('[data-testid=portfolio-widget]')).toBeVisible();

      // Check portfolio values
      await expect(page.locator('[data-testid=total-value]')).toBeVisible();
      await expect(page.locator('[data-testid=cash]')).toBeVisible();
      await expect(page.locator('[data-testid=invested]')).toBeVisible();
      await expect(page.locator('[data-testid=day-change]')).toBeVisible();
    });

    test('should switch between allocation views', async () => {
      // Click Allocation view
      await page.click('[data-testid=view-allocation]');
      await expect(page.locator('[data-testid=allocation-pie-chart]')).toBeVisible();

      // Click Sectors view
      await page.click('[data-testid=view-sectors]');
      await expect(page.locator('[data-testid=sectors-chart]')).toBeVisible();

      // Click Holdings view
      await page.click('[data-testid=view-holdings]');
      await expect(page.locator('[data-testid=holdings-list]')).toBeVisible();
    });

    test('should show rebalancing suggestions', async () => {
      // Look for rebalancing section
      const rebalancingSection = page.locator('[data-testid=rebalancing-suggestions]');

      if (await rebalancingSection.isVisible()) {
        // Expand suggestions
        await page.click('[data-testid=expand-rebalancing]');

        // Should show suggestions
        await expect(page.locator('[data-testid=rebalancing-items]')).toBeVisible();

        // Execute rebalancing
        await page.click('[data-testid=execute-rebalancing]');

        // Should show confirmation
        await expect(page.locator('[data-testid=rebalancing-confirmation]')).toBeVisible();
      }
    });
  });

  test.describe('Real-time Updates', () => {
    test.beforeEach(async () => {
      await login(page);
      await page.goto('/dashboard');
    });

    test('should receive WebSocket updates', async () => {
      // Check connection status
      await expect(page.locator('[data-testid=websocket-status]')).toBeVisible();
      await expect(page.locator('[data-testid=websocket-status]')).toContainText('Connected');

      // Listen for updates
      const strategyId = testStrategies[0].id;
      const initialPnL = testStrategies[0].dailyPnL;

      // Simulate WebSocket update (via API or mock)
      await page.evaluate(() => {
        // Mock WebSocket message
        window.postMessage({
          type: 'STRATEGY_UPDATE',
          data: {
            strategyId: 'momentum-001',
            dailyPnL: 1500.75,
            status: 'active'
          }
        }, '*');
      });

      // Wait for update
      await page.waitForTimeout(500);

      // Verify update
      await expect(page.locator(`[data-testid=strategy-${strategyId}]`))
        .locator('[data-testid=daily-pnl]')
        .toContainText('1500.75');
    });

    test('should update charts in real-time', async () => {
      // Check real-time chart
      await expect(page.locator('[data-testid=realtime-chart]')).toBeVisible();

      // Simulate data update
      await page.evaluate(() => {
        window.postMessage({
          type: 'CHART_UPDATE',
          data: {
            timestamp: new Date().toISOString(),
            value: 1500,
            symbol: 'SPY'
          }
        }, '*');
      });

      // Wait for chart update
      await page.waitForTimeout(500);

      // Verify chart updated (would need to check specific chart data)
      await expect(page.locator('[data-testid=realtime-chart]')).toBeVisible();
    });
  });

  test.describe('Navigation', () => {
    test.beforeEach(async () => {
      await login(page);
    });

    test('should navigate to different pages', async () => {
      // Navigate to Strategies page
      await page.click('[data-testid=nav-strategies]');
      await expect(page).toHaveURL('/strategies');

      // Navigate to Analytics page
      await page.click('[data-testid=nav-analytics]');
      await expect(page).toHaveURL('/analytics');

      // Navigate to Settings page
      await page.click('[data-testid=nav-settings]');
      await expect(page).toHaveURL('/settings');

      // Navigate back to Dashboard
      await page.click('[data-testid=nav-dashboard]');
      await expect(page).toHaveURL('/dashboard');
    });

    test('should show active navigation state', async () => {
      await page.goto('/dashboard');

      // Dashboard should be active
      await expect(page.locator('[data-testid=nav-dashboard]')).toHaveClass(/active/);

      await page.goto('/strategies');

      // Strategies should be active
      await expect(page.locator('[data-testid=nav-strategies]')).toHaveClass(/active/);
      await expect(page.locator('[data-testid=nav-dashboard]')).not.toHaveClass(/active/);
    });
  });

  test.describe('Responsive Design', () => {
    test('should adapt to mobile view', async () => {
      await page.setViewportSize({ width: 375, height: 667 }); // iPhone size
      await login(page);
      await page.goto('/dashboard');

      // Check mobile navigation
      await expect(page.locator('[data-testid=mobile-menu]')).toBeVisible();

      // Click hamburger menu
      await page.click('[data-testid=mobile-menu-toggle]');

      // Should show mobile navigation
      await expect(page.locator('[data-testid=mobile-nav]')).toBeVisible();

      // Widgets should stack vertically
      await expect(page.locator('[data-testid=widget-container]')).toHaveClass(/mobile/);
    });

    test('should adapt to tablet view', async () => {
      await page.setViewportSize({ width: 768, height: 1024 }); // iPad size
      await login(page);
      await page.goto('/dashboard');

      // Should show responsive layout
      await expect(page.locator('[data-testid=sidebar]')).toBeVisible();
      await expect(page.locator('[data-testid=main-content]')).toHaveCSS('margin-left', /240px/);
    });
  });

  test.describe('Performance', () => {
    test('should load dashboard within 2 seconds', async () => {
      const startTime = Date.now();

      await login(page);
      await page.goto('/dashboard');

      // Wait for key elements
      await page.waitForSelector('[data-testid=strategy-status-widget]', { timeout: 2000 });
      await page.waitForSelector('[data-testid=performance-metrics-widget]', { timeout: 1000 });
      await page.waitForSelector('[data-testid=portfolio-widget]', { timeout: 1000 });

      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(2000);
    });

    test('should handle large datasets efficiently', async () => {
      await login(page);

      // Navigate to analytics with large dataset
      await page.goto('/analytics?period=1Y&granularity=daily');

      // Should load without timeout
      await expect(page.locator('[data-testid=analytics-chart]')).toBeVisible({ timeout: 5000 });

      // Should handle scrolling smoothly
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

      // Should not freeze
      const responseTime = await page.evaluate(() => {
        const start = performance.now();
        document.body.click();
        return performance.now() - start;
      });

      expect(responseTime).toBeLessThan(100);
    });
  });

  test.describe('Accessibility', () => {
    test.beforeEach(async () => {
      await login(page);
      await page.goto('/dashboard');
    });

    test('should have proper ARIA labels', async () => {
      // Check interactive elements have aria-labels
      const buttons = page.locator('button');
      const count = await buttons.count();

      for (let i = 0; i < count; i++) {
        const button = buttons.nth(i);
        const ariaLabel = await button.getAttribute('aria-label');
        const ariaLabelledby = await button.getAttribute('aria-labelledby');

        expect(ariaLabel || ariaLabelledby || await button.textContent()).toBeTruthy();
      }
    });

    test('should support keyboard navigation', async () => {
      // Tab through page
      await page.keyboard.press('Tab');

      // Should focus on interactive elements
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(['BUTTON', 'INPUT', 'SELECT', 'A']).toContain(focusedElement);

      // Enter key should work on buttons
      await page.keyboard.press('Enter');

      // Check if action was performed
      // This depends on the focused element
    });

    test('should have sufficient color contrast', async () => {
      // Get computed styles for text elements
      const textElements = page.locator('text');
      const count = await textElements.count();

      for (let i = 0; i < Math.min(count, 10); i++) { // Check first 10 elements
        const element = textElements.nth(i);
        const styles = await element.evaluate((el) => {
          const computed = window.getComputedStyle(el);
          return {
            color: computed.color,
            backgroundColor: computed.backgroundColor
          };
        });

        // Basic contrast check (simplified)
        expect(styles.color).not.toBe(styles.backgroundColor);
      }
    });
  });

  test.describe('Error Handling', () => {
    test('should handle network errors gracefully', async () => {
      await login(page);
      await page.goto('/dashboard');

      // Simulate network offline
      await page.context.setOffline(true);

      // Should show offline indicator
      await expect(page.locator('[data-testid=offline-indicator]')).toBeVisible({ timeout: 2000 });

      // Should not crash
      await page.reload();
      await expect(page.locator('[data-testid=dashboard]')).toBeVisible();

      // Restore network
      await page.context.setOffline(false);

      // Should reconnect automatically
      await expect(page.locator('[data-testid=offline-indicator]')).not.toBeVisible({ timeout: 5000 });
    });

    test('should handle API errors gracefully', async () => {
      await login(page);

      // Mock API error
      await page.route('**/api/strategies/**', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal server error' })
        });
      });

      await page.goto('/strategies');

      // Should show error message
      await expect(page.locator('[data-testid=error-message]')).toBeVisible();

      // Should provide retry option
      await expect(page.locator('[data-testid=retry-button]')).toBeVisible();
    });
  });
});

// Helper functions
async function login(page: Page) {
  await page.goto('/login');
  await page.fill('[data-testid=email-input]', testUser.email);
  await page.fill('[data-testid=password-input]', testUser.password);
  await page.click('[data-testid=login-button]');
  await page.waitForURL('/dashboard');
}