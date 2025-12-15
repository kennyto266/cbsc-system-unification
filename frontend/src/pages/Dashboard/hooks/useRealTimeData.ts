import { useState, useEffect, useCallback, useRef } from 'react';
import { RealTimePrice } from '../../../types/dashboard';
import { dashboardWS } from '../../../services/dashboardAPI';

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

interface UseRealTimeDataReturn {
  realTimePrices: RealTimePrice[];
  notifications: Notification[];
  subscribeToPrices: (callback: (prices: RealTimePrice[]) => void) => void;
  subscribeToNotifications: (callback: (notification: Notification) => void) => void;
  markNotificationAsRead: (id: string) => void;
  clearAllNotifications: () => void;
}

export const useRealTimeData = (): UseRealTimeDataReturn => {
  const [realTimePrices, setRealTimePrices] = useState<RealTimePrice[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const priceCallbacksRef = useRef<Set<(prices: RealTimePrice[]) => void>>(new Set());
  const notificationCallbacksRef = useRef<Set<(notification: Notification) => void>>(new Set());

  // Mock initial prices
  useEffect(() => {
    const mockPrices: RealTimePrice[] = [
      {
        symbol: '000001',
        price: 10.85,
        change: 0.15,
        changePercent: 1.40,
        volume: 1256800,
        timestamp: new Date().toISOString(),
      },
      {
        symbol: '000002',
        price: 25.63,
        change: -0.32,
        changePercent: -1.23,
        volume: 892340,
        timestamp: new Date().toISOString(),
      },
      {
        symbol: '600036',
        price: 42.18,
        change: 0.88,
        changePercent: 2.13,
        volume: 1567800,
        timestamp: new Date().toISOString(),
      },
      {
        symbol: 'IF2312',
        price: 3998.6,
        change: 15.4,
        changePercent: 0.39,
        volume: 56789,
        timestamp: new Date().toISOString(),
      },
    ];
    setRealTimePrices(mockPrices);
  }, []);

  // Subscribe to price updates
  const subscribeToPrices = useCallback((callback: (prices: RealTimePrice[]) => void) => {
    priceCallbacksRef.current.add(callback);

    // Also subscribe to WebSocket for real-time updates
    dashboardWS.subscribe('price_update', (data) => {
      setRealTimePrices(prev => {
        const updated = [...prev];
        const index = updated.findIndex(p => p.symbol === data.symbol);
        if (index !== -1) {
          updated[index] = data;
        } else {
          updated.push(data);
        }
        return updated;
      });

      // Notify all subscribers
      priceCallbacksRef.current.forEach(cb => cb(realTimePrices));
    });

    // Unsubscribe function
    return () => {
      priceCallbacksRef.current.delete(callback);
    };
  }, [realTimePrices]);

  // Subscribe to notifications
  const subscribeToNotifications = useCallback((callback: (notification: Notification) => void) => {
    notificationCallbacksRef.current.add(callback);

    // Subscribe to WebSocket for notifications
    dashboardWS.subscribe('notification', (data) => {
      const notification: Notification = {
        id: Date.now().toString(),
        ...data,
        timestamp: new Date().toISOString(),
        read: false,
      };

      setNotifications(prev => [notification, ...prev]);

      // Notify all subscribers
      notificationCallbacksRef.current.forEach(cb => cb(notification));
    });

    // Unsubscribe function
    return () => {
      notificationCallbacksRef.current.delete(callback);
    };
  }, []);

  // Mark notification as read
  const markNotificationAsRead = useCallback((id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  }, []);

  // Clear all notifications
  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // Simulate real-time price updates
  useEffect(() => {
    const interval = setInterval(() => {
      setRealTimePrices(prev => prev.map(price => ({
        ...price,
        price: price.price * (1 + (Math.random() - 0.5) * 0.002),
        change: price.change + (Math.random() - 0.5) * 0.1,
        changePercent: price.changePercent + (Math.random() - 0.5) * 0.2,
        volume: price.volume + Math.floor(Math.random() * 10000),
        timestamp: new Date().toISOString(),
      })));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Simulate notifications
  useEffect(() => {
    const mockNotifications = [
      {
        type: 'success' as const,
        title: '策略执行成功',
        message: '双均线策略已成功买入 000001',
      },
      {
        type: 'warning' as const,
        title: '风险提醒',
        message: '当前回撤超过15%，请注意风险控制',
      },
      {
        type: 'info' as const,
        title: '系统更新',
        message: '新版本已上线，优化了回测性能',
      },
    ];

    const interval = setInterval(() => {
      const randomNotification = mockNotifications[Math.floor(Math.random() * mockNotifications.length)];
      const notification: Notification = {
        id: Date.now().toString(),
        ...randomNotification,
        timestamp: new Date().toISOString(),
        read: false,
      };
      setNotifications(prev => [notification, ...prev].slice(0, 10));
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  return {
    realTimePrices,
    notifications,
    subscribeToPrices,
    subscribeToNotifications,
    markNotificationAsRead,
    clearAllNotifications,
  };
};