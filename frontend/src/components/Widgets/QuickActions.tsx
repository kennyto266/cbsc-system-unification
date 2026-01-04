import React from 'react';

interface QuickActionsProps {
  data?: any;
  onAction?: (action: string) => void;
}

export const QuickActions: React.FC<QuickActionsProps> = ({ onAction }) => {
  return (
    <div className="quick-actions-widget">
      <h3>快捷操作</h3>
      <div className="widget-content">
        <button onClick={() => onAction?.('create-strategy')}>创建策略</button>
        <button onClick={() => onAction?.('run-backtest')}>运行回测</button>
        <button onClick={() => onAction?.('view-reports')}>查看报告</button>
      </div>
    </div>
  );
};
