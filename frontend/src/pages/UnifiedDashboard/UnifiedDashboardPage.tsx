/**
 * Unified Dashboard Page
 * Main page combining all dashboard components
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Tabs, Button, Space } from 'antd';
import {
  LayoutDashboard,
  Activity,
  TrendingUp,
  Settings,
  Maximize2,
  Minimize2,
} from 'lucide-react';

import { UnifiedDashboard } from '../../components/Dashboard/UnifiedDashboard';
import { MonitoringTab } from '../../components/Dashboard/MonitoringTab/MonitoringTab';
import { AlertTicker } from '../../components/Dashboard/MonitoringTab/AlertTicker';
import { ChartsDashboard } from '../../components/Charts/ChartsDashboard';
import { OverviewTab } from '../../components/Dashboard/OverviewTab/OverviewTab';
import { PerformanceTab } from '../../components/Dashboard/PerformanceTab/PerformanceTab';

import { useAppSelector } from '../../hooks/redux';
import { Strategy } from '../../types/strategy';

import './UnifiedDashboardPage.css';

const { TabPane } = Tabs;

/**
 * UnifiedDashboardPage Component
 */
export const UnifiedDashboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Get strategies from Redux store
  const strategies = useAppSelector((state) => state.strategy.strategies);

  /**
   * Handle tab change
   */
  const handleTabChange = (key: string) => {
    setActiveTab(key);
  };

  /**
   * Handle strategy click
   */
  const handleStrategyClick = (strategyId: string) => {
    // Navigate to strategy detail page
    window.location.href = `/strategies/${strategyId}`;
  };

  /**
   * Toggle fullscreen
   */
  const toggleFullscreen = () => {
    setIsFullscreen((prev) => !prev);
    if (!isFullscreen) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className={`unified-dashboard-page ${isFullscreen ? 'fullscreen' : ''}`}
    >
      {/* Page Header */}
      <div className="page-header mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              量化交易系統儀表盤
            </h1>
            <p className="text-gray-500 dark:text-gray-400">
              CBSC Trading System Dashboard - 策略管理、實時監控、性能分析
            </p>
          </div>

          <Space>
            <Button
              icon={isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
              onClick={toggleFullscreen}
            >
              {isFullscreen ? '退出全屏' : '全屏顯示'}
            </Button>
          </Space>
        </div>
      </div>

      {/* Main Content */}
      <Tabs
        activeKey={activeTab}
        onChange={handleTabChange}
        type="card"
        size="large"
        className="dashboard-tabs"
      >
        {/* Overview Tab */}
        <TabPane
          tab={
            <span className="flex items-center gap-2">
              <LayoutDashboard size={18} />
              總覽
            </span>
          }
          key="overview"
        >
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <OverviewTab />
          </motion.div>
        </TabPane>

        {/* Real-Time Monitoring Tab */}
        <TabPane
          tab={
            <span className="flex items-center gap-2">
              <Activity size={18} />
              實時監控
            </span>
          }
          key="monitoring"
        >
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <MonitoringTab />
          </motion.div>
        </TabPane>

        {/* Performance Analysis Tab */}
        <TabPane
          tab={
            <span className="flex items-center gap-2">
              <TrendingUp size={18} />
              性能分析
            </span>
          }
          key="performance"
        >
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <PerformanceTab />
          </motion.div>
        </TabPane>

        {/* Settings Tab */}
        <TabPane
          tab={
            <span className="flex items-center gap-2">
              <Settings size={18} />
              設置
            </span>
          }
          key="settings"
        >
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="settings-container"
          >
            <div className="text-center py-12">
              <Settings size={48} className="mx-auto mb-4 text-gray-400" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                儀表盤設置
              </h3>
              <p className="text-gray-500">
                自定義儀表盤配置、布局和顯示選項
              </p>
              <div className="mt-6">
                <Button type="primary" onClick={() => setActiveTab('overview')}>
                  返回總覽
                </Button>
              </div>
            </div>
          </motion.div>
        </TabPane>
      </Tabs>

      {/* Alert Ticker */}
      <AlertTicker />
    </motion.div>
  );
};

export default UnifiedDashboardPage;
