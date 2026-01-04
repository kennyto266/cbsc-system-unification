/**
 * Alert Service for Economic Indicators and Strategy Monitoring
 * Handles real-time alert detection, processing, and management
 */

import { EconomicIndicator } from '../types/economicData';
import { Strategy } from '../types/strategyTypes';

// Alert types and interfaces
export interface AlertRule {
  id: string;
  name: string;
  description: string;
  type: 'threshold' | 'change_rate' | 'pattern' | 'anomaly';
  source: 'economic' | 'strategy' | 'portfolio';
  priority: 'low' | 'medium' | 'high' | 'critical';
  conditions: AlertCondition[];
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
  userId: string;
}

export interface AlertCondition {
  field: string; // e.g., 'inflation_rate', 'unemployment_rate'
  operator: '>' | '<' | '=' | '>=' | '<=' | '!=' | 'change_pct' | 'deviation';
  value: number | string;
  timeframe?: string; // For time-based conditions
}

export interface Alert {
  id: string;
  ruleId: string;
  ruleName: string;
  type: AlertRule['type'];
  source: AlertRule['source'];
  priority: AlertRule['priority'];
  title: string;
  message: string;
  details: Record<string, any>;
  status: 'active' | 'acknowledged' | 'resolved' | 'suppressed';
  triggeredAt: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
  acknowledgedBy?: string;
  isAggregated: boolean;
  relatedAlerts?: string[]; // For aggregated alerts
  userId: string;
}

export interface AlertAggregation {
  id: string;
  priority: Alert['priority'];
  type: string;
  source: string;
  count: number;
  title: string;
  summary: string;
  alerts: Alert[];
  createdAt: string;
  userId: string;
}

export interface AlertStatistics {
  total: number;
  active: number;
  acknowledged: number;
  resolved: number;
  byPriority: Record<Alert['priority'], number>;
  byType: Record<string, number>;
  bySource: Record<string, number>;
  triggerRate: number; // Alerts per hour in last 24h
  resolutionTime: number; // Average resolution time in hours
}

export interface AlertHistory {
  alerts: Alert[];
  aggregations: AlertAggregation[];
  statistics: AlertStatistics;
  filters: AlertHistoryFilters;
}

export interface AlertHistoryFilters {
  dateRange: {
    start: string;
    end: string;
  };
  priorities: Alert['priority'][];
  types: AlertRule['type'][];
  sources: AlertRule['source'][];
  status: Alert['status'][];
  search?: string;
}

class AlertService {
  private rules: Map<string, AlertRule> = new Map();
  private alerts: Map<string, Alert> = new Map();
  private aggregations: Map<string, AlertAggregation> = new Map();
  private aggregationTimer: NodeJS.Timeout | null = null;
  private readonly AGGREGATION_WINDOW = 5 * 60 * 1000; // 5 minutes

  constructor() {
    this.loadRulesFromStorage();
    this.loadAlertsFromStorage();
    this.startAggregation();
  }

