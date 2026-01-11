import React from 'react'
import { Space, Badge, Tooltip, Typography } from 'antd'
import {
  WifiOutlined,
  DisconnectOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'

const { Text } = Typography

interface SystemStatusIndicatorProps {
  isConnected: boolean
  systemHealth?: {
    cpuUsage?: number
    memoryUsage?: number
    diskUsage?: number
  }
  showLabel?: boolean
  compact?: boolean
}

const SystemStatusIndicator: React.FC<SystemStatusIndicatorProps> = ({
  isConnected,
  systemHealth,
  showLabel = true,
  compact = false
}) => {
  const getConnectionStatus = () => {
    if (isConnected) {
      return {
        status: 'success' as const,
        text: '已连接',
        icon: <CheckCircleOutlined />,
        color: '#52c41a',
      }
    } else {
      return {
        status: 'error' as const,
        text: '连接断开',
        icon: <DisconnectOutlined />,
        color: '#ff4d4f',
      }
    }
  }

  const getSystemStatus = () => {
    if (!systemHealth) return { status: 'default' as const, text: '未知' }

    const { cpuUsage = 0, memoryUsage = 0, diskUsage = 0 } = systemHealth
    const avgUsage = (cpuUsage + memoryUsage + diskUsage) / 3

    if (avgUsage > 80) {
      return {
        status: 'error' as const,
        text: '系统负载高',
        color: '#ff4d4f',
      }
    } else if (avgUsage > 60) {
      return {
        status: 'warning' as const,
        text: '系统负载中',
        color: '#faad14',
      }
    } else {
      return {
        status: 'success' as const,
        text: '系统正常',
        color: '#52c41a',
      }
    }
  }

  const connectionStatus = getConnectionStatus()
  const systemStatus = getSystemStatus()

  if (compact) {
    return (
      <Tooltip title={`连接: ${connectionStatus.text} | 系统: ${systemStatus.text}`}>
        <Badge
          status={isConnected ? 'success' : 'error'}
          text={
            <Space size={4}>
              {isConnected ? <WifiOutlined /> : <DisconnectOutlined />}
              {systemHealth && (
                <Badge
                  color={systemStatus.color}
                  text={`${systemHealth.cpuUsage.toFixed(0)}%`}
                />
              )}
            </Space>
          }
        />
      </Tooltip>
    )
  }

  return (
    <Space size="small">
      {/* Connection Status */}
      <Tooltip title={`WebSocket连接状态: ${connectionStatus.text}`}>
        <Space size={4}>
          {connectionStatus.icon}
          {showLabel && (
            <Text style={{ color: connectionStatus.color, fontSize: 12 }}>
              {connectionStatus.text}
            </Text>
          )}
        </Space>
      </Tooltip>

      {/* System Health Status */}
      {systemHealth && (
        <Tooltip title={`系统状态: ${systemStatus.text} (CPU: ${systemHealth.cpuUsage.toFixed(1)}%, 内存: ${systemHealth.memoryUsage.toFixed(1)}%)`}>
          <Space size={4}>
            <Badge color={systemStatus.color} />
            {showLabel && (
              <Text style={{ color: systemStatus.color, fontSize: 12 }}>
                {systemStatus.text}
              </Text>
            )}
          </Space>
        </Tooltip>
      )}
    </Space>
  )
}

export default SystemStatusIndicator