/**
 * Strategy List Component
 * Displays strategy status with real-time updates
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  TrendingUp,
  TrendingDown,
  Minus,
  Eye,
  Play,
  Pause,
  Edit
} from 'lucide-react';
import { Dropdown, Button, Space } from 'antd';
import type { MenuProps } from 'antd';
import { selectDashboardStats } from '../../../store/slices/dashboardSlice';
import { strategiesApi } from '../../../store/services/strategiesApi';
import './StrategyList.css';

// Strategy interface
interface Strategy {
  id: string;
  name: string;
  status: 'running' | 'paused' | 'stopped' | 'error';
  dailyReturn: number;
  totalReturn: number;
  lastUpdate: string;
}

/**
 * StrategyList Component
 */
export const StrategyList: React.FC = () => {
  const navigate = useNavigate();
  const stats = useSelector(selectDashboardStats);
  const [strategies, setStrategies] = useState<Strategy[]>([
    // Mock data for demo - replace with real API call
    {
      id: 'strategy-1',
      name: '經濟動量策略',
      status: 'running',
      dailyReturn: 2.3,
      totalReturn: 15.7,
      lastUpdate: new Date().toISOString()
    },
    {
      id: 'strategy-2',
      name: '流動性情緒策略',
      status: 'running',
      dailyReturn: 0.8,
      totalReturn: 8.2,
      lastUpdate: new Date().toISOString()
    },
    {
      id: 'strategy-3',
      name: '宏觀平衡策略',
      status: 'paused',
      dailyReturn: -1.2,
      totalReturn: -3.5,
      lastUpdate: new Date().toISOString()
    },
    {
      id: 'strategy-4',
      name: 'HIBOR利率策略',
      status: 'running',
      dailyReturn: 1.5,
      totalReturn: 12.3,
      lastUpdate: new Date().toISOString()
    }
  ]);

  // Get status icon
  const getStatusIcon = (status: Strategy['status']) => {
    switch (status) {
      case 'running':
        return <CheckCircle2 size={16} className="status-icon status-running" />;
      case 'paused':
        return <AlertTriangle size={16} className="status-icon status-paused" />;
      case 'stopped':
        return <XCircle size={16} className="status-icon status-stopped" />;
      case 'error':
        return <AlertTriangle size={16} className="status-icon status-error" />;
      default:
        return <Minus size={16} className="status-icon status-unknown" />;
    }
  };

  // Get trend icon
  const getTrendIcon = (value: number) => {
    if (value > 0) return <TrendingUp size={14} className="trend-up" />;
    if (value < 0) return <TrendingDown size={14} className="trend-down" />;
    return <Minus size={14} className="trend-neutral" />;
  };

  // Get action menu items
  const getActionMenuItems = (strategy: Strategy): MenuProps['items'] => [
    {
      key: 'view',
      icon: <Eye size={14} />,
      label: '查看詳情',
      onClick: () => navigate(`/strategies/${strategy.id}`)
    },
    {
      key: 'edit',
      icon: <Edit size={14} />,
      label: '編輯策略',
      onClick: () => navigate(`/strategies/${strategy.id}/edit`)
    },
    {
      type: 'divider'
    },
    strategy.status === 'running'
      ? {
          key: 'pause',
          icon: <Pause size={14} />,
          label: '暫停策略',
          onClick: () => handleToggleStrategy(strategy.id, 'paused')
        }
      : {
          key: 'start',
          icon: <Play size={14} />,
          label: strategy.status === 'paused' ? '恢復策略' : '啟動策略',
          onClick: () => handleToggleStrategy(strategy.id, 'running')
        }
  ];

  // Handle strategy action
  const handleToggleStrategy = async (strategyId: string, newStatus: Strategy['status']) => {
    try {
      // API call to toggle strategy status
      // await strategiesApi.updateStrategyStatus(strategyId, newStatus);

      // Update local state
      setStrategies(prev =>
        prev.map(s =>
          s.id === strategyId ? { ...s, status: newStatus } : s
        )
      );
    } catch (error) {
      console.error('Failed to toggle strategy:', error);
    }
  };

  // Handle strategy click
  const handleStrategyClick = (strategyId: string) => {
    navigate(`/strategies/${strategyId}`);
  };

  return (
    <div className="strategy-list-container">
      <div className="strategy-list-header">
        <h3 className="strategy-list-title">策略狀態</h3>
        <div className="strategy-list-stats">
          <span className="stat-item">
            <span className="stat-dot stat-running"></span>
            運行中: {strategies.filter(s => s.status === 'running').length}
          </span>
          <span className="stat-item">
            <span className="stat-dot stat-paused"></span>
            已暫停: {strategies.filter(s => s.status === 'paused').length}
          </span>
          <span className="stat-item">
            <span className="stat-dot stat-stopped"></span>
            已停止: {strategies.filter(s => s.status === 'stopped').length}
          </span>
        </div>
      </div>

      <div className="strategy-list">
        {strategies.map((strategy, index) => (
          <motion.div
            key={strategy.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            className="strategy-list-item"
            onClick={() => handleStrategyClick(strategy.id)}
          >
            {/* Strategy Info */}
            <div className="strategy-info">
              <div className="strategy-status-icon">
                {getStatusIcon(strategy.status)}
              </div>
              <div className="strategy-details">
                <div className="strategy-name">{strategy.name}</div>
                <div className="strategy-meta">
                  總收益: <span className={strategy.totalReturn >= 0 ? 'text-green' : 'text-red'}>
                    {strategy.totalReturn >= 0 ? '+' : ''}{strategy.totalReturn.toFixed(2)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Daily Return */}
            <div className="strategy-return">
              <div className="return-value">
                {getTrendIcon(strategy.dailyReturn)}
                <span className={strategy.dailyReturn >= 0 ? 'text-green' : 'text-red'}>
                  {strategy.dailyReturn >= 0 ? '+' : ''}{strategy.dailyReturn.toFixed(2)}%
                </span>
              </div>
              <div className="return-label">今日</div>
            </div>

            {/* Actions */}
            <div className="strategy-actions" onClick={(e) => e.stopPropagation()}>
              <Dropdown menu={{ items: getActionMenuItems(strategy) }} trigger={['click']}>
                <Button type="text" icon={<Eye size={16} />}>
                  操作
                </Button>
              </Dropdown>
            </div>
          </motion.div>
        ))}
      </div>

      {/* View All Button */}
      <div className="strategy-list-footer">
        <Button
          type="link"
          icon={<Eye size={16} />}
          onClick={() => navigate('/strategies')}
        >
          查看全部策略
        </Button>
      </div>
    </div>
  );
};

export default StrategyList;
