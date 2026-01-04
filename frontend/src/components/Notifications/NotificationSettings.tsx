/**
 * NotificationSettings Component
 * Configure notification preferences, channels, and templates
 */

import React, { useState, useEffect, useCallback } from 'react';
import { notificationService, NotificationChannel, NotificationSettings } from '../../services/notificationService';
import { AlertPriority } from '../../services/alertService';

interface NotificationSettingsProps {
  className?: string;
  onSave?: (settings: NotificationSettings) => void;
}

const NotificationSettings: React.FC<NotificationSettingsProps> = ({
  className = '',
  onSave
}) => {
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState<Record<string, boolean>>({});
  const [hasChanges, setHasChanges] = useState(false);

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = useCallback(async () => {
    setIsLoading(true);
    try {
      await notificationService.loadSettings();
      setSettings(notificationService.getSettings());
    } catch (error) {
      console.error('Failed to load notification settings:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Update local settings and mark as changed
  const updateLocalSettings = useCallback((updates: Partial<NotificationSettings>) => {
    if (!settings) return;

    const newSettings = {
      ...settings,
      ...updates
    };

    // Deep merge for nested objects
    if (updates.channels) {
      newSettings.channels = updates.channels;
    }
    if (updates.frequency) {
      newSettings.frequency = { ...settings.frequency, ...updates.frequency };
    }
    if (updates.rules) {
      newSettings.rules = { ...settings.rules, ...updates.rules };
    }

    setSettings(newSettings);
    setHasChanges(true);
  }, [settings]);

  // Save settings
  const handleSave = useCallback(async () => {
    if (!settings || !hasChanges) return;

    setIsLoading(true);
    try {
      await notificationService.updateSettings(settings);
      setHasChanges(false);
      onSave?.(settings);
    } catch (error) {
      console.error('Failed to save notification settings:', error);
    } finally {
      setIsLoading(false);
    }
  }, [settings, hasChanges, onSave]);

  // Update channel
  const updateChannel = useCallback((channelId: string, updates: Partial<NotificationChannel>) => {
    if (!settings) return;

    const channels = settings.channels.map(channel =>
      channel.id === channelId ? { ...channel, ...updates } : channel
    );

    updateLocalSettings({ channels });
  }, [settings, updateLocalSettings]);

  // Test channel
  const testChannel = useCallback(async (channelId: string) => {
    const success = await notificationService.testNotification(channelId);
    setTestResults(prev => ({ ...prev, [channelId]: success }));
  }, []);

  // Request browser permission
  const requestBrowserPermission = useCallback(async () => {
    const granted = await notificationService.requestBrowserPermission();
    if (granted && settings) {
      // Update browser channel status
      updateChannel('browser-1', { isEnabled: true });
    }
  }, [settings, updateChannel]);

  if (isLoading && !settings) {
    return (
      <div className={`notification-settings ${className}`}>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className={`notification-settings ${className}`}>
        <div className="text-center py-8 text-gray-500">
          Failed to load notification settings
        </div>
      </div>
    );
  }

  return (
    <div className={`notification-settings ${className}`}>
      <div className="bg-white rounded-lg shadow">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">通知設置</h2>
            {hasChanges && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-orange-600">有未保存的更改</span>
                <button
                  onClick={handleSave}
                  disabled={isLoading}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                  {isLoading ? '保存中...' : '保存更改'}
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="p-6 space-y-8">
          {/* Notification Channels */}
          <section>
            <h3 className="text-md font-medium text-gray-900 mb-4">通知渠道</h3>
            <div className="space-y-4">
              {settings.channels.map(channel => (
                <div key={channel.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="font-medium">{channel.name}</h4>
                      <p className="text-sm text-gray-600">{channel.description}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {channel.type === 'browser' && (
                        <button
                          onClick={requestBrowserPermission}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          請求權限
                        </button>
                      )}
                      <button
                        onClick={() => testChannel(channel.id)}
                        className="px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
                      >
                        測試
                      </button>
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={channel.isEnabled}
                          onChange={(e) => updateChannel(channel.id, { isEnabled: e.target.checked })}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <span className="text-sm">啟用</span>
                      </label>
                    </div>
                  </div>

                  {testResults[channel.id] !== undefined && (
                    <div className={`text-sm mb-3 ${testResults[channel.id] ? 'text-green-600' : 'text-red-600'}`}>
                      {testResults[channel.id] ? '✓ 測試成功' : '✗ 測試失敗'}
                    </div>
                  )}

                  {/* Channel-specific configuration */}
                  {channel.type === 'email' && channel.isEnabled && (
                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-gray-700">
                        郵箱地址
                      </label>
                      <input
                        type="email"
                        placeholder="your@email.com"
                        value={channel.config.address || ''}
                        onChange={(e) => updateChannel(channel.id, {
                          config: { ...channel.config, address: e.target.value }
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  )}

                  {channel.type === 'sms' && channel.isEnabled && (
                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-gray-700">
                        手機號碼
                      </label>
                      <input
                        type="tel"
                        placeholder="+852 1234 5678"
                        value={channel.config.phoneNumber || ''}
                        onChange={(e) => updateChannel(channel.id, {
                          config: { ...channel.config, phoneNumber: e.target.value }
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  )}

                  {channel.type === 'webhook' && channel.isEnabled && (
                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-gray-700">
                        Webhook URL
                      </label>
                      <input
                        type="url"
                        placeholder="https://your-webhook-url.com"
                        value={channel.config.url || ''}
                        onChange={(e) => updateChannel(channel.id, {
                          config: { ...channel.config, url: e.target.value }
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* Frequency Settings */}
          <section>
            <h3 className="text-md font-medium text-gray-900 mb-4">頻率設置</h3>
            <div className="bg-gray-50 rounded-lg p-4 space-y-4">
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.frequency.immediate}
                    onChange={(e) => updateLocalSettings({
                      frequency: { immediate: e.target.checked }
                    })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="text-sm font-medium">立即發送嚴重警報</span>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  批量通知間隔（分鐘）
                </label>
                <input
                  type="number"
                  min="1"
                  max="1440"
                  value={settings.frequency.batchInterval}
                  onChange={(e) => updateLocalSettings({
                    frequency: { batchInterval: Number(e.target.value) }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  非嚴重警報將在此時間間隔內批量發送
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  每小時最大通知數
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={settings.frequency.maxPerHour}
                  onChange={(e) => updateLocalSettings({
                    frequency: { maxPerHour: Number(e.target.value) }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="border-t pt-4">
                <label className="flex items-center gap-2 mb-3">
                  <input
                    type="checkbox"
                    checked={settings.frequency.quietHours.enabled}
                    onChange={(e) => updateLocalSettings({
                      frequency: {
                        quietHours: { ...settings.frequency.quietHours, enabled: e.target.checked }
                      }
                    })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="text-sm font-medium">啟用免打擾時間</span>
                </label>

                {settings.frequency.quietHours.enabled && (
                  <div className="flex items-center gap-2">
                    <input
                      type="time"
                      value={settings.frequency.quietHours.start}
                      onChange={(e) => updateLocalSettings({
                        frequency: {
                          quietHours: { ...settings.frequency.quietHours, start: e.target.value }
                        }
                      })}
                      className="px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                    <span className="text-sm">到</span>
                    <input
                      type="time"
                      value={settings.frequency.quietHours.end}
                      onChange={(e) => updateLocalSettings({
                        frequency: {
                          quietHours: { ...settings.frequency.quietHours, end: e.target.value }
                        }
                      })}
                      className="px-2 py-1 border border-gray-300 rounded text-sm"
                    />
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="weekends"
                  checked={settings.frequency.weekends}
                  onChange={(e) => updateLocalSettings({
                    frequency: { weekends: e.target.checked }
                  })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="weekends" className="text-sm">
                  週末接收通知
                </label>
              </div>
            </div>
          </section>

          {/* Notification Rules */}
          <section>
            <h3 className="text-md font-medium text-gray-900 mb-4">通知規則</h3>
            <div className="bg-gray-50 rounded-lg p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  最小通知優先級
                </label>
                <select
                  value={settings.rules.minPriority}
                  onChange={(e) => updateLocalSettings({
                    rules: { minPriority: e.target.value as AlertPriority }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="low">低</option>
                  <option value="medium">中</option>
                  <option value="high">高</option>
                  <option value="critical">嚴重</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  只會發送此優先級及以上的警報通知
                </p>
              </div>

              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.rules.excludeResolved}
                    onChange={(e) => updateLocalSettings({
                      rules: { excludeResolved: e.target.checked }
                    })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="text-sm">排除已解決的警報</span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={settings.rules.groupSimilar}
                    onChange={(e) => updateLocalSettings({
                      rules: { groupSimilar: e.target.checked }
                    })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="text-sm">合併相似通知</span>
                </label>
              </div>

              {settings.rules.groupSimilar && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    最大合併數量
                  </label>
                  <input
                    type="number"
                    min="2"
                    max="20"
                    value={settings.rules.maxGroupSize}
                    onChange={(e) => updateLocalSettings({
                      rules: { maxGroupSize: Number(e.target.value) }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}
            </div>
          </section>

          {/* Templates */}
          <section>
            <h3 className="text-md font-medium text-gray-900 mb-4">通知模板</h3>
            <div className="text-sm text-gray-600 bg-gray-50 rounded-lg p-4">
              通知模板功能正在開發中，敬請期待。您將能夠自定義不同類型警報的通知內容。
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default NotificationSettings;