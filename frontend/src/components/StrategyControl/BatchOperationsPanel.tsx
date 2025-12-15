import React, { useState, useCallback, useMemo } from 'react';
import { toast } from 'react-toastify';
import { strategyControlAdapter } from '../../services/strategyControlAdapter';
import { StrategyData, StrategyStatus } from './StrategyToggleEnhanced';

// Batch operation types
export type BatchOperation = 'enable' | 'disable' | 'pause' | 'stop';

// Component props
interface BatchOperationsPanelProps {
  strategies: StrategyData[];
  selectedStrategies: Set<string>;
  onSelectionChange: (selectedIds: Set<string>) => void;
  onBatchControl?: (operation: BatchOperation, strategyIds: string[]) => void;
  className?: string;
}

// Toast configuration
const toastConfig = {
  position: 'top-right' as const,
  autoClose: 5000,
  hideProgressBar: false,
  closeOnClick: true,
  pauseOnHover: true,
  draggable: true,
};

/**
 * Batch Operations Panel for managing multiple strategies
 */
const BatchOperationsPanel: React.FC<BatchOperationsPanelProps> = ({
  strategies,
  selectedStrategies,
  onSelectionChange,
  onBatchControl,
  className = '',
}) => {
  const [loading, setLoading] = useState(false);
  const [operationInProgress, setOperationInProgress] = useState<BatchOperation | null>(null);

  // Strategy statistics
  const statistics = useMemo(() => {
    const total = strategies.length;
    const active = strategies.filter(s => s.status === 'active').length;
    const inactive = strategies.filter(s => s.status === 'inactive').length;
    const paused = strategies.filter(s => s.status === 'paused').length;
    const stopped = strategies.filter(s => s.status === 'stopped').length;
    const error = strategies.filter(s => s.status === 'error').length;

    return { total, active, inactive, paused, stopped, error };
  }, [strategies]);

  // Handle selection change
  const handleSelectionChange = useCallback((strategyId: string, selected: boolean) => {
    const newSelection = new Set(selectedStrategies);
    if (selected) {
      newSelection.add(strategyId);
    } else {
      newSelection.delete(strategyId);
    }
    onSelectionChange(newSelection);
  }, [selectedStrategies, onSelectionChange]);

  // Select all strategies
  const handleSelectAll = useCallback(() => {
    if (selectedStrategies.size === strategies.length) {
      onSelectionChange(new Set());
    } else {
      onSelectionChange(new Set(strategies.map(s => s.id)));
    }
  }, [selectedStrategies, strategies, onSelectionChange]);

  // Select by status
  const handleSelectByStatus = useCallback((status: StrategyStatus) => {
    const strategiesByStatus = strategies
      .filter(s => s.status === status)
      .map(s => s.id);
    onSelectionChange(new Set(strategiesByStatus));
  }, [strategies, onSelectionChange]);

  // Execute batch operation
  const executeBatchOperation = useCallback(async (
    operation: BatchOperation,
    strategyIds: string[]
  ) => {
    setLoading(true);
    setOperationInProgress(operation);

    try {
      // Call API service for batch control
      const result = await strategyControlAdapter.batchControlStrategies(
        strategyIds,
        operation
      );

      if (result.success) {
        // Show success toast with details
        const successCount = result.results?.filter(r => r.success).length || 0;
        const totalCount = strategyIds.length;

        toast.success(
          <div>
            <div className="font-semibold">
              批量{getOperationName(operation)}操作完成
            </div>
            <div className="text-sm mt-1">
              成功: {successCount}/{totalCount} 个策略
            </div>
          </div>,
          toastConfig
        );

        // Call parent callback
        if (onBatchControl) {
          onBatchControl(operation, strategyIds);
        }
      } else {
        // Show error toast
        toast.error(
          `批量操作失败: ${result.error || '未知错误'}`,
          toastConfig
        );
      }
    } catch (error) {
      console.error('Batch operation error:', error);
      toast.error(
        `批量操作失败: 网络或服务器错误`,
        toastConfig
      );
    } finally {
      setLoading(false);
      setOperationInProgress(null);
    }
  }, [onBatchControl]);

  // Get operation display name
  const getOperationName = (operation: BatchOperation): string => {
    switch (operation) {
      case 'enable':
        return '启用';
      case 'disable':
        return '禁用';
      case 'pause':
        return '暂停';
      case 'stop':
        return '停止';
      default:
        return '操作';
    }
  };

  // Get operation confirmation message
  const getOperationConfirmation = (
    operation: BatchOperation,
    count: number
  ): string => {
    const operationName = getOperationName(operation);
    return `确定要${operationName}选中的 ${count} 个策略吗？\n\n此操作无法撤销。`;
  };

  // Handle batch operation with confirmation
  const handleBatchOperation = useCallback(async (operation: BatchOperation) => {
    if (selectedStrategies.size === 0) {
      toast.warning('请先选择要操作的策略', toastConfig);
      return;
    }

    const strategyIds = Array.from(selectedStrategies);
    const confirmed = window.confirm(
      getOperationConfirmation(operation, strategyIds.length)
    );

    if (!confirmed) {
      return;
    }

    await executeBatchOperation(operation, strategyIds);
  }, [selectedStrategies, executeBatchOperation]);

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          批量操作
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          选择多个策略进行批量操作
        </p>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {statistics.total}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">总数</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {statistics.active}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">运行中</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-600">
            {statistics.inactive}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">未激活</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-yellow-600">
            {statistics.paused}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">已暂停</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">
            {statistics.stopped}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">已停止</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-700">
            {statistics.error}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">错误</div>
        </div>
      </div>

      {/* Selection controls */}
      <div className="mb-6 space-y-3">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleSelectAll}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
              selectedStrategies.size === strategies.length
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            {selectedStrategies.size === strategies.length ? '取消全选' : '全选'}
          </button>
          <button
            onClick={() => handleSelectByStatus('active')}
            className="px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200 dark:bg-green-900 dark:text-green-300 dark:hover:bg-green-800 transition-colors"
          >
            选择运行中
          </button>
          <button
            onClick={() => handleSelectByStatus('inactive')}
            className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            选择未激活
          </button>
          <button
            onClick={() => handleSelectByStatus('paused')}
            className="px-3 py-1.5 text-sm bg-yellow-100 text-yellow-700 rounded-md hover:bg-yellow-200 dark:bg-yellow-900 dark:text-yellow-300 dark:hover:bg-yellow-800 transition-colors"
          >
            选择已暂停
          </button>
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          已选择 {selectedStrategies.size} 个策略
        </div>
      </div>

      {/* Strategy selection list */}
      <div className="mb-6 max-h-48 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-md">
        {strategies.length === 0 ? (
          <div className="p-4 text-center text-gray-500 dark:text-gray-400">
            暂无策略
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {strategies.map((strategy) => (
              <div
                key={strategy.id}
                className="flex items-center p-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <input
                  type="checkbox"
                  checked={selectedStrategies.has(strategy.id)}
                  onChange={(e) => handleSelectionChange(strategy.id, e.target.checked)}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  id={`batch-select-${strategy.id}`}
                />
                <label
                  htmlFor={`batch-select-${strategy.id}`}
                  className="ml-3 flex-1 cursor-pointer"
                >
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {strategy.name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    状态: {getOperationName(strategy.status as BatchOperation)}
                  </div>
                </label>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Batch operation buttons */}
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => handleBatchOperation('enable')}
          disabled={loading || selectedStrategies.size === 0}
          className="flex-1 sm:flex-none px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading && operationInProgress === 'enable' ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              启用中...
            </span>
          ) : (
            '批量启用'
          )}
        </button>
        <button
          onClick={() => handleBatchOperation('disable')}
          disabled={loading || selectedStrategies.size === 0}
          className="flex-1 sm:flex-none px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading && operationInProgress === 'disable' ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              禁用中...
            </span>
          ) : (
            '批量禁用'
          )}
        </button>
        <button
          onClick={() => handleBatchOperation('pause')}
          disabled={loading || selectedStrategies.size === 0}
          className="flex-1 sm:flex-none px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading && operationInProgress === 'pause' ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              暂停中...
            </span>
          ) : (
            '批量暂停'
          )}
        </button>
        <button
          onClick={() => handleBatchOperation('stop')}
          disabled={loading || selectedStrategies.size === 0}
          className="flex-1 sm:flex-none px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading && operationInProgress === 'stop' ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              停止中...
            </span>
          ) : (
            '批量停止'
          )}
        </button>
      </div>
    </div>
  );
};

export default BatchOperationsPanel;