import React from 'react';

interface StrategyOverviewProps {
  data?: any;
}

export const StrategyOverview: React.FC<StrategyOverviewProps> = ({ data }) => {
  return (
    <div className="strategy-overview-widget">
      <h3>策略概览</h3>
      <div className="widget-content">
        <div className="stat-item">
          <span className="label">总策略数</span>
          <span className="value">{data?.totalStrategies || 0}</span>
        </div>
        <div className="stat-item">
          <span className="label">活跃策略</span>
          <span className="value">{data?.activeStrategies || 0}</span>
        </div>
      </div>
    </div>
  );
};