  // Alert Rules Management
  async createRule(rule: Omit<AlertRule, 'id' | 'createdAt' | 'updatedAt'>): Promise<AlertRule> {
    const newRule: AlertRule = {
      ...rule,
      id: this.generateId(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    this.rules.set(newRule.id, newRule);
    this.saveRulesToStorage();

    return newRule;
  }

  async updateRule(id: string, updates: Partial<AlertRule>): Promise<AlertRule | null> {
    const rule = this.rules.get(id);
    if (!rule) return null;

    const updatedRule: AlertRule = {
      ...rule,
      ...updates,
      updatedAt: new Date().toISOString()
    };

    this.rules.set(id, updatedRule);
    this.saveRulesToStorage();

    return updatedRule;
  }

  async deleteRule(id: string): Promise<boolean> {
    const deleted = this.rules.delete(id);
    if (deleted) {
      this.saveRulesToStorage();
    }
    return deleted;
  }

  getRules(userId?: string): AlertRule[] {
    const rules = Array.from(this.rules.values());
    return userId ? rules.filter(rule => rule.userId === userId) : rules;
  }

  getActiveRules(userId?: string): AlertRule[] {
    return this.getRules(userId).filter(rule => rule.isActive);
  }

  // Alert Detection and Processing
  async processData(data: EconomicIndicator | Strategy | any, source: AlertRule['source']): Promise<void> {
    const activeRules = this.getActiveRules().filter(rule => rule.source === source);

    for (const rule of activeRules) {
      if (this.evaluateRule(rule, data)) {
        await this.triggerAlert(rule, data);
      }
    }
  }

  private evaluateRule(rule: AlertRule, data: any): boolean {
    // Early return for performance
    if (!rule.isActive || rule.conditions.length === 0) return false;

    // Evaluate all conditions (AND logic)
    return rule.conditions.every(condition => this.evaluateCondition(condition, data));
  }

  private evaluateCondition(condition: AlertCondition, data: any): boolean {
    const value = this.getValueByPath(data, condition.field);
    if (value === undefined || value === null) return false;

    switch (condition.operator) {
      case '>':
        return Number(value) > Number(condition.value);
      case '<':
        return Number(value) < Number(condition.value);
      case '=':
        return value === condition.value;
      case '>=':
        return Number(value) >= Number(condition.value);
      case '<=':
        return Number(value) <= Number(condition.value);
      case '!=':
        return value !== condition.value;
      case 'change_pct':
        return this.calculatePercentageChange(value, condition.value);
      case 'deviation':
        return this.calculateDeviation(value, condition.value);
      default:
        return false;
    }
  }

  private getValueByPath(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }

  private calculatePercentageChange(current: number, threshold: number): boolean {
    // This would need historical data for actual calculation
    // Simplified implementation for now
    return Math.abs(current) > threshold;
  }

  private calculateDeviation(value: number, threshold: number): boolean {
    // Calculate standard deviation from mean
    // Simplified implementation
    return Math.abs(value) > threshold;
  }

  private async triggerAlert(rule: AlertRule, data: any): Promise<void> {
    const alert: Alert = {
      id: this.generateId(),
      ruleId: rule.id,
      ruleName: rule.name,
      type: rule.type,
      source: rule.source,
      priority: rule.priority,
      title: this.generateAlertTitle(rule, data),
      message: this.generateAlertMessage(rule, data),
      details: data,
      status: 'active',
      triggeredAt: new Date().toISOString(),
      isAggregated: false,
      userId: rule.userId
    };

    this.alerts.set(alert.id, alert);
    this.saveAlertsToStorage();

    // Trigger notification
    this.notifyAlert(alert);
  }

  private generateAlertTitle(rule: AlertRule, data: any): string {
    return `${rule.name} Alert Triggered`;
  }

  private generateAlertMessage(rule: AlertRule, data: any): string {
    return `Alert rule "${rule.name}" has been triggered by ${rule.source} data.`;
  }

  // Alert Aggregation
  private startAggregation(): void {
    this.aggregationTimer = setInterval(() => {
      this.aggregateAlerts();
    }, this.AGGREGATION_WINDOW);
  }

  private aggregateAlerts(): void {
    const activeAlerts = Array.from(this.alerts.values())
      .filter(alert => alert.status === 'active' && !alert.isAggregated);

    // Group alerts by type, source, and priority
    const groups = this.groupAlerts(activeAlerts);

    groups.forEach(group => {
      if (group.alerts.length > 1) {
        this.createAggregation(group);
      }
    });
  }

  private groupAlerts(alerts: Alert[]): Array<{
    type: string;
    source: string;
    priority: Alert['priority'];
    alerts: Alert[];
  }> {
    const groups = new Map<string, Alert[]>();

    alerts.forEach(alert => {
      const key = `${alert.type}-${alert.source}-${alert.priority}`;
      if (!groups.has(key)) {
        groups.set(key, []);
      }
      groups.get(key)!.push(alert);
    });

    return Array.from(groups.entries()).map(([key, alerts]) => {
      const [type, source, priority] = key.split('-');
      return {
        type,
        source,
        priority: priority as Alert['priority'],
        alerts
      };
    });
  }

  private createAggregation(group: {
    type: string;
    source: string;
    priority: Alert['priority'];
    alerts: Alert[];
  }): void {
    const aggregation: AlertAggregation = {
      id: this.generateId(),
      priority: group.priority,
      type: group.type,
      source: group.source,
      count: group.alerts.length,
      title: `${group.alerts.length} ${group.type} alerts from ${group.source}`,
      summary: `Multiple ${group.type} alerts detected in ${group.source}`,
      alerts: group.alerts,
      createdAt: new Date().toISOString(),
      userId: group.alerts[0].userId
    };

    // Mark alerts as aggregated
    group.alerts.forEach(alert => {
      alert.isAggregated = true;
      alert.relatedAlerts = group.alerts.map(a => a.id).filter(id => id !== alert.id);
    });

    this.aggregations.set(aggregation.id, aggregation);
    this.saveAggregationsToStorage();
  }

  // Alert Management
  async acknowledgeAlert(alertId: string, userId: string): Promise<boolean> {
    const alert = this.alerts.get(alertId);
    if (!alert || alert.status !== 'active') return false;

    alert.status = 'acknowledged';
    alert.acknowledgedAt = new Date().toISOString();
    alert.acknowledgedBy = userId;

    this.alerts.set(alertId, alert);
    this.saveAlertsToStorage();

    return true;
  }

  async resolveAlert(alertId: string): Promise<boolean> {
    const alert = this.alerts.get(alertId);
    if (!alert) return false;

    alert.status = 'resolved';
    alert.resolvedAt = new Date().toISOString();

    this.alerts.set(alertId, alert);
    this.saveAlertsToStorage();

    return true;
  }

  async suppressAlert(alertId: string): Promise<boolean> {
    const alert = this.alerts.get(alertId);
    if (!alert) return false;

    alert.status = 'suppressed';

    this.alerts.set(alertId, alert);
    this.saveAlertsToStorage();

    return true;
  }

  // History and Statistics
  getAlertHistory(filters: AlertHistoryFilters): AlertHistory {
    let alerts = Array.from(this.alerts.values());
    let aggregations = Array.from(this.aggregations.values());

    // Apply filters
    if (filters.dateRange) {
      const start = new Date(filters.dateRange.start).getTime();
      const end = new Date(filters.dateRange.end).getTime();

      alerts = alerts.filter(alert => {
        const time = new Date(alert.triggeredAt).getTime();
        return time >= start && time <= end;
      });

      aggregations = aggregations.forEach(agg => {
        agg.alerts = agg.alerts.filter(alert => {
          const time = new Date(alert.triggeredAt).getTime();
          return time >= start && time <= end;
        });
      });
    }

    if (filters.priorities.length > 0) {
      alerts = alerts.filter(alert => filters.priorities.includes(alert.priority));
    }

    if (filters.types.length > 0) {
      alerts = alerts.filter(alert => filters.types.includes(alert.type));
    }

    if (filters.sources.length > 0) {
      alerts = alerts.filter(alert => filters.sources.includes(alert.source));
    }

    if (filters.status.length > 0) {
      alerts = alerts.filter(alert => filters.status.includes(alert.status));
    }

    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      alerts = alerts.filter(alert =>
        alert.title.toLowerCase().includes(searchLower) ||
        alert.message.toLowerCase().includes(searchLower) ||
        alert.ruleName.toLowerCase().includes(searchLower)
      );
    }

    // Calculate statistics
    const statistics = this.calculateStatistics(alerts);

    return {
      alerts,
      aggregations,
      statistics,
      filters
    };
  }

  private calculateStatistics(alerts: Alert[]): AlertStatistics {
    const now = Date.now();
    const last24h = now - 24 * 60 * 60 * 1000;

    const recentAlerts = alerts.filter(alert =>
      new Date(alert.triggeredAt).getTime() > last24h
    );

    const resolvedAlerts = alerts.filter(alert =>
      alert.status === 'resolved' && alert.resolvedAt
    );

    const resolutionTimes = resolvedAlerts.map(alert => {
      const triggered = new Date(alert.triggeredAt).getTime();
      const resolved = new Date(alert.resolvedAt!).getTime();
      return (resolved - triggered) / (1000 * 60 * 60); // Convert to hours
    });

    return {
      total: alerts.length,
      active: alerts.filter(a => a.status === 'active').length,
      acknowledged: alerts.filter(a => a.status === 'acknowledged').length,
      resolved: alerts.filter(a => a.status === 'resolved').length,
      byPriority: this.groupBy(alerts, 'priority'),
      byType: this.groupBy(alerts, 'type'),
      bySource: this.groupBy(alerts, 'source'),
      triggerRate: recentAlerts.length / 24, // Alerts per hour
      resolutionTime: resolutionTimes.length > 0
        ? resolutionTimes.reduce((a, b) => a + b, 0) / resolutionTimes.length
        : 0
    };
  }

  private groupBy<T>(array: T[], key: keyof T): Record<string, number> {
    return array.reduce((acc, item) => {
      const value = String(item[key]);
      acc[value] = (acc[value] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }

  // Notification
  private notifyAlert(alert: Alert): void {
    // Emit event for notification system
    window.dispatchEvent(new CustomEvent('alert-triggered', { detail: alert }));
  }

  // Storage Methods
  private loadRulesFromStorage(): void {
    try {
      const stored = localStorage.getItem('alertRules');
      if (stored) {
        const rules = JSON.parse(stored) as AlertRule[];
        rules.forEach(rule => this.rules.set(rule.id, rule));
      }
    } catch (error) {
      console.error('Failed to load alert rules:', error);
    }
  }

  private saveRulesToStorage(): void {
    try {
      const rules = Array.from(this.rules.values());
      localStorage.setItem('alertRules', JSON.stringify(rules));
    } catch (error) {
      console.error('Failed to save alert rules:', error);
    }
  }

  private loadAlertsFromStorage(): void {
    try {
      const stored = localStorage.getItem('alerts');
      if (stored) {
        const alerts = JSON.parse(stored) as Alert[];
        alerts.forEach(alert => this.alerts.set(alert.id, alert));
      }
    } catch (error) {
      console.error('Failed to load alerts:', error);
    }
  }

  private saveAlertsToStorage(): void {
    try {
      const alerts = Array.from(this.alerts.values());
      localStorage.setItem('alerts', JSON.stringify(alerts));
    } catch (error) {
      console.error('Failed to save alerts:', error);
    }
  }

  private saveAggregationsToStorage(): void {
    try {
      const aggregations = Array.from(this.aggregations.values());
      localStorage.setItem('alertAggregations', JSON.stringify(aggregations));
    } catch (error) {
      console.error('Failed to save alert aggregations:', error);
    }
  }

  // Utility Methods
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  // Cleanup
  destroy(): void {
    if (this.aggregationTimer) {
      clearInterval(this.aggregationTimer);
    }
  }
}

// Singleton instance
export const alertService = new AlertService();

// Export types
export type { AlertService };