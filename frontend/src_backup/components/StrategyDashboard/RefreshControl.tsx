import React, { useState, useCallback } from 'react';
import { getRealtimeManager } from '../../services/realtimeManager';
import { useLoading } from './LoadingManager';

interface RefreshControlProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'button' | 'icon';
  showText?: boolean;
  onRefresh?: () => Promise<void>;
}

export const RefreshControl: React.FC<RefreshControlProps> = ({
  className = '',
  size = 'md',
  variant = 'button',
  showText = true,
  onRefresh
}) => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  const { showLoading, hideLoading } = useLoading();
  const realtimeManager = getRealtimeManager();

  // Update last sync time from real-time manager
  React.useEffect(() => {
    const updateLastSyncTime = () => {
      const stats = realtimeManager.getStats();
      if (stats.lastSyncTime) {
        setLastSyncTime(stats.lastSyncTime);
      }
    };

    updateLastSyncTime();
    const interval = setInterval(updateLastSyncTime, 1000);

    return () => clearInterval(interval);
  }, [realtimeManager]);

  const handleRefresh = useCallback(async () => {
    if (isRefreshing) return;

    try {
      setIsRefreshing(true);
      showLoading('refetch');

      // Use custom refresh handler if provided, otherwise use real-time manager
      if (onRefresh) {
        await onRefresh();
      } else {
        await realtimeManager.triggerManualRefresh();
      }

      // Update last sync time
      const stats = realtimeManager.getStats();
      if (stats.lastSyncTime) {
        setLastSyncTime(stats.lastSyncTime);
      }

    } catch (error) {
      console.error('Refresh failed:', error);
      // Could show error notification here
    } finally {
      setIsRefreshing(false);
      hideLoading('refetch');
    }
  }, [isRefreshing, onRefresh, showLoading, hideLoading, realtimeManager]);

  const formatLastSyncTime = (date: Date): string => {
    const now = new Date();
    const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffSeconds < 60) {
      return `${diffSeconds}秒前`;
    } else if (diffSeconds < 3600) {
      return `${Math.floor(diffSeconds / 60)}分鐘前`;
    } else if (diffSeconds < 86400) {
      return `${Math.floor(diffSeconds / 3600)}小時前`;
    } else {
      return date.toLocaleDateString('zh-TW');
    }
  };

  const sizeClasses = {
    sm: variant === 'button' ? 'px-3 py-1.5 text-sm' : 'w-8 h-8',
    md: variant === 'button' ? 'px-4 py-2' : 'w-10 h-10',
    lg: variant === 'button' ? 'px-6 py-3 text-lg' : 'w-12 h-12'
  };

  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };

  if (variant === 'icon') {
    return (
      <button
        onClick={handleRefresh}
        disabled={isRefreshing}
        className={`relative flex items-center justify-center rounded-lg bg-white border border-gray-300 hover:border-blue-500 hover:bg-blue-50 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${sizeClasses[size]} ${className}`}
        title={lastSyncTime ? `最後更新: ${formatLastSyncTime(lastSyncTime)}` : '點擊重新整理'}
      >
        {isRefreshing ? (
          <div className={`${iconSizes[size]} border-2 border-blue-600 border-t-transparent rounded-full animate-spin`}></div>
        ) : (
          <svg
            className={`${iconSizes[size]} text-gray-600`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        )}
      </button>
    );
  }

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      <button
        onClick={handleRefresh}
        disabled={isRefreshing}
        className={`flex items-center justify-center space-x-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${sizeClasses[size]}`}
      >
        {isRefreshing ? (
          <div className={`${iconSizes[size]} border-2 border-white border-t-transparent rounded-full animate-spin`}></div>
        ) : (
          <svg
            className={`${iconSizes[size]}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        )}
        {showText && (
          <span>{isRefreshing ? '更新中...' : '重新整理'}</span>
        )}
      </button>

      {lastSyncTime && (
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>最後更新: {formatLastSyncTime(lastSyncTime)}</span>
        </div>
      )}
    </div>
  );
};

// Compact refresh button for mobile
export const CompactRefreshButton: React.FC<{
  onClick?: () => void;
  isRefreshing?: boolean;
  className?: string;
}> = ({ onClick, isRefreshing = false, className = '' }) => {
  return (
    <button
      onClick={onClick}
      disabled={isRefreshing}
      className={`p-2 rounded-full hover:bg-gray-100 transition-colors disabled:opacity-50 ${className}`}
      title="重新整理"
    >
      {isRefreshing ? (
        <div className="w-4 h-4 border-2 border-gray-600 border-t-transparent rounded-full animate-spin"></div>
      ) : (
        <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
      )}
    </button>
  );
};

// Auto-refresh toggle control
export const AutoRefreshToggle: React.FC<{
  interval?: number;
  onIntervalChange?: (interval: number) => void;
  className?: string;
}> = ({ interval = 10, onIntervalChange, className = '' }) => {
  const [isEnabled, setIsEnabled] = useState(true);
  const [currentInterval, setCurrentInterval] = useState(interval);
  const realtimeManager = getRealtimeManager();

  const handleToggle = () => {
    const newState = !isEnabled;
    setIsEnabled(newState);

    if (newState) {
      realtimeManager.resume();
    } else {
      realtimeManager.pause();
    }
  };

  const handleIntervalChange = (newInterval: number) => {
    setCurrentInterval(newInterval);
    onIntervalChange?.(newInterval);
  };

  const intervalOptions = [
    { label: '10秒', value: 10 },
    { label: '30秒', value: 30 },
    { label: '1分鐘', value: 60 },
    { label: '5分鐘', value: 300 }
  ];

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      <div className="flex items-center space-x-2">
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={isEnabled}
            onChange={handleToggle}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          <span className="ml-3 text-sm font-medium text-gray-700">自動更新</span>
        </label>
      </div>

      {isEnabled && (
        <select
          value={currentInterval}
          onChange={(e) => handleIntervalChange(Number(e.target.value))}
          className="text-sm border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
        >
          {intervalOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      )}
    </div>
  );
};

export default RefreshControl;