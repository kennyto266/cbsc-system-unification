/**
 * Notification Service
 * Handles browser push notifications, email, and SMS notifications
 */

import { Alert } from './alertService';

// Notification interfaces
export interface NotificationChannel {
  id: string;
  type: 'browser' | 'email' | 'sms' | 'webhook';
  name: string;
  description: string;
  isEnabled: boolean;
  config: Record<string, any>;
}

export interface NotificationTemplate {
  id: string;
  name: string;
  type: Alert['type'];
  priority: Alert['priority'];
  subject: string;
  body: string;
  variables: string[];
  defaultEnabled: boolean;
}

export interface NotificationSettings {
  userId: string;
  channels: NotificationChannel[];
  templates: NotificationTemplate[];
  frequency: {
    immediate: boolean;
    batchInterval: number; // minutes
    maxPerHour: number;
    quietHours: {
      enabled: boolean;
      start: string; // HH:mm
      end: string;   // HH:mm
    };
    weekends: boolean;
  };
  rules: {
    minPriority: Alert['priority']; // Only notify for this priority and above
    excludeResolved: boolean;
    groupSimilar: boolean;
    maxGroupSize: number;
  };
}

export interface Notification {
  id: string;
  alertId: string;
  channel: NotificationChannel['type'];
  template: string;
  recipient: string;
  subject: string;
  body: string;
  status: 'pending' | 'sent' | 'delivered' | 'failed';
  sentAt?: string;
  deliveredAt?: string;
  error?: string;
  metadata: Record<string, any>;
}

export interface NotificationStatistics {
  total: number;
  sent: number;
  delivered: number;
  failed: number;
  pending: number;
  byChannel: Record<NotificationChannel['type'], number>;
  successRate: number;
  avgDeliveryTime: number; // milliseconds
}

class NotificationService {
  private settings: NotificationSettings | null = null;
  private notificationQueue: Notification[] = [];
  private batchTimer: NodeJS.Timeout | null = null;
  private isPermissionGranted = false;

  constructor() {
    this.loadSettings();
    this.checkBrowserPermission();
    this.setupEventListeners();
  }

  // Browser notification setup
  private async checkBrowserPermission(): Promise<void> {
    if ('Notification' in window) {
      this.isPermissionGranted = Notification.permission === 'granted';
    }
  }

