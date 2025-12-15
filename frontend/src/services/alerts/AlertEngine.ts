/**
 * Alert Engine
 * Core engine for processing alert rules and triggering notifications
 */

import { EventEmitter } from 'events';
import {
  Alert,
  AlertRule,
  AlertCondition,
  AlertSeverity,
  AlertStatus,
  AlertOperator,
  NotificationChannel,
  AlertEvent
} from './types';

export interface AlertEngineConfig {
  maxConcurrentEvaluations: number;
  evaluationTimeoutMs: number;
  batchSize: number;
  metricsRetentionDays: number;
  defaultCooldownMinutes: number;
}

export interface EvaluationContext {
  timestamp: Date;
  userId?: string;
  source: string;
  data: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface RuleEvaluationResult {
  ruleId: string;
  triggered: boolean;
  condition?: string;
  value?: any;
  threshold?: any;
  error?: string;
  duration: number;
}

export class AlertEngine extends EventEmitter {
  private rules: Map<string, AlertRule> = new Map();
  private activeAlerts: Map<string, Alert> = new Map();
  private recentEvaluations: Map<string, Date> = new Map();
  private config: AlertEngineConfig;
  private evaluationQueue: Array<() => Promise<void>> = [];
  private isProcessingQueue = false;

  constructor(config: Partial<AlertEngineConfig> = {}) {
    super();
    this.config = {
      maxConcurrentEvaluations: 10,
      evaluationTimeoutMs: 5000,
      batchSize: 100,
      metricsRetentionDays: 90,
      defaultCooldownMinutes: 5,
      ...config
    };

    // Setup periodic cleanup
    setInterval(() => this.cleanup(), 60 * 60 * 1000); // Every hour
  }

  /**
   * Register an alert rule
   */
  async registerRule(rule: AlertRule): Promise<void> {
    // Validate rule
    this.validateRule(rule);

    // Store rule
    this.rules.set(rule.id, rule);

    // Emit event
    this.emit('rule_registered', { ruleId: rule.id, rule });

    console.log(`Alert rule registered: ${rule.name} (${rule.id})`);
  }

  /**
   * Unregister an alert rule
   */
  async unregisterRule(ruleId: string): Promise<void> {
    const rule = this.rules.get(ruleId);
    if (rule) {
      this.rules.delete(ruleId);

      // Suppress active alerts from this rule
      const alertsToSuppress = Array.from(this.activeAlerts.values())
        .filter(alert => alert.ruleId === ruleId && alert.status === AlertStatus.ACTIVE);

      for (const alert of alertsToSuppress) {
        await this.suppressAlert(alert.id, 'Rule unregistered');
      }

      this.emit('rule_unregistered', { ruleId });
      console.log(`Alert rule unregistered: ${ruleId}`);
    }
  }

  /**
   * Evaluate alert rules against provided data
   */
  async evaluateRules(
    rules?: string[],
    context: EvaluationContext
  ): Promise<RuleEvaluationResult[]> {
    const rulesToEvaluate = rules
      ? rules.map(id => this.rules.get(id)).filter(Boolean) as AlertRule[]
      : Array.from(this.rules.values()).filter(rule => rule.enabled);

    if (rulesToEvaluate.length === 0) {
      return [];
    }

    const results: RuleEvaluationResult[] = [];

    // Process rules in batches
    for (let i = 0; i < rulesToEvaluate.length; i += this.config.batchSize) {
      const batch = rulesToEvaluate.slice(i, i + this.config.batchSize);
      const batchResults = await Promise.all(
        batch.map(rule => this.evaluateRule(rule, context))
      );
      results.push(...batchResults);
    }

    return results;
  }

