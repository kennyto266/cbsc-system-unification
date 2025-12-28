/**
 * Dashboard Header - Quick Action Toolbar
 * Fast action buttons for backtesting, strategy creation, templates, and results
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Space } from 'antd';
import {
  BarChart2,
  Plus,
  LayoutTemplate,
  FileSearch
} from 'lucide-react';

/**
 * DashboardHeader Component
 */
export const DashboardHeader: React.FC = () => {
  const navigate = useNavigate();

  /**
   * Handle quick backtest - navigate to backtest page
   */
  const handleQuickBacktest = () => {
    navigate('/backtests');
  };

  /**
   * Handle new strategy - navigate to strategy generator
   */
  const handleNewStrategy = () => {
    navigate('/strategies/generator');
  };

  /**
   * Handle strategy templates - show templates modal or navigate
   */
  const handleStrategyTemplates = () => {
    navigate('/strategies?tab=templates');
  };

  /**
   * Handle view results - navigate to results page
   */
  const handleViewResults = () => {
    navigate('/strategies?tab=results');
  };

  return (
    <div className="dashboard-header-toolbar">
      <Space size="middle" style={{ width: '100%', justifyContent: 'flex-start' }}>
        <Button
          type="primary"
          icon={<BarChart2 size={18} />}
          onClick={handleQuickBacktest}
          style={{
            borderRadius: '8px',
            height: '40px',
            fontSize: '14px',
            fontWeight: 500
          }}
        >
          立即回測
        </Button>

        <Button
          icon={<Plus size={18} />}
          onClick={handleNewStrategy}
          style={{
            borderRadius: '8px',
            height: '40px',
            fontSize: '14px',
            fontWeight: 500
          }}
        >
          新建策略
        </Button>

        <Button
          icon={<LayoutTemplate size={18} />}
          onClick={handleStrategyTemplates}
          style={{
            borderRadius: '8px',
            height: '40px',
            fontSize: '14px',
            fontWeight: 500
          }}
        >
          策略模板
        </Button>

        <Button
          icon={<FileSearch size={18} />}
          onClick={handleViewResults}
          style={{
            borderRadius: '8px',
            height: '40px',
            fontSize: '14px',
            fontWeight: 500
          }}
        >
          查看結果
        </Button>
      </Space>
    </div>
  );
};

export default DashboardHeader;
