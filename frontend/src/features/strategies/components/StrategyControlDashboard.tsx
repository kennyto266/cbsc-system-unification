import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { toast } from 'react-toastify';
import { StrategyData, StrategyStatus, BatchOperation } from '../types';
import StrategyToggleEnhanced from './StrategyToggleEnhanced';
import BatchOperationsPanel from './BatchOperationsPanel';

// Component props
interface StrategyControlDashboardProps {
  strategies?: StrategyData[];
  onStrategyUpdate?: (strategies: StrategyData[]) => void;
  className?: string;
}

// Toast configuration
const toastConfig = {
  position: 'top-right' as const,
  autoClose: 3000,
  hideProgressBar: false,
  closeOnClick: true,
  pauseOnHover: true,
  draggable: true,
};

/**
 * Strategy Control Dashboard - Comprehensive strategy management interface
 */
const StrategyControlDashboard: React.FC<StrategyControlDashboardProps> = ({
  strategies: initialStrategies = [],
  onStrategyUpdate,
  className = '',
}) => {
  // State management
  const [strategies, setStrategies] = useState<StrategyData[]>(initialStrategies);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<StrategyStatus | 'all'>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedStrategies, setSelectedStrategies] = useState<Set<string>>(new Set());
  const [operationHistory, setOperationHistory] = useState<Array<{
    id: string;
    operation: string;
    strategyName: string;
    timestamp: Date;
    success: boolean;
  }>>([]);

  // Load strategies on mount
  useEffect(() => {
    loadStrategies();
  }, []);

  // Sync strategies when props change
  useEffect(() => {
    setStrategies(initialStrategies);
  }, [initialStrategies]);

  // Load strategies from API
  const loadStrategies = useCallback(async () => {
    setLoading(true);
    try {
      // TODO: Call API service - will be implemented with strategiesApi
      // For now, use mock data
      const mockData: StrategyData[] = [
        {
          id: '1',
          name: '动量策略',
          isActive: true,
          status: 'active',
          performance: { sharpeRatio: 1.5, maxDrawdown: 0.15, totalReturn: 0.25, winRate: 0.6 }
        },
        {
          id: '2',
          name: '均值回归策略',
          isActive: false,
          status: 'inactive',
          performance: { sharpeRatio: 1.2, maxDrawdown: 0.12, totalReturn: 0.18, winRate: 0.55 }
        },
        {
          id: '3',
          name: '突破策略',
          isActive: true,
          status: 'active',
          performance: { sharpeRatio: 1.8, maxDrawdown: 0.2, totalReturn: 0.35, winRate: 0.65 }
        }
      ];
      setStrategies(mockData);
      if (onStrategyUpdate) {
        onStrategyUpdate(mockData);
      }
    } catch (error) {
      console.error('Load strategies error:', error);
      toast.error('加载策略失败: 网络或服务器错误', toastConfig);
    } finally {
      setLoading(false);
    }
  }, [onStrategyUpdate]);

  // Handle strategy toggle
  const handleStrategyToggle = useCallback(async (
    strategyId: string,
    newActiveState: boolean
  ) => {
    // Find strategy
    const strategy = strategies.find(s => s.id === strategyId);
    if (!strategy) return;

    // Update local state immediately for better UX
    const updatedStrategies = strategies.map(s =>
      s.id === strategyId
        ? { ...s, isActive: newActiveState, status: newActiveState ? 'active' : 'inactive' as StrategyStatus }
        : s
    );
    setStrategies(updatedStrategies);

    // Add to operation history
    setOperationHistory(prev => [
      {
        id: Date.now().toString(),
        operation: newActiveState ? '启用' : '禁用',
        strategyName: strategy.name,
        timestamp: new Date(),
        success: true,
      },
      ...prev.slice(0, 49), // Keep only last 50 operations
    ]);

    // Notify parent
    if (onStrategyUpdate) {
      onStrategyUpdate(updatedStrategies);
    }
  }, [strategies, onStrategyUpdate]);

  // Handle batch control
  const handleBatchControl = useCallback((
    operation: string,
    strategyIds: string[]
  ) => {
    // Update local state
    const updatedStrategies = strategies.map(s => {
      if (strategyIds.includes(s.id)) {
        let newStatus: StrategyStatus = s.status;
        switch (operation) {
          case '启用':
            newStatus = 'active';
            s.isActive = true;
            break;
          case '禁用':
            newStatus = 'inactive';
            s.isActive = false;
            break;
          case '暂停':
            newStatus = 'paused';
            break;
          case '停止':
            newStatus = 'stopped';
            s.isActive = false;
            break;
        }
        return { ...s, status: newStatus };
      }
      return s;
    });

    setStrategies(updatedStrategies);
    setSelectedStrategies(new Set());

    // Add to operation history
    setOperationHistory(prev => [
      {
        id: Date.now().toString(),
        operation: `批量${operation}`,
        strategyName: `${strategyIds.length}个策略`,
        timestamp: new Date(),
        success: true,
      },
      ...prev.slice(0, 49),
    ]);

    // Notify parent
    if (onStrategyUpdate) {
      onStrategyUpdate(updatedStrategies);
    }
  }, [strategies, onStrategyUpdate]);

  // Filter and search strategies
  const filteredStrategies = useMemo(() => {
    return strategies.filter(strategy => {
      // Search filter
      if (searchTerm && !strategy.name.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }

      // Status filter
      if (filterStatus !== 'all' && strategy.status !== filterStatus) {
        return false;
      }

      return true;
    });
  }, [strategies, searchTerm, filterStatus]);

  // Status counts
  const statusCounts = useMemo(() => {
    const counts = {
      total: strategies.length,
      active: 0,
      inactive: 0,
      paused: 0,
      stopped: 0,
      error: 0,
    };

    strategies.forEach(strategy => {
      counts[strategy.status as keyof typeof counts]++;
    });

    return counts;
  }, [strategies]);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          策略控制中心
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          管理和控制您的交易策略
        </p>
      </div>

      {/* Status Summary */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 text-center">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {statusCounts.total}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">总数</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 text-center">
          <div className="text-2xl font-bold text-green-600">
            {statusCounts.active}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">运行中</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 text-center">
          <div className="text-2xl font-bold text-gray-600">
            {statusCounts.inactive}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">未激活</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 text-center">
          <div className="text-2xl font-bold text-yellow-600">
            {statusCounts.paused}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">已暂停</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 text-center">
          <div className="text-2xl font-bold text-red-600">
            {statusCounts.stopped}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">已停止</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 text-center">
          <div className="text-2xl font-bold text-red-700">
            {statusCounts.error}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">错误</div>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="搜索策略..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>

          {/* Status Filter */}
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-4 py-2 rounded-md transition-colors ${
                filterStatus === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              全部
            </button>
            <button
              onClick={() => setFilterStatus('active')}
              className={`px-4 py-2 rounded-md transition-colors ${
                filterStatus === 'active'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              运行中
            </button>
            <button
              onClick={() => setFilterStatus('inactive')}
              className={`px-4 py-2 rounded-md transition-colors ${
                filterStatus === 'inactive'
                  ? 'bg-gray-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              未激活
            </button>
            <button
              onClick={() => setFilterStatus('paused')}
              className={`px-4 py-2 rounded-md transition-colors ${
                filterStatus === 'paused'
                  ? 'bg-yellow-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              已暂停
            </button>
          </div>

          {/* View Mode Toggle */}
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-2 rounded-md transition-colors ${
                viewMode === 'grid'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              网格
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-2 rounded-md transition-colors ${
                viewMode === 'list'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              列表
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Strategy List */}
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              策略列表 ({filteredStrategies.length})
            </h2>

            {loading ? (
              <div className="flex items-center justify-center py-8">
                <svg className="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            ) : filteredStrategies.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                {searchTerm || filterStatus !== 'all'
                  ? '没有找到匹配的策略'
                  : '暂无策略'}
              </div>
            ) : (
              <div className={
                viewMode === 'grid'
                  ? 'grid md:grid-cols-2 gap-4'
                  : 'space-y-4'
              }>
                {filteredStrategies.map((strategy) => (
                  <div
                    key={strategy.id}
                    className={`border border-gray-200 dark:border-gray-700 rounded-lg p-4 ${
                      viewMode === 'list' ? 'flex items-center justify-between' : ''
                    }`}
                  >
                    {viewMode === 'grid' ? (
                      // Grid view
                      <div className="space-y-3">
                        <div>
                          <h3 className="font-medium text-gray-900 dark:text-white">
                            {strategy.name}
                          </h3>
                          <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            ID: {strategy.id}
                          </div>
                        </div>
                        <StrategyToggleEnhanced
                          strategyId={strategy.id}
                          strategyName={strategy.name}
                          isActive={strategy.isActive}
                          status={strategy.status}
                          onToggle={handleStrategyToggle}
                          size="small"
                          showLabels={false}
                        />
                        {strategy.performance && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 grid grid-cols-2 gap-2">
                            <div>SR: {strategy.performance.sharpeRatio.toFixed(2)}</div>
                            <div>MDD: {(strategy.performance.maxDrawdown * 100).toFixed(1)}%</div>
                            <div>收益: {(strategy.performance.totalReturn * 100).toFixed(1)}%</div>
                            <div>胜率: {(strategy.performance.winRate * 100).toFixed(1)}%</div>
                          </div>
                        )}
                      </div>
                    ) : (
                      // List view
                      <>
                        <div className="flex-1">
                          <h3 className="font-medium text-gray-900 dark:text-white">
                            {strategy.name}
                          </h3>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            ID: {strategy.id} | 状态: {strategy.status}
                          </div>
                        </div>
                        <StrategyToggleEnhanced
                          strategyId={strategy.id}
                          strategyName={strategy.name}
                          isActive={strategy.isActive}
                          status={strategy.status}
                          onToggle={handleStrategyToggle}
                          size="medium"
                          showLabels={true}
                        />
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="space-y-6">
          {/* Batch Operations */}
          <BatchOperationsPanel
            strategies={strategies}
            selectedStrategies={selectedStrategies}
            onSelectionChange={setSelectedStrategies}
            onBatchControl={handleBatchControl}
          />

          {/* Operation History */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              操作历史
            </h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {operationHistory.length === 0 ? (
                <div className="text-center text-gray-500 dark:text-gray-400 py-4">
                  暂无操作记录
                </div>
              ) : (
                operationHistory.map((op) => (
                  <div
                    key={op.id}
                    className="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-700 rounded"
                  >
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {op.operation}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {op.strategyName}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-xs ${op.success ? 'text-green-600' : 'text-red-600'}`}>
                        {op.success ? '成功' : '失败'}
                      </div>
                      <div className="text-xs text-gray-400">
                        {op.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategyControlDashboard;
