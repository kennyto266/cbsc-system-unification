/**
 * Market-Wide Optimization Results Page
 * Displays complete optimization results with interactive charts and tables
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Result, Button, Progress, Alert, Breadcrumb, Spin, Space } from 'antd';
import { HomeOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import useTaskPolling from '../hooks/useTaskPolling';
import MetricsSummaryCards from '../components/MarketOptimization/MetricsSummaryCards';
import EquityCurveChart from '../components/MarketOptimization/EquityCurveChart';
import TopStrategiesTable from '../components/MarketOptimization/TopStrategiesTable';
import type { StrategyResult } from '../types/market-optimization';
import './MarketOptimizationResultsPage.css';

const MarketOptimizationResultsPage: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();

  // State
  const [selectedIndex, setSelectedIndex] = useState<number>(0);

  // Polling hook
  const {
    progress,
    results,
    isLoading,
    error,
    startPolling,
    isPolling
  } = useTaskPolling();

  // Start polling when taskId is available
  useEffect(() => {
    if (taskId) {
      startPolling(taskId);
    }
  }, [taskId, startPolling]);

  // Handle row selection
  const handleSelectStrategy = useCallback((index: number) => {
    setSelectedIndex(index);
  }, []);

  // Get selected strategy
  const selectedStrategy: StrategyResult | null = results?.top_10?.[selectedIndex] || null;

  // Error state
  if (error) {
    return (
      <div className="page-container">
        <Result
          status="error"
          title="優化任務失敗"
          subTitle={error}
          extra={
            <Space>
              <Button type="primary" onClick={() => navigate('/market-optimization')}>
                返回配置
              </Button>
              <Button onClick={() => window.location.reload()}>重試</Button>
            </Space>
          }
        />
      </div>
    );
  }

  // Loading state - task is running
  if (isLoading && isPolling && progress) {
    return (
      <div className="page-container">
        <Breadcrumb className="breadcrumb">
          <Breadcrumb.Item>
            <Link to="/"><HomeOutlined /> 首頁</Link>
          </Breadcrumb.Item>
          <Breadcrumb.Item>
            <Link to="/market-optimization">市場優化</Link>
          </Breadcrumb.Item>
          <Breadcrumb.Item>優化結果</Breadcrumb.Item>
        </Breadcrumb>

        <div className="loading-container">
          <Spin size="large" />
          <div className="loading-content">
            <h2>市場廣域參數優化進行中...</h2>
            <Progress
              percent={progress.progress_percentage}
              status="active"
              strokeColor="#1890ff"
              className="progress-bar"
            />
            <Alert
              message={
                <span>
                  正在處理：<strong>#{String(progress.current_stock_number).padStart(3, '0')} {progress.current_stock_symbol}</strong>
                </span>
              }
              description={
                <span>
                  進度：{progress.completed_stocks}/{progress.total_stocks} |{' '}
                  預計剩餘：{Math.ceil(progress.estimated_remaining_seconds / 60)} 分 {Math.floor(progress.estimated_remaining_seconds % 60)} 秒
                </span>
              }
              type="info"
              showIcon
            />
            {progress.best_sharpe_ratio > 0 && (
              <Alert
                message={
                  <span>
                    當前最佳：<strong>{progress.best_symbol}</strong> | Sharpe Ratio: {progress.best_sharpe_ratio.toFixed(2)}
                  </span>
                }
                type="success"
                showIcon
              />
            )}
          </div>
        </div>
      </div>
    );
  }

  // Loading state - initial load
  if (isLoading) {
    return (
      <div className="page-container">
        <div className="loading-container">
          <Spin size="large" />
          <p>載入中...</p>
        </div>
      </div>
    );
  }

  // No results
  if (!results || results.top_10.length === 0) {
    return (
      <div className="page-container">
        <Breadcrumb className="breadcrumb">
          <Breadcrumb.Item>
            <Link to="/"><HomeOutlined /> 首頁</Link>
          </Breadcrumb.Item>
          <Breadcrumb.Item>
            <Link to="/market-optimization">市場優化</Link>
          </Breadcrumb.Item>
          <Breadcrumb.Item>優化結果</Breadcrumb.Item>
        </Breadcrumb>

        <Result
          status="info"
          title="沒有符合條件的策略"
          subTitle="沒有策略通過 Sharpe Ratio 過濾條件，請調整參數重新優化"
          extra={
            <Space>
              <Button type="primary" onClick={() => navigate('/market-optimization')}>
                調整參數
              </Button>
              <Button onClick={() => navigate('/')}>返回首頁</Button>
            </Space>
          }
        />
      </div>
    );
  }

  // Success - display results
  return (
    <div className="page-container">
      <Breadcrumb className="breadcrumb">
        <Breadcrumb.Item>
          <Link to="/"><HomeOutlined /> 首頁</Link>
        </Breadcrumb.Item>
        <Breadcrumb.Item>
          <Link to="/market-optimization">市場優化</Link>
        </Breadcrumb.Item>
        <Breadcrumb.Item>優化結果</Breadcrumb.Item>
      </Breadcrumb>

      <div className="results-header">
        <h1>市場廣域優化結果</h1>
        <Space direction="vertical" size="small">
          <div className="result-summary">
            <span>Task ID: <strong>{taskId}</strong></span>
            <span> | </span>
            <span>耗時: <strong>{results.total_time_seconds.toFixed(1)}秒</strong></span>
            <span> | </span>
            <span>總回測: <strong>{results.summary.total_backtests_run.toLocaleString()}</strong></span>
            <span> | </span>
            <span>合格策略: <strong>{results.qualified_results_count.toLocaleString()}</strong></span>
          </div>
        </Space>
      </div>

      {/* Metrics Summary Cards */}
      <MetricsSummaryCards strategy={selectedStrategy} />

      {/* Equity Curve Chart */}
      <EquityCurveChart strategy={selectedStrategy} />

      {/* Top 10 Strategies Table */}
      <TopStrategiesTable
        strategies={results.top_10}
        selectedIndex={selectedIndex}
        onSelectStrategy={handleSelectStrategy}
      />
    </div>
  );
};

export default MarketOptimizationResultsPage;
