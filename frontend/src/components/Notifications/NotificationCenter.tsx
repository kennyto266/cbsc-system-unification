import React, { useState, useEffect, useCallback } from 'react';
import { Bell, X, Check, Settings, Trash2, AlertCircle, Info, AlertTriangle, CheckCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

// Types
interface Notification {
  id: string;
  type: 'email' | 'browser_push' | 'in_app' | 'sms' | 'webhook';
  title: string;
  content: string;
  status: 'pending' | 'sent' | 'failed';
  read: boolean;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  metadata?: Record<string, any>;
}

interface AlertRule {
  id: string;
  name: string;
  description?: string;
  enabled: boolean;
  alert_type: 'threshold' | 'event' | 'custom' | 'scheduled';
  severity: 'low' | 'medium' | 'high' | 'critical';
  notification_channels: string[];
  last_triggered?: string;
  trigger_count: number;
}

interface NotificationCenterProps {
  className?: string;
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({ className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [alertRules, setAlertRules] = useState<AlertRule[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [activeTab, setActiveTab] = useState<'notifications' | 'rules'>('notifications');
  const [loading, setLoading] = useState(false);

  // Fetch notifications
  const fetchNotifications = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/alerts/notifications?limit=50');
      const data = await response.json();
      setNotifications(data);

      // Calculate unread count
      const unread = data.filter((n: Notification) => !n.read).length;
      setUnreadCount(unread);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch alert rules
  const fetchAlertRules = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/alerts/rules');
      const data = await response.json();
      setAlertRules(data);
    } catch (error) {
      console.error('Failed to fetch alert rules:', error);
    }
  }, []);

  // Initial load
  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
      fetchAlertRules();
    }
  }, [isOpen, fetchNotifications, fetchAlertRules]);

  // WebSocket for real-time updates
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:3000/ws/realtime');

    ws.onopen = () => {
      console.log('NotificationCenter WebSocket connected');
      ws.send(JSON.stringify({
        type: 'subscribe',
        payload: { channel: 'notifications' }
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'notification') {
        setNotifications(prev => [data.notification, ...prev]);
        setUnreadCount(prev => prev + 1);
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  // Mark notification as read
  const markAsRead = async (notificationId: string) => {
    try {
      await fetch(`/api/v1/alerts/notifications/${notificationId}/read`, {
        method: 'PUT'
      });

      setNotifications(prev =>
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  // Mark all as read
  const markAllAsRead = async () => {
    try {
      await fetch('/api/v1/alerts/notifications/read-all', {
        method: 'PUT'
      });

      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  };

  // Toggle alert rule
  const toggleAlertRule = async (ruleId: string, enabled: boolean) => {
    try {
      const rule = alertRules.find(r => r.id === ruleId);
      if (!rule) return;

      const response = await fetch(`/api/v1/alerts/rules/${ruleId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...rule, enabled })
      });

      if (response.ok) {
        setAlertRules(prev =>
          prev.map(r => r.id === ruleId ? { ...r, enabled } : r)
        );
      }
    } catch (error) {
      console.error('Failed to toggle alert rule:', error);
    }
  };

  // Test notification
  const testNotification = async (channel: string) => {
    try {
      await fetch('/api/v1/alerts/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel,
          title: '测试通知',
          message: '这是一条测试通知，用于验证通知系统是否正常工作。'
        })
      });
    } catch (error) {
      console.error('Failed to send test notification:', error);
    }
  };

  // Get severity icon
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'low':
        return <Info className="w-4 h-4 text-blue-500" />;
      case 'medium':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      case 'high':
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      case 'critical':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default:
        return <Info className="w-4 h-4 text-gray-500" />;
    }
  };

  // Get channel label
  const getChannelLabel = (channel: string) => {
    const labels: Record<string, string> = {
      email: '邮件',
      browser_push: '浏览器推送',
      in_app: '应用内',
      sms: '短信',
      webhook: 'Webhook'
    };
    return labels[channel] || channel;
  };

  return (
    <div className={`relative ${className}`}>
      {/* Bell button with unread count */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 transition-colors"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notification Center Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold">通知中心</h2>
            <div className="flex items-center space-x-2">
              {activeTab === 'notifications' && unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  全部标记为已读
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('notifications')}
              className={`flex-1 py-2 px-4 text-sm font-medium transition-colors ${
                activeTab === 'notifications'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              通知
              {unreadCount > 0 && (
                <span className="ml-2 bg-red-500 text-white text-xs rounded-full px-2 py-0.5">
                  {unreadCount}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('rules')}
              className={`flex-1 py-2 px-4 text-sm font-medium transition-colors ${
                activeTab === 'rules'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              告警规则
            </button>
          </div>

          {/* Content */}
          <div className="max-h-96 overflow-y-auto">
            {activeTab === 'notifications' ? (
              <>
                {loading ? (
                  <div className="p-4 text-center text-gray-500">
                    加载中...
                  </div>
                ) : notifications.length === 0 ? (
                  <div className="p-4 text-center text-gray-500">
                    暂无通知
                  </div>
                ) : (
                  <div className="divide-y divide-gray-200">
                    {notifications.map((notification) => (
                      <div
                        key={notification.id}
                        className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                          !notification.read ? 'bg-blue-50' : ''
                        }`}
                        onClick={() => !notification.read && markAsRead(notification.id)}
                      >
                        <div className="flex items-start space-x-3">
                          {getSeverityIcon(notification.severity)}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <p className="text-sm font-medium text-gray-900 truncate">
                                {notification.title}
                              </p>
                              <span className="text-xs text-gray-500">
                                {formatDistanceToNow(new Date(notification.timestamp), {
                                  addSuffix: true,
                                  locale: zhCN
                                })}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mt-1">
                              {notification.content}
                            </p>
                            <div className="flex items-center mt-2 space-x-2 text-xs text-gray-500">
                              <span>{getChannelLabel(notification.type)}</span>
                              <span>•</span>
                              <span className={
                                notification.status === 'sent' ? 'text-green-600' :
                                notification.status === 'failed' ? 'text-red-600' :
                                'text-yellow-600'
                              }>
                                {notification.status === 'sent' ? '已发送' :
                                 notification.status === 'failed' ? '发送失败' :
                                 '待发送'}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <>
                {alertRules.length === 0 ? (
                  <div className="p-4 text-center text-gray-500">
                    暂无告警规则
                  </div>
                ) : (
                  <div className="divide-y divide-gray-200">
                    {alertRules.map((rule) => (
                      <div key={rule.id} className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            {getSeverityIcon(rule.severity)}
                            <div>
                              <p className="text-sm font-medium text-gray-900">
                                {rule.name}
                              </p>
                              {rule.description && (
                                <p className="text-xs text-gray-600 mt-1">
                                  {rule.description}
                                </p>
                              )}
                              <div className="flex items-center mt-2 space-x-2 text-xs text-gray-500">
                                <span>触发次数: {rule.trigger_count}</span>
                                {rule.last_triggered && (
                                  <>
                                    <span>•</span>
                                    <span>
                                      最后触发: {formatDistanceToNow(new Date(rule.last_triggered), {
                                        addSuffix: true,
                                        locale: zhCN
                                      })}
                                    </span>
                                  </>
                                )}
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={() => toggleAlertRule(rule.id, !rule.enabled)}
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
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>

          {/* Footer */}
          {activeTab === 'notifications' && (
            <div className="p-4 border-t border-gray-200">
              <button
                onClick={() => testNotification('browser_push')}
                className="w-full py-2 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md text-sm font-medium transition-colors"
              >
                发送测试通知
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;