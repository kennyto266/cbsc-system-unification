import React, { useState } from 'react'
import { Card, List, Tag, Button, Space, Typography, Timeline, Alert as AntAlert, Empty, Tooltip } from 'antd'
import {
  AlertOutlined,
  DeleteOutlined,
  EyeOutlined,
  CheckOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

const { Text, Title } = Typography

interface AlertItem {
  id: string
  type: 'error' | 'warning' | 'info'
  title: string
  message: string
  timestamp: string
  strategy?: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  read?: boolean
}

interface AlertPanelProps {
  title: string
  alerts: AlertItem[]
  maxItems?: number
  showSeverity?: boolean
  onAlertClick?: (alert: AlertItem) => void
  onClearAll?: () => void
  onMarkAsRead?: (alertId: string) => void
}

const AlertPanel: React.FC<AlertPanelProps> = ({
  title,
  alerts,
  maxItems = 10,
  showSeverity = true,
  onAlertClick,
  onClearAll,
  onMarkAsRead,
}) => {
  const [viewMode, setViewMode] = useState<'list' | 'timeline'>('list')

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14' }} />
      case 'info':
        return <InfoCircleOutlined style={{ color: '#1890ff' }} />
      default:
        return <AlertOutlined />
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'red'
      case 'high':
        return 'orange'
      case 'medium':
        return 'gold'
      case 'low':
        return 'blue'
      default:
        return 'default'
    }
  }

  const formatTime = (timestamp: string) => {
    try {
      return formatDistanceToNow(new Date(timestamp), {
        addSuffix: true,
        locale: zhCN,
      })
    } catch (error) {
      return timestamp
    }
  }

  const displayAlerts = alerts.slice(0, maxItems)

  const renderListItem = (alert: AlertItem) => (
    <List.Item
      key={alert.id}
      className={`cursor-pointer hover:bg-gray-50 ${!alert.read ? 'bg-blue-50' : ''}`}
      onClick={() => onAlertClick?.(alert)}
      actions={[
        <Tooltip title="標記為已讀" key="mark-read">
          <Button
            type="text"
            size="small"
            icon={<CheckOutlined />}
            onClick={(e) => {
              e.stopPropagation()
              onMarkAsRead?.(alert.id)
            }}
          />
        </Tooltip>,
        <Tooltip title="查看詳情" key="view">
          <Button
            type="text"
            size="small"
            icon={<EyeOutlined />}
            onClick={(e) => {
              e.stopPropagation()
              onAlertClick?.(alert)
            }}
          />
        </Tooltip>,
      ]}
    >
      <List.Item.Meta
        avatar={getAlertIcon(alert.type)}
        title={
          <Space>
            <Text strong={!alert.read}>{alert.title}</Text>
            {alert.strategy && (
              <Tag color="blue" size="small">
                {alert.strategy}
              </Tag>
            )}
            {showSeverity && (
              <Tag color={getSeverityColor(alert.severity)} size="small">
                {alert.severity === 'critical' ? '嚴重' :
                 alert.severity === 'high' ? '高' :
                 alert.severity === 'medium' ? '中' : '低'}
              </Tag>
            )}
            {!alert.read && <div className="w-2 h-2 bg-blue-500 rounded-full" />}
          </Space>
        }
        description={
          <Space direction="vertical" size="small" className="w-full">
            <Text type="secondary">{alert.message}</Text>
            <Text type="secondary" className="text-xs">
              {formatTime(alert.timestamp)}
            </Text>
          </Space>
        }
      />
    </List.Item>
  )

  const renderTimelineItem = (alert: AlertItem) => (
    <Timeline.Item
      key={alert.id}
      dot={getAlertIcon(alert.type)}
      color={
        alert.type === 'error' ? 'red' :
        alert.type === 'warning' ? 'orange' : 'blue'
      }
      className="cursor-pointer"
      onClick={() => onAlertClick?.(alert)}
    >
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <Text strong={!alert.read}>{alert.title}</Text>
          {alert.strategy && <Tag color="blue" size="small">{alert.strategy}</Tag>}
          {showSeverity && (
            <Tag color={getSeverityColor(alert.severity)} size="small">
              {alert.severity}
            </Tag>
          )}
        </div>
        <Text type="secondary" className="text-sm">
          {alert.message}
        </Text>
        <Text type="secondary" className="text-xs">
          {formatTime(alert.timestamp)}
        </Text>
      </div>
    </Timeline.Item>
  )

  if (displayAlerts.length === 0) {
    return (
      <Card title={title} size="small">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暫無告警"
        />
      </Card>
    )
  }

  return (
    <Card
      title={title}
      size="small"
      extra={
        <Space>
          <Button
            type={viewMode === 'list' ? 'primary' : 'link'}
            size="small"
            onClick={() => setViewMode('list')}
          >
            列表
          </Button>
          <Button
            type={viewMode === 'timeline' ? 'primary' : 'link'}
            size="small"
            onClick={() => setViewMode('timeline')}
          >
            時間軸
          </Button>
          {onClearAll && (
            <Button
              type="text"
              size="small"
              icon={<DeleteOutlined />}
              onClick={onClearAll}
              danger
            >
              清空
            </Button>
          )}
        </Space>
      }
    >
      <div className="max-h-96 overflow-auto">
        {viewMode === 'list' ? (
          <List
            dataSource={displayAlerts}
            renderItem={renderListItem}
            size="small"
          />
        ) : (
          <Timeline>
            {displayAlerts.map(renderTimelineItem)}
          </Timeline>
        )}
      </div>

      {alerts.length > maxItems && (
        <div className="text-center mt-4">
          <Button type="link" size="small">
            查看更多告警 ({alerts.length - maxItems}+)
          </Button>
        </div>
      )}
    </Card>
  )
}

export default AlertPanel