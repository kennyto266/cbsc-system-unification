/**
 * PerformanceTab Component
 * Performance analysis with charts and stress test
 */

import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Row, Col, Alert, Spin } from 'antd';
import { useAppDispatch, useAppSelector } from '../../../hooks/redux';
import { fetchPerformanceAnalytics } from '../../../store/slices/performanceAnalyticsSlice';
import { PerformanceHeader } from './PerformanceHeader';
import { ReturnAttributionChart } from './ReturnAttribution';
import { RiskRadarChart } from './RiskAnalysis';
import { CorrelationHeatmap } from './CorrelationAnalysis';
import { StressTestTable } from './StressTest';
import './PerformanceTab.css';

export const PerformanceTab: React.FC = () => {
  const dispatch = useAppDispatch();
  const { isLoading, error } = useAppSelector((state) => state.performanceAnalytics);

  // Load initial data
  useEffect(() => {
    dispatch(fetchPerformanceAnalytics({ timeRange: '1m' }));
  }, [dispatch]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="performance-tab"
    >
      {/* Error Display */}
      {error && (
        <Alert
          message="數據加載失敗"
          description={error}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Global Loading Indicator */}
      {isLoading && (
        <div style={{ textAlign: 'center', padding: '100px 0' }}>
          <Spin size="large" tip="加載性能分析數據中..." />
        </div>
      )}

      {/* Control Header */}
      <PerformanceHeader />

      {/* Return Attribution Chart - Full Width */}
      <div className="performance-section">
        <ReturnAttributionChart />
      </div>

      {/* Risk Radar and Correlation Heatmap - Side by Side */}
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <div className="performance-section">
            <RiskRadarChart />
          </div>
        </Col>
        <Col xs={24} lg={12}>
          <div className="performance-section">
            <CorrelationHeatmap />
          </div>
        </Col>
      </Row>

      {/* Stress Test Results - Full Width */}
      <div className="performance-section">
        <h3 className="performance-section-title">壓力測試結果</h3>
        <StressTestTable />
      </div>
    </motion.div>
  );
};

export default PerformanceTab;
