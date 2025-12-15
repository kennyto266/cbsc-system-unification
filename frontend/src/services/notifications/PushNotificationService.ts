/**
 * Push Notification Service
 * Manages browser push notifications and service worker registration
 */

import {
  PushNotificationPayload,
  NotificationAction,
  NotificationChannel,
  AlertSeverity,
  Alert
} from '../alerts/types';

export interface PushNotificationConfig {
  publicKey: string;
  serverKey?: string;
  vapidPublicKey: string;
}

export interface PushSubscription {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
}

export interface PermissionStatus {
  granted: boolean;
  denied: boolean;
  default: boolean;
}

export class PushNotificationService {
  private registration: ServiceWorkerRegistration | null = null;
  private subscription: PushSubscription | null = null;
  private config: PushNotificationConfig;
  private isSupported: boolean = false;
  private listeners: Map<string, Function[]> = new Map();

  constructor(config: PushNotificationConfig) {
    this.config = config;
    this.checkSupport();
  }

  /**
   * Check if push notifications are supported
   */
  private checkSupport(): void {
    this.isSupported = 'serviceWorker' in navigator &&
                     'PushManager' in window &&
                     'Notification' in window;

    if (!this.isSupported) {
      console.warn('Push notifications are not supported in this browser');
    }
  }

  /**
   * Initialize the push notification service
   */
  async initialize(): Promise<boolean> {
    if (!this.isSupported) {
      return false;
    }

    try {
      // Register service worker
      await this.registerServiceWorker();

      // Get existing subscription
      await this.getSubscription();

      // Setup message listener
      this.setupMessageListener();

      console.log('Push notification service initialized');
      return true;
    } catch (error) {
      console.error('Failed to initialize push notification service:', error);
      return false;
    }
  }

  /**
   * Register service worker
   */
  private async registerServiceWorker(): Promise<void> {
    if ('serviceWorker' in navigator) {
      this.registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      });

      // Wait for service worker to be ready
      await navigator.serviceWorker.ready;

      console.log('Service worker registered successfully');
    }
  }

  /**
   * Get existing push subscription
   */
  private async getSubscription(): Promise<void> {
    if (!this.registration) {
      return;
    }

    try {
      this.subscription = await this.registration.pushManager.getSubscription();

      if (this.subscription) {
        console.log('Existing push subscription found');
        this.emit('subscription_updated', this.subscription);
      }
    } catch (error) {
      console.error('Failed to get push subscription:', error);
    }
  }

  /**
   * Request permission for notifications
   */
  async requestPermission(): Promise<PermissionStatus> {
    if (!this.isSupported) {
      return { granted: false, denied: true, default: false };
    }

    const permission = await Notification.requestPermission();

    const status: PermissionStatus = {
      granted: permission === 'granted',
      denied: permission === 'denied',
      default: permission === 'default'
    };

    this.emit('permission_changed', status);

    return status;
  }

  /**
   * Get current permission status
   */
  getPermissionStatus(): PermissionStatus {
    if (!this.isSupported) {
      return { granted: false, denied: true, default: false };
    }

    const permission = Notification.permission;
    return {
      granted: permission === 'granted',
      denied: permission === 'denied',
      default: permission === 'default'
    };
  }

  /**
   * Subscribe to push notifications
   */
  async subscribe(userIdentifier?: string): Promise<PushSubscription | null> {
    if (!this.isSupported || !this.registration) {
      throw new Error('Push notifications not supported or service worker not registered');
    }

    const permission = this.getPermissionStatus();
    if (!permission.granted) {
      throw new Error('Notification permission not granted');
    }

    try {
      // Create application server key
      const applicationServerKey = this.urlB64ToUint8Array(this.config.vapidPublicKey);

      // Subscribe to push
      this.subscription = await this.registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey
      });

      console.log('Successfully subscribed to push notifications');

      // Send subscription to server
      await this.sendSubscriptionToServer(this.subscription, userIdentifier);

      this.emit('subscription_created', this.subscription);

      return this.subscription;
    } catch (error) {
      console.error('Failed to subscribe to push notifications:', error);
      throw error;
    }
  }

  /**
   * Unsubscribe from push notifications
   */
  async unsubscribe(): Promise<boolean> {
    if (!this.subscription) {
      return true;
    }

    try {
      const successful = await this.subscription.unsubscribe();

      if (successful) {
        // Remove from server
        await this.removeSubscriptionFromServer(this.subscription);

        this.subscription = null;
        console.log('Successfully unsubscribed from push notifications');
        this.emit('subscription_removed');
      }

      return successful;
    } catch (error) {
      console.error('Failed to unsubscribe from push notifications:', error);
      return false;
    }
  }

  /**
   * Send push notification (server-side)
   * This would be called from the server
   */
  async sendNotification(payload: PushNotificationPayload): Promise<void> {
    // This method would be implemented on the server
    // Frontend just prepares the payload
    console.log('Preparing push notification:', payload);
  }

  /**
   * Show local notification (fallback when push is not available)
   */
  async showLocalNotification(
    payload: PushNotificationPayload,
    options?: NotificationOptions
  ): Promise<Notification | null> {
    if (!this.isSupported) {
      return null;
    }

    const permission = this.getPermissionStatus();
    if (!permission.granted) {
      console.warn('Notification permission not granted');
      return null;
    }

    try {
      // Create notification options
      const notificationOptions: NotificationOptions = {
        body: payload.body,
        icon: payload.icon || '/static/icons/icon-192x192.png',
        badge: payload.badge || '/static/icons/badge-72x72.png',
        tag: payload.tag,
        data: payload.data,
        actions: this.convertActions(payload.actions),
        requireInteraction: payload.requireInteraction || false,
        silent: payload.silent || false,
        image: payload.image,
        ...options
      };

      // Show notification
      const notification = new Notification(payload.title, notificationOptions);

      // Setup click handlers
      this.setupNotificationClickHandlers(notification, payload);

      // Auto-close after 5 seconds if not critical
      if (!payload.requireInteraction) {
        setTimeout(() => {
          notification.close();
        }, 5000);
      }

      this.emit('notification_shown', { notification, payload });

      return notification;
    } catch (error) {
      console.error('Failed to show local notification:', error);
      return null;
    }
  }

  /**
   * Show notification for alert
   */
  async showAlertNotification(alert: Alert): Promise<Notification | null> {
    const severityConfig = {
      [AlertSeverity.INFO]: {
        icon: '/static/icons/info-icon.png',
        requireInteraction: false,
        vibrate: [200]
      },
      [AlertSeverity.WARNING]: {
        icon: '/static/icons/warning-icon.png',
        requireInteraction: false,
        vibrate: [200, 100, 200]
      },
      [AlertSeverity.CRITICAL]: {
        icon: '/static/icons/critical-icon.png',
        requireInteraction: true,
        vibrate: [200, 100, 200, 100, 200, 100, 200]
      }
    };

    const config = severityConfig[alert.severity] || severityConfig[AlertSeverity.INFO];

    const payload: PushNotificationPayload = {
      title: alert.title,
      body: alert.message,
      icon: config.icon,
      tag: `alert-${alert.id}`,
      data: {
        alertId: alert.id,
        severity: alert.severity,
        source: alert.source,
        timestamp: alert.createdAt.toISOString()
      },
      actions: [
        {
          action: 'view-alert',
          title: 'View',
          icon: '/static/icons/view-icon.png'
        },
        {
          action: alert.severity === AlertSeverity.CRITICAL ? 'resolve' : 'acknowledge',
          title: alert.severity === AlertSeverity.CRITICAL ? 'Resolve' : 'Ack',
          icon: '/static/icons/check-icon.png'
        }
      ],
      requireInteraction: config.requireInteraction,
      vibrate: config.vibrate
    };

    return this.showLocalNotification(payload);
  }

  /**
   * Convert action objects to NotificationAction format
   */
  private convertActions(actions?: NotificationAction[]): NotificationAction[] | undefined {
    if (!actions) {
      return undefined;
    }

    return actions.map(action => ({
      action: action.action,
      title: action.title,
      icon: action.icon
    }));
  }

  /**
   * Setup click handlers for notification
   */
  private setupNotificationClickHandlers(
    notification: Notification,
    payload: PushNotificationPayload
  ): void {
    notification.onclick = (event) => {
      event.preventDefault();

      // Close notification
      notification.close();

      // Handle click based on action or default
      this.handleNotificationClick('default', payload);
    };
  }

  /**
   * Handle notification click
   */
  private handleNotificationClick(action: string, payload: PushNotificationPayload): void {
    const data = payload.data || {};

    // Navigate based on action
    const url = this.getUrlForAction(action, data);
    if (url) {
      window.open(url, '_blank');
    }

    // Emit event for application to handle
    this.emit('notification_clicked', { action, payload, url });
  }

  /**
   * Get URL for notification action
   */
  private getUrlForAction(action: string, data: any): string | null {
    const baseUrl = window.location.origin;

    switch (action) {
      case 'view-alert':
        return data.alertId ? `${baseUrl}/alerts/${data.alertId}` : `${baseUrl}/alerts`;
      case 'acknowledge':
      case 'resolve':
        // These would update the alert status
        this.updateAlertStatus(data.alertId, action);
        return `${baseUrl}/alerts`;
      case 'view-strategy':
        return data.strategyId ? `${baseUrl}/strategies/${data.strategyId}` : `${baseUrl}/strategies`;
      case 'view-portfolio':
        return `${baseUrl}/portfolio`;
      case 'view-dashboard':
        return `${baseUrl}/dashboard`;
      default:
        return `${baseUrl}/notifications`;
    }
  }

  /**
   * Update alert status
   */
  private async updateAlertStatus(alertId: string, action: string): Promise<void> {
    try {
      const response = await fetch(`/api/alerts/${alertId}/status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          status: action === 'acknowledge' ? 'acknowledged' : 'resolved'
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to update alert status: ${response.statusText}`);
      }

      this.emit('alert_status_updated', { alertId, action });
    } catch (error) {
      console.error('Failed to update alert status:', error);
    }
  }

  /**
   * Send subscription to server
   */
  private async sendSubscriptionToServer(
    subscription: PushSubscription,
    userIdentifier?: string
  ): Promise<void> {
    try {
      await fetch('/api/notifications/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          subscription,
          userIdentifier,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString()
        })
      });
    } catch (error) {
      console.error('Failed to send subscription to server:', error);
    }
  }

  /**
   * Remove subscription from server
   */
  private async removeSubscriptionFromServer(subscription: PushSubscription): Promise<void> {
    try {
      await fetch('/api/notifications/unsubscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          subscription: {
            endpoint: subscription.endpoint
          }
        })
      });
    } catch (error) {
      console.error('Failed to remove subscription from server:', error);
    }
  }

  /**
   * Setup message listener from service worker
   */
  private setupMessageListener(): void {
    navigator.serviceWorker.addEventListener('message', (event) => {
      const { type, payload } = event.data;

      switch (type) {
        case 'NOTIFICATION_CLICK':
          this.handleNotificationClick(payload.action, payload.data);
          break;
        case 'ALERT_TRIGGERED':
          this.emit('alert_triggered', payload);
          break;
        case 'SUBSCRIPTION_UPDATED':
          this.emit('subscription_updated', payload);
          break;
        default:
          console.log('Unknown message type:', type);
      }
    });
  }

  /**
   * Event emitter methods
   */
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
   * Utility function to convert URL base64 to Uint8Array
   */
  private urlB64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/\-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }

    return outputArray;
  }

  /**
   * Check if push notifications are enabled
   */
  isEnabled(): boolean {
    return this.isSupported && this.getPermissionStatus().granted && !!this.subscription;
  }

  /**
   * Get subscription details
   */
  getSubscription(): PushSubscription | null {
    return this.subscription;
  }

  /**
   * Clear all notifications
   */
  clearAllNotifications(): void {
    if (this.isSupported) {
      // Close all visible notifications
      const notifications = document.querySelectorAll('.notification');
      notifications.forEach(notification => {
        const notificationObj = notification as any;
        if (notificationObj.close) {
          notificationObj.close();
        }
      });
    }
  }
}