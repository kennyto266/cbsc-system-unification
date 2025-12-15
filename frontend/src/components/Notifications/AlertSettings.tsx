import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Save, X, AlertCircle } from 'lucide-react';

// Types
interface AlertCondition {
  metric: string;
  operator: string;
  threshold: number;
  time_window?: number;
}

interface AlertRule {
  id?: string;
  name: string;
  description?: string;
  enabled: boolean;
  alert_type: 'threshold' | 'event' | 'custom' | 'scheduled';
  severity: 'low' | 'medium' | 'high' | 'critical';
  conditions: AlertCondition[];
  notification_channels: string[];
  schedule_cron?: string;
  cooldown_minutes: number;
}

interface AlertSettingsProps {
  strategyId?: string;
  className?: string;
}

const AlertSettings: React.FC<AlertSettingsProps> = ({ strategyId, className = '' }) => {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // Fetch alert rules
  const fetchRules = async () => {
    try {
      setLoading(true);
      const url = strategyId
        ? `/api/v1/alerts/rules?strategy_id=${strategyId}`
        : '/api/v1/alerts/rules';

      const response = await fetch(url);
      const data = await response.json();
      setRules(data);
    } catch (error) {
      console.error('Failed to fetch alert rules:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, [strategyId]);

  // Save rule
  const saveRule = async (rule: AlertRule) => {
    try {
      setSaving(true);
      const url = rule.id
        ? `/api/v1/alerts/rules/${rule.id}`
        : '/api/v1/alerts/rules';

      const method = rule.id ? 'PUT' : 'POST';
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(rule)
      });

      if (response.ok) {
        await fetchRules();
        setShowForm(false);
        setEditingRule(null);
      } else {
        throw new Error('Failed to save rule');
      }
    } catch (error) {
      console.error('Failed to save alert rule:', error);
      alert('保存失败，请重试');
    } finally {
      setSaving(false);
    }
  };

  // Delete rule
  const deleteRule = async (ruleId: string) => {
    if (!confirm('确定要删除这个告警规则吗？')) return;

    try {
      const response = await fetch(`/api/v1/alerts/rules/${ruleId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        await fetchRules();
      } else {
        throw new Error('Failed to delete rule');
      }
    } catch (error) {
      console.error('Failed to delete alert rule:', error);
      alert('删除失败，请重试');
    }
  };

  // Toggle rule
  const toggleRule = async (rule: AlertRule) => {
    try {
      await saveRule({ ...rule, enabled: !rule.enabled });
    } catch (error) {
      console.error('Failed to toggle rule:', error);
    }
  };

  // Initialize new rule
  const initializeRule = (): AlertRule => ({
    name: '',
    description: '',
    enabled: true,
    alert_type: 'threshold',
    severity: 'medium',
    conditions: [{
      metric: 'drawdown',
      operator: 'lt',
      threshold: -0.1,
      time_window: 60
    }],
    notification_channels: ['email', 'browser_push'],
    cooldown_minutes: 60
  });

  // Add condition to rule
  const addCondition = (rule: AlertRule) => {
    rule.conditions.push({
      metric: 'return',
      operator: 'gt',
      threshold: 0.05
    });
  };

  // Remove condition from rule
  const removeCondition = (rule: AlertRule, index: number) => {
    rule.conditions.splice(index, 1);
  };

  // Get severity color
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low':
        return 'text-blue-600 bg-blue-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'high':
        return 'text-orange-600 bg-orange-100';
      case 'critical':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  // Metric options
  const metricOptions = [
    { value: 'drawdown', label: '回撤率' },
    { value: 'return', label: '收益率' },
    { value: 'volatility', label: '波动率' },
    { value: 'sharpe_ratio', label: '夏普比率' },
    { value: 'win_rate', label: '胜率' },
    { value: 'daily_pnl', label: '日盈亏' },
    { value: 'exposure', label: '持仓比例' },
    { value: 'max_position_size', label: '最大持仓' }
  ];

  // Operator options
  const operatorOptions = [
    { value: 'gt', label: '>' },
    { value: 'gte', label: '>=' },
    { value: 'lt', label: '<' },
    { value: 'lte', label: '<=' },
    { value: 'eq', label: '=' },
    { value: 'ne', label: '!=' }
  ];

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">告警规则</h2>
          <button
            onClick={() => {
              setEditingRule(initializeRule());
              setShowForm(true);
            }}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>新建规则</span>
          </button>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500">
            加载中...
          </div>
        ) : rules.length === 0 ? (
          <div className="text-center py-8">
            <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">暂无告警规则</p>
            <button
              onClick={() => {
                setEditingRule(initializeRule());
                setShowForm(true);
              }}
              className="mt-4 text-blue-600 hover:text-blue-700"
            >
              创建第一个告警规则
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {rules.map((rule) => (
              <div key={rule.id} className="border rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-medium text-gray-900">
                        {rule.name}
                      </h3>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(rule.severity)}`}>
                        {rule.severity === 'low' && '低'}
                        {rule.severity === 'medium' && '中'}
                        {rule.severity === 'high' && '高'}
                        {rule.severity === 'critical' && '严重'}
                      </span>
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-600">
                        {rule.alert_type === 'threshold' && '阈值告警'}
                        {rule.alert_type === 'event' && '事件告警'}
                        {rule.alert_type === 'scheduled' && '定时告警'}
                        {rule.alert_type === 'custom' && '自定义'}
                      </span>
                    </div>
                    {rule.description && (
                      <p className="text-sm text-gray-600 mt-1">{rule.description}</p>
                    )}
                    {rule.alert_type === 'threshold' && (
                      <div className="mt-3 space-y-1">
                        {rule.conditions.map((condition, index) => (
                          <div key={index} className="text-sm text-gray-600">
                            当 {metricOptions.find(m => m.value === condition.metric)?.label}
                            {' '}{operatorOptions.find(o => o.value === condition.operator)?.label}
                            {' '}{condition.threshold}
                            {condition.time_window && ` (过去${condition.time_window}分钟)`}
                          </div>
                        ))}
                      </div>
                    )}
                    {rule.alert_type === 'scheduled' && rule.schedule_cron && (
                      <p className="text-sm text-gray-600 mt-2">
                        定时执行: {rule.schedule_cron}
                      </p>
                    )}
                    <div className="flex items-center mt-3 space-x-4 text-sm text-gray-500">
                      <span>冷却时间: {rule.cooldown_minutes}分钟</span>
                      <span>通知方式: {rule.notification_channels.map(c =>
                        c === 'email' ? '邮件' :
                        c === 'browser_push' ? '浏览器推送' :
                        c === 'sms' ? '短信' : c
                      ).join(', ')}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => toggleRule(rule)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        rule.enabled ? 'bg-blue-600' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          rule.enabled ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                    <button
                      onClick={() => {
                        setEditingRule(rule);
                        setShowForm(true);
                      }}
                      className="p-1 text-gray-400 hover:text-gray-600"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => rule.id && deleteRule(rule.id)}
                      className="p-1 text-gray-400 hover:text-red-600"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Rule Form Modal */}
      {showForm && editingRule && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-gray-900">
                  {editingRule.id ? '编辑告警规则' : '新建告警规则'}
                </h3>
                <button
                  onClick={() => {
                    setShowForm(false);
                    setEditingRule(null);
                  }}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-6">
                {/* Basic Info */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    规则名称
                  </label>
                  <input
                    type="text"
                    value={editingRule.name}
                    onChange={(e) => setEditingRule({ ...editingRule, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="输入规则名称"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    描述（可选）
                  </label>
                  <textarea
                    value={editingRule.description || ''}
                    onChange={(e) => setEditingRule({ ...editingRule, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="输入规则描述"
                  />
                </div>

                {/* Type and Severity */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      告警类型
                    </label>
                    <select
                      value={editingRule.alert_type}
                      onChange={(e) => setEditingRule({ ...editingRule, alert_type: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="threshold">阈值告警</option>
                      <option value="event">事件告警</option>
                      <option value="scheduled">定时告警</option>
                      <option value="custom">自定义</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      严重程度
                    </label>
                    <select
                      value={editingRule.severity}
                      onChange={(e) => setEditingRule({ ...editingRule, severity: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="low">低</option>
                      <option value="medium">中</option>
                      <option value="high">高</option>
                      <option value="critical">严重</option>
                    </select>
                  </div>
                </div>

                {/* Conditions for threshold alerts */}
                {editingRule.alert_type === 'threshold' && (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="block text-sm font-medium text-gray-700">
                        触发条件
                      </label>
                      <button
                        type="button"
                        onClick={() => addCondition(editingRule)}
                        className="text-sm text-blue-600 hover:text-blue-700"
                      >
                        添加条件
                      </button>
                    </div>
                    <div className="space-y-3">
                      {editingRule.conditions.map((condition, index) => (
                        <div key={index} className="flex items-center space-x-2 p-3 border rounded-lg bg-gray-50">
                          <select
                            value={condition.metric}
                            onChange={(e) => {
                              const newConditions = [...editingRule.conditions];
                              newConditions[index] = { ...condition, metric: e.target.value };
                              setEditingRule({ ...editingRule, conditions: newConditions });
                            }}
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            {metricOptions.map(option => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>

                          <select
                            value={condition.operator}
                            onChange={(e) => {
                              const newConditions = [...editingRule.conditions];
                              newConditions[index] = { ...condition, operator: e.target.value };
                              setEditingRule({ ...editingRule, conditions: newConditions });
                            }}
                            className="w-20 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            {operatorOptions.map(option => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>

                          <input
                            type="number"
                            step="0.01"
                            value={condition.threshold}
                            onChange={(e) => {
                              const newConditions = [...editingRule.conditions];
                              newConditions[index] = { ...condition, threshold: parseFloat(e.target.value) };
                              setEditingRule({ ...editingRule, conditions: newConditions });
                            }}
                            className="w-24 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />

                          <input
                            type="number"
                            value={condition.time_window || ''}
                            onChange={(e) => {
                              const newConditions = [...editingRule.conditions];
                              newConditions[index] = {
                                ...condition,
                                time_window: e.target.value ? parseInt(e.target.value) : undefined
                              };
                              setEditingRule({ ...editingRule, conditions: newConditions });
                            }}
                            placeholder="时间窗口(分钟)"
                            className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />

                          {editingRule.conditions.length > 1 && (
                            <button
                              type="button"
                              onClick={() => removeCondition(editingRule, index)}
                              className="p-1 text-red-500 hover:text-red-700"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Cron expression for scheduled alerts */}
                {editingRule.alert_type === 'scheduled' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Cron表达式
                    </label>
                    <input
                      type="text"
                      value={editingRule.schedule_cron || ''}
                      onChange={(e) => setEditingRule({ ...editingRule, schedule_cron: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="0 17 * * *"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      示例: 0 17 * * * (每天下午5点)
                    </p>
                  </div>
                )}

                {/* Notification Channels */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    通知方式
                  </label>
                  <div className="space-y-2">
                    {['email', 'browser_push', 'in_app', 'sms'].map((channel) => (
                      <label key={channel} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={editingRule.notification_channels.includes(channel)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setEditingRule({
                                ...editingRule,
                                notification_channels: [...editingRule.notification_channels, channel]
                              });
                            } else {
                              setEditingRule({
                                ...editingRule,
                                notification_channels: editingRule.notification_channels.filter(c => c !== channel)
                              });
                            }
                          }}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">
                          {channel === 'email' && '邮件'}
                          {channel === 'browser_push' && '浏览器推送'}
                          {channel === 'in_app' && '应用内'}
                          {channel === 'sms' && '短信'}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Cooldown */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    冷却时间（分钟）
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={editingRule.cooldown_minutes}
                    onChange={(e) => setEditingRule({ ...editingRule, cooldown_minutes: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    同一告警在冷却时间内不会重复触发
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end space-x-3 mt-8">
                <button
                  onClick={() => {
                    setShowForm(false);
                    setEditingRule(null);
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={() => editingRule && saveRule(editingRule)}
                  disabled={saving || !editingRule.name}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Save className="w-4 h-4" />
                  <span>{saving ? '保存中...' : '保存'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertSettings;