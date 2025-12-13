import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';

interface StrategyToggleEnhancedProps {
  strategyId: string;
  strategyName: string;
  isActive: boolean;
  status: string;
  onToggle: (strategyId: string, action: 'enable' | 'disable' | 'start' | 'stop' | 'pause') => Promise<boolean>;
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  showLabels?: boolean;
  className?: string;
}

// Enhanced strategy toggle with better UX and accessibility
export const StrategyToggleEnhanced: React.FC<StrategyToggleEnhancedProps> = ({
  strategyId,
  strategyName,
  isActive,
  status,
  onToggle,
  size = 'medium',
  disabled = false,
  showLabels = true,
  className = ''
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false);
  const [pendingAction, setPendingAction] = useState<'enable' | 'disable' | 'start' | 'stop' | 'pause' | null>(null);
  const [lastToggleTime, setLastToggleTime] = useState<Date | null>(null);

  // Get size classes for the toggle switch
  const getSizeClasses = () => {
    switch (size) {
      case 'small':
        return {
          switch: 'w-8 h-4',
          thumb: 'w-3 h-3',
          translate: 'translate-x-4'
        };
      case 'large':
        return {
          switch: 'w-16 h-8',
          thumb: 'w-7 h-7',
          translate: 'translate-x-8'
        };
      default: // medium
        return {
          switch: 'w-12 h-6',
          thumb: 'w-5 h-5',
          translate: 'translate-x-6'
        };
    }
  };

  const sizeClasses = getSizeClasses();

  // Handle toggle with debouncing
  const handleToggle = useCallback(async (action: 'enable' | 'disable' | 'start' | 'stop' | 'pause') => {
    // Prevent rapid successive toggles
    if (lastToggleTime && (new Date().getTime() - lastToggleTime.getTime()) < 1000) {
      toast.warning('請稍候再試，操作間隔需大於1秒', {
        position: 'top-right',
        autoClose: 2000,
      });
      return;
    }

    // For dangerous operations, show confirmation dialog
    const dangerousActions = ['stop', 'disable'];
    if (dangerousActions.includes(action)) {
      setPendingAction(action);
      setIsConfirmDialogOpen(true);
      return;
    }

    // Execute safe operations directly
    executeAction(action);
  }, [lastToggleTime]);

  // Execute the action
  const executeAction = useCallback(async (action: 'enable' | 'disable' | 'start' | 'stop' | 'pause', reason?: string) => {
    setIsLoading(true);
    setLastToggleTime(new Date());

    try {
      const success = await onToggle(strategyId, action);

      if (success) {
        const actionText = {
          enable: '啟用',
          disable: '禁用',
          start: '啟動',
          stop: '停止',
          pause: '暫停'
        }[action];

        // Show success toast with custom styling
        toast.success(
          <div className="flex items-center">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
            <div>
              <div className="font-semibold">操作成功</div>
              <div className="text-sm">策略 "{strategyName}" 已成功{actionText}</div>
            </div>
          </div>,
          {
            position: 'top-right',
            autoClose: 3000,
            icon: false,
            style: {
              background: '#10B981',
              color: 'white'
            }
          }
        );

        // Log operation for debugging
        console.log(`策略 ${strategyId} ${actionText}成功`, {
          timestamp: new Date().toISOString(),
          reason: reason || '用戶操作'
        });
      } else {
        toast.error(
          <div className="flex items-center">
            <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
            <div>
              <div className="font-semibold">操作失敗</div>
              <div className="text-sm">請檢查網絡連接或稍後重試</div>
            </div>
          </div>,
          {
            position: 'top-right',
            autoClose: 5000,
            icon: false
          }
        );
      }
    } catch (error) {
      console.error('策略控制失敗:', error);

      // Show detailed error toast
      toast.error(
        <div className="flex items-center">
          <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
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
      setIsLoading(false);
      setIsConfirmDialogOpen(false);
      setPendingAction(null);
    }
  }, [strategyId, strategyName, onToggle]);

  // Enhanced confirmation dialog
  const ConfirmDialog = () => {
    if (!isConfirmDialogOpen || !pendingAction) return null;

    const isStopAction = pendingAction === 'stop';
    const isDisableAction = pendingAction === 'disable';
    const title = isStopAction ? '確認停止策略' : isDisableAction ? '確認禁用策略' : '確認操作';
    const message = isStopAction
      ? `您確定要停止策略 "${strategyName}" 嗎？停止後策略將不再執行交易。`
      : isDisableAction
      ? `您確定要禁用策略 "${strategyName}" 嗎？禁用後策略將暫停運行。`
      : `您確定要對策略 "${strategyName}" 執行 "${pendingAction}" 操作嗎？`;
    const confirmText = isStopAction ? '停止' : isDisableAction ? '禁用' : '確認';

    return (
      <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 backdrop-blur-sm">
        <div className="bg-white rounded-xl shadow-2xl max-w-md w-full mx-4 p-6 transform transition-all">
          {/* Icon and Title */}
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
            <h3 className="ml-3 text-lg font-semibold text-gray-900">{title}</h3>
          </div>

          {/* Message */}
          <p className="text-gray-600 mb-6 leading-relaxed">{message}</p>

          {/* Reason Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              操作原因（可選）
            </label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={3}
              placeholder="請輸入操作原因（可選）..."
              onChange={(e) => {
                (e.target as HTMLTextAreaElement).dataset.reason = e.target.value;
              }}
            />
          </div>

          {/* Warning Message */}
          {(isStopAction || isDisableAction) && (
            <div className="mb-6 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center">
                <svg className="w-4 h-4 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <span className="text-sm text-yellow-700">
                  {isStopAction ? '停止策略後，當前持倉將被平倉' : '禁用策略不會影響當前持倉'}
                </span>
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
              disabled={isLoading}
            >
              取消
            </button>
            <button
              onClick={() => {
                const textarea = document.querySelector('textarea[data-reason]') as HTMLTextAreaElement;
                const reason = textarea?.value?.trim() || undefined;
                executeAction(pendingAction!, reason);
              }}
              className={`px-4 py-2 text-white rounded-lg transition-colors font-medium ${
                isStopAction
                  ? 'bg-red-600 hover:bg-red-700'
                  : isDisableAction
                  ? 'bg-yellow-600 hover:bg-yellow-700'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  處理中...
                </div>
              ) : (
                confirmText
              )}
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Determine action based on current state
  const getAction = () => {
    if (isActive || status === 'active') {
      return 'disable';
    }
    return 'enable';
  };

  const action = getAction();

  return (
    <>
      <div className={`flex items-center space-x-2 ${className}`}>
        {/* Enhanced Toggle Switch */}
        <button
          onClick={() => handleToggle(action)}
          disabled={disabled || isLoading}
          className={`
            relative inline-flex items-center rounded-full transition-all duration-200 ease-in-out
            focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
            ${sizeClasses.switch}
            ${isActive || status === 'active'
              ? 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 shadow-green-200'
              : 'bg-gradient-to-r from-gray-300 to-gray-400 hover:from-gray-400 hover:to-gray-500'
            }
            ${(disabled || isLoading) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            shadow-lg
          `}
          aria-label={`切換策略 ${strategyName} 狀態`}
          role="switch"
          aria-checked={isActive || status === 'active'}
        >
          <span
            className={`
              inline-block transform transition-transform duration-200 ease-in-out
              rounded-full bg-white shadow-lg
              ${sizeClasses.thumb}
              ${isActive || status === 'active' ? sizeClasses.translate : 'translate-x-0.5'}
            `}
          />

          {/* Loading indicator inside toggle */}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="animate-spin rounded-full h-3 w-3 border-b border-white opacity-75"></div>
            </div>
          )}
        </button>

        {/* Enhanced Status Labels */}
        {showLabels && (
          <div className="flex flex-col">
            <span className={`text-sm font-medium ${
              isActive || status === 'active' ? 'text-green-600' : 'text-gray-500'
            }`}>
              {isLoading ? '處理中...' : (isActive || status === 'active' ? '運行中' : '已停止')}
            </span>
            {lastToggleTime && (
              <span className="text-xs text-gray-400">
                最後更新: {lastToggleTime.toLocaleTimeString()}
              </span>
            )}
          </div>
        )}

        {/* External Loading Spinner */}
        {isLoading && (
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />
        )}
      </div>

      {/* Enhanced Confirm Dialog */}
      <ConfirmDialog />
    </>
  );
};

export default StrategyToggleEnhanced;