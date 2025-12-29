/**
 * MonitoringTab Component
 * Real-time monitoring tab with strategy execution and market data
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity } from 'lucide-react';
import { MonitoringHeader } from '../shared/MonitoringHeader';
import { useAppDispatch } from '../../../hooks/redux';
import './MonitoringTab.css';

export const MonitoringTab: React.FC = () => {
  const dispatch = useAppDispatch();
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const loadInitialData = () => {
      // Will be implemented after monitoringSlice is created
      // dispatch(fetchMonitoringData() as any);
      setLastRefresh(new Date());
    };

    loadInitialData();

    const interval = setInterval(() => {
      loadInitialData();
    }, 30000);

    return () => clearInterval(interval);
  }, [dispatch]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="monitoring-tab"
    >
      {/* Header with controls */}
      <MonitoringHeader lastRefresh={lastRefresh} />

      {/* Main content area */}
      <div className="monitoring-content">
        <div className="monitoring-grid">
          {/* Left: Strategy Execution Panel (60%) */}
          <div className="monitoring-grid-section monitoring-grid-section-left">
            <div className="monitoring-placeholder">
              <Activity size={48} />
              <p>策略執行面板（待實現）</p>
            </div>
          </div>

          {/* Right: Market Data Panel (40%) */}
          <div className="monitoring-grid-section monitoring-grid-section-right">
            <div className="monitoring-placeholder">
              <Activity size={48} />
              <p>市場數據面板（待實現）</p>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom: Alert Ticker */}
      <div className="alert-ticker-placeholder">
        警報滾動條（待實現）
      </div>
    </motion.div>
  );
};

export default MonitoringTab;