  /**
   * Evaluate a single alert rule
   */
  private async evaluateRule(
    rule: AlertRule,
    context: EvaluationContext
  ): Promise<RuleEvaluationResult> {
    const startTime = Date.now();

    try {
      // Check cooldown period
      if (this.isInCooldown(rule.id, rule.cooldownPeriod)) {
        return {
          ruleId: rule.id,
          triggered: false,
          duration: Date.now() - startTime
        };
      }

      // Check quiet hours
      if (this.isInQuietHours(rule)) {
        return {
          ruleId: rule.id,
          triggered: false,
          duration: Date.now() - startTime
        };
      }

      // Evaluate conditions
      const evaluationResult = await this.evaluateConditions(rule.conditions, context);

      if (evaluationResult.triggered) {
        // Check throttling
        if (rule.throttle.enabled && this.isThrottled(rule)) {
          return {
            ruleId: rule.id,
            triggered: false,
            duration: Date.now() - startTime
          };
        }

        // Check deduplication
        let deduplicationKey: string | undefined;
        if (rule.deduplication.enabled) {
          deduplicationKey = this.generateDeduplicationKey(rule, context);
          if (this.isDuplicate(deduplicationKey, rule.deduplication.windowMinutes)) {
            return {
              ruleId: rule.id,
              triggered: false,
              duration: Date.now() - startTime
            };
          }
        }

        // Create alert
        const alert = await this.createAlert(rule, context, evaluationResult);

        // Update cooldown
        this.updateCooldown(rule.id, rule.cooldownPeriod);

        // Update deduplication tracking
        if (deduplicationKey) {
          this.updateDeduplication(deduplicationKey, rule.deduplication.windowMinutes);
        }

        // Update throttling counter
        if (rule.throttle.enabled) {
          this.updateThrottling(rule);
        }

        // Emit alert triggered event
        this.emit('alert_triggered', { alert, rule, context });

        return {
          ruleId: rule.id,
          triggered: true,
          condition: evaluationResult.condition,
          value: evaluationResult.value,
          threshold: evaluationResult.threshold,
          duration: Date.now() - startTime
        };
      }

      return {
        ruleId: rule.id,
        triggered: false,
        duration: Date.now() - startTime
      };

    } catch (error) {
      console.error(`Error evaluating rule ${rule.id}:`, error);

      this.emit('rule_evaluation_error', {
        ruleId: rule.id,
        error: error instanceof Error ? error.message : String(error),
        context
      });

      return {
        ruleId: rule.id,
        triggered: false,
        error: error instanceof Error ? error.message : String(error),
        duration: Date.now() - startTime
      };
    }
  }

  /**
   * Evaluate rule conditions
   */
  private async evaluateConditions(
    conditions: AlertCondition[],
    context: EvaluationContext
  ): Promise<{ triggered: boolean; condition?: string; value?: any; threshold?: any }> {
    if (conditions.length === 0) {
      return { triggered: false };
    }

    // For now, implement simple AND logic
    // TODO: Support complex logical operators (AND, OR, NOT)
    for (const condition of conditions) {
      const result = await this.evaluateCondition(condition, context);
      if (!result) {
        return { triggered: false };
      }
    }

    // Return the first condition's details for now
    const firstCondition = conditions[0];
    const value = this.getFieldValue(firstCondition.field, context);

    return {
      triggered: true,
      condition: this.buildConditionString(firstCondition),
      value,
      threshold: firstCondition.value
    };
  }

  /**
   * Evaluate a single condition
   */
  private async evaluateCondition(
    condition: AlertCondition,
    context: EvaluationContext
  ): Promise<boolean> {
    const value = this.getFieldValue(condition.field, context);
    const threshold = condition.value;

    switch (condition.operator) {
      case AlertOperator.EQUALS:
        return value === threshold;

      case AlertOperator.NOT_EQUALS:
        return value !== threshold;

      case AlertOperator.GREATER_THAN:
        return Number(value) > Number(threshold);

      case AlertOperator.GREATER_THAN_OR_EQUAL:
        return Number(value) >= Number(threshold);

      case AlertOperator.LESS_THAN:
        return Number(value) < Number(threshold);

      case AlertOperator.LESS_THAN_OR_EQUAL:
        return Number(value) <= Number(threshold);

      case AlertOperator.CONTAINS:
        return String(value).includes(String(threshold));

      case AlertOperator.NOT_CONTAINS:
        return !String(value).includes(String(threshold));

      case AlertOperator.IN:
        return Array.isArray(threshold) && threshold.includes(value);

      case AlertOperator.NOT_IN:
        return Array.isArray(threshold) && !threshold.includes(value);

      case AlertOperator.REGEX:
        try {
          const regex = new RegExp(threshold);
          return regex.test(String(value));
        } catch {
          return false;
        }

      default:
        return false;
    }
  }

  /**
   * Get field value from context
   */
  private getFieldValue(field: string, context: EvaluationContext): any {
    // Support nested field access with dot notation
    const parts = field.split('.');
    let value: any = context.data;

    for (const part of parts) {
      if (value && typeof value === 'object' && part in value) {
        value = value[part];
      } else {
        return undefined;
      }
    }

    return value;
  }

  /**
   * Build condition string for display
   */
  private buildConditionString(condition: AlertCondition): string {
    const operatorMap = {
      [AlertOperator.EQUALS]: '==',
      [AlertOperator.NOT_EQUALS]: '!=',
      [AlertOperator.GREATER_THAN]: '>',
      [AlertOperator.GREATER_THAN_OR_EQUAL]: '>=',
      [AlertOperator.LESS_THAN]: '<',
      [AlertOperator.LESS_THAN_OR_EQUAL]: '<=',
      [AlertOperator.CONTAINS]: 'contains',
      [AlertOperator.NOT_CONTAINS]: 'does not contain',
      [AlertOperator.IN]: 'in',
      [AlertOperator.NOT_IN]: 'not in',
      [AlertOperator.REGEX]: 'matches'
    };

    const operator = operatorMap[condition.operator] || condition.operator;
    return `${condition.field} ${operator} ${condition.value}`;
  }

  /**
   * Create a new alert
   */
  private async createAlert(
    rule: AlertRule,
    context: EvaluationContext,
    evaluationResult: { value?: any; threshold?: any }
  ): Promise<Alert> {
    const alertId = this.generateAlertId();

    const alert: Alert = {
      id: alertId,
      ruleId: rule.id,
      ruleName: rule.name,
      severity: rule.severity,
      status: AlertStatus.ACTIVE,
      title: this.generateAlertTitle(rule, context),
      message: this.generateAlertMessage(rule, context),
      source: {
        type: context.source,
        id: context.data.id || 'unknown',
        name: context.data.name || context.source
      },
      trigger: {
        condition: evaluationResult.condition || 'Unknown',
        value: evaluationResult.value,
        threshold: evaluationResult.threshold,
        triggeredAt: context.timestamp
      },
      metadata: context.metadata,
      createdAt: context.timestamp,
      updatedAt: context.timestamp,
      tags: rule.tags
    };

    // Store alert
    this.activeAlerts.set(alertId, alert);

    return alert;
  }

