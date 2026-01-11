/**
 * Alert Manager
 * Central coordination point for the alert system
 */

import { AlertEngine } from './AlertEngine';
import { PushNotificationService } from '../notifications/PushNotificationService';
import { EmailService } from '../notifications/EmailService';
import {
  Alert,
  AlertRule,
  NotificationChannel,
  AlertSeverity,
  AlertStatus,
  NotificationStatus,
  UserNotificationPreferences,
  AlertEvent
} from './types';

export interface AlertManagerConfig {
  alertEngine: any;
  pushNotifications: any;
  email: any;
  webhooks?: Map<string, any>;
}

export class AlertManager {
  private alertEngine: AlertEngine;
  private pushNotificationService: PushNotificationService;
  private emailService: EmailService;
  private webhooks: Map<string, any> = new Map();
  private userPreferences: Map<string, UserNotificationPreferences> = new Map();

  constructor(config: AlertManagerConfig) {
    this.alertEngine = config.alertEngine;
    this.pushNotificationService = config.pushNotifications;
    this.emailService = config.email;

    if (config.webhooks) {
      this.webhooks = config.webhooks;
    }

    this.setupEventListeners();
  }

  /**
   * Setup event listeners for alert engine
   */
  private setupEventListeners(): void {
    this.alertEngine.on('alert_triggered', (data: { alert: Alert; rule: AlertRule }) => {
      this.handleAlertTriggered(data.alert, data.rule);
    });

    this.alertEngine.on('alert_acknowledged', (data: { alert: Alert; userId: string }) => {
      this.handleAlertAcknowledged(data.alert, data.userId);
    });

    this.alertEngine.on('alert_resolved', (data: { alert: Alert; userId: string }) => {
      this.handleAlertResolved(data.alert, data.userId);
    });
  }

  /**
   * Handle triggered alert
   */
  private async handleAlertTriggered(alert: Alert, rule: AlertRule): Promise<void> {
    console.log(`Alert triggered: ${alert.title}`);

    // Get user preferences for affected users
    const preferences = await this.getUserPreferencesForAlert(alert);

    // Send notifications based on preferences
    for (const [userId, userPrefs] of preferences) {
      if (!this.shouldSendNotification(alert, userPrefs)) {
        continue;
      }

      const notificationTasks = [];

      // Browser push notifications
      if (userPrefs.channels.browser_push.enabled && rule.notificationChannels.includes(NotificationChannel.BROWSER_PUSH)) {
        notificationTasks.push(
          this.sendPushNotification(alert, userId, userPrefs)
        );
      }

      // Email notifications
      if (userPrefs.channels.email.enabled && rule.notificationChannels.includes(NotificationChannel.EMAIL)) {
        notificationTasks.push(
          this.sendEmailNotification(alert, userPrefs)
        );
      }

      // SMS notifications (for critical alerts)
      if (
        alert.severity === AlertSeverity.CRITICAL &&
        userPrefs.channels.sms.enabled &&
        userPrefs.channels.sms.verified &&
        rule.notificationChannels.includes(NotificationChannel.SMS)
      ) {
        notificationTasks.push(
          this.sendSMSNotification(alert, userPrefs)
        );
      }

      // Webhook notifications
      for (const channel of rule.notificationChannels) {
        if (channel === NotificationChannel.WEBHOOK || channel === NotificationChannel.SLACK || channel === NotificationChannel.TEAMS) {
          notificationTasks.push(
            this.sendWebhookNotification(alert, channel)
          );
        }
      }

      // Execute notifications in parallel
      await Promise.allSettled(notificationTasks);
    }
  }

  /**
   * Send push notification
   */
  private async sendPushNotification(alert: Alert, userId: string, preferences: UserNotificationPreferences): Promise<void> {
    try {
      // Check quiet hours
      if (this.isQuietHours(preferences)) {
        console.log(`Skipping push notification for user ${userId} due to quiet hours`);
        return;
      }

      await this.pushNotificationService.showAlertNotification(alert);
    } catch (error) {
      console.error('Failed to send push notification:', error);
    }
  }

  /**
   * Send email notification
   */
  private async sendEmailNotification(alert: Alert, preferences: UserNotificationPreferences): Promise<void> {
    try {
      // Check email frequency settings
      if (preferences.channels.email.frequency !== 'immediate') {
        // Queue for batch sending
        await this.queueEmail(alert, preferences);
        return;
      }

      await this.emailService.sendAlertNotification(
        alert,
        preferences.channels.email.addresses
      );
    } catch (error) {
      console.error('Failed to send email notification:', error);
    }
  }

