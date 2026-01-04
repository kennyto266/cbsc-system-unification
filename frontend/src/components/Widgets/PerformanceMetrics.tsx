import React from 'react';

interface PerformanceMetricsProps {
  data?: any;
}

export const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ data }) => {
  return (
    <div className="performance-metrics-widget">
      <h3>性能指标</h3>
      <div className="widget-content">
        <div className="stat-item">
          <span className="label">总收益率</span>
          <span className="value">{data?.totalReturn || 0}%</span>
        </div>
        <div className="stat-item">
          <span className="label">夏普比率</span>
          <span className="value">{data?.sharpeRatio || 0}</span>
        </div>
      </div>
    </div>
  );
};
