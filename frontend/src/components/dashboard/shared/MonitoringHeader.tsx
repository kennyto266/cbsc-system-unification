/**
 * MonitoringHeader Component
 * Header with refresh status, connection state, and settings
 */

import React from 'react';
import { Space, Button, Badge, Tag } from 'antd';
import {
  RefreshCw,
  Settings,
  Clock,
  Wifi,
  WifiOff,
  AlertTriangle
} from 'lucide-react';
import { useAppSelector } from '../../../hooks/redux';
import './MonitoringHeader.css';

interface MonitoringHeaderProps {
  lastRefresh: Date;
}

export const MonitoringHeader: React.FC<MonitoringHeaderProps> = ({ lastRefresh }) => {
  // Use default values if monitoring slice doesn't exist yet
  const connectionStatus = useAppSelector((state) =>
    state.monitoring?.connectionStatus || 'connected'
  );
  const unreadAlertsCount = useAppSelector((state) =>
    state.monitoring?.alerts?.filter((a: any) => !a.read).length || 0
  );

  // Calculate time since last refresh
  const getTimeSinceRefresh = () => {
    const seconds = Math.floor((Date.now() - lastRefresh.getTime()) / 1000);
    if (seconds < 60) return `${seconds}秒前刷新`;
    const minutes = Math.floor(seconds / 60);
    return `${minutes}分鐘前刷新`;
  };

  return (
    <div className="monitoring-header">
      <Space size="large">
        {/* Refresh indicator */}
        <div className="monitoring-header-item">
          <Clock size={16} />
          <span>{getTimeSinceRefresh()}</span>
        </div>

        {/* Connection status */}
        <div className="monitoring-header-item">
          {connectionStatus === 'connected' ? (
            <Tag icon={<Wifi size={14} />} color="success">
              連接正常
            </Tag>
          ) : connectionStatus === 'delayed' ? (
            <Tag icon={<Wifi size={14} />} color="warning">
              連接延遲
            </Tag>
          ) : (
            <Tag icon={<WifiOff size={14} />} color="error">
              連接斷開
            </Tag>
          )}
        </div>

        {/* Alerts badge */}
        <Badge count={unreadAlertsCount} size="small">
          <Button
            type="text"
            icon={<AlertTriangle size={16} />}
            className="monitoring-header-alerts"
          >
            警報
          </Button>
        </Badge>

        {/* Settings button */}
        <Button
          type="text"
          icon={<Settings size={16} />}
          onClick={() => {/* TODO: Open settings modal */}}
        >
          設置
        </Button>
      </Space>
    </div>
  );
};

export default MonitoringHeader;
