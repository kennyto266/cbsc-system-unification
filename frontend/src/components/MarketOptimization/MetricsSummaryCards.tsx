/**
 * Metrics Summary Cards Component
 * Displays 6 key performance metrics in a grid layout
 */

import React from 'react';
import { Row, Col } from 'antd';
import MetricCard from './MetricCard';
import type { MetricData } from '../../types/market-optimization';
import type { StrategyResult } from '../../types/market-optimization';
import './MetricsSummaryCards.css';

interface MetricsSummaryCardsProps {
  strategy: StrategyResult | null;
}

const MetricsSummaryCards: React.FC<MetricsSummaryCardsProps> = ({ strategy }) => {
  if (!strategy) {
    return (
      <div className="metrics-summary-empty">
        請選擇一個策略查看詳細指標
      </div>
    );
  }

  const metrics: MetricData[] = [
    {
      label: '總回報率',
      value: strategy.total_return,
      format: 'percentage',
      trend: strategy.total_return >= 0 ? 'up' : 'down'
    },
    {
      label: 'Sharpe Ratio',
      value: strategy.sharpe_ratio,
      format: 'number',
      trend: strategy.sharpe_ratio >= 1 ? 'up' : strategy.sharpe_ratio >= 0 ? 'flat' : 'down'
    },
    {
      label: '最大回撤',
      value: strategy.max_drawdown,
      format: 'percentage',
      trend: 'down' // Lower is better for drawdown
    },
    {
      label: '超額回報',
      value: strategy.excess_return,
      format: 'percentage',
      trend: strategy.excess_return >= 0 ? 'up' : 'down'
    },
    {
      label: 'Information Ratio',
      value: strategy.information_ratio,
      format: 'number'
    },
    {
      label: '交易天數',
      value: strategy.equity_curve?.length || 0,
      format: 'number'
    }
  ];

  return (
    <div className="metrics-summary-cards">
      <Row gutter={[16, 16]}>
        {metrics.map((metric, index) => (
          <Col xs={12} sm={8} md={4} lg={4} key={index}>
            <MetricCard data={metric} />
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default MetricsSummaryCards;
