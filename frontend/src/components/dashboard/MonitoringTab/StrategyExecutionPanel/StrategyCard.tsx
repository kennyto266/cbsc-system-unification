/**
 * StrategyCard Component
 * Displays single strategy execution status in a card
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Card, Tag } from 'antd';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  TrendingUp,
  TrendingDown,
  Activity,
  MoreVertical
} from 'lucide-react';
import { StrategyExecution } from '../../../../store/slices/monitoringSlice';
import './StrategyCard.css';

interface StrategyCardProps {
  strategy: StrategyExecution;
  onDragStart?: () => void;
}

export const StrategyCard: React.FC<StrategyCardProps> = ({ strategy, onDragStart }) => {
  const getStatusIcon = () => {
    switch (strategy.status) {
      case 'running':
        return <CheckCircle2 size={16} className="status-running" />;
      case 'paused':
        return <AlertTriangle size={16} className="status-paused" />;
      case 'stopped':
      case 'error':
        return <XCircle size={16} className="status-stopped" />;
    }
  };

  const getStatusText = () => {
    switch (strategy.status) {
      case 'running': return '運行中';
      case 'paused': return '已暫停';
      case 'stopped': return '已停止';
      case 'error': return '異常';
    }
  };

  const getStatusColor = () => {
    switch (strategy.status) {
      case 'running': return 'success';
      case 'paused': return 'warning';
      case 'stopped': return 'default';
      case 'error': return 'error';
    }
  };

  const isPositive = strategy.dailyPnl >= 0;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.2 }}
      className="strategy-card"
      draggable
      onDragStart={onDragStart}
    >
      <Card
        size="small"
        className={`strategy-card-inner ${strategy.status}`}
        hoverable
      >
        {/* Card Header */}
        <div className="strategy-card-header">
          <div className="strategy-card-title">
            <h3>{strategy.name}</h3>
            <Tag icon={getStatusIcon()} color={getStatusColor()}>
              {getStatusText()}
            </Tag>
          </div>
          <button className="strategy-card-menu">
            <MoreVertical size={16} />
          </button>
        </div>

        {/* P&L Display */}
        <div className="strategy-card-pnl">
          <div className={`pnl-value ${isPositive ? 'positive' : 'negative'}`}>
            {isPositive ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
            <span className="pnl-amount">
              {strategy.dailyPnl > 0 ? '+' : ''}
              {strategy.dailyPnl.toLocaleString()}
            </span>
            <span className="pnl-percent">
              ({strategy.dailyPnlPercent > 0 ? '+' : ''}
              {strategy.dailyPnlPercent}%)
            </span>
          </div>
        </div>

        {/* Metrics */}
        <div className="strategy-card-metrics">
          <div className="metric-item">
            <span className="metric-label">持倉</span>
            <span className="metric-value">{strategy.positions}</span>
          </div>

          {strategy.lastSignal && (
            <div className="metric-item">
              <span className="metric-label">最後信號</span>
              <Tag color={strategy.lastSignal.type === 'buy' ? 'green' : strategy.lastSignal.type === 'sell' ? 'red' : 'default'}>
                {strategy.lastSignal.type === 'buy' ? '買入' : strategy.lastSignal.type === 'sell' ? '賣出' : '持有'}
              </Tag>
            </div>
          )}
        </div>

        {/* Activity indicator */}
        {strategy.activity.length > 0 && (
          <div className="strategy-card-activity">
            <Activity size={14} />
            <span>{strategy.activity.length} 條新活動</span>
          </div>
        )}
      </Card>
    </motion.div>
  );
};

export default StrategyCard;
