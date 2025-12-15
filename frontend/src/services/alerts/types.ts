/**
 * Alert System Type Definitions
 * Core types for alerts, notifications, and rules
 */

// Alert severity levels
export enum AlertSeverity {
  INFO = 'info',
  WARNING = 'warning',
  CRITICAL = 'critical'
}

// Alert status
export enum AlertStatus {
  ACTIVE = 'active',
  ACKNOWLEDGED = 'acknowledged',
  RESOLVED = 'resolved',
  SUPPRESSED = 'suppressed'
}

// Alert rule operator types
export enum AlertOperator {
  EQUALS = 'eq',
  NOT_EQUALS = 'ne',
  GREATER_THAN = 'gt',
  GREATER_THAN_OR_EQUAL = 'gte',
  LESS_THAN = 'lt',
  LESS_THAN_OR_EQUAL = 'lte',
  CONTAINS = 'contains',
  NOT_CONTAINS = 'not_contains',
  IN = 'in',
  NOT_IN = 'not_in',
  REGEX = 'regex'
}

// Alert rule condition types
export enum AlertConditionType {
  METRIC = 'metric',
  EVENT = 'event',
  SYSTEM = 'system',
  CUSTOM = 'custom'
}

// Notification channel types
export enum NotificationChannel {
  BROWSER_PUSH = 'browser_push',
  EMAIL = 'email',
  SMS = 'sms',
  WEBHOOK = 'webhook',
  SLACK = 'slack',
  TEAMS = 'teams'
}

// Alert interface
export interface Alert {
  id: string;
  ruleId: string;
  ruleName: string;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  message: string;
  description?: string;
  source: {
    type: string;
    id: string;
    name: string;
  };
  trigger: {
    condition: string;
    value: any;
    threshold: any;
    triggeredAt: Date;
  };
  metadata?: Record<string, any>;
  acknowledgedAt?: Date;
  acknowledgedBy?: string;
  resolvedAt?: Date;
  resolvedBy?: string;
  createdAt: Date;
  updatedAt: Date;
  notifications?: Notification[];
}

// Alert rule interface
export interface AlertRule {
  id: string;
  name: string;
  description?: string;
  enabled: boolean;
  severity: AlertSeverity;
  conditions: AlertCondition[];
  notificationChannels: NotificationChannel[];
  cooldownPeriod: number; // minutes
  quietHours?: {
    enabled: boolean;
    startTime: string; // HH:MM
    endTime: string; // HH:MM
    timezone: string;
  };
  escalationPolicy?: {
    enabled: boolean;
    levels: EscalationLevel[];
  };
  throttle: {
    enabled: boolean;
    maxAlerts: number;
    windowMinutes: number;
  };
  deduplication: {
    enabled: boolean;
    windowMinutes: number;
    key: string[];
  };
  tags: string[];
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;
  updatedBy: string;
}

// Alert condition interface
export interface AlertCondition {
  id: string;
  type: AlertConditionType;
  field: string;
  operator: AlertOperator;
  value: any;
  aggregation?: string; // avg, sum, count, min, max
  timeWindow?: number; // minutes
  groupBy?: string[];
  description?: string;
}

// Escalation level interface
export interface EscalationLevel {
  level: number;
  delayMinutes: number;
  severity: AlertSeverity;
  channels: NotificationChannel[];
  additionalRecipients?: string[];
}

// Notification interface
export interface Notification {
  id: string;
  alertId: string;
  channel: NotificationChannel;
  recipient: string;
  status: NotificationStatus;
  sentAt?: Date;
  deliveredAt?: Date;
  readAt?: Date;
  error?: string;
  retryCount: number;
  metadata?: Record<string, any>;
}

// Notification status
export enum NotificationStatus {
  PENDING = 'pending',
  SENT = 'sent',
  DELIVERED = 'delivered',
  READ = 'read',
  FAILED = 'failed'
}

// Push notification payload
export interface PushNotificationPayload {
  title: string;
  body: string;
  icon?: string;
  badge?: string;
  tag?: string;
  data?: Record<string, any>;
  actions?: NotificationAction[];
  requireInteraction?: boolean;
  silent?: boolean;
}

// Notification action
export interface NotificationAction {
  action: string;
  title: string;
  icon?: string;
}

// Email notification payload
export interface EmailNotificationPayload {
  to: string[];
  cc?: string[];
  bcc?: string[];
  subject: string;
  template: string;
  data: Record<string, any>;
  attachments?: EmailAttachment[];
}