  /**
   * Generate unique alert ID
   */
  private generateAlertId(): string {
    return `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Generate alert title
   */
  private generateAlertTitle(rule: AlertRule, context: EvaluationContext): string {
    // Simple title generation - can be enhanced with templates
    const sourceName = context.data.name || context.source;
    return `${rule.severity.toUpperCase()}: ${rule.name} - ${sourceName}`;
  }

  /**
   * Generate alert message
   */
  private generateAlertMessage(rule: AlertRule, context: EvaluationContext): string {
    // Simple message generation - can be enhanced with templates
    if (rule.description) {
      return rule.description;
    }

    const sourceName = context.data.name || context.source;
    return `Alert triggered for ${sourceName} by rule "${rule.name}"`;
  }

  /**
   * Check if rule is in cooldown period
   */
  private isInCooldown(ruleId: string, cooldownMinutes: number): boolean {
    const lastEvaluation = this.recentEvaluations.get(ruleId);
    if (!lastEvaluation) {
      return false;
    }

    const cooldownMs = cooldownMinutes * 60 * 1000;
    return Date.now() - lastEvaluation.getTime() < cooldownMs;
  }

  /**
   * Update cooldown timestamp
   */
  private updateCooldown(ruleId: string, cooldownMinutes: number): void {
    this.recentEvaluations.set(ruleId, new Date());
  }

  /**
   * Check if currently in quiet hours
   */
  private isInQuietHours(rule: AlertRule): boolean {
    if (!rule.quietHours || !rule.quietHours.enabled) {
      return false;
    }

    const now = new Date();
    const currentTime = this.toTimeString(now);

    return this.isTimeInRange(
      currentTime,
      rule.quietHours.startTime,
      rule.quietHours.endTime
    );
  }

  /**
   * Check if throttling should prevent alert
   */
  private isThrottled(rule: AlertRule): boolean {
    if (!rule.throttle.enabled) {
      return false;
    }

    const throttleKey = `throttle:${rule.id}`;
    const recentAlerts = this.recentEvaluations.get(throttleKey);

    if (!recentAlerts) {
      return false;
    }

    const windowMs = rule.throttle.windowMinutes * 60 * 1000;
    const timeSinceWindow = Date.now() - recentAlerts.getTime();

    if (timeSinceWindow > windowMs) {
      // Window expired
      this.recentEvaluations.delete(throttleKey);
      return false;
    }

    // Need to track count - for simplicity, using a basic approach
    // In production, you'd want a more sophisticated counting mechanism
    return false;
  }

  /**
   * Update throttling counter
   */
  private updateThrottling(rule: AlertRule): void {
    if (!rule.throttle.enabled) {
      return;
    }

    const throttleKey = `throttle:${rule.id}`;
    const lastUpdate = this.recentEvaluations.get(throttleKey);

    if (!lastUpdate) {
      this.recentEvaluations.set(throttleKey, new Date());
      return;
    }

    const windowMs = rule.throttle.windowMinutes * 60 * 1000;
    const timeSinceWindow = Date.now() - lastUpdate.getTime();

    if (timeSinceWindow > windowMs) {
      // Window expired, reset
      this.recentEvaluations.set(throttleKey, new Date());
    }
  }

  /**
   * Generate deduplication key
   */
  private generateDeduplicationKey(rule: AlertRule, context: EvaluationContext): string {
    const keyParts = [rule.id, context.source];

    for (const field of rule.deduplication.key) {
      const value = this.getFieldValue(field, context);
      keyParts.push(String(value || 'null'));
    }

    return keyParts.join(':');
  }

  /**
   * Check if alert is duplicate
   */
  private isDuplicate(deduplicationKey: string, windowMinutes: number): boolean {
    const lastAlert = this.recentEvaluations.get(deduplicationKey);
    if (!lastAlert) {
      return false;
    }

    const windowMs = windowMinutes * 60 * 1000;
    return Date.now() - lastAlert.getTime() < windowMs;
  }

  /**
   * Update deduplication tracking
   */
  private updateDeduplication(deduplicationKey: string, windowMinutes: number): void {
    this.recentEvaluations.set(deduplicationKey, new Date());
  }

  /**
   * Acknowledge an alert
   */
  async acknowledgeAlert(alertId: string, userId: string): Promise<boolean> {
    const alert = this.activeAlerts.get(alertId);
    if (!alert || alert.status !== AlertStatus.ACTIVE) {
      return false;
    }

    alert.status = AlertStatus.ACKNOWLEDGED;
    alert.acknowledgedAt = new Date();
    alert.acknowledgedBy = userId;
    alert.updatedAt = new Date();

    this.emit('alert_acknowledged', { alert, userId });
    return true;
  }

  /**
   * Resolve an alert
   */
  async resolveAlert(alertId: string, userId: string, reason?: string): Promise<boolean> {
    const alert = this.activeAlerts.get(alertId);
    if (!alert) {
      return false;
    }

    alert.status = AlertStatus.RESOLVED;
    alert.resolvedAt = new Date();
    alert.resolvedBy = userId;
    alert.updatedAt = new Date();
    if (reason) {
      alert.metadata = { ...alert.metadata, resolutionReason: reason };
    }

    this.emit('alert_resolved', { alert, userId, reason });

    // Remove from active alerts after a delay
    setTimeout(() => {
      this.activeAlerts.delete(alertId);
    }, 60000); // Keep for 1 minute

    return true;
  }

  /**
   * Suppress an alert
   */
  async suppressAlert(alertId: string, reason: string): Promise<boolean> {
    const alert = this.activeAlerts.get(alertId);
    if (!alert) {
      return false;
    }

    alert.status = AlertStatus.SUPPRESSED;
    alert.updatedAt = new Date();
    alert.metadata = { ...alert.metadata, suppressionReason: reason };

    this.emit('alert_suppressed', { alert, reason });

    // Remove from active alerts
    this.activeAlerts.delete(alertId);

    return true;
  }

  /**
   * Get active alerts
   */
  getActiveAlerts(filters?: {
    severity?: AlertSeverity[];
    source?: string[];
    ruleId?: string[];
    tags?: string[];
  }): Alert[] {
    let alerts = Array.from(this.activeAlerts.values());

    if (filters) {
      if (filters.severity) {
        alerts = alerts.filter(alert => filters.severity!.includes(alert.severity));
      }
      if (filters.source) {
        alerts = alerts.filter(alert => filters.source!.includes(alert.source.type));
      }
      if (filters.ruleId) {
        alerts = alerts.filter(alert => filters.ruleId!.includes(alert.ruleId));
      }
      if (filters.tags) {
        alerts = alerts.filter(alert =>
          filters.tags!.some(tag => alert.tags.includes(tag))
        );
      }
    }

    return alerts.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
  }

  /**
   * Get alert statistics
   */
  getStatistics(): {
    total: number;
    active: number;
    acknowledged: number;
    resolved: number;
    suppressed: number;
    bySeverity: Record<AlertSeverity, number>;
    rules: number;
  } {
    const alerts = Array.from(this.activeAlerts.values());

    const stats = {
      total: alerts.length,
      active: alerts.filter(a => a.status === AlertStatus.ACTIVE).length,
      acknowledged: alerts.filter(a => a.status === AlertStatus.ACKNOWLEDGED).length,
      resolved: alerts.filter(a => a.status === AlertStatus.RESOLVED).length,
      suppressed: alerts.filter(a => a.status === AlertStatus.SUPPRESSED).length,
      bySeverity: {
        [AlertSeverity.INFO]: 0,
        [AlertSeverity.WARNING]: 0,
        [AlertSeverity.CRITICAL]: 0
      },
      rules: this.rules.size
    };

    alerts.forEach(alert => {
      stats.bySeverity[alert.severity]++;
    });

    return stats;
  }

  /**
   * Validate alert rule
   */
  private validateRule(rule: AlertRule): void {
    if (!rule.id || !rule.name) {
      throw new Error('Rule must have id and name');
    }

    if (!Object.values(AlertSeverity).includes(rule.severity)) {
      throw new Error('Invalid severity level');
    }

    if (!Array.isArray(rule.conditions) || rule.conditions.length === 0) {
      throw new Error('Rule must have at least one condition');
    }

    if (!Array.isArray(rule.notificationChannels) || rule.notificationChannels.length === 0) {
      throw new Error('Rule must have at least one notification channel');
    }

    // Validate each condition
    for (const condition of rule.conditions) {
      if (!condition.field || !condition.operator) {
        throw new Error('Condition must have field and operator');
      }
    }
  }

  /**
   * Convert date to time string (HH:MM)
   */
  private toTimeString(date: Date): string {
    return date.toTimeString().substr(0, 5);
  }

  /**
   * Check if time is in range
   */
  private isTimeInRange(current: string, start: string, end: string): boolean {
    const currentNum = parseInt(current.replace(':', ''), 10);
    const startNum = parseInt(start.replace(':', ''), 10);
    const endNum = parseInt(end.replace(':', ''), 10);

    if (startNum <= endNum) {
      // Normal range (e.g., 09:00 - 17:00)
      return currentNum >= startNum && currentNum <= endNum;
    } else {
      // Overnight range (e.g., 22:00 - 06:00)
      return currentNum >= startNum || currentNum <= endNum;
    }
  }

  /**
   * Cleanup old data
   */
  private cleanup(): void {
    const cutoffTime = Date.now() - (this.config.metricsRetentionDays * 24 * 60 * 60 * 1000);

    // Clean old evaluation records
    for (const [key, timestamp] of this.recentEvaluations.entries()) {
      if (timestamp.getTime() < cutoffTime) {
        this.recentEvaluations.delete(key);
      }
    }

    // Clean resolved alerts older than 24 hours
    for (const [alertId, alert] of this.activeAlerts.entries()) {
      if (
        alert.status === AlertStatus.RESOLVED &&
        alert.resolvedAt &&
        Date.now() - alert.resolvedAt.getTime() > 24 * 60 * 60 * 1000
      ) {
        this.activeAlerts.delete(alertId);
      }
    }

    this.emit('cleanup_completed', {
      timestamp: new Date(),
      cleanedRecords: this.recentEvaluations.size
    });
  }
}