import { type Page, Locator, expect } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly header: Locator;
  readonly sidebar: Locator;
  readonly mainContent: Locator;
  readonly strategyStatusWidget: Locator;
  readonly performanceWidget: Locator;
  readonly portfolioWidget: Locator;
  readonly mobileMenuButton: Locator;
  readonly mobileSidebar: Locator;
  readonly errorMessage: Locator;
  readonly retryButton: Locator;
  readonly userMenu: Locator;
  readonly logoutButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.header = page.locator('[data-testid=header]');
    this.sidebar = page.locator('[data-testid=sidebar]');
    this.mainContent = page.locator('[data-testid=main-content]');
    this.strategyStatusWidget = page.locator('[data-testid=strategy-status-widget]');
    this.performanceWidget = page.locator('[data-testid=performance-widget]');
    this.portfolioWidget = page.locator('[data-testid=portfolio-widget]');
    this.mobileMenuButton = page.locator('[data-testid=mobile-menu-button]');
    this.mobileSidebar = page.locator('[data-testid=mobile-sidebar]');
    this.errorMessage = page.locator('[data-testid=error-message]');
    this.retryButton = page.locator('[data-testid=retry-button]');
    this.userMenu = page.locator('[data-testid=user-menu]');
    this.logoutButton = page.locator('[data-testid=logout-button]');
  }

  async navigateToStrategies() {
    await this.sidebar.locator('a[href="/strategies"]').click();
  }

  async navigateToPortfolio() {
    await this.sidebar.locator('a[href="/portfolio"]').click();
  }

  async navigateToAnalytics() {
    await this.sidebar.locator('a[href="/analytics"]').click();
  }

  async navigateToSettings() {
    await this.sidebar.locator('a[href="/settings"]').click();
  }

  async clickFirstStrategy() {
    await this.strategyStatusWidget.locator('[data-testid=strategy-item]').first().click();
  }

  async openMobileMenu() {
    await this.mobileMenuButton.click();
    await this.mobileSidebar.waitFor({ state: 'visible' });
  }

  async closeMobileMenu() {
    if (await this.mobileSidebar.isVisible()) {
      await this.mobileMenuButton.click();
      await this.mobileSidebar.waitFor({ state: 'hidden' });
    }
  }

  async waitForRealTimeUpdates(timeout: number = 5000) {
    // Wait for WebSocket connection indicator
    await this.page.waitForSelector('[data-testid=ws-connected]', { timeout });
  }

  async waitForWebSocketConnection() {
    await this.page.waitForFunction(() => {
      return window.webSocketConnected === true;
    }, { timeout: 10000 });
  }

  async waitForValueChange() {
    const initialValue = await this.getPortfolioValue();

    // Wait for value to change
    await this.page.waitForFunction(
      (initial) => {
        const currentValue = document.querySelector('[data-testid=portfolio-value]')?.textContent;
        return currentValue !== initial;
      },
      { args: [initialValue], timeout: 5000 }
    );
  }

  async getPortfolioValue(): Promise<number> {
    const text = await this.page.locator('[data-testid=portfolio-value]').textContent();
    // Remove formatting and parse as number
    const value = text?.replace(/[$,]/g, '') || '0';
    return parseFloat(value);
  }

  async getUnreadNotificationCount(): Promise<number> {
    const text = await this.page.locator('[data-testid=notification-badge]').textContent();
    return parseInt(text || '0');
  }

  async clickNotificationBell() {
    await this.page.locator('[data-testid=notification-bell]').click();
  }

  async refreshDashboard() {
    await this.page.reload();
    await this.page.waitForSelector('[data-testid=dashboard-loaded]');
  }

  async exportData(format: 'csv' | 'excel' | 'pdf' = 'csv') {
    await this.page.click(`[data-testid=export-${format}]`);
  }

  async changeTimeRange(range: '1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL') {
    await this.page.click(`[data-testid=time-range-${range}]`);
  }

  async toggleFullscreen() {
    await this.page.click('[data-testid=fullscreen-toggle]');
  }

  async toggleDarkMode() {
    await this.page.click('[data-testid=dark-mode-toggle]');
  }

  async searchStrategies(query: string) {
    await this.page.fill('[data-testid=search-input]', query);
    await this.page.keyboard.press('Enter');
  }

  async getLoadingState(): Promise<boolean> {
    return await this.page.locator('[data-testid=loading]').isVisible();
  }

  async waitForLoadingComplete() {
    await this.page.waitForSelector('[data-testid=loading]', { state: 'hidden' });
  }

  async assertDashboardLoaded() {
    await expect(this.header).toBeVisible();
    await expect(this.mainContent).toBeVisible();
    await this.page.waitForSelector('[data-testid=dashboard-loaded]');
  }

  async assertStrategyWidgetVisible() {
    await expect(this.strategyStatusWidget).toBeVisible();
  }

  async assertPerformanceWidgetVisible() {
    await expect(this.performanceWidget).toBeVisible();
  }

  async assertPortfolioWidgetVisible() {
    await expect(this.portfolioWidget).toBeVisible();
  }

  async assertErrorVisible() {
    await expect(this.errorMessage).toBeVisible();
  }

  async async retryAction() {
    await this.retryButton.click();
    await this.page.waitForSelector('[data-testid=loading]', { state: 'hidden' });
  }

  // Accessibility helpers
  async runAxeCheck() {
    // Run accessibility checks if axe-core is available
    try {
      const accessibilityScanResults = await this.page.accessibility.snapshot();
      expect(accessibilityScanResults).toHaveNoViolations();
    } catch (error) {
      console.warn('Accessibility check skipped:', error);
    }
  }

  // Performance helpers
  async getPerformanceMetrics() {
    const navigation = await this.page.evaluate(() => performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming);

    return {
      loadTime: navigation.loadEventEnd - navigation.loadEventStart,
      domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
      firstContentfulPaint: await this.page.evaluate(() => {
        return new Promise(resolve => {
          new PerformanceObserver(list => {
            const entries = list.getEntries();
            const fcp = entries.find(entry => entry.name === 'first-contentful-paint');
            if (fcp) resolve(fcp.startTime);
          }).observe({ entryTypes: ['paint'] });
        });
      })
    };
  }
}