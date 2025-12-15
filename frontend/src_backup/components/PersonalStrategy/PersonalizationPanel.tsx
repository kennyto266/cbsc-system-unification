import React, { useState, useEffect } from 'react';
import { Strategy, PersonalStrategyConfig, NotificationSettings } from '../../types/index';
import { Card } from '../ui/Card';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

interface PersonalizationPanelProps {
  strategy: Strategy | null;
  userId: string;
  apiUrl: string;
  onSave: (config: PersonalStrategyConfig) => void;
  onCancel: () => void;
}

export const PersonalizationPanel: React.FC<PersonalizationPanelProps> = ({
  strategy,
  userId,
  apiUrl,
  onSave,
  onCancel
}) => {
  const [config, setConfig] = useState<PersonalStrategyConfig>({
    userId,
    customParameters: {},
    riskTolerance: 'moderate',
    capitalAllocation: 0,
    maxPositionSize: 0,
    stopLoss: 0,
    takeProfit: 0,
    notifications: {
      email: true,
      sms: false,
      push: true,
      signalAlert: true,
      riskAlert: true,
      performanceReport: true,
      frequency: 'daily'
    },
    autoTrading: false
  });

  const [customName, setCustomName] = useState('');
  const [notes, setNotes] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (strategy?.personalConfig) {
      setConfig(strategy.personalConfig);
      setCustomName(strategy.personalConfig.customName || '');
      setNotes(strategy.personalConfig.notes || '');
    } else {
      // Set default values based on strategy type
      const defaults = getDefaultPersonalization(strategy);
      setConfig(prev => ({ ...prev, ...defaults }));
    }
  }, [strategy]);

  const getDefaultPersonalization = (strategy: Strategy | null) => {
    if (!strategy) return {};

    const riskDefaults = {
      conservative: { capitalAllocation: 0.1, maxPositionSize: 0.05, stopLoss: 2, takeProfit: 3 },
      moderate: { capitalAllocation: 0.2, maxPositionSize: 0.1, stopLoss: 3, takeProfit: 5 },
      aggressive: { capitalAllocation: 0.3, maxPositionSize: 0.15, stopLoss: 5, takeProfit: 8 }
    };

    return riskDefaults[config.riskTolerance];
  };

  const handleInputChange = (field: keyof PersonalStrategyConfig, value: any) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  const handleNotificationChange = (field: keyof NotificationSettings, value: any) => {
    setConfig(prev => ({
      ...prev,
      notifications: { ...prev.notifications, [field]: value }
    }));
  };

  const validateConfig = (): string | null => {
    if (!config.capitalAllocation || config.capitalAllocation <= 0) {
      return '资金分配必须大于0';
    }
    if (config.capitalAllocation > 1) {
      return '资金分配不能超过100%';
    }
    if (!config.maxPositionSize || config.maxPositionSize <= 0) {
      return '最大仓位必须大于0';
    }
    if (config.stopLoss <= 0 || config.takeProfit <= 0) {
      return '止损和止盈必须大于0';
    }
    if (config.takeProfit <= config.stopLoss) {
      return '止盈必须大于止损';
    }
    return null;
  };

  const handleSave = async () => {
    const validationError = validateConfig();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const saveConfig = {
        ...config,
        customName: customName || undefined,
        notes: notes || undefined
      };

      // Save to API
      const response = await fetch(`${apiUrl}/users/${userId}/strategies/${strategy?.id}/personalize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(saveConfig)
      });

      if (!response.ok) {
        throw new Error('保存失败');
      }

      const result = await response.json();
      onSave(result.config);

    } catch (err) {
      console.error('Failed to save personalization:', err);
      setError(err instanceof Error ? err.message : '保存失败');
    } finally {
      setIsLoading(false);
    }
  };

  const riskToleranceOptions = [
    { value: 'conservative', label: '保守型', description: '低风险，稳定收益' },
    { value: 'moderate', label: '稳健型', description: '平衡风险和收益' },
    { value: 'aggressive', label: '激进型', description: '高风险，高收益' }
  ];

  const frequencyOptions = [
    { value: 'realtime', label: '实时' },
    { value: 'hourly', label: '每小时' },
    { value: 'daily', label: '每日' },
    { value: 'weekly', label: '每周' }
  ];

  if (!strategy) {
    return (
      <div className="text-center py-8">
        <p className="text-neutral-600">请选择一个策略进行个性化设置</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Strategy Info */}
      <Card className="p-4 bg-neutral-50">
        <h3 className="font-medium text-neutral-900 mb-2">{strategy.name}</h3>
        <p className="text-sm text-neutral-600">{strategy.description}</p>
        <div className="flex items-center space-x-2 mt-2">
          <Badge variant="primary">{strategy.category}</Badge>
          <Badge variant={
            strategy.riskLevel === 'low' ? 'success' :
            strategy.riskLevel === 'medium' ? 'warning' : 'error'
          }>
            {strategy.riskLevel === 'low' ? '低风险' :
             strategy.riskLevel === 'medium' ? '中等风险' : '高风险'}
          </Badge>
        </div>
      </Card>

      {/* Custom Name */}
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-2">
          自定义名称 (可选)
        </label>
        <Input
          value={customName}
          onChange={(e) => setCustomName(e.target.value)}
          placeholder={`为"${strategy.name}"设置一个个性化名称`}
        />
      </div>

      {/* Risk Tolerance */}
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-2">
          风险偏好
        </label>
        <div className="space-y-2">
          {riskToleranceOptions.map((option) => (
            <label key={option.value} className="flex items-center p-3 border border-neutral-200 rounded-lg cursor-pointer hover:bg-neutral-50">
              <input
                type="radio"
                name="riskTolerance"
                value={option.value}
                checked={config.riskTolerance === option.value}
                onChange={(e) => handleInputChange('riskTolerance', e.target.value)}
                className="mr-3"
              />
              <div>
                <div className="font-medium text-neutral-900">{option.label}</div>
                <div className="text-sm text-neutral-600">{option.description}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Capital Configuration */}
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-2">
          资金配置
        </label>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-neutral-600 mb-1">资金分配比例</label>
            <div className="relative">
              <Input
                type="number"
                value={config.capitalAllocation * 100}
                onChange={(e) => handleInputChange('capitalAllocation', parseFloat(e.target.value) / 100)}
                min="0"
                max="100"
                step="1"
              />
              <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-neutral-500">%</span>
            </div>
          </div>
          <div>
            <label className="block text-xs text-neutral-600 mb-1">最大仓位比例</label>
            <div className="relative">
              <Input
                type="number"
                value={config.maxPositionSize * 100}
                onChange={(e) => handleInputChange('maxPositionSize', parseFloat(e.target.value) / 100)}
                min="0"
                max="100"
                step="1"
              />
              <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-neutral-500">%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Stop Loss and Take Profit */}
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-2">
          止盈止损设置
        </label>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-neutral-600 mb-1">止损百分比</label>
            <div className="relative">
              <Input
                type="number"
                value={config.stopLoss}
                onChange={(e) => handleInputChange('stopLoss', parseFloat(e.target.value))}
                min="0"
                max="50"
                step="0.1"
              />
              <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-neutral-500">%</span>
            </div>
          </div>
          <div>
            <label className="block text-xs text-neutral-600 mb-1">止盈百分比</label>
            <div className="relative">
              <Input
                type="number"
                value={config.takeProfit}
                onChange={(e) => handleInputChange('takeProfit', parseFloat(e.target.value))}
                min="0"
                max="100"
                step="0.1"
              />
              <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-neutral-500">%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Notification Settings */}
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-2">
          通知设置
        </label>
        <Card className="p-4 space-y-3">
          <div className="grid grid-cols-3 gap-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.notifications.email}
                onChange={(e) => handleNotificationChange('email', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">邮件通知</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.notifications.sms}
                onChange={(e) => handleNotificationChange('sms', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">短信通知</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.notifications.push}
                onChange={(e) => handleNotificationChange('push', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">推送通知</span>
            </label>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.notifications.signalAlert}
                onChange={(e) => handleNotificationChange('signalAlert', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">交易信号</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.notifications.riskAlert}
                onChange={(e) => handleNotificationChange('riskAlert', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">风险预警</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.notifications.performanceReport}
                onChange={(e) => handleNotificationChange('performanceReport', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">表现报告</span>
            </label>
          </div>

          <div>
            <label className="block text-xs text-neutral-600 mb-1">通知频率</label>
            <Select
              value={config.notifications.frequency}
              onChange={(value) => handleNotificationChange('frequency', value)}
              options={frequencyOptions}
            />
          </div>
        </Card>
      </div>

      {/* Auto Trading */}
      <div>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={config.autoTrading}
            onChange={(e) => handleInputChange('autoTrading', e.target.checked)}
            className="mr-3"
          />
          <div>
            <div className="font-medium text-neutral-900">启用自动交易</div>
            <div className="text-sm text-neutral-600">策略将自动执行交易信号</div>
          </div>
        </label>
        {config.autoTrading && (
          <div className="mt-2 p-3 bg-warning-50 border border-warning-200 rounded-lg">
            <p className="text-sm text-warning-800">
              ⚠️ 自动交易存在风险，请确保您已充分了解并设置了合适的风险控制参数。
            </p>
          </div>
        )}
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-2">
          备注说明 (可选)
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
          className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          placeholder="添加个性化设置的备注..."
        />
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-error-50 border border-error-200 rounded-lg">
          <p className="text-sm text-error-800">{error}</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end space-x-3 pt-4 border-t border-neutral-200">
        <Button
          variant="outline"
          onClick={onCancel}
          disabled={isLoading}
        >
          取消
        </Button>
        <Button
          variant="primary"
          onClick={handleSave}
          disabled={isLoading}
        >
          {isLoading ? '保存中...' : '保存设置'}
        </Button>
      </div>
    </div>
  );
};