  /**
   * Send SMS notification
   */
  private async sendSMSNotification(alert: Alert, preferences: UserNotificationPreferences): Promise<void> {
    try {
      const message = `CBSC ${alert.severity.toUpperCase()}: ${alert.title}. ${alert.message}`;

      // This would integrate with your SMS provider
      console.log(`SMS to ${preferences.channels.sms.phoneNumber}: ${message}`);
    } catch (error) {
      console.error('Failed to send SMS notification:', error);
    }
  }

  /**
   * Send webhook notification
   */
  private async sendWebhookNotification(alert: Alert, channel: NotificationChannel): Promise<void> {
    try {
      const webhook = this.webhooks.get(channel);
      if (!webhook) {
        console.log(`Webhook not configured for channel: ${channel}`);
        return;
      }

      const payload = {
        alert: {
          id: alert.id,
          title: alert.title,
          message: alert.message,
          severity: alert.severity,
          status: alert.status,
          source: alert.source,
          triggeredAt: alert.trigger.triggeredAt,
          createdAt: alert.createdAt
        },
        timestamp: new Date().toISOString()
      };

      await this.sendWebhook(webhook.url, payload, webhook.method || 'POST', webhook.headers);
    } catch (error) {
      console.error('Failed to send webhook notification:', error);
    }
  }

  /**
   * Send webhook request
   */
  private async sendWebhook(url: string, payload: any, method: string = 'POST', headers?: Record<string, string>): Promise<void> {
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Webhook failed: ${response.statusText}`);
    }
  }

  /**
   * Queue email for batch sending
   */
  private async queueEmail(alert: Alert, preferences: UserNotificationPreferences): Promise<void> {
    // This would integrate with your email batching system
    console.log(`Queuing email for user with frequency: ${preferences.channels.email.frequency}`);
  }

  /**
   * Get user preferences for alert
   */
  private async getUserPreferencesForAlert(alert: Alert): Promise<Map<string, UserNotificationPreferences>> {
    // This would fetch from your user preferences API
    const preferences = new Map<string, UserNotificationPreferences>();

    // Default preferences for demo
    preferences.set('demo-user', {
      userId: 'demo-user',
      channels: {
        browser_push: {
          enabled: true,
          quietHours: false,
          quietStartTime: '22:00',
          quietEndTime: '07:00'
        },
        email: {
          enabled: true,
          addresses: ['user@example.com'],
          frequency: 'immediate'
        },
        sms: {
          enabled: false,
          phoneNumber: '',
          verified: false
        }
      },
      severityFilters: {
        [AlertSeverity.INFO]: true,
        [AlertSeverity.WARNING]: true,
        [AlertSeverity.CRITICAL]: true
      },
      quietHours: {
        enabled: false,
        startTime: '22:00',
        endTime: '07:00',
        timezone: 'UTC'
      }
    });

    return preferences;
  }

  /**
   * Check if notification should be sent based on preferences
   */
  private shouldSendNotification(alert: Alert, preferences: UserNotificationPreferences): boolean {
    // Check severity filter
    if (!preferences.severityFilters[alert.severity]) {
      return false;
    }

    return true;
  }

  /**
   * Check if currently in quiet hours
   */
  private isQuietHours(preferences: UserNotificationPreferences): boolean {
    if (!preferences.quietHours.enabled) {
      return false;
    }

    const now = new Date();
    const currentTime = now.getHours() * 60 + now.getMinutes();

    const [startHour, startMin] = preferences.quietHours.startTime.split(':').map(Number);
    const [endHour, endMin] = preferences.quietHours.endTime.split(':').map(Number);

    const startTime = startHour * 60 + startMin;
    const endTime = endHour * 60 + endMin;

    if (startTime <= endTime) {
      // Normal range (e.g., 22:00 - 07:00)
      return currentTime >= startTime && currentTime <= endTime;
    } else {
      // Overnight range (e.g., 22:00 - 07:00)
      return currentTime >= startTime || currentTime <= endTime;
    }
  }

  /**
   * Handle alert acknowledged
   */
  private handleAlertAcknowledged(alert: Alert, userId: string): void {
    console.log(`Alert acknowledged by ${userId}: ${alert.id}`);

    // Update notification status
    this.emit('alert_status_updated', {
      alertId: alert.id,
      status: AlertStatus.ACKNOWLEDGED,
      userId,
      timestamp: new Date()
    });
  }

  /**
   * Handle alert resolved
   */
  private handleAlertResolved(alert: Alert, userId: string): void {
    console.log(`Alert resolved by ${userId}: ${alert.id}`);

    // Update notification status
    this.emit('alert_status_updated', {
      alertId: alert.id,
      status: AlertStatus.RESOLVED,
      userId,
      timestamp: new Date()
    });
  }

  /**
   * Public API methods
   */

  /**
   * Create alert rule
   */
  async createRule(rule: Omit<AlertRule, 'id' | 'createdAt' | 'updatedAt' | 'createdBy' | 'updatedBy'>): Promise<AlertRule> {
    const newRule: AlertRule = {
      ...rule,
      id: this.generateRuleId(),
      createdAt: new Date(),
      updatedAt: new Date(),
      createdBy: 'current-user',
      updatedBy: 'current-user'
    };

    await this.alertEngine.registerRule(newRule);
    return newRule;
  }

  /**
   * Update alert rule
   */
  async updateRule(ruleId: string, updates: Partial<AlertRule>): Promise<AlertRule | null> {
    const rule = this.alertEngine.getActiveRules().find(r => r.id === ruleId);
    if (!rule) {
      return null;
    }

    const updatedRule = {
      ...rule,
      ...updates,
      updatedAt: new Date(),
      updatedBy: 'current-user'
    };

    await this.alertEngine.unregisterRule(ruleId);
    await this.alertEngine.registerRule(updatedRule);

    return updatedRule;
  }

  /**
   * Delete alert rule
   */
  async deleteRule(ruleId: string): Promise<boolean> {
    try {
      await this.alertEngine.unregisterRule(ruleId);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get alert rules
   */
  getRules(): AlertRule[] {
    return this.alertEngine.getActiveRules();
  }

  /**
   * Get active alerts
   */
  getActiveAlerts(filters?: any): Alert[] {
    return this.alertEngine.getActiveAlerts(filters);
  }

  /**
   * Acknowledge alert
   */
  async acknowledgeAlert(alertId: string, userId: string): Promise<boolean> {
    return await this.alertEngine.acknowledgeAlert(alertId, userId);
  }

  /**
   * Resolve alert
   */
  async resolveAlert(alertId: string, userId: string, reason?: string): Promise<boolean> {
    return await this.alertEngine.resolveAlert(alertId, userId, reason);
  }

  /**
   * Get alert statistics
   */
  getStatistics() {
    return this.alertEngine.getStatistics();
  }

  /**
   * Test notification
   */
  async testNotification(userId: string, channel: NotificationChannel): Promise<boolean> {
    const testAlert: Alert = {
      id: 'test-alert',
      ruleId: 'test-rule',
      ruleName: 'Test Notification',
      severity: AlertSeverity.INFO,
      status: AlertStatus.ACTIVE,
      title: 'Test Notification',
      message: 'This is a test notification to verify your notification settings.',
      source: {
        type: 'system',
        id: 'test',
        name: 'Test System'
      },
      trigger: {
        condition: 'test',
        value: 'test',
        threshold: 'test',
        triggeredAt: new Date()
      },
      createdAt: new Date(),
      updatedAt: new Date()
    };

    const preferences = await this.getUserPreferencesForAlert(testAlert);
    const userPrefs = preferences.get(userId);

    if (!userPrefs) {
      return false;
    }

    try {
      switch (channel) {
        case NotificationChannel.BROWSER_PUSH:
          await this.pushNotificationService.showAlertNotification(testAlert);
          return true;
        case NotificationChannel.EMAIL:
          await this.emailService.sendAlertNotification(testAlert, userPrefs.channels.email.addresses);
          return true;
        default:
          return false;
      }
    } catch (error) {
      console.error('Test notification failed:', error);
      return false;
    }
  }

  /**
   * Update user notification preferences
   */
  async updateUserPreferences(userId: string, preferences: UserNotificationPreferences): Promise<void> {
    this.userPreferences.set(userId, preferences);

    // In production, save to your preferences API
    console.log(`Updated preferences for user ${userId}`);
  }

  /**
   * Get user notification preferences
   */
  async getUserPreferences(userId: string): Promise<UserNotificationPreferences | null> {
    return this.userPreferences.get(userId) || null;
  }

  /**
   * Event emitter methods
   */
  private listeners: Map<string, Function[]> = new Map();

  on(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  off(event: string, callback: Function): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  private emit(event: string, data?: any): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  /**
   * Utility methods
   */
  private generateRuleId(): string {
    return `rule_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}