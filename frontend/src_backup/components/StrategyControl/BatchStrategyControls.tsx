import React, { useState, useCallback } from 'react';
import { toast } from 'react-toastify';

interface Strategy {
  id: string;
  name: string;
  isActive: boolean;
  status: string;
}

interface BatchStrategyControlsProps {
  strategies: Strategy[];
  selectedStrategies: Set<string>;
  onSelectionChange: (selectedIds: Set<string>) => void;
  onBatchControl: (strategyIds: string[], action: 'enable' | 'disable' | 'start' | 'stop' | 'pause', reason?: string) => Promise<{
    success_count: number;
    failure_count: number;
    results: Array<{
      strategy_id: string;
      success: boolean;
      message: string;
    }>;
  }>;
  isLoading?: boolean;
}

export const BatchStrategyControls: React.FC<BatchStrategyControlsProps> = ({
  strategies,
  selectedStrategies,
  onSelectionChange,
  onBatchControl,
  isLoading = false
}) => {
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false);
  const [pendingAction, setPendingAction] = useState<'enable' | 'disable' | 'start' | 'stop' | 'pause' | null>(null);
  const [batchReason, setBatchReason] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  // 全选/取消全选
  const handleSelectAll = useCallback(() => {
    if (selectedStrategies.size === strategies.length) {
      // 全部取消选择
      onSelectionChange(new Set());
    } else {
      // 全部选择
      onSelectionChange(new Set(strategies.map(s => s.id)));
    }
  }, [strategies, selectedStrategies, onSelectionChange]);

  // 单个策略选择/取消选择
  const handleStrategySelect = useCallback((strategyId: string) => {
    const newSelected = new Set(selectedStrategies);
    if (newSelected.has(strategyId)) {
      newSelected.delete(strategyId);
    } else {
      newSelected.add(strategyId);
    }
    onSelectionChange(newSelected);
  }, [selectedStrategies, onSelectionChange]);

  // 批量操作处理
  const handleBatchAction = useCallback(async (action: 'enable' | 'disable' | 'start' | 'stop' | 'pause') => {
    if (selectedStrategies.size === 0) {
      toast.warning('请先选择要操作的策略', {
        position: 'top-right',
        autoClose: 3000,
      });
      return;
    }

    // 对于危险操作，显示确认对话框
    const dangerousActions = ['stop', 'disable'];
    if (dangerousActions.includes(action)) {
      setPendingAction(action);
      setIsConfirmDialogOpen(true);
      return;
    }

    // 直接执行安全操作
    executeBatchAction(action);
  }, [selectedStrategies]);

  // 执行批量操作
  const executeBatchAction = useCallback(async (action: 'enable' | 'disable' | 'start' | 'stop' | 'pause') => {
    setIsProcessing(true);
    try {
      const strategyIds = Array.from(selectedStrategies);
      const result = await onBatchControl(strategyIds, action, batchReason);

      if (result.success_count > 0) {
        const actionText = {
          enable: '启用',
          disable: '禁用',
          start: '启动',
          stop: '停止',
          pause: '暂停'
        }[action];

        toast.success(
          <div>
            <div className="font-semibold">批量操作完成</div>
            <div className="text-sm mt-1">
              成功: {result.success_count} 个，失败: {result.failure_count} 个
            </div>
          </div>,
          {
            position: 'top-right',
            autoClose: 5000,
          }
        );

        // 显示失败的策略
        if (result.failure_count > 0) {
          const failures = result.results.filter(r => !r.success);
          console.error('批量操作失败的策略:', failures);

          toast.error(
            <div>
              <div className="font-semibold">部分策略操作失败</div>
              <div className="text-sm mt-1 max-h-32 overflow-y-auto">
                {failures.map(f => (
                  <div key={f.strategy_id} className="text-xs">
                    {f.strategy_id}: {f.message}
                  </div>
                ))}
              </div>
            </div>,
            {
              position: 'top-right',
              autoClose: 10000,
            }
          );
        }
      } else {
        toast.error('批量操作全部失败，请重试', {
          position: 'top-right',
          autoClose: 3000,
        });
      }

      // 清空选择
      onSelectionChange(new Set());
      setBatchReason('');

    } catch (error) {
      console.error('批量操作失败:', error);
      toast.error(`批量操作失败: ${error instanceof Error ? error.message : '未知错误'}`, {
        position: 'top-right',
        autoClose: 5000,
      });
    } finally {
      setIsProcessing(false);
      setIsConfirmDialogOpen(false);
      setPendingAction(null);
    }
  }, [selectedStrategies, batchReason, onBatchControl, onSelectionChange]);

  // 获取操作按钮样式
  const getActionButtonClass = (action: 'enable' | 'disable' | 'start' | 'stop' | 'pause') => {
    const baseClass = 'px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed';
    const disabledClass = selectedStrategies.size === 0 || isProcessing || isLoading ? 'opacity-50 cursor-not-allowed' : '';

    switch (action) {
      case 'enable':
      case 'start':
        return `${baseClass} bg-green-600 text-white hover:bg-green-700 ${disabledClass}`;
      case 'disable':
        return `${baseClass} bg-gray-600 text-white hover:bg-gray-700 ${disabledClass}`;
      case 'stop':
        return `${baseClass} bg-red-600 text-white hover:bg-red-700 ${disabledClass}`;
      case 'pause':
        return `${baseClass} bg-yellow-600 text-white hover:bg-yellow-700 ${disabledClass}`;
      default:
        return baseClass;
    }
  };

  // 确认对话框
  const ConfirmDialog = () => {
    if (!isConfirmDialogOpen || !pendingAction) return null;

    const isStopAction = pendingAction === 'stop';
    const isDisableAction = pendingAction === 'disable';
    const title = isStopAction ? '确认批量停止' : isDisableAction ? '确认批量禁用' : '确认批量操作';
    const count = selectedStrategies.size;
    const message = isStopAction
      ? `您确定要停止选中的 ${count} 个策略吗？停止后这些策略将不再执行交易。`
      : isDisableAction
      ? `您确定要禁用选中的 ${count} 个策略吗？禁用后这些策略将暂停运行。`
      : `您确定要对选中的 ${count} 个策略执行"${pendingAction}"操作吗？`;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg max-w-lg w-full mx-4 p-6">
          <div className="flex items-center mb-4">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              isStopAction ? 'bg-red-100' : isDisableAction ? 'bg-yellow-100' : 'bg-blue-100'
            }`}>
              {isStopAction ? (
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10h6v4H9z" />
                </svg>
              ) : isDisableAction ? (
                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                </svg>
              ) : (
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
            </div>
            <h3 className="ml-3 text-lg font-semibold text-gray-900">{title}</h3>
          </div>

          <p className="text-gray-600 mb-6">{message}</p>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              操作原因（可选）
            </label>
            <textarea
              value={batchReason}
              onChange={(e) => setBatchReason(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
              placeholder="请输入批量操作的原因..."
            />
          </div>

          {/* 选中策略列表 */}
          <div className="mb-6">
            <div className="text-sm text-gray-600 mb-2">选中的策略 ({count} 个):</div>
            <div className="max-h-32 overflow-y-auto border border-gray-200 rounded-md p-2">
              {strategies
                .filter(s => selectedStrategies.has(s.id))
                .map(strategy => (
                  <div key={strategy.id} className="text-xs text-gray-700 py-1">
                    • {strategy.name}
                  </div>
                ))}
            </div>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              onClick={() => {
                setIsConfirmDialogOpen(false);
                setPendingAction(null);
              }}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              disabled={isProcessing}
            >
              取消
            </button>
            <button
              onClick={() => executeBatchAction(pendingAction!)}
              className={`px-4 py-2 text-white rounded-lg transition-colors ${
                isStopAction
                  ? 'bg-red-600 hover:bg-red-700'
                  : isDisableAction
                  ? 'bg-yellow-600 hover:bg-yellow-700'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
              disabled={isProcessing}
            >
              {isProcessing ? '处理中...' : `确认${isStopAction ? '停止' : isDisableAction ? '禁用' : '执行'}`}
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
      {/* Selection Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
        <div className="flex items-center space-x-4">
          {/* Select All Checkbox */}
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={selectedStrategies.size === strategies.length && strategies.length > 0}
              onChange={handleSelectAll}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              disabled={isLoading}
            />
            <span className="ml-2 text-sm text-gray-700">
              全选 ({selectedStrategies.size}/{strategies.length})
            </span>
          </label>
        </div>

        {/* Batch Action Buttons */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => handleBatchAction('enable')}
            disabled={selectedStrategies.size === 0 || isProcessing || isLoading}
            className={getActionButtonClass('enable')}
          >
            <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            批量启用
          </button>

          <button
            onClick={() => handleBatchAction('disable')}
            disabled={selectedStrategies.size === 0 || isProcessing || isLoading}
            className={getActionButtonClass('disable')}
          >
            <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
            批量禁用
          </button>

          <button
            onClick={() => handleBatchAction('pause')}
            disabled={selectedStrategies.size === 0 || isProcessing || isLoading}
            className={getActionButtonClass('pause')}
          >
            <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6" />
            </svg>
            批量暂停
          </button>

          <button
            onClick={() => handleBatchAction('stop')}
            disabled={selectedStrategies.size === 0 || isProcessing || isLoading}
            className={getActionButtonClass('stop')}
          >
            <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10h6v4H9z" />
            </svg>
            批量停止
          </button>
        </div>
      </div>

      {/* Selected Strategies Info */}
      {selectedStrategies.size > 0 && (
        <div className="text-sm text-gray-600">
          已选择 {selectedStrategies.size} 个策略进行批量操作
        </div>
      )}

      {/* Processing Indicator */}
      {isProcessing && (
        <div className="mt-4 flex items-center text-sm text-blue-600">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
          正在执行批量操作，请稍候...
        </div>
      )}

      {/* Confirm Dialog */}
      <ConfirmDialog />
    </div>
  );
};

export default BatchStrategyControls;