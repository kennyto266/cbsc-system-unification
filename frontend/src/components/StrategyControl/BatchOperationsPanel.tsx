import React, { useState, useCallback, useMemo } from 'react';
import { toast } from 'react-toastify';

interface Strategy {
  id: string;
  name: string;
  isActive: boolean;
  status: string;
  category?: string;
  lastUpdated?: string;
}

interface BatchOperationsPanelProps {
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

// Enhanced batch operations panel with advanced features
export const BatchOperationsPanel: React.FC<BatchOperationsPanelProps> = ({
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
  const [selectAllMode, setSelectAllMode] = useState<'all' | 'none' | 'active' | 'inactive'>('none');

  // Filtered strategies for selection
  const filteredStrategies = useMemo(() => {
    if (selectAllMode === 'none') return [];
    if (selectAllMode === 'all') return strategies;
    if (selectAllMode === 'active') return strategies.filter(s => s.isActive || s.status === 'active');
    if (selectAllMode === 'inactive') return strategies.filter(s => !s.isActive && s.status !== 'active');
    return [];
  }, [strategies, selectAllMode]);

  // Enhanced selection handlers
  const handleSelectByMode = useCallback(() => {
    const newSelected = new Set(filteredStrategies.map(s => s.id));
    onSelectionChange(newSelected);
    setSelectAllMode('none'); // Reset after selection
  }, [filteredStrategies, onSelectionChange]);

  const handleSelectAll = useCallback(() => {
    if (selectedStrategies.size === strategies.length) {
      // Clear all selection
      onSelectionChange(new Set());
    } else {
      // Select all strategies
      onSelectionChange(new Set(strategies.map(s => s.id)));
    }
  }, [strategies, selectedStrategies, onSelectionChange]);

  const handleStrategySelect = useCallback((strategyId: string) => {
    const newSelected = new Set(selectedStrategies);
    if (newSelected.has(strategyId)) {
      newSelected.delete(strategyId);
    } else {
      newSelected.add(strategyId);
    }
    onSelectionChange(newSelected);
  }, [selectedStrategies, onSelectionChange]);

  // Quick action handlers
  const handleQuickAction = useCallback(async (action: 'enable' | 'disable' | 'start' | 'stop' | 'pause') => {
    // Quick actions work on selected strategies or all strategies of certain type
    let targetStrategies = Array.from(selectedStrategies);

    if (targetStrategies.length === 0) {
      // If no strategies selected, perform action on all inactive strategies for enable, or all active for disable
      if (action === 'enable' || action === 'start') {
        targetStrategies = strategies
          .filter(s => !s.isActive && s.status !== 'active')
          .map(s => s.id);
      } else if (action === 'disable' || action === 'stop') {
        targetStrategies = strategies
          .filter(s => s.isActive || s.status === 'active')
          .map(s => s.id);
      }
    }

    if (targetStrategies.length === 0) {
      toast.warning('沒有符合條件的策略可以操作', {
        position: 'top-right',
        autoClose: 3000,
      });
      return;
    }

    // For dangerous operations, show confirmation dialog
    const dangerousActions = ['stop', 'disable'];
    if (dangerousActions.includes(action)) {
      setPendingAction(action);
      setIsConfirmDialogOpen(true);
      // Auto-set the target strategies for confirmation dialog
      onSelectionChange(new Set(targetStrategies));
      return;
    }

    // Execute safe operations directly
    executeBatchAction(action, targetStrategies);
  }, [selectedStrategies, strategies, onSelectionChange]);

  // Execute batch action with enhanced feedback
  const executeBatchAction = useCallback(async (action: 'enable' | 'disable' | 'start' | 'stop' | 'pause', strategyIds?: string[]) => {
    const targetIds = strategyIds || Array.from(selectedStrategies);
    setIsProcessing(true);

    try {
      const result = await onBatchControl(targetIds, action, batchReason);

      // Show comprehensive success feedback
      if (result.success_count > 0) {
        const actionText = {
          enable: '啟用',
          disable: '禁用',
          start: '啟動',
          stop: '停止',
          pause: '暫停'
        }[action];

        // Success toast with detailed information
        toast.success(
          <div className="max-w-sm">
            <div className="flex items-center mb-2">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
              <div className="font-semibold">批量操作完成</div>
            </div>
            <div className="text-sm space-y-1">
              <div>✅ 成功: {result.success_count} 個策略</div>
              {result.failure_count > 0 && (
                <div className="text-yellow-600">⚠️ 失敗: {result.failure_count} 個策略</div>
              )}
              <div className="text-xs text-gray-500 mt-1">
                操作: {actionText} {batchReason && `(${batchReason})`}
              </div>
            </div>
          </div>,
          {
            position: 'top-right',
            autoClose: 5000,
            icon: false,
            style: {
              background: result.failure_count > 0 ? '#F59E0B' : '#10B981',
              color: 'white'
            }
          }
        );

        // Show detailed failure information
        if (result.failure_count > 0) {
          const failures = result.results.filter(r => !r.success);

          // Detailed failure toast
          setTimeout(() => {
            toast.error(
              <div className="max-w-md">
                <div className="font-semibold mb-2">部分策略操作失敗詳情:</div>
                <div className="text-xs space-y-1 max-h-32 overflow-y-auto">
                  {failures.map(failure => (
                    <div key={failure.strategy_id} className="flex items-start">
                      <span className="mr-2">•</span>
                      <div>
                        <span className="font-medium">{failure.strategy_id}:</span>
                        <span className="ml-1">{failure.message}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>,
              {
                position: 'top-right',
                autoClose: 10000,
                icon: false
              }
            );
          }, 1000);
        }
      } else {
        // All operations failed
        toast.error(
          <div className="flex items-center">
            <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
            <div>
              <div className="font-semibold">批量操作全部失敗</div>
              <div className="text-sm">請檢查網絡連接或聯繫系統管理員</div>
            </div>
          </div>,
          {
            position: 'top-right',
            autoClose: 5000,
            icon: false
          }
        );
      }

      // Clear selection and reason after successful operation
      onSelectionChange(new Set());
      setBatchReason('');
      setSelectAllMode('none');

    } catch (error) {
      console.error('批量操作失敗:', error);
      toast.error(
        <div className="flex items-center">
          <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
          <div>
            <div className="font-semibold">系統錯誤</div>
            <div className="text-sm">
              {error instanceof Error ? error.message : '未知錯誤'}
            </div>
          </div>
        </div>,
        {
          position: 'top-right',
          autoClose: 5000,
          icon: false
        }
      );
    } finally {
      setIsProcessing(false);
      setIsConfirmDialogOpen(false);
      setPendingAction(null);
    }
  }, [selectedStrategies, batchReason, onBatchControl, onSelectionChange]);

  // Enhanced confirmation dialog
  const ConfirmDialog = () => {
    if (!isConfirmDialogOpen || !pendingAction) return null;

    const isStopAction = pendingAction === 'stop';
    const isDisableAction = pendingAction === 'disable';
    const title = isStopAction ? '確認批量停止' : isDisableAction ? '確認批量禁用' : '確認批量操作';
    const count = selectedStrategies.size;
    const message = isStopAction
      ? `您確定要停止選中的 ${count} 個策略嗎？停止後這些策略將不再執行交易並平倉持倉。`
      : isDisableAction
      ? `您確定要禁用選中的 ${count} 個策略嗎？禁用後這些策略將暫停運行但不影響持倉。`
      : `您確定要對選中的 ${count} 個策略執行"${pendingAction}"操作嗎？`;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 backdrop-blur-sm">
        <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full mx-4 p-6 transform transition-all">
          {/* Header */}
          <div className="flex items-center mb-4">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              isStopAction ? 'bg-red-100' : isDisableAction ? 'bg-yellow-100' : 'bg-blue-100'
            }`}>
              {isStopAction ? (
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10h6v4H9z" />
                </svg>
              ) : isDisableAction ? (
                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636" />
                </svg>
              ) : (
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
            </div>
            <h3 className="ml-3 text-xl font-semibold text-gray-900">{title}</h3>
          </div>

          {/* Message */}
          <p className="text-gray-600 mb-6 leading-relaxed">{message}</p>

          {/* Strategy List */}
          <div className="mb-6">
            <div className="text-sm font-medium text-gray-700 mb-2">將要操作的策略 ({count} 個):</div>
            <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-lg p-3 bg-gray-50">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {strategies
                  .filter(s => selectedStrategies.has(s.id))
                  .map(strategy => (
                    <div key={strategy.id} className="flex items-center text-xs text-gray-700">
                      <div className={`w-2 h-2 rounded-full mr-2 ${
                        strategy.isActive || strategy.status === 'active' ? 'bg-green-500' : 'bg-gray-400'
                      }`}></div>
                      <div>
                        <div className="font-medium">{strategy.name}</div>
                        <div className="text-gray-500">
                          {strategy.category && `${strategy.category} • `}
                          {strategy.status}
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>

          {/* Reason Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              操作原因（可選）
            </label>
            <textarea
              value={batchReason}
              onChange={(e) => setBatchReason(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={3}
              placeholder="請輸入批量操作的原因（可選）..."
            />
          </div>

          {/* Warning Message */}
          {(isStopAction || isDisableAction) && (
            <div className={`mb-6 p-4 rounded-lg border ${
              isStopAction
                ? 'bg-red-50 border-red-200'
                : 'bg-yellow-50 border-yellow-200'
            }`}>
              <div className="flex items-start">
                <svg className={`w-5 h-5 mr-2 mt-0.5 ${
                  isStopAction ? 'text-red-600' : 'text-yellow-600'
                }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <div className="text-sm">
                  <div className={`font-medium mb-1 ${
                    isStopAction ? 'text-red-700' : 'text-yellow-700'
                  }`}>
                    重要提醒
                  </div>
                  <div className={isStopAction ? 'text-red-600' : 'text-yellow-600'}>
                    {isStopAction
                      ? '停止策略後，系統將自動平倉所有持倉，可能產生損失。'
                      : '禁用策略不會影響當前持倉，但會停止新的交易信號。'
                    }
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => {
                setIsConfirmDialogOpen(false);
                setPendingAction(null);
              }}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors font-medium"
              disabled={isProcessing}
            >
              取消
            </button>
            <button
              onClick={() => executeBatchAction(pendingAction!)}
              className={`px-6 py-2 text-white rounded-lg transition-colors font-medium ${
                isStopAction
                  ? 'bg-red-600 hover:bg-red-700'
                  : isDisableAction
                  ? 'bg-yellow-600 hover:bg-yellow-700'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  處理中...
                </div>
              ) : (
                `確認${isStopAction ? '停止' : isDisableAction ? '禁用' : '執行'}`
              )}
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Quick action button classes
  const getQuickActionButtonClass = (action: 'enable' | 'disable' | 'start' | 'stop' | 'pause') => {
    const baseClass = 'px-3 py-1.5 rounded-lg font-medium text-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center';

    switch (action) {
      case 'enable':
      case 'start':
        return `${baseClass} bg-green-50 text-green-700 hover:bg-green-100 border border-green-200`;
      case 'disable':
        return `${baseClass} bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200`;
      case 'stop':
        return `${baseClass} bg-red-50 text-red-700 hover:bg-red-100 border border-red-200`;
      case 'pause':
        return `${baseClass} bg-yellow-50 text-yellow-700 hover:bg-yellow-100 border border-yellow-200`;
      default:
        return baseClass;
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
      {/* Selection Controls */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-6">
        <div className="flex items-center space-x-4">
          {/* Selection Summary */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">已選擇:</span>
            <span className="font-semibold text-blue-600">{selectedStrategies.size}</span>
            <span className="text-sm text-gray-600">/ {strategies.length}</span>
          </div>

          {/* Quick Selection Buttons */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleSelectAll}
              className="px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors font-medium"
              disabled={isLoading}
            >
              {selectedStrategies.size === strategies.length ? '取消全選' : '全選'}
            </button>
          </div>

          {/* Advanced Selection */}
          <div className="flex items-center space-x-2">
            <select
              value={selectAllMode}
              onChange={(e) => setSelectAllMode(e.target.value as any)}
              className="text-sm border border-gray-300 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            >
              <option value="none">快速選擇</option>
              <option value="active">僅選擇運行中</option>
              <option value="inactive">僅選擇已停止</option>
            </select>
            {selectAllMode !== 'none' && (
              <button
                onClick={handleSelectByMode}
                className="text-sm bg-green-50 text-green-700 px-2 py-1 rounded-lg hover:bg-green-100 transition-colors"
              >
                套用
              </button>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => handleQuickAction('enable')}
            disabled={isProcessing || isLoading}
            className={getQuickActionButtonClass('enable')}
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            全部啟用
          </button>

          <button
            onClick={() => handleQuickAction('disable')}
            disabled={isProcessing || isLoading}
            className={getQuickActionButtonClass('disable')}
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
            全部禁用
          </button>

          <button
            onClick={() => handleQuickAction('pause')}
            disabled={isProcessing || isLoading}
            className={getQuickActionButtonClass('pause')}
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6" />
            </svg>
            全部暫停
          </button>

          <button
            onClick={() => handleQuickAction('stop')}
            disabled={isProcessing || isLoading}
            className={getQuickActionButtonClass('stop')}
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10h6v4H9z" />
            </svg>
            緊急停止
          </button>
        </div>
      </div>

      {/* Selected Strategies Info */}
      {selectedStrategies.size > 0 && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="text-sm text-blue-700">
              已選擇 {selectedStrategies.size} 個策略進行批量操作
            </div>
            <button
              onClick={() => {
                onSelectionChange(new Set());
                setSelectAllMode('none');
              }}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              清除選擇
            </button>
          </div>
        </div>
      )}

      {/* Processing Indicator */}
      {isProcessing && (
        <div className="mt-4 flex items-center justify-center p-4 bg-blue-50 rounded-lg">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-3"></div>
          <span className="text-blue-700 font-medium">正在執行批量操作，請稍候...</span>
        </div>
      )}

      {/* Enhanced Confirm Dialog */}
      <ConfirmDialog />
    </div>
  );
};

export default BatchOperationsPanel;