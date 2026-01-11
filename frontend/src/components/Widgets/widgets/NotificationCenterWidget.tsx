import React, { useState, useEffect } from 'react';
import { Widget } from '../../../types/widget';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent } from '../../ui/card';
import {
  Bell,
  AlertCircle,
  CheckCircle,
  Info,
  AlertTriangle,
  X,
  Clock,
  TrendingUp,
  Shield,
  Zap,
} from 'lucide-react';

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'alert';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  category?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface NotificationCenterWidgetProps {
  widget: Widget;
}

export function NotificationCenterWidget({ widget }: NotificationCenterWidgetProps) {
  const [notifications, setNotifications] = useState<Notification[]>([
    {
      id: '1',
      type: 'alert',
      title: '策略觸發信號',
      message: 'CBSC多因子策略檢測到0700.HK買入信號',
      timestamp: new Date(Date.now() - 1000 * 60 * 5),
      read: false,
      category: '策略信號',
      action: {
        label: '查看詳情',
        onClick: () => console.log('View strategy signal'),
      },
    },
    {
      id: '2',
      type: 'warning',
      title: '風險提醒',
      message: '動量突破策略當日虧損已超過2%',
      timestamp: new Date(Date.now() - 1000 * 60 * 15),
      read: false,
      category: '風險管理',
    },
    {
      id: '3',
      type: 'success',
      title: '交易執行成功',
      message: '已成功買入TCEHY 1000股，價格$312.60',
      timestamp: new Date(Date.now() - 1000 * 60 * 30),
      read: true,
      category: '交易執行',
    },
    {
      id: '4',
      type: 'info',
      title: '市場開盤提醒',
      message: '香港市場將於30分鐘後開盤',
      timestamp: new Date(Date.now() - 1000 * 60 * 60),
      read: true,
      category: '系統',
    },
    {
      id: '5',
      type: 'error',
      title: '數據延遲',
      message: '部分實時行情數據更新延遲',
      timestamp: new Date(Date.now() - 1000 * 60 * 120),
      read: true,
      category: '系統',
    },
  ]);

  const [filter, setFilter] = useState<string>('all');

  // Simulate new notifications
  useEffect(() => {
    const interval = setInterval(() => {
      if (Math.random() > 0.7) {
        const types: Notification['type'][] = ['info', 'success', 'warning', 'error', 'alert'];
        const categories = ['策略信號', '風險管理', '交易執行', '系統'];
        const messages = [
          '策略檢測到新的交易機會',
          '系統性能優化完成',
          '風險指標超出正常範圍',
          '新策略已成功部署',
          '數據同步完成',
        ];

        const newNotification: Notification = {
          id: Date.now().toString(),
          type: types[Math.floor(Math.random() * types.length)],
          title: '系統通知',
          message: messages[Math.floor(Math.random() * messages.length)],
          timestamp: new Date(),
          read: false,
          category: categories[Math.floor(Math.random() * categories.length)],
        };

        setNotifications(prev => [newNotification, ...prev.slice(0, 9)]);
      }
    }, (widget.config?.refreshInterval || 15) * 1000);

    return () => clearInterval(interval);
  }, [widget.config?.refreshInterval]);

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);

    if (minutes < 1) return '剛剛';
    if (minutes < 60) return `${minutes} 分鐘前`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)} 小時前`;
    return date.toLocaleDateString('zh-TW');
  };

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <X className="h-4 w-4 text-red-500" />;
      case 'alert':
        return <Bell className="h-4 w-4 text-purple-500" />;
      default:
        return <Info className="h-4 w-4" />;
    }
  };

  const getBackgroundClass = (type: Notification['type']) => {
    switch (type) {
      case 'info':
        return 'bg-blue-50 dark:bg-blue-950/20 border-l-blue-500';
      case 'success':
        return 'bg-green-50 dark:bg-green-950/20 border-l-green-500';
      case 'warning':
        return 'bg-yellow-50 dark:bg-yellow-950/20 border-l-yellow-500';
      case 'error':
        return 'bg-red-50 dark:bg-red-950/20 border-l-red-500';
      case 'alert':
        return 'bg-purple-50 dark:bg-purple-950/20 border-l-purple-500';
      default:
        return '';
    }
  };

  const filteredNotifications = notifications.filter(n => {
    if (filter === 'all') return true;
    if (filter === 'unread') return !n.read;
    return n.category === filter;
  });

  const categories = Array.from(
    new Set(notifications.map(n => n.category).filter(Boolean))
  );

  return (
    <div className="h-full flex flex-col">
      {/* Controls */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Button
            variant={filter === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('all')}
            className="h-7 text-xs"
          >
            全部
            {notifications.filter(n => !n.read).length > 0 && (
              <Badge variant="destructive" className="ml-1 h-4 text-xs">
                {notifications.filter(n => !n.read).length}
              </Badge>
            )}
          </Button>
          <Button
            variant={filter === 'unread' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('unread')}
            className="h-7 text-xs"
          >
            未讀
          </Button>
          {categories.map(cat => (
            <Button
              key={cat}
              variant={filter === cat ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter(cat)}
              className="h-7 text-xs"
            >
              {cat}
            </Button>
          ))}
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={markAllAsRead}
          className="h-7 text-xs"
        >
          全部標記已讀
        </Button>
      </div>

      {/* Notifications list */}
      <div className="flex-1 overflow-auto space-y-2">
        {filteredNotifications.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <div className="text-sm">暫無通知</div>
          </div>
        ) : (
          filteredNotifications.map((notification) => (
            <Card
              key={notification.id}
              className={`p-3 cursor-pointer transition-all border-l-4 ${
                getBackgroundClass(notification.type)
              } ${
                !notification.read ? 'font-semibold' : ''
              }`}
              onClick={() => markAsRead(notification.id)}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2 flex-1">
                  {getIcon(notification.type)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium truncate">
                        {notification.title}
                      </span>
                      {!notification.read && (
                        <div className="w-2 h-2 bg-blue-500 rounded-full" />
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground mb-1">
                      {notification.message}
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Clock className="h-3 w-3" />
                        <span className="text-xs text-muted-foreground">
                          {formatTime(notification.timestamp)}
                        </span>
                        {notification.category && (
                          <Badge variant="outline" className="text-xs">
                            {notification.category}
                          </Badge>
                        )}
                      </div>
                    </div>
                    {notification.action && (
                      <Button
                        variant="link"
                        size="sm"
                        className="text-xs h-auto p-0 mt-2"
                        onClick={(e) => {
                          e.stopPropagation();
                          notification.action!.onClick();
                        }}
                      >
                        {notification.action.label}
                      </Button>
                    )}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 flex-shrink-0 opacity-50 hover:opacity-100"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeNotification(notification.id);
                  }}
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Quick stats */}
      <div className="mt-3 pt-3 border-t">
        <div className="grid grid-cols-4 gap-2 text-center text-xs">
          <div>
            <div className="text-muted-foreground">全部</div>
            <div className="font-semibold">{notifications.length}</div>
          </div>
          <div>
            <div className="text-muted-foreground">未讀</div>
            <div className="font-semibold text-blue-600">
              {notifications.filter(n => !n.read).length}
            </div>
          </div>
          <div>
            <div className="text-muted-foreground">警告</div>
            <div className="font-semibold text-yellow-600">
              {notifications.filter(n => n.type === 'warning' || n.type === 'error').length}
            </div>
          </div>
          <div>
            <div className="text-muted-foreground">信號</div>
            <div className="font-semibold text-purple-600">
              {notifications.filter(n => n.type === 'alert').length}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}