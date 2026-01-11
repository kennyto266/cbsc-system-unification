import React, { useState, useCallback, useRef } from 'react';
import { Switch } from '@headlessui/react';
import { toast } from 'react-toastify';
import { strategyControlAdapter } from '../../services/strategyControlAdapter';

// Strategy status types
export type StrategyStatus = 'active' | 'inactive' | 'paused' | 'stopped' | 'error';

// Strategy data interface
export interface StrategyData {
  id: string;
  name: string;
  isActive: boolean;
  status: StrategyStatus;
  lastUpdated?: string;
  performance?: {
    sharpeRatio: number;
    maxDrawdown: number;
    totalReturn: number;
    winRate: number;
  };
}

// Component props
interface StrategyToggleEnhancedProps {
  strategyId: string;
  strategyName: string;
  isActive: boolean;
  status: StrategyStatus;
  onToggle?: (strategyId: string, newActiveState: boolean) => void;
  size?: 'small' | 'medium' | 'large';
  showLabels?: boolean;
  disabled?: boolean;
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
 * Enhanced Strategy Toggle Component with debouncing and safety features
 */
const StrategyToggleEnhanced: React.FC<StrategyToggleEnhancedProps> = ({
  strategyId,
  strategyName,
  isActive,
  status,
  onToggle,
  size = 'medium',
  showLabels = true,
  disabled = false,
  className = '',
}) => {
  // State management
  const [enabled, setEnabled] = useState(isActive);
  const [loading, setLoading] = useState(false);
  const [lastToggleTime, setLastToggleTime] = useState<Date | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Size configurations
  const sizeClasses = {
    small: 'scale-75',
    medium: 'scale-100',
    large: 'scale-125',
  };

  // Status color mapping
  const getStatusColor = (status: StrategyStatus) => {
    switch (status) {
      case 'active':
        return 'bg-green-500';
      case 'inactive':
        return 'bg-gray-400';
      case 'paused':
        return 'bg-yellow-500';
      case 'stopped':
        return 'bg-red-500';
      case 'error':
        return 'bg-red-600';
      default:
        return 'bg-gray-400';
    }
  };

  // Debounced toggle handler
  const debouncedToggle = useCallback(
    async (newState: boolean) => {
      // Clear existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Set loading state
      setLoading(true);

      try {
        // Call API service
        const result = await strategyControlAdapter.toggleStrategy(strategyId, newState);

        if (result.success) {
          // Update local state
          setEnabled(newState);
          setLastToggleTime(new Date());

          // Show success toast
          toast.success(
            `策略 "${strategyName}" 已成功${newState ? '启用' : '禁用'}`,
            toastConfig
          );

          // Call parent callback
          if (onToggle) {
            onToggle(strategyId, newState);
          }
        } else {
          // Show error toast
          toast.error(
            `操作失败: ${result.error || '未知错误'}`,
            toastConfig
          );
          // Revert state on error
          setEnabled(!newState);
        }
      } catch (error) {
        // Handle unexpected errors
        console.error('Strategy toggle error:', error);
        toast.error(
          `操作失败: 网络或服务器错误`,
          toastConfig
        );
        // Revert state on error
        setEnabled(!newState);
      } finally {
        // Clear loading state after debounce delay
        timeoutRef.current = setTimeout(() => {
          setLoading(false);
        }, 500);
      }
    },
    [strategyId, strategyName, onToggle]
  );

  // Handle toggle change with confirmation
  const handleToggleChange = useCallback(async (newState: boolean) => {
    // Prevent multiple rapid toggles
    if (loading) {
      return;
    }

    // Show confirmation dialog for critical operations
    const isCriticalOperation = !newState && enabled; // Disabling an active strategy
    if (isCriticalOperation) {
      const confirmed = window.confirm(
        `确定要禁用策略 "${strategyName}" 吗？这将停止策略的所有运行和交易。`
      );

      if (!confirmed) {
        return;
      }
    }

    // Execute debounced toggle
    await debouncedToggle(newState);
  }, [enabled, loading, strategyName, debouncedToggle]);

  // Handle keyboard events
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleToggleChange(!enabled);
    }
  }, [enabled, handleToggleChange]);

  // Cleanup timeout on unmount
  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      {/* Status indicator */}
      <div
        className={`w-3 h-3 rounded-full ${getStatusColor(status)} ${
          loading ? 'animate-pulse' : ''
        }`}
        aria-hidden="true"
      />

      {/* Strategy name label */}
      {showLabels && (
        <label
          htmlFor={`strategy-toggle-${strategyId}`}
          className="text-sm font-medium text-gray-700 dark:text-gray-300 select-none"
        >
          {strategyName}
        </label>
      )}

      {/* Toggle switch */}
      <Switch
        id={`strategy-toggle-${strategyId}`}
        checked={enabled}
        onChange={handleToggleChange}
        disabled={disabled || loading}
        className={`
          ${sizeClasses[size]}
          relative inline-flex h-6 w-11 items-center rounded-full
          transition-colors duration-200 ease-in-out
          focus:outline-none focus:ring-2 focus:ring-offset-2
          ${enabled
            ? 'bg-blue-600 focus:ring-blue-500'
            : 'bg-gray-200 focus:ring-gray-500'
          }
          ${(disabled || loading) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
        onKeyDown={handleKeyDown}
        aria-label={`Toggle ${strategyName} strategy`}
        aria-describedby={`strategy-status-${strategyId}`}
      >
        <span className="sr-only">Toggle strategy</span>
        <span
          className={`
            inline-block h-4 w-4 transform rounded-full bg-white
            transition-transform duration-200 ease-in-out
            ${enabled ? 'translate-x-6' : 'translate-x-1'}
          `}
        />
      </Switch>

      {/* Status text */}
      {showLabels && (
        <span
          id={`strategy-status-${strategyId}`}
          className="text-xs text-gray-500 dark:text-gray-400"
          aria-live="polite"
        >
          {loading ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-1 h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              处理中...
            </span>
          ) : (
            enabled ? '已启用' : '已禁用'
          )}
        </span>
      )}

      {/* Last toggle time (for debugging) */}
      {process.env.NODE_ENV === 'development' && lastToggleTime && (
        <span className="text-xs text-gray-400 ml-2">
          {lastToggleTime.toLocaleTimeString()}
        </span>
      )}
    </div>
  );
};

export default StrategyToggleEnhanced;