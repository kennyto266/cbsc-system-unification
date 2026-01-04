/**
 * Metrics Cards Component
 * Displays 8 key performance metrics as cards
 */

import React from 'react';
import { motion } from 'framer-motion';
import { useSelector } from 'react-redux';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Shield,
  Zap,
  AlertCircle,
  CheckCircle2,
  DollarSign
} from 'lucide-react';
import { selectDashboardStats, selectSystemHealth } from '../../../store/slices/dashboardSlice';
import './MetricsCards.css';

// Metric card interface
interface MetricCard {
  id: string;
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  color: string;
  gradient: string;
}

/**
 * MetricsCards Component
 */
export const MetricsCards: React.FC = () => {
  const stats = useSelector(selectDashboardStats);
  const health = useSelector(selectSystemHealth);

  // Format number as percentage
  const formatPercent = (value: number, decimals: number = 2): string => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
  };

  // Format number with commas
  const formatNumber = (value: number): string => {
    return new Intl.NumberFormat('zh-HK').format(value);
  };

  // Get trend icon
  const getTrendIcon = (change: number) => {
    if (change > 0) return <TrendingUp size={16} className="text-green-400" />;
    if (change < 0) return <TrendingDown size={16} className="text-red-400" />;
    return <Activity size={16} className="text-gray-400" />;
  };

  // Build metric cards from data
  const getMetricCards = (): MetricCard[] => {
    if (!stats || !health) {
      // Return placeholder cards when no data
      return Array(8).fill(null).map((_, i) => ({
        id: `metric-${i}`,
        title: '加載中...',
        value: '--',
        icon: <Activity size={24} />,
        color: '#6b7280',
        gradient: 'from-gray-500 to-gray-600'
      }));
    }

    return [
      {
        id: 'total-return',
        title: '總收益率',
        value: formatPercent(stats.totalReturn || 0),
        change: stats.dailyReturn || 0,
        icon: <DollarSign size={24} />,
        color: '#10b981',
        gradient: 'from-green-500 to-emerald-600'
      },
      {
        id: 'win-rate',
        title: '勝率',
        value: formatPercent(stats.winRate || 0),
        icon: <CheckCircle2 size={24} />,
        color: '#3b82f6',
        gradient: 'from-blue-500 to-cyan-600'
      },
      {
        id: 'max-drawdown',
        title: '最大回撤',
        value: formatPercent(stats.maxDrawdown || 0),
        icon: <TrendingDown size={24} />,
        color: '#ef4444',
        gradient: 'from-red-500 to-rose-600'
      },
      {
        id: 'sharpe-ratio',
        title: '夏普比率',
        value: (stats.sharpeRatio || 0).toFixed(2),
        icon: <Activity size={24} />,
        color: '#8b5cf6',
        gradient: 'from-purple-500 to-violet-600'
      },
      {
        id: 'active-strategies',
        title: '運行中策略',
        value: `${stats.activeStrategies || 0} / ${stats.totalStrategies || 0}`,
        icon: <Zap size={24} />,
        color: '#f59e0b',
        gradient: 'from-amber-500 to-orange-600'
      },
      {
        id: 'daily-pnl',
        title: '今日盈虧',
        value: formatPercent(stats.dailyReturn || 0),
        change: stats.dailyReturn || 0,
        icon: <DollarSign size={24} />,
        color: stats.dailyReturn >= 0 ? '#10b981' : '#ef4444',
        gradient: stats.dailyReturn >= 0 ? 'from-green-500 to-emerald-600' : 'from-red-500 to-rose-600'
      },
      {
        id: 'risk-level',
        title: '風險等級',
        value: '中等',
        icon: <Shield size={24} />,
        color: health?.status === 'healthy' ? '#10b981' : health?.status === 'warning' ? '#f59e0b' : '#ef4444',
        gradient: health?.status === 'healthy' ? 'from-green-500 to-emerald-600' : health?.status === 'warning' ? 'from-amber-500 to-orange-600' : 'from-red-500 to-rose-600'
      },
      {
        id: 'system-health',
        title: '系統健康度',
        value: health?.status === 'healthy' ? '良好' : health?.status === 'warning' ? '注意' : '異常',
        icon: health?.status === 'healthy' ? <CheckCircle2 size={24} /> : <AlertCircle size={24} />,
        color: health?.status === 'healthy' ? '#10b981' : health?.status === 'warning' ? '#f59e0b' : '#ef4444',
        gradient: health?.status === 'healthy' ? 'from-green-500 to-emerald-600' : health?.status === 'warning' ? 'from-amber-500 to-orange-600' : 'from-red-500 to-rose-600'
      }
    ];
  };

  const cards = getMetricCards();

  return (
    <div className="metrics-cards-container">
      <div className="metrics-cards-grid">
        {cards.map((card, index) => (
          <motion.div
            key={card.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            className="metric-card"
            style={{
              background: `linear-gradient(135deg, var(--${card.color}-light), var(--${card.color}-dark))`,
              '--color-light': card.gradient.includes('green') ? '#10b981' :
                             card.gradient.includes('blue') ? '#3b82f6' :
                             card.gradient.includes('red') ? '#ef4444' :
                             card.gradient.includes('purple') ? '#8b5cf6' :
                             card.gradient.includes('amber') ? '#f59e0b' : '#6b7280',
              '--color-dark': card.gradient.includes('green') ? '#059669' :
                            card.gradient.includes('blue') ? '#2563eb' :
                            card.gradient.includes('red') ? '#dc2626' :
                            card.gradient.includes('purple') ? '#7c3aed' :
                            card.gradient.includes('amber') ? '#d97706' : '#4b5563'
            } as React.CSSProperties}
          >
            {/* Card Header */}
            <div className="metric-card-header">
              <div className="metric-card-icon" style={{ color: card.color }}>
                {card.icon}
              </div>
              {card.change !== undefined && (
                <div className="metric-card-change">
                  {getTrendIcon(card.change)}
                  <span className={card.change >= 0 ? 'text-green-400' : 'text-red-400'}>
                    {formatPercent(Math.abs(card.change))}
                  </span>
                </div>
              )}
            </div>

            {/* Card Value */}
            <div className="metric-card-value">
              {card.value}
            </div>

            {/* Card Title */}
            <div className="metric-card-title">
              {card.title}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default MetricsCards;
