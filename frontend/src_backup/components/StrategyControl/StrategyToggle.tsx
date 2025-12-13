import React, { useState, useCallback } from 'react';
import { toast } from 'react-toastify';

interface StrategyToggleProps {
  strategyId: string;
  strategyName: string;
  isActive: boolean;
  status: string;
  onToggle: (strategyId: string, action: 'enable' | 'disable' | 'start' | 'stop' | 'pause') => Promise<boolean>;
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  showLabels?: boolean;
}

export const StrategyToggle: React.FC<StrategyToggleProps> = ({
  strategyId,
  strategyName,
  isActive,
  status,
  onToggle,
  size = 'medium',
  disabled = false,
  showLabels = true
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false);
  const [pendingAction, setPendingAction] = useState<'enable' | 'disable' | 'start' | 'stop' | 'pause' | null>(null);

  // 获取开关组件的尺寸样式
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

  // 处理开关切换
  const handleToggle = useCallback(async (action: 'enable' | 'disable' | 'start' | 'stop' | 'pause') => {
    // 对于危险操作，显示确认对话框
    const dangerousActions = ['stop', 'disable'];
    if (dangerousActions.includes(action)) {
      setPendingAction(action);
      setIsConfirmDialogOpen(true);
      return;
    }

    // 直接执行安全操作
    executeAction(action);
  }, []);

  // 执行操作
  const executeAction = useCallback(async (action: 'enable' | 'disable' | 'start' | 'stop' | 'pause', reason?: string) => {
    setIsLoading(true);
    try {
      const success = await onToggle(strategyId, action);
      if (success) {
        const actionText = {
          enable: '启用',
          disable: '禁用',
          start: '启动',
          stop: '停止',
          pause: '暂停'
        }[action];

        toast.success(`策略 "${strategyName}" 已成功${actionText}`, {
          position: 'top-right',
          autoClose: 3000,
        });
      } else {
        toast.error(`操作失败，请重试`, {
          position: 'top-right',
          autoClose: 3000,
        });
      }
    } catch (error) {
      console.error('策略控制失败:', error);
      toast.error(`操作失败: ${error instanceof Error ? error.message : '未知错误'}`, {
        position: 'top-right',
        autoClose: 5000,
      });
    } finally {
      setIsLoading(false);
      setIsConfirmDialogOpen(false);
      setPendingAction(null);
    }
  }, [strategyId, strategyName, onToggle]);

  // 确认对话框
  const ConfirmDialog = () => {
    if (!isConfirmDialogOpen || !pendingAction) return null;

    const isStopAction = pendingAction === 'stop';
    const title = isStopAction ? '确认停止策略' : '确认禁用策略';
    const message = isStopAction
      ? `您确定要停止策略 "${strategyName}" 吗？停止后策略将不再执行交易。`
      : `您确定要禁用策略 "${strategyName}" 吗？禁用后策略将暂停运行。`;
    const confirmText = isStopAction ? '停止' : '禁用';

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg max-w-md w-full mx-4 p-6">
          <div className="flex items-center mb-4">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              isStopAction ? 'bg-red-100' : 'bg-yellow-100'
            }`}>
              {isStopAction ? (
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10h6v4H9z" />
                </svg>
              ) : (
                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z" />
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
              placeholder="请输入操作原因..."
              onChange={(e) => {
                // 存储原因以便在确认时使用
                (e.target as HTMLTextAreaElement).dataset.reason = e.target.value;
              }}
            />
          </div>

          <div className="flex justify-end space-x-3">
            <button
              onClick={() => {
                setIsConfirmDialogOpen(false);
                setPendingAction(null);
              }}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              disabled={isLoading}
            >
              取消
            </button>
            <button
              onClick={() => {
                const textarea = document.querySelector('textarea[data-reason]') as HTMLTextAreaElement;
                const reason = textarea?.value;
                executeAction(pendingAction!, reason);
              }}
              className={`px-4 py-2 text-white rounded-lg transition-colors ${
                isStopAction
                  ? 'bg-red-600 hover:bg-red-700'
                  : 'bg-yellow-600 hover:bg-yellow-700'
              }`}
              disabled={isLoading}
            >
              {isLoading ? '处理中...' : confirmText}
            </button>
          </div>
        </div>
      </div>
    );
  };

  // 根据状态确定应显示的操作
  const getAction = () => {
    if (isActive || status === 'active') {
      return 'disable';
    }
    return 'enable';
  };

  const action = getAction();

  return (
    <>
      <div className="flex items-center space-x-2">
        {/* Toggle Switch */}
        <button
          onClick={() => handleToggle(action)}
          disabled={disabled || isLoading}
          className={`
            relative inline-flex items-center rounded-full transition-colors duration-200 ease-in-out
            focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
            ${sizeClasses.switch}
            ${isActive || status === 'active'
              ? 'bg-green-600 hover:bg-green-700'
              : 'bg-gray-300 hover:bg-gray-400'
            }
            ${(disabled || isLoading) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
          aria-label={`切换策略 ${strategyName} 状态`}
        >
          <span
            className={`
              inline-block transform transition-transform duration-200 ease-in-out
              rounded-full bg-white shadow-lg
              ${sizeClasses.thumb}
              ${isActive || status === 'active' ? sizeClasses.translate : 'translate-x-0.5'}
            `}
          />
        </button>

        {/* Status Labels */}
        {showLabels && (
          <span className={`text-sm font-medium ${
            isActive || status === 'active' ? 'text-green-600' : 'text-gray-500'
          }`}>
            {isLoading ? '处理中...' : (isActive || status === 'active' ? '运行中' : '已停止')}
          </span>
        )}

        {/* Loading Spinner */}
        {isLoading && (
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />
        )}
      </div>

      {/* Confirm Dialog */}
      <ConfirmDialog />
    </>
  );
};

export default StrategyToggle;