  private setupEventListeners(): void {
    // Listen for alert events
    window.addEventListener('alert-triggered', this.handleAlertTriggered.bind(this));

    // Listen for visibility changes to batch notifications when tab is hidden
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.processBatchNotifications();
      }
    });
  }

  // Permission management
  async requestBrowserPermission(): Promise<boolean> {
    if (!('Notification' in window)) {
      console.warn('Browser notifications not supported');
      return false;
    }

    if (Notification.permission === 'granted') {
      this.isPermissionGranted = true;
      return true;
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      this.isPermissionGranted = permission === 'granted';
      return this.isPermissionGranted;
    }

    return false;
  }

  // Settings management
  async loadSettings(): Promise<void> {
    try {
      const stored = localStorage.getItem('notificationSettings');
      if (stored) {
        this.settings = JSON.parse(stored);
      } else {
        // Initialize with default settings
        this.settings = this.getDefaultSettings();
        await this.saveSettings();
      }
    } catch (error) {
      console.error('Failed to load notification settings:', error);
      this.settings = this.getDefaultSettings();
    }
  }

  async saveSettings(): Promise<void> {
    if (!this.settings) return;

    try {
      localStorage.setItem('notificationSettings', JSON.stringify(this.settings));
    } catch (error) {
      console.error('Failed to save notification settings:', error);
    }
  }

  private getDefaultSettings(): NotificationSettings {
    return {
      userId: 'current-user',
      channels: [
        {
          id: 'browser-1',
          type: 'browser',
          name: 'Browser Notifications',
          description: 'Show notifications in your browser',
          isEnabled: true,
          config: {}
        },
        {
          id: 'email-1',
          type: 'email',
          name: 'Email',
          description: 'Receive notifications via email',
          isEnabled: false,
          config: {
            address: '',
            includeDetails: true
          }
        },
        {
          id: 'sms-1',
          type: 'sms',
          name: 'SMS',
          description: 'Receive critical alerts via SMS',
          isEnabled: false,
          config: {
            phoneNumber: '',
            countryCode: '+1'
          }
        }
      ],
      templates: this.getDefaultTemplates(),
      frequency: {
        immediate: true,
        batchInterval: 15, // 15 minutes
        maxPerHour: 10,
        quietHours: {
          enabled: false,
          start: '22:00',
          end: '07:00'
        },
        weekends: true
      },
      rules: {
        minPriority: 'medium',
        excludeResolved: false,
        groupSimilar: true,
        maxGroupSize: 5
      }
    };
  }

  private getDefaultTemplates(): NotificationTemplate[] {
    return [
      {
        id: 'critical-alert',
        name: 'Critical Alert',
        type: 'threshold',
        priority: 'critical',
        subject: '🚨 Critical Alert: {{alertTitle}}',
        body: 'A critical alert has been triggered:\n\n{{alertMessage}}\n\nSource: {{source}}\nTime: {{timestamp}}',
        variables: ['alertTitle', 'alertMessage', 'source', 'timestamp'],
        defaultEnabled: true
      },
      {
        id: 'high-alert',
        name: 'High Priority Alert',
        type: 'threshold',
        priority: 'high',
        subject: '⚠️ High Priority Alert: {{alertTitle}}',
        body: 'High priority alert detected:\n\n{{alertMessage}}',
        variables: ['alertTitle', 'alertMessage'],
        defaultEnabled: true
      },
      {
        id: 'medium-alert',
        name: 'Medium Priority Alert',
        type: 'threshold',
        priority: 'medium',
        subject: 'ℹ️ Alert: {{alertTitle}}',
        body: '{{alertMessage}}',
        variables: ['alertTitle', 'alertMessage'],
        defaultEnabled: true
      },
      {
        id: 'low-alert',
        name: 'Low Priority Alert',
        type: 'threshold',
        priority: 'low',
        subject: 'Information: {{alertTitle}}',
        body: '{{alertMessage}}',
        variables: ['alertTitle', 'alertMessage'],
        defaultEnabled: false
      }
    ];
  }

  // Getters
  getSettings(): NotificationSettings | null {
    return this.settings;
  }

  getEnabledChannels(): NotificationChannel[] {
    return this.settings?.channels.filter(c => c.isEnabled) || [];
  }

  getTemplate(alertType: Alert['type'], priority: Alert['priority']): NotificationTemplate | null {
    return this.settings?.templates.find(
      t => t.type === alertType && t.priority === priority
    ) || null;
  }

  // Notification processing
  private async handleAlertTriggered(event: CustomEvent): Promise<void> {
    const alert = event.detail as Alert;

    // Check if alert should be notified
    if (!this.shouldNotify(alert)) return;

    // Get enabled channels
    const channels = this.getEnabledChannels();
    if (channels.length === 0) return;

    // Get template
    const template = this.getTemplate(alert.type, alert.priority);
    if (!template) return;

    // Process notification for each channel
    for (const channel of channels) {
      await this.processNotification(alert, channel, template);
    }
  }

  private shouldNotify(alert: Alert): boolean {
    if (!this.settings) return false;

    // Check priority
    const priorities = ['low', 'medium', 'high', 'critical'];
    const alertPriorityIndex = priorities.indexOf(alert.priority);
    const minPriorityIndex = priorities.indexOf(this.settings.rules.minPriority);

    if (alertPriorityIndex < minPriorityIndex) return false;

    // Check if resolved
    if (this.settings.rules.excludeResolved && alert.status === 'resolved') return false;

    // Check quiet hours
    if (this.settings.frequency.quietHours.enabled) {
      const now = new Date();
      const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;

      if (this.isInQuietHours(currentTime, this.settings.frequency.quietHours.start, this.settings.frequency.quietHours.end)) {
        // Only allow critical alerts during quiet hours
        if (alert.priority !== 'critical') return false;
      }
    }

    // Check weekends
    if (!this.settings.frequency.weekends) {
      const dayOfWeek = new Date().getDay();
      if (dayOfWeek === 0 || dayOfWeek === 6) return false; // Sunday or Saturday
    }

    return true;
  }

  private isInQuietHours(current: string, start: string, end: string): boolean {
    const currentMinutes = this.timeToMinutes(current);
    const startMinutes = this.timeToMinutes(start);
    const endMinutes = this.timeToMinutes(end);

    if (startMinutes <= endMinutes) {
      // Same day (e.g., 22:00 to 07:00 crosses midnight)
      return currentMinutes >= startMinutes || currentMinutes <= endMinutes;
    } else {
      // Crosses midnight
      return currentMinutes >= startMinutes && currentMinutes <= endMinutes;
    }
  }

  private timeToMinutes(time: string): number {
    const [hours, minutes] = time.split(':').map(Number);
    return hours * 60 + minutes;
  }

  private async processNotification(alert: Alert, channel: NotificationChannel, template: NotificationTemplate): Promise<void> {
    // Prepare notification data
    const notificationData = {
      id: this.generateId(),
      alertId: alert.id,
      channel: channel.type,
      template: template.id,
      recipient: this.getRecipient(channel),
      subject: this.replaceVariables(template.subject, alert),
      body: this.replaceVariables(template.body, alert),
      status: 'pending' as const,
      metadata: {
        alert,
        channelConfig: channel.config
      }
    };

    // Check if immediate or batched
    if (this.settings?.frequency.immediate && alert.priority === 'critical') {
      // Send immediately for critical alerts
      await this.sendNotification(notificationData);
    } else {
      // Add to batch queue
      this.addToBatchQueue(notificationData);
    }
  }

  private getRecipient(channel: NotificationChannel): string {
    switch (channel.type) {
      case 'browser':
        return 'browser';
      case 'email':
        return channel.config.address || '';
      case 'sms':
        return channel.config.phoneNumber || '';
      case 'webhook':
        return channel.config.url || '';
      default:
        return '';
    }
  }

  private replaceVariables(template: string, alert: Alert): string {
    return template
      .replace(/\{\{alertTitle\}\}/g, alert.title)
      .replace(/\{\{alertMessage\}\}/g, alert.message)
      .replace(/\{\{source\}\}/g, alert.source)
      .replace(/\{\{type\}\}/g, alert.type)
      .replace(/\{\{priority\}\}/g, alert.priority)
      .replace(/\{\{timestamp\}\}/g, new Date(alert.triggeredAt).toLocaleString());
  }

  private addToBatchQueue(notification: Notification): void {
    this.notificationQueue.push(notification);

    // Start batch timer if not already running
    if (!this.batchTimer) {
      this.batchTimer = setTimeout(() => {
        this.processBatchNotifications();
      }, this.settings?.frequency.batchInterval * 60 * 1000 || 15 * 60 * 1000);
    }
  }

  private async processBatchNotifications(): Promise<void> {
    if (this.notificationQueue.length === 0) return;

    const batch = [...this.notificationQueue];
    this.notificationQueue = [];

    // Clear batch timer
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }

    // Group similar notifications if enabled
    if (this.settings?.rules.groupSimilar) {
      const grouped = this.groupSimilarNotifications(batch);
      for (const group of grouped) {
        await this.sendNotificationGroup(group);
      }
    } else {
      // Send individually
      for (const notification of batch) {
        await this.sendNotification(notification);
      }
    }
  }

  private groupSimilarNotifications(notifications: Notification[]): Notification[][] {
    const groups: Record<string, Notification[]> = {};

    notifications.forEach(notification => {
      // Group by channel, template, and alert type
      const key = `${notification.channel}-${notification.template}-${notification.metadata.alert.type}`;

      if (!groups[key]) {
        groups[key] = [];
      }

      groups[key].push(notification);

      // Limit group size
      if (groups[key].length >= (this.settings?.rules.maxGroupSize || 5)) {
        // Start a new group
        groups[key + '-' + Date.now()] = groups[key].splice(this.settings?.rules.maxGroupSize || 5);
      }
    });

    return Object.values(groups);
  }

  private async sendNotificationGroup(group: Notification[]): Promise<void> {
    if (group.length === 1) {
      await this.sendNotification(group[0]);
      return;
    }

    // Create summary notification
    const summary: Notification = {
      ...group[0],
      id: this.generateId(),
      subject: `Multiple ${group[0].metadata.alert.type} alerts`,
      body: `${group.length} alerts detected:\n\n` +
            group.map(n => `• ${n.metadata.alert.title}`).join('\n'),
      metadata: {
        ...group[0].metadata,
        isGrouped: true,
        originalNotifications: group.map(n => n.id)
      }
    };

    await this.sendNotification(summary);

    // Mark all as sent
    group.forEach(notification => {
      notification.status = 'sent';
      notification.sentAt = new Date().toISOString();
    });
  }

  private async sendNotification(notification: Notification): Promise<void> {
    try {
      const startTime = Date.now();

      switch (notification.channel) {
        case 'browser':
          await this.sendBrowserNotification(notification);
          break;
        case 'email':
          await this.sendEmailNotification(notification);
          break;
        case 'sms':
          await this.sendSMSNotification(notification);
          break;
        case 'webhook':
          await this.sendWebhookNotification(notification);
          break;
        default:
          console.warn(`Unknown notification channel: ${notification.channel}`);
      }

      const deliveryTime = Date.now() - startTime;

      // Update notification status
      notification.status = 'delivered';
      notification.deliveredAt = new Date().toISOString();
      notification.metadata.deliveryTime = deliveryTime;

    } catch (error) {
      console.error(`Failed to send ${notification.channel} notification:`, error);
      notification.status = 'failed';
      notification.error = error instanceof Error ? error.message : 'Unknown error';
    }
  }

  private async sendBrowserNotification(notification: Notification): Promise<void> {
    if (!this.isPermissionGranted) {
      throw new Error('Browser notification permission not granted');
    }

    const browserNotification = new Notification(notification.subject, {
      body: notification.body,
      icon: '/favicon.ico',
      tag: notification.alertId, // Group similar notifications
      requireInteraction: notification.metadata.alert.priority === 'critical',
      data: {
        alertId: notification.alertId,
        url: `/alerts/${notification.alertId}`
      }
    });

    // Handle click
    browserNotification.onclick = () => {
      window.focus();
      browserNotification.close();
      // Navigate to alert details
      if (browserNotification.data?.url) {
        window.location.href = browserNotification.data.url;
      }
    };

    // Auto-close after 5 seconds for non-critical alerts
    if (notification.metadata.alert.priority !== 'critical') {
      setTimeout(() => {
        browserNotification.close();
      }, 5000);
    }
  }

  private async sendEmailNotification(notification: Notification): Promise<void> {
    // This would integrate with an email service
    // For now, just log it
    console.log('Email notification:', {
      to: notification.recipient,
      subject: notification.subject,
      body: notification.body
    });

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  private async sendSMSNotification(notification: Notification): Promise<void> {
    // This would integrate with an SMS service like Twilio
    // For now, just log it
    console.log('SMS notification:', {
      to: notification.recipient,
      message: `${notification.subject}: ${notification.body}`
    });

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  private async sendWebhookNotification(notification: Notification): Promise<void> {
    // This would send a POST request to a webhook URL
    // For now, just log it
    console.log('Webhook notification:', {
      url: notification.recipient,
      payload: {
        alert: notification.metadata.alert,
        subject: notification.subject,
        body: notification.body
      }
    });

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  // Statistics
  getStatistics(): NotificationStatistics {
    // This would typically fetch from a backend
    // For now, return mock statistics
    return {
      total: 0,
      sent: 0,
      delivered: 0,
      failed: 0,
      pending: 0,
      byChannel: {
        browser: 0,
        email: 0,
        sms: 0,
        webhook: 0
      },
      successRate: 0,
      avgDeliveryTime: 0
    };
  }

  // Settings updates
  async updateSettings(updates: Partial<NotificationSettings>): Promise<void> {
    if (!this.settings) return;

    this.settings = {
      ...this.settings,
      ...updates
    };

    await this.saveSettings();
  }

  async updateChannel(channelId: string, updates: Partial<NotificationChannel>): Promise<void> {
    if (!this.settings) return;

    const channelIndex = this.settings.channels.findIndex(c => c.id === channelId);
    if (channelIndex === -1) return;

    this.settings.channels[channelIndex] = {
      ...this.settings.channels[channelIndex],
      ...updates
    };

    await this.saveSettings();
  }

  async updateTemplate(templateId: string, updates: Partial<NotificationTemplate>): Promise<void> {
    if (!this.settings) return;

    const templateIndex = this.settings.templates.findIndex(t => t.id === templateId);
    if (templateIndex === -1) return;

    this.settings.templates[templateIndex] = {
      ...this.settings.templates[templateIndex],
      ...updates
    };

    await this.saveSettings();
  }

  // Test notification
  async testNotification(channelId: string): Promise<boolean> {
    if (!this.settings) return false;

    const channel = this.settings.channels.find(c => c.id === channelId);
    if (!channel) return false;

    const testNotification: Notification = {
      id: this.generateId(),
      alertId: 'test',
      channel: channel.type,
      template: 'test',
      recipient: this.getRecipient(channel),
      subject: 'Test Notification',
      body: 'This is a test notification to verify your settings are working correctly.',
      status: 'pending',
      metadata: {
        channelConfig: channel.config,
        alert: {
          id: 'test',
          title: 'Test Alert',
          message: 'This is a test alert',
          type: 'threshold',
          source: 'test',
          priority: 'medium',
          status: 'active',
          triggeredAt: new Date().toISOString(),
          isAggregated: false,
          userId: this.settings.userId
        }
      }
    };

    try {
      await this.sendNotification(testNotification);
      return true;
    } catch (error) {
      console.error('Test notification failed:', error);
      return false;
    }
  }

  // Utility
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }
}

// Singleton instance
export const notificationService = new NotificationService();

// Export types
export type { NotificationService };