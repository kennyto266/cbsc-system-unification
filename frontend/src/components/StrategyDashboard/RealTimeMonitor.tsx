import React from 'react';

interface RealTimeMonitorProps {
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastUpdate: Date;
}

export const RealTimeMonitor: React.FC<RealTimeMonitorProps> = ({
  connectionStatus,
  lastUpdate
}) => {
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
        return '已连接';
      case 'connecting':
        return '连接中';
      case 'error':
        return '连接错误';
      case 'disconnected':
      default:
        return '未连接';
    }
  };

  const formatLastUpdate = (date: Date): string => {
    const now = new Date();
    const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffSeconds < 60) {
      return `${diffSeconds}秒前`;
    } else if (diffSeconds < 3600) {
      return `${Math.floor(diffSeconds / 60)}分钟前`;
    } else if (diffSeconds < 86400) {
      return `${Math.floor(diffSeconds / 3600)}小时前`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div className="flex items-center space-x-6">
      {/* Connection Status */}
      <div className="flex items-center space-x-2">
        <span className="text-sm text-gray-600">连接状态:</span>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${getStatusColor(connectionStatus)} ${
            connectionStatus === 'connecting' ? 'animate-pulse' : ''
          }`}></div>
          <span className={`text-sm font-medium ${
            connectionStatus === 'connected' ? 'text-green-600' :
            connectionStatus === 'connecting' ? 'text-yellow-600' :
            connectionStatus === 'error' ? 'text-red-600' :
            'text-gray-600'
          }`}>
            {getStatusText(connectionStatus)}
          </span>
        </div>
      </div>

      {/* Last Update */}
      <div className="flex items-center space-x-2">
        <span className="text-sm text-gray-600">最后更新:</span>
        <span className="text-sm font-medium text-gray-900">
          {formatLastUpdate(lastUpdate)}
        </span>
      </div>

      {/* Live Indicator */}
      {connectionStatus === 'connected' && (
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1">
            <div className="w-1 h-1 bg-green-500 rounded-full animate-pulse"></div>
            <div className="w-1 h-1 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-1 h-1 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
          </div>
          <span className="text-xs text-green-600 font-medium">实时</span>
        </div>
      )}
    </div>
  );
};