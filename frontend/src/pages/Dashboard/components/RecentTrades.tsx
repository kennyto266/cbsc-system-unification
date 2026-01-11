import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trade } from '../../../types/dashboard';
import Card from '../../../components/ui/Card';
import Badge from '../../../components/ui/Badge';
import { formatCurrency } from '../../../utils/formatters';

interface RecentTradesProps {
  trades: Trade[];
  maxItems?: number;
}

interface TradeItemProps {
  trade: Trade;
  delay: number;
}

const TradeItem: React.FC<TradeItemProps> = ({ trade, delay }) => {
  const isBuy = trade.side === 'buy';
  const isProfit = trade.profit > 0;

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}天前`;
    if (hours > 0) return `${hours}小时前`;
    if (minutes > 0) return `${minutes}分钟前`;
    return '刚刚';
  };

  const statusConfig = {
    filled: { label: '已成交', color: 'green' as const },
    pending: { label: '待成交', color: 'yellow' as const },
    cancelled: { label: '已取消', color: 'gray' as const },
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      transition={{ duration: 0.3, delay }}
      className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg transition-colors"
    >
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <Badge
            color={isBuy ? 'green' : 'red'}
            className="text-xs font-semibold"
          >
            {isBuy ? '买入' : '卖出'}
          </Badge>
          <span className="font-medium text-gray-900">{trade.symbol}</span>
          <span className="text-xs text-gray-500">
            {trade.quantity}股 @ {formatCurrency(trade.price)}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>{trade.strategyName}</span>
          <span>·</span>
          <span>{formatTime(trade.timestamp)}</span>
        </div>
      </div>
      <div className="text-right">
        <div className="text-sm font-medium text-gray-900 mb-1">
          {formatCurrency(trade.amount)}
        </div>
        {trade.status === 'filled' && (
          <div className={`text-sm font-medium ${
            isProfit ? 'text-green-600' : 'text-red-600'
          }`}>
            {isProfit ? '+' : ''}{formatCurrency(trade.profit)}
          </div>
        )}
        {trade.status !== 'filled' && (
          <Badge
            color={statusConfig[trade.status].color}
            className="text-xs"
          >
            {statusConfig[trade.status].label}
          </Badge>
        )}
      </div>
    </motion.div>
  );
};

export const RecentTrades: React.FC<RecentTradesProps> = ({
  trades,
  maxItems = 10,
}) => {
  const [filter, setFilter] = useState<'all' | 'filled' | 'pending'>('all');
  const [sortBy, setSortBy] = useState<'time' | 'amount' | 'profit'>('time');

  // Filter trades
  const filteredTrades = useMemo(() => {
    let filtered = trades;

    if (filter !== 'all') {
      filtered = filtered.filter(trade => trade.status === filter);
    }

    // Sort trades
    filtered = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'time':
          return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
        case 'amount':
          return b.amount - a.amount;
        case 'profit':
          return b.profit - a.profit;
        default:
          return 0;
      }
    });

    return filtered.slice(0, maxItems);
  }, [trades, filter, sortBy, maxItems]);

  // Calculate statistics
  const stats = useMemo(() => {
    const filledTrades = filteredTrades.filter(t => t.status === 'filled');
    const totalProfit = filledTrades.reduce((sum, t) => sum + t.profit, 0);
    const profitTrades = filledTrades.filter(t => t.profit > 0).length;
    const winRate = filledTrades.length > 0 ? (profitTrades / filledTrades.length) * 100 : 0;

    return {
      totalProfit,
      winRate: winRate.toFixed(1),
      tradeCount: filledTrades.length,
    };
  }, [filteredTrades]);

  return (
    <Card title={`最新交易 (${filteredTrades.length})`} className="h-full flex flex-col">
      {/* Controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as any)}
            className="text-sm px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">全部</option>
            <option value="filled">已成交</option>
            <option value="pending">待成交</option>
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="text-sm px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="time">按时间</option>
            <option value="amount">按金额</option>
            <option value="profit">按盈亏</option>
          </select>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-3 gap-2 mb-4 p-3 bg-gray-50 rounded-lg">
        <div className="text-center">
          <p className="text-xs text-gray-500">总盈亏</p>
          <p className={`text-sm font-semibold ${
            stats.totalProfit >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {stats.totalProfit >= 0 ? '+' : ''}{formatCurrency(stats.totalProfit)}
          </p>
        </div>
        <div className="text-center border-l border-r border-gray-200">
          <p className="text-xs text-gray-500">胜率</p>
          <p className="text-sm font-semibold text-gray-900">{stats.winRate}%</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">交易数</p>
          <p className="text-sm font-semibold text-gray-900">{stats.tradeCount}</p>
        </div>
      </div>

      {/* Trade List */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence mode="popLayout">
          {filteredTrades.map((trade, index) => (
            <TradeItem
              key={`${trade.id}-${trade.timestamp}`}
              trade={trade}
              delay={index * 0.05}
            />
          ))}
        </AnimatePresence>

        {/* Empty State */}
        {filteredTrades.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-gray-500">
            <svg
              className="h-12 w-12 text-gray-300 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
              />
            </svg>
            <p className="text-sm">暂无交易记录</p>
          </div>
        )}
      </div>

      {/* View More Link */}
      {trades.length > maxItems && (
        <div className="mt-4 pt-3 border-t border-gray-200">
          <button className="w-full text-center text-sm text-blue-600 hover:text-blue-700 font-medium">
            查看全部交易记录 →
          </button>
        </div>
      )}
    </Card>
  );
};