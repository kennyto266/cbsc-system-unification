/**
 * WebSocket Status Indicator Component
 * Shows real-time WebSocket connection status and quality
 */

import React, { useEffect, useState } from 'react';
import { useWebSocketContext } from '../contexts/WebSocketContext';
import { ConnectionState } from '../types/websocket';

interface WebSocketStatusProps {
  showDetails?: boolean;
  showQuality?: boolean;
  className?: string;
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
}

export const WebSocketStatus: React.FC<WebSocketStatusProps> = ({
  showDetails = false,
  showQuality = true,
  className = '',
  position = 'top-right'
}) => {
  const { isConnected, connectionState, connectionQuality, getStats } = useWebSocketContext();
  const [stats, setStats] = useState<any>(null);

  // Update stats periodically
  useEffect(() => {
    const updateStats = () => {
      setStats(getStats());
    };

    updateStats();
    const interval = setInterval(updateStats, 1000);

    return () => clearInterval(interval);
  }, [getStats]);

  // Status color and icon
  const getStatusInfo = () => {
    switch (connectionState) {
      case ConnectionState.CONNECTED:
        return {
          color: 'bg-green-500',
          icon: (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          ),
          text: 'Connected'
        };
      case ConnectionState.CONNECTING:
        return {
          color: 'bg-yellow-500',
          icon: (
            <svg className="w-4 h-4 animate-spin" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
            </svg>
          ),
          text: 'Connecting...'
        };
      case ConnectionState.RECONNECTING:
        return {
          color: 'bg-yellow-500',
          icon: (
            <svg className="w-4 h-4 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
            </svg>
          ),
          text: 'Reconnecting...'
        };
      case ConnectionState.ERROR:
        return {
          color: 'bg-red-500',
          icon: (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          ),
          text: 'Error'
        };
      default:
        return {
          color: 'bg-gray-500',
          icon: (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
            </svg>
          ),
          text: 'Disconnected'
        };
    }
  };

  // Quality indicator
  const getQualityIndicator = () => {
    switch (connectionQuality) {
      case 'excellent':
        return { color: 'bg-green-500', text: 'Excellent' };
      case 'good':
        return { color: 'bg-green-400', text: 'Good' };
      case 'fair':
        return { color: 'bg-yellow-500', text: 'Fair' };
      case 'poor':
        return { color: 'bg-red-500', text: 'Poor' };
      default:
        return { color: 'bg-gray-500', text: 'Unknown' };
    }
  };

  // Position styles
  const getPositionStyles = () => {
    const baseStyles = 'fixed z-50 flex items-center space-x-2 p-2 rounded-lg shadow-lg bg-white';
    const positionStyles = {
      'top-left': 'top-4 left-4',
      'top-right': 'top-4 right-4',
      'bottom-left': 'bottom-4 left-4',
      'bottom-right': 'bottom-4 right-4'
    };
    return `${baseStyles} ${positionStyles[position]}`;
  };

  const statusInfo = getStatusInfo();
  const qualityInfo = getQualityIndicator();

  return (
    <div className={`${getPositionStyles()} ${className}`}>
      {/* Connection status */}
      <div className="flex items-center space-x-2">
        <div className={`w-3 h-3 rounded-full ${statusInfo.color} flex items-center justify-center text-white`}>
          {statusInfo.icon}
        </div>
        <span className="text-sm font-medium text-gray-900">{statusInfo.text}</span>
      </div>

      {/* Quality indicator */}
      {showQuality && isConnected && (
        <div className="flex items-center space-x-1">
          <span className="text-xs text-gray-600">Quality:</span>
          <div className={`w-2 h-2 rounded-full ${qualityInfo.color}`} />
          <span className="text-xs text-gray-900">{qualityInfo.text}</span>
        </div>
      )}

      {/* Detailed stats */}
      {showDetails && stats && (
        <div className="ml-4 text-xs text-gray-600 border-l pl-4">
          <div>Messages: {stats.connection?.metrics?.messagesReceived || 0}</div>
          <div>Latency: {stats.connection?.metrics?.latency || 0}ms</div>
          <div>Reconnects: {stats.connection?.metrics?.reconnectCount || 0}</div>
        </div>
      )}
    </div>
  );
};

/**
 * Minimal WebSocket status indicator
 */
export const WebSocketStatusMinimal: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { isConnected, connectionState } = useWebSocketContext();

  const getStatusColor = () => {
    switch (connectionState) {
      case ConnectionState.CONNECTED:
        return 'bg-green-500';
      case ConnectionState.CONNECTING:
      case ConnectionState.RECONNECTING:
        return 'bg-yellow-500';
      case ConnectionState.ERROR:
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className={`w-2 h-2 rounded-full ${getStatusColor()} ${className}`} />
  );
};

/**
 * Connection status badge
 */
export const WebSocketStatusBadge: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { connectionState } = useWebSocketContext();

  const getBadgeInfo = () => {
    switch (connectionState) {
      case ConnectionState.CONNECTED:
        return { color: 'bg-green-100 text-green-800', text: 'Connected' };
      case ConnectionState.CONNECTING:
        return { color: 'bg-yellow-100 text-yellow-800', text: 'Connecting' };
      case ConnectionState.RECONNECTING:
        return { color: 'bg-yellow-100 text-yellow-800', text: 'Reconnecting' };
      case ConnectionState.ERROR:
        return { color: 'bg-red-100 text-red-800', text: 'Error' };
      default:
        return { color: 'bg-gray-100 text-gray-800', text: 'Disconnected' };
    }
  };

  const badgeInfo = getBadgeInfo();

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badgeInfo.color} ${className}`}>
      {badgeInfo.text}
    </span>
  );
};

export default WebSocketStatus;