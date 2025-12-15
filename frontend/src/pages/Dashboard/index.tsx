import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Outlet } from 'react-router-dom';
import { toast } from 'react-toastify';

// Grid System
import { GridProvider } from '../../components/Grid/GridProvider';
import { GridSystem } from '../../components/Grid/GridSystem';
import { widgetRegistry } from '../../components/WidgetTypes';
import { WidgetConfig } from '../../types/grid';

// Hooks
import { useDashboardData } from './hooks/useDashboardData';
import { useRealTimeData } from './hooks/useRealTimeData';

// Services
import { dashboardWS } from '../../services/dashboardAPI';

// Styles
import './Dashboard.css';

// Default widgets for the dashboard
const defaultWidgets: WidgetConfig[] = [
  {
    id: 'strategy-overview-1',
    type: 'strategy-overview',
    title: '策略概览',
    x: 0,
    y: 0,
    w: 6,
    h: 4,
    isDraggable: true,
    isResizable: true
  },
  {
    id: 'performance-metrics-1',
    type: 'performance-metrics',
    title: '性能指标',
    x: 6,
    y: 0,
    w: 6,
    h: 4,
    isDraggable: true,
    isResizable: true
  },
  {
    id: 'realtime-monitor-1',
    type: 'realtime-monitor',
    title: '实时监控',
    x: 0,
    y: 4,
    w: 6,
    h: 4,
    isDraggable: true,
    isResizable: true
  },
  {
    id: 'quick-actions-1',
    type: 'quick-actions',
    title: '快捷操作',
    x: 6,
    y: 4,
    w: 6,
    h: 4,
    isDraggable: true,
    isResizable: false
  }
];

/**
 * Main Dashboard Component
 * CBSC量化交易策略管理系统主仪表盘
 */
export const Dashboard: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState('1M');

  // Custom hooks for data management
  const {
    stats,
    strategies,
    performanceData,
    trades,
    isLoading,
    error,
    refetch,
  } = useDashboardData(selectedPeriod);

  // Real-time data subscription
  const {
    realTimePrices,
    notifications,
    subscribeToPrices,
    subscribeToNotifications,
  } = useRealTimeData();

  // Initialize WebSocket connection
  useEffect(() => {
    dashboardWS.connect();

    // Subscribe to real-time data
    subscribeToPrices((data) => {
      // Handle price updates
    });

    subscribeToNotifications((data) => {
      toast.info(data.message);
    });

    return () => {
      dashboardWS.disconnect();
    };
  }, []);

  // Handle period change
  const handlePeriodChange = (period: string) => {
    setSelectedPeriod(period);
  };

  // Add widget handler
  const handleAddWidget = (widgetType: string) => {
    // This will be handled by the GridSystem
    console.log('Adding widget:', widgetType);
  };

  if (error) {
    return (
      <div className="dashboard-error">
        <h3>加载失败</h3>
        <p>{error.message}</p>
        <button onClick={refetch}>重试</button>
      </div>
    );
  }

  return (
    <GridProvider defaultWidgets={defaultWidgets}>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="dashboard-container"
      >
        {/* Dashboard Header */}
        <div className="dashboard-header bg-background border-b border-border px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="dashboard-title text-2xl font-bold">量化交易策略仪表盘</h1>
            <div className="dashboard-controls flex items-center space-x-4">
              <select
                value={selectedPeriod}
                onChange={(e) => handlePeriodChange(e.target.value)}
                className="period-selector px-3 py-1 border border-border rounded-md bg-background"
              >
                <option value="1D">今日</option>
                <option value="1W">本周</option>
                <option value="1M">本月</option>
                <option value="3M">三个月</option>
                <option value="6M">六个月</option>
                <option value="1Y">一年</option>
                <option value="ALL">全部</option>
              </select>
              <button
                onClick={refetch}
                className="refresh-button px-4 py-1 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
              >
                刷新数据
              </button>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="dashboard-loading flex items-center justify-center h-64">
            <div className="spinner mr-3"></div>
            <p>加载数据中...</p>
          </div>
        )}

        {/* Dashboard Grid Content */}
        {!isLoading && (
          <div className="dashboard-content p-6">
            <GridSystem
              widgetRegistry={widgetRegistry}
              onAddWidget={handleAddWidget}
            />
          </div>
        )}

        {/* Nested Routes */}
        <Outlet />
      </motion.div>
    </GridProvider>
  );
};

export default Dashboard;