import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Outlet } from 'react-router-dom';
import { toast } from 'react-toastify';

// Components
import { StatCards } from './components/StatCards';
import { PerformanceChart } from './components/PerformanceChart';
import { StrategyList } from './components/StrategyList';
import { RecentTrades } from './components/RecentTrades';
import { RealTimePrices } from './components/RealTimePrices';
import { QuickActions } from './components/QuickActions';

// Hooks
import { useDashboardData } from './hooks/useDashboardData';
import { useRealTimeData } from './hooks/useRealTimeData';

// Services
import { dashboardWS } from '../../services/dashboardAPI';

// Styles
import './Dashboard.css';

/**
 * Main Dashboard Component
 * CBSC量化交易策略管理系统主仪表盘
 */
export const Dashboard: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState('1M');
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([]);

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

  // Handle strategy selection
  const handleStrategySelect = (strategyId: string, selected: boolean) => {
    setSelectedStrategies(prev =>
      selected
        ? [...prev, strategyId]
        : prev.filter(id => id !== strategyId)
    );
  };

  // Handle batch operations
  const handleBatchStart = async () => {
    try {
      // API call to batch start strategies
      toast.success('策略批量启动成功');
      refetch();
    } catch (error) {
      toast.error('批量启动失败');
    }
  };

  const handleBatchStop = async () => {
    try {
      // API call to batch stop strategies
      toast.success('策略批量停止成功');
      refetch();
    } catch (error) {
      toast.error('批量停止失败');
    }
  };

  // Handle period change
  const handlePeriodChange = (period: string) => {
    setSelectedPeriod(period);
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
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="dashboard-container"
    >
      {/* Dashboard Header */}
      <div className="dashboard-header">
        <h1 className="dashboard-title">量化交易策略仪表盘</h1>
        <div className="dashboard-controls">
          <select
            value={selectedPeriod}
            onChange={(e) => handlePeriodChange(e.target.value)}
            className="period-selector"
          >
            <option value="1D">今日</option>
            <option value="1W">本周</option>
            <option value="1M">本月</option>
            <option value="3M">三个月</option>
            <option value="6M">六个月</option>
            <option value="1Y">一年</option>
            <option value="ALL">全部</option>
          </select>
          <button onClick={refetch} className="refresh-button">
            刷新数据
          </button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="dashboard-loading">
          <div className="spinner"></div>
          <p>加载数据中...</p>
        </div>
      )}

      {/* Dashboard Content */}
      {!isLoading && (
        <div className="dashboard-content">
          {/* Statistics Cards */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="dashboard-section"
          >
            <StatCards stats={stats} isLoading={isLoading} />
          </motion.div>

          {/* Main Grid Layout */}
          <div className="dashboard-grid">
            {/* Performance Chart Section */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="grid-item grid-item-2x2"
            >
              <PerformanceChart
                data={performanceData}
                period={selectedPeriod}
                title="策略收益曲线"
              />
            </motion.div>

            {/* Real-time Prices */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="grid-item"
            >
              <RealTimePrices prices={realTimePrices} />
            </motion.div>

            {/* Strategy List */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="grid-item grid-item-2x1"
            >
              <StrategyList
                strategies={strategies}
                selectedStrategies={selectedStrategies}
                onStrategySelect={handleStrategySelect}
                onBatchStart={handleBatchStart}
                onBatchStop={handleBatchStop}
              />
            </motion.div>

            {/* Recent Trades */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.5 }}
              className="grid-item"
            >
              <RecentTrades trades={trades} />
            </motion.div>
          </div>

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="dashboard-section"
          >
            <QuickActions />
          </motion.div>
        </div>
      )}

      {/* Nested Routes */}
      <Outlet />
    </motion.div>
  );
};

export default Dashboard;