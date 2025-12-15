import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Strategy } from '../../../types/dashboard';
import Card from '../../../components/ui/Card';
import Button from '../../../components/ui/Button';
import Badge from '../../../components/ui/Badge';
import { formatPercentage, formatCurrency } from '../../../utils/formatters';

interface StrategyListProps {
  strategies: Strategy[];
  selectedStrategies: string[];
  onStrategySelect: (strategyId: string, selected: boolean) => void;
  onBatchStart: () => void;
  onBatchStop: () => void;
}

type SortField = 'return' | 'dailyReturn' | 'sharpeRatio' | 'winRate' | 'maxDrawdown';
type SortOrder = 'asc' | 'desc';
type FilterStatus = 'all' | 'running' | 'stopped' | 'paused' | 'error';

export const StrategyList: React.FC<StrategyListProps> = ({
  strategies,
  selectedStrategies,
  onStrategySelect,
  onBatchStart,
  onBatchStop,
}) => {
  const [sortField, setSortField] = useState<SortField>('return');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Status configuration
  const statusConfig = {
    running: {
      label: '运行中',
      color: 'green' as const,
      icon: '⚡',
    },
    stopped: {
      label: '已停止',
      color: 'gray' as const,
      icon: '⏹️',
    },
    paused: {
      label: '已暂停',
      color: 'yellow' as const,
      icon: '⏸️',
    },
    error: {
      label: '错误',
      color: 'red' as const,
      icon: '❌',
    },
  };

  // Filter and sort strategies
  const filteredStrategies = useMemo(() => {
    let filtered = strategies;

    // Apply status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(s => s.status === filterStatus);
    }

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(s =>
        s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.instruments.some(inst => inst.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Apply sorting
    filtered = [...filtered].sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      const modifier = sortOrder === 'asc' ? 1 : -1;
      return (aValue - bValue) * modifier;
    });

    return filtered;
  }, [strategies, filterStatus, searchTerm, sortField, sortOrder]);

  // Handle sort change
  const handleSortChange = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  // Handle strategy action
  const handleStrategyAction = async (strategyId: string, action: 'start' | 'stop' | 'pause') => {
    // TODO: Implement API call
    console.log(`${action} strategy ${strategyId}`);
  };

  return (
    <Card className="h-full flex flex-col" title={`策略列表 (${filteredStrategies.length})`}>
      {/* Filters and Controls */}
      <div className="space-y-4 mb-4">
        {/* Search */}
        <div className="relative">
          <input
            type="text"
            placeholder="搜索策略名称、类型或交易品种..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <svg
            className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        {/* Status Filter */}
        <div className="flex flex-wrap gap-2">
          {Object.entries({ all: '全部', ...statusConfig }).map(([key, config]) => (
            <button
              key={key}
              onClick={() => setFilterStatus(key as FilterStatus)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                filterStatus === key
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {key === 'all' ? config : `${config.icon} ${config.label}`}
            </button>
          ))}
        </div>

        {/* Batch Actions */}
        {selectedStrategies.length > 0 && (
          <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
            <span className="text-sm text-blue-700">
              已选择 {selectedStrategies.length} 个策略
            </span>
            <div className="flex gap-2">
              <Button size="sm" onClick={onBatchStart}>
                批量启动
              </Button>
              <Button size="sm" variant="secondary" onClick={onBatchStop}>
                批量停止
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Table Header */}
      <div className="grid grid-cols-12 gap-2 px-2 py-2 text-xs font-medium text-gray-500 border-b border-gray-200">
        <div className="col-span-1">
          <input
            type="checkbox"
            checked={selectedStrategies.length === filteredStrategies.length && filteredStrategies.length > 0}
            onChange={(e) => {
              if (e.target.checked) {
                filteredStrategies.forEach(s => onStrategySelect(s.id, true));
              } else {
                selectedStrategies.forEach(id => onStrategySelect(id, false));
              }
            }}
            className="rounded border-gray-300"
          />
        </div>
        <div
          className="col-span-3 cursor-pointer hover:text-gray-700"
          onClick={() => handleSortChange('return' as SortField)}
        >
          策略 {sortField === 'return' && (sortOrder === 'asc' ? '↑' : '↓')}
        </div>
        <div
          className="col-span-2 cursor-pointer hover:text-gray-700"
          onClick={() => handleSortChange('dailyReturn' as SortField)}
        >
          日收益 {sortField === 'dailyReturn' && (sortOrder === 'asc' ? '↑' : '↓')}
        </div>
        <div className="col-span-2">状态</div>
        <div
          className="col-span-1 cursor-pointer hover:text-gray-700 text-right"
          onClick={() => handleSortChange('sharpeRatio' as SortField)}
        >
          夏普 {sortField === 'sharpeRatio' && (sortOrder === 'asc' ? '↑' : '↓')}
        </div>
        <div
          className="col-span-1 cursor-pointer hover:text-gray-700 text-right"
          onClick={() => handleSortChange('maxDrawdown' as SortField)}
        >
          回撤 {sortField === 'maxDrawdown' && (sortOrder === 'asc' ? '↑' : '↓')}
        </div>
        <div className="col-span-1 text-center">操作</div>
      </div>

      {/* Strategy List */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence>
          {filteredStrategies.map((strategy, index) => (
            <motion.div
              key={strategy.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              className="grid grid-cols-12 gap-2 px-2 py-3 items-center hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
            >
              {/* Checkbox */}
              <div className="col-span-1">
                <input
                  type="checkbox"
                  checked={selectedStrategies.includes(strategy.id)}
                  onChange={(e) => onStrategySelect(strategy.id, e.target.checked)}
                  className="rounded border-gray-300"
                />
              </div>

              {/* Strategy Info */}
              <div className="col-span-3">
                <div className="font-medium text-gray-900 truncate">
                  {strategy.name}
                </div>
                <div className="text-xs text-gray-500 truncate">
                  {strategy.type} · {strategy.instruments.slice(0, 3).join(', ')}
                  {strategy.instruments.length > 3 && '...'}
                </div>
              </div>

              {/* Daily Return */}
              <div className="col-span-2">
                <div className={`font-medium ${
                  strategy.dailyReturn >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {strategy.dailyReturn >= 0 ? '+' : ''}{formatPercentage(strategy.dailyReturn)}
                </div>
                <div className="text-xs text-gray-500">
                  总收益: {formatPercentage(strategy.return)}
                </div>
              </div>

              {/* Status */}
              <div className="col-span-2">
                <Badge
                  color={statusConfig[strategy.status].color}
                  className="text-xs"
                >
                  {statusConfig[strategy.status].icon} {statusConfig[strategy.status].label}
                </Badge>
              </div>

              {/* Sharpe Ratio */}
              <div className="col-span-1 text-right text-sm">
                {strategy.sharpeRatio.toFixed(2)}
              </div>

              {/* Max Drawdown */}
              <div className="col-span-1 text-right text-sm text-red-600">
                {formatPercentage(strategy.maxDrawdown)}
              </div>

              {/* Actions */}
              <div className="col-span-1 flex justify-center gap-1">
                {strategy.status === 'running' ? (
                  <Button
                    size="xs"
                    variant="secondary"
                    onClick={() => handleStrategyAction(strategy.id, 'stop')}
                  >
                    停止
                  </Button>
                ) : (
                  <Button
                    size="xs"
                    onClick={() => handleStrategyAction(strategy.id, 'start')}
                  >
                    启动
                  </Button>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Empty State */}
        {filteredStrategies.length === 0 && (
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
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            <p className="text-sm">没有找到匹配的策略</p>
          </div>
        )}
      </div>
    </Card>
  );
};