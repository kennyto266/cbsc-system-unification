/**
 * Metric Card Component
 * Displays a single performance metric with trend indicator
 */

import React from 'react';
import { Card, Statistic } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons';
import type { MetricData } from '../../types/market-optimization';
import './MetricCard.css';

interface MetricCardProps {
  data: MetricData;
}

const MetricCard: React.FC<MetricCardProps> = ({ data }) => {
  const { label, value, unit = '', trend, format = 'number' } = data;

  // Determine value display
  let displayValue: React.ReactNode;
  let valueColor: string = '#000';

  if (typeof value === 'number') {
    switch (format) {
      case 'percentage':
        displayValue = `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
        valueColor = value >= 0 ? '#52c41a' : '#ff4d4f';
        break;
      case 'currency':
        displayValue = `$${value.toLocaleString()}`;
        break;
      default:
        displayValue = value.toFixed(2);
    }
  } else {
    displayValue = value;
  }

  // Determine trend icon
  let trendIcon: React.ReactNode = <MinusOutlined />;
  let trendColor: string = '#8c8c8c';

  if (trend === 'up') {
    trendIcon = <ArrowUpOutlined />;
    trendColor = '#52c41a';
  } else if (trend === 'down') {
    trendIcon = <ArrowDownOutlined />;
    trendColor = '#ff4d4f';
  }

  return (
    <Card className="metric-card" bordered={false}>
      <div className="metric-card-header">
        <span className="metric-label">{label}</span>
        <span className="metric-trend" style={{ color: trendColor }}>
          {trendIcon}
        </span>
      </div>
      <div className="metric-value" style={{ color: valueColor }}>
        {displayValue}
      </div>
      {unit && <div className="metric-unit">{unit}</div>}
    </Card>
  );
};

export default MetricCard;
