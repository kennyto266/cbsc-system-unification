import React, { useState, useEffect } from 'react';
import { getRealtimeManager } from '../../services/realtimeManager';

interface RealTimeMonitorProps {
  connectionStatus?: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastUpdate?: Date;
  className?: string;
  showDetails?: boolean;
  compact?: boolean;
}

interface MonitorStats {
  updateCount: number;
  errorCount: number;
  lastSyncTime: Date | null;
  networkStatus: {
    isOnline: boolean;
    connectionType: string;
    effectiveType: string;
  };
  isActive: boolean;
  isPaused: boolean;
}

export const RealTimeMonitor: React.FC<RealTimeMonitorProps> = ({
  connectionStatus,
  lastUpdate,
  className = '',
  showDetails = false,
  compact = false
}) => {
  const [stats, setStats] = useState<MonitorStats | null>(null);
  const [timeSinceLastUpdate, setTimeSinceLastUpdate] = useState<string>('--');
  const realtimeManager = getRealtimeManager();

  useEffect(() => {
    // Initialize with real-time manager
    if (!connectionStatus || !lastUpdate) {
      setStats(realtimeManager.getStats() as MonitorStats);
    }

    // Update stats every second
    const statsInterval = setInterval(() => {
      if (!connectionStatus || !lastUpdate) {
        setStats(realtimeManager.getStats() as MonitorStats);
      }
    }, 1000);

    // Update time since last sync every second
    const timeInterval = setInterval(() => {
      let updateTime = lastUpdate;

      if (!updateTime && stats?.lastSyncTime) {
        updateTime = stats.lastSyncTime;
      }

      if (updateTime) {
        const now = new Date();
        const diff = now.getTime() - updateTime.getTime();

        if (diff < 60000) { // Less than 1 minute
          setTimeSinceLastUpdate(`${Math.floor(diff / 1000)}秒前`);
        } else if (diff < 3600000) { // Less than 1 hour
          setTimeSinceLastUpdate(`${Math.floor(diff / 60000)}分鐘前`);
        } else {
          setTimeSinceLastUpdate(`${Math.floor(diff / 3600000)}小時前`);
        }
      } else {
        setTimeSinceLastUpdate('從未更新');
      }
    }, 1000);

    return () => {
      clearInterval(statsInterval);
      clearInterval(timeInterval);
    };
  }, [connectionStatus, lastUpdate, stats?.lastSyncTime, realtimeManager]);

  // Use provided props or stats from real-time manager
  const currentStatus = connectionStatus || (
    stats ? (
      !stats.networkStatus.isOnline ? 'error' :
      !stats.isActive ? 'disconnected' :
      stats.isPaused ? 'connecting' :
      'connected'
    ) : 'disconnected'
  );

  if (compact) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className={`w-2 h-2 rounded-full ${getStatusColor(currentStatus)} ${
          currentStatus === 'connecting' ? 'animate-pulse' : ''
        }`}></div>
        <span className="text-xs text-gray-600">{timeSinceLastUpdate}</span>
      </div>
    );
  }

  return (
    <div className={`flex items-center space-x-4 ${className}`}>
      {/* Connection Status Indicator */}
      <div className="flex items-center space-x-2">
        <div className="relative">
          <div className={`w-3 h-3 rounded-full ${getStatusColor(currentStatus)} ${
            currentStatus === 'connecting' ? 'animate-pulse' : ''
          }`}></div>
          {currentStatus === 'connected' && (
            <div className={`absolute inset-0 rounded-full ${getStatusColor(currentStatus)} animate-ping opacity-75`}></div>
          )}
        </div>
        <span className="text-sm font-medium text-gray-700">{getStatusText(currentStatus)}</span>
      </div>

      {/* Last Update Time */}
      <div className="flex items-center space-x-2">
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="text-sm text-gray-600">最後更新: {timeSinceLastUpdate}</span>
      </div>

      {/* Detailed Stats */}
      {showDetails && stats && (
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <span>更新: {stats.updateCount}次</span>
          {stats.errorCount > 0 && (
            <span className="text-red-600">錯誤: {stats.errorCount}次</span>
          )}
          <span>網路: {getNetworkType(stats.networkStatus.connectionType)}</span>
          {stats.networkStatus.effectiveType !== 'unknown' && (
            <span>{stats.networkStatus.effectiveType}</span>
          )}
        </div>
      )}

      {/* Network Status Indicator */}
      {stats && !stats.networkStatus.isOnline && (
        <div className="flex items-center space-x-2 px-3 py-1 bg-red-100 rounded-lg">
          <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-12.728 12.728m0-12.728l12.728 12.728M12 12h.01" />
          </svg>
          <span className="text-sm font-medium text-red-700">網路連線中斷</span>
        </div>
      )}

      {/* Error Indicator */}
      {stats && stats.errorCount > 0 && stats.networkStatus.isOnline && (
        <div className="flex items-center space-x-2 px-3 py-1 bg-orange-100 rounded-lg">
          <svg className="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <span className="text-sm font-medium text-orange-700">部分更新失敗</span>
        </div>
      )}

      {/* Live Indicator */}
      {currentStatus === 'connected' && (
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1">
            <div className="w-1 h-1 bg-green-500 rounded-full animate-pulse"></div>
            <div className="w-1 h-1 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-1 h-1 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
          </div>
          <span className="text-xs text-green-600 font-medium">實時</span>
        </div>
      )}
    </div>
  );
};

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'connected':
      return 'bg-green-500';
    case 'connecting':
      return 'bg-yellow-500';
    case 'error':
      return 'bg-red-500';
    case 'disconnected':
    default:
      return 'bg-gray-400';
  }
};

const getStatusText = (status: string): string => {
  switch (status) {
    case 'connected':
      return '實時更新中';
    case 'connecting':
      return '連接中';
    case 'error':
      return '連接錯誤';
    case 'disconnected':
    default:
      return '未連接';
  }
};

const getNetworkType = (type: string): string => {
  switch (type) {
    case 'wifi': return 'WiFi';
    case 'cellular': return '行動網路';
    case 'ethernet': return '有線網路';
    case 'bluetooth': return '藍牙';
    default: return '未知';
  }
};

// Compact version for mobile or tight spaces
export const CompactRealTimeMonitor: React.FC<RealTimeMonitorProps> = ({
  className = ''
}) => {
  return <RealTimeMonitor compact={true} className={className} />;
};

export default RealTimeMonitor;