// Email attachment
export interface EmailAttachment {
  filename: string;
  content: string | Buffer;
  contentType: string;
}

// SMS notification payload
export interface SMSNotificationPayload {
  to: string;
  message: string;
  metadata?: Record<string, any>;
}

// Webhook notification payload
export interface WebhookNotificationPayload {
  url: string;
  method: 'POST' | 'PUT' | 'PATCH';
  headers?: Record<string, string>;
  payload: Record<string, any>;
  timeout?: number;
  retries?: number;
}

// User notification preferences
export interface UserNotificationPreferences {
  userId: string;
  channels: {
    browser_push: {
      enabled: boolean;
      quietHours: boolean;
      quietStartTime: string;
      quietEndTime: string;
    };
    email: {
      enabled: boolean;
      addresses: string[];
      frequency: 'immediate' | 'hourly' | 'daily';
    };
    sms: {
      enabled: boolean;
      phoneNumber: string;
      verified: boolean;
    };
  };
  severityFilters: {
    [AlertSeverity.INFO]: boolean;
    [AlertSeverity.WARNING]: boolean;
    [AlertSeverity.CRITICAL]: boolean;
  };
  quietHours: {
    enabled: boolean;
    startTime: string;
    endTime: string;
    timezone: string;
  };
}

// Alert statistics
export interface AlertStatistics {
  total: number;
  active: number;
  acknowledged: number;
  resolved: number;
  suppressed: number;
  bySeverity: {
    [key in AlertSeverity]: number;
  };
  bySource: Record<string, number>;
  averageResolutionTime: number; // minutes
  acknowledgmentRate: number; // percentage
}

// Alert history query
export interface AlertHistoryQuery {
  startDate?: Date;
  endDate?: Date;
  severity?: AlertSeverity[];
  status?: AlertStatus[];
  source?: string[];
  ruleId?: string[];
  tags?: string[];
  search?: string;
  page?: number;
  limit?: number;
}

// Alert rule builder configuration
export interface AlertRuleBuilderConfig {
  sources: AlertSourceDefinition[];
  fields: AlertFieldDefinition[];
  operators: AlertOperatorDefinition[];
  aggregations: AlertAggregationDefinition[];
}

// Alert source definition
export interface AlertSourceDefinition {
  type: string;
  name: string;
  description: string;
  fields: string[];
  icon?: string;
  color?: string;
}

// Alert field definition
export interface AlertFieldDefinition {
  field: string;
  name: string;
  type: 'string' | 'number' | 'boolean' | 'date' | 'array' | 'object';
  description: string;
  unit?: string;
  example?: any;
}

// Alert operator definition
export interface AlertOperatorDefinition {
  operator: AlertOperator;
  name: string;
  description: string;
  supportedTypes: string[];
}

// Alert aggregation definition
export interface AlertAggregationDefinition {
  aggregation: string;
  name: string;
  description: string;
  requiresGroupBy: boolean;
  example: string;
}

// Alert test result
export interface AlertTestResult {
  success: boolean;
  triggered: boolean;
  condition: string;
  actualValue: any;
  expectedValue: any;
  error?: string;
  duration: number; // milliseconds
  sampleSize: number;
}

// Alert export/import
export interface AlertRuleExport {
  version: string;
  exportedAt: Date;
  rules: Omit<AlertRule, 'id' | 'createdAt' | 'updatedAt' | 'createdBy' | 'updatedBy'>[];
  metadata?: {
    exportBy: string;
    description?: string;
  };
}

// Real-time alert events
export interface AlertEvent {
  type: 'alert_triggered' | 'alert_acknowledged' | 'alert_resolved' | 'alert_suppressed';
  alertId: string;
  userId?: string;
  timestamp: Date;
  data?: Record<string, any>;
}

// Export all types
export type {
  Alert,
  AlertRule,
  AlertCondition,
  AlertStatistics,
  AlertHistoryQuery,
  AlertTestResult,
  Notification,
  PushNotificationPayload,
  EmailNotificationPayload,
  SMSNotificationPayload,
  WebhookNotificationPayload,
  UserNotificationPreferences,
  AlertRuleBuilderConfig,
  AlertSourceDefinition,
  AlertFieldDefinition,
  AlertOperatorDefinition,
  AlertAggregationDefinition,
  AlertRuleExport,
  AlertEvent,
  EscalationLevel,
  EmailAttachment,
  NotificationAction
};