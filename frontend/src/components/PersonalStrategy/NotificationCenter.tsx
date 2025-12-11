import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface Notification {
  id: string;
  type: 'signal' | 'risk' | 'performance' | 'system';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

interface NotificationCenterProps {
  userId: string;
  apiUrl: string;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  userId,
  apiUrl
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Mock notifications data
    const mockNotifications: Notification[] = [
      {
        id: '1',
        type: 'signal',
        title: 'RSI策略买入信号',
        message: '直接RSI情绪策略检测到强烈买入信号，置信度85%',
        timestamp: new Date(Date.now() - 5 * 60 * 1000),
        read: false,
        severity: 'medium'
      },
      {
        id: '2',
        type: 'risk',
        title: '风险预警',
        message: '投资组合VaR超过设定阈值，建议检查仓位配置',
        timestamp: new Date(Date.now() - 15 * 60 * 1000),
        read: false,
        severity: 'high'
      },
      {
        id: '3',
        type: 'performance',
        title: '月度表现报告',
        message: '本月收益率+3.2%，夏普比率1.85，表现良好',
        timestamp: new Date(Date.now() - 60 * 60 * 1000),
        read: true,
        severity: 'low'
      },
      {
        id: '4',
        type: 'system',
        title: '系统维护通知',
        message: '系统将于今晚23:00-24:00进行例行维护',
        timestamp: new Date(Date.now() - 120 * 60 * 1000),
        read: true,
        severity: 'low'
      }
    ];

    setTimeout(() => {
      setNotifications(mockNotifications);
      setIsLoading(false);
    }, 1000);
  }, [userId, apiUrl]);

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'signal':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        );
      case 'risk':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        );
      case 'performance':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        );
      case 'system':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'primary';
      case 'low': return 'neutral';
      default: return 'neutral';
    }
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    return `${diffDays}天前`;
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  if (isLoading) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">通知中心</h3>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-neutral-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-neutral-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-neutral-900">
          通知中心
          {unreadCount > 0 && (
            <Badge variant="error" size="sm" className="ml-2">
              {unreadCount}
            </Badge>
          )}
        </h3>
        <Button variant="outline" size="sm">
          全部标记为已读
        </Button>
      </div>

      <div className="space-y-3">
        {notifications.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-neutral-400 mb-4">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            </div>
            <p className="text-neutral-600">暂无通知</p>
          </div>
        ) : (
          notifications.map((notification) => (
            <div
              key={notification.id}
              className={`p-4 border rounded-lg transition-colors ${
                notification.read
                  ? 'border-neutral-200 bg-white'
                  : 'border-primary-200 bg-primary-50'
              }`}
            >
              <div className="flex items-start space-x-3">
                <div className={`mt-1 ${
                  notification.type === 'signal' ? 'text-primary-600' :
                  notification.type === 'risk' ? 'text-warning-600' :
                  notification.type === 'performance' ? 'text-success-600' :
                  'text-neutral-600'
                }`}>
                  {getNotificationIcon(notification.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-medium text-neutral-900 truncate">
                      {notification.title}
                    </h4>
                    <div className="flex items-center space-x-2 ml-4">
                      <Badge
                        variant={getSeverityColor(notification.severity) as any}
                        size="xs"
                      >
                        {notification.severity === 'critical' ? '紧急' :
                         notification.severity === 'high' ? '重要' :
                         notification.severity === 'medium' ? '中等' : '一般'}
                      </Badge>
                      {!notification.read && (
                        <span className="w-2 h-2 bg-primary-600 rounded-full"></span>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-neutral-600 mb-2">
                    {notification.message}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-neutral-500">
                      {formatTimeAgo(notification.timestamp)}
                    </span>
                    {!notification.read && (
                      <Button variant="ghost" size="xs">
                        标记为已读
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {notifications.length > 0 && (
        <div className="mt-6 text-center">
          <Button variant="outline" size="sm">
            查看所有通知
          </Button>
        </div>
      )}
    </Card>
  );
};