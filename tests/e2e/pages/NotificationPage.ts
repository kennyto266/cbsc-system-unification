import { type Page, Locator, expect } from '@playwright/test';

export interface AlertRuleData {
  name: string;
  description?: string;
  type: 'threshold' | 'event' | 'custom' | 'scheduled';
  severity: 'low' | 'medium' | 'high' | 'critical';
  conditions?: AlertCondition[];
  channels: string[];
}

export interface AlertCondition {
  metric: string;
  operator: string;
  threshold: number;
}

export class NotificationPage {
  readonly page: Page;
  readonly notificationCenter: Locator;
  readonly unreadBadge: Locator;
  readonly notificationList: Locator;
  readonly alertRulesList: Locator;
  readonly notificationTabs: Locator;
  readonly createAlertRuleButton: Locator;
  readonly testNotification: Locator;

  constructor(page: Page) {
    this.page = page;
    this.notificationCenter = page.locator('[data-testid=notification-center]');
    this.unreadBadge = page.locator('[data-testid=unread-badge]');
    this.notificationList = page.locator('[data-testid=notification-list]');
    this.alertRulesList = page.locator('[data-testid=alert-rules-list]');
    this.notificationTabs = page.locator('[data-testid=notification-tabs]');
    this.createAlertRuleButton = page.locator('[data-testid=create-alert-rule]');
    this.testNotification = page.locator('[data-testid=test-notification]');
  }

  async openNotificationCenter() {
    await this.page.locator('[data-testid=notification-bell]').click();
    await this.notificationCenter.waitFor({ state: 'visible' });
  }

  async closeNotificationCenter() {
    await this.page.click('[data-testid=close-notification-center]');
    await this.notificationCenter.waitFor({ state: 'hidden' });
  }

  async switchToAlertRules() {
    await this.notificationTabs.locator('[data-testid=alert-rules-tab]').click();
  }

  async switchToNotifications() {
    await this.notificationTabs.locator('[data-testid=notifications-tab]').click();
  }

  async createAlertRule(ruleData: AlertRuleData) {
    await this.createAlertRuleButton.click();

    // Fill rule form
    await this.page.fill('[data-testid=rule-name]', ruleData.name);
    if (ruleData.description) {
      await this.page.fill('[data-testid=rule-description]', ruleData.description);
    }
    await this.page.selectOption('[data-testid=rule-type]', ruleData.type);
    await this.page.selectOption('[data-testid=rule-severity]', ruleData.severity);

    // Add conditions if threshold type
    if (ruleData.type === 'threshold' && ruleData.conditions) {
      for (const condition of ruleData.conditions) {
        await this.page.selectOption('[data-testid=condition-metric]', condition.metric);
        await this.page.selectOption('[data-testid=condition-operator]', condition.operator);
        await this.page.fill('[data-testid=condition-threshold]', condition.threshold.toString());
      }
    }

    // Select notification channels
    for (const channel of ruleData.channels) {
      await this.page.check(`[data-testid=channel-${channel}]`);
    }

    // Save rule
    await this.page.click('[data-testid=save-rule]');
    await this.page.waitForSelector('[data-testid=rule-saved]', { state: 'visible' });
  }

  async editAlertRule(ruleId: string) {
    await this.alertRulesList.locator(`[data-testid=rule-${ruleId}] [data-testid=edit-rule]`).click();
  }

  async deleteAlertRule(ruleId: string) {
    await this.alertRulesList.locator(`[data-testid=rule-${ruleId}] [data-testid=delete-rule]`).click();
    await this.page.locator('[data-testid=confirm-delete]').click();
  }

  async toggleAlertRule(ruleId: string) {
    await this.alertRulesList.locator(`[data-testid=rule-${ruleId}] [data-testid=toggle-rule]`).click();
  }

  async testAlertRule(ruleName: string) {
    await this.alertRulesList.locator(`[data-testid-rule="${ruleName}"] [data-testid=test-rule]`).click();
  }

  async createTestNotification(channel: string) {
    await this.page.click('[data-testid=test-notification-btn]');
    await this.page.selectOption('[data-testid=notification-channel]', channel);
    await this.page.fill('[data-testid=test-title]', 'Test Notification');
    await this.page.fill('[data-testid=test-message]', 'This is a test notification');
    await this.page.click('[data-testid=send-test]');
  }

  async markNotificationAsRead(notificationId: string) {
    await this.notificationList.locator(`[data-testid=notification-${notificationId}]`).click();
  }

  async markAllNotificationsAsRead() {
    await this.page.click('[data-testid=mark-all-read]');
  }

  async deleteNotification(notificationId: string) {
    await this.notificationList.locator(`[data-testid=notification-${notificationId}] [data-testid=delete]`).click();
  }

  async getUnreadCount(): Promise<number> {
    const text = await this.unreadBadge.textContent();
    return parseInt(text || '0');
  }

  async getNotificationCount(): Promise<number> {
    return await this.notificationList.locator('[data-testid=notification-item]').count();
  }

  async getAlertRuleCount(): Promise<number> {
    return await this.alertRulesList.locator('[data-testid=alert-rule-item]').count();
  }

  async searchNotifications(query: string) {
    await this.page.fill('[data-testid=notification-search]', query);
  }

  async filterNotificationsByType(type: string) {
    await this.page.selectOption('[data-testid=notification-filter]', type);
  }

  async filterNotificationsByDateRange(startDate: string, endDate: string) {
    await this.page.fill('[data-testid=start-date]', startDate);
    await this.page.fill('[data-testid=end-date]', endDate);
    await this.page.click('[data-testid=apply-date-filter]');
  }

  async exportNotifications(format: 'csv' | 'json') {
    await this.page.click(`[data-testid=export-${format}]`);
  }

  async configureNotificationSettings(settings: {
    email: boolean;
    browser_push: boolean;
    sms: boolean;
    quiet_hours_enabled: boolean;
    quiet_hours_start: string;
    quiet_hours_end: string;
  }) {
    await this.page.click('[data-testid=notification-settings]');

    await this.page.setChecked('[data-testid=email-enabled]', settings.email);
    await this.page.setChecked('[data-testid=push-enabled]', settings.browser_push);
    await this.page.setChecked('[data-testid=sms-enabled]', settings.sms);
    await this.page.setChecked('[data-testid=quiet-hours]', settings.quiet_hours_enabled);

    if (settings.quiet_hours_enabled) {
      await this.page.fill('[data-testid=quiet-start]', settings.quiet_hours_start);
      await this.page.fill('[data-testid=quiet-end]', settings.quiet_hours_end);
    }

    await this.page.click('[data-testid=save-settings]');
  }

  async subscribeToStrategy(strategyId: string) {
    await this.page.click(`[data-testid=strategy-${strategyId}-subscribe]`);
  }

  async unsubscribeFromStrategy(strategyId: string) {
    await this.page.click(`[data-testid=strategy-${strategyId}-unsubscribe]`);
  }

  async waitForNotificationToast(message: string, timeout: number = 5000) {
    await this.page.waitForSelector(`[data-testid=toast]:has-text("${message}")`, { timeout });
  }

  async assertNotificationReceived(title: string) {
    await expect(this.notificationList.locator(`[data-testid-notification-title="${title}"]`)).toBeVisible();
  }

  async assertAlertRuleCreated(ruleName: string) {
    await expect(this.alertRulesList).toContainText(ruleName);
  }

  async assertNotificationRead(notificationId: string) {
    const notification = this.notificationList.locator(`[data-testid=notification-${notificationId}]`);
    await expect(notification).toHaveClass(/read/);
  }

  // Helper methods for handling browser notifications
  async handleBrowserNotificationPermission(accept: boolean = true) {
    this.page.on('dialog', async dialog => {
      if (accept) {
        await dialog.accept();
      } else {
        await dialog.dismiss();
      }
    });
  }

  async listenForBrowserNotification() {
    return new Promise((resolve) => {
      this.page.on('notification', resolve);
    });
  }

  // Accessibility helpers
  async runAccessibilityCheck() {
    await this.page.accessibility.snapshot().then((results: any) => {
      expect(results).toHaveNoViolations();
    });
  }

  // Performance helpers
  async measureNotificationCenterOpenTime(): Promise<number> {
    const start = Date.now();
    await this.openNotificationCenter();
    await this.notificationCenter.waitFor({ state: 'visible' });
    return Date.now() - start;
  }
}