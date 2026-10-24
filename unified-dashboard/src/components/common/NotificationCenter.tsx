import React, { useState, useMemo } from 'react'
import {
  Drawer,
  List,
  Badge,
  Button,
  Space,
  Typography,
  Empty,
  Divider,
  Tag,
  Avatar,
  Tooltip,
} from 'antd'
import {
  BellOutlined,
  RocketOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  DeleteOutlined,
  CheckOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Title, Text } = Typography

interface NotificationCenterProps {
  visible: boolean
  onClose: () => void
  alerts: Array<{
    id: string
    type: 'info' | 'warning' | 'error' | 'success'
    title: string
    message: string
    timestamp: string
    read: boolean
    strategyId?: string
  }>
  strategies: Array<{
    id: string
    name: string
    status: string
  }>
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({
  visible,
  onClose,
  alerts,
  strategies
}) => {
  const [selectedFilter, setSelectedFilter] = useState<string>('all')
  const [markingAllAsRead, setMarkingAllAsRead] = useState(false)

  // Filter alerts
  const filteredAlerts = useMemo(() => {
    if (selectedFilter === 'all') return alerts
    return alerts.filter(alert => alert.type === selectedFilter)
  }, [alerts, selectedFilter])

  // Unread alerts count
  const unreadCount = alerts.filter(alert => !alert.read).length

  // Get alert icon and color
  const getAlertConfig = (type: string) => {
    switch (type) {
      case 'error':
        return { icon: <ExclamationCircleOutlined />, color: '#ff4d4f', bgColor: '#fff2f0' }
      case 'warning':
        return { icon: <AlertOutlined />, color: '#faad14', bgColor: '#fffbe6' }
      case 'success':
        return { icon: <CheckCircleOutlined />, color: '#52c41a', bgColor: '#f6ffed' }
      default:
        return { icon: <InfoCircleOutlined />, color: '#1890ff', bgColor: '#e6f7ff' }
    }
  }

  // Get strategy name by ID
  const getStrategyName = (strategyId?: string) => {
    if (!strategyId) return null
    const strategy = strategies.find(s => s.id === strategyId)
    return strategy?.name || '未知策略'
  }

  // Mark all as read
  const handleMarkAllAsRead = async () => {
    setMarkingAllAsRead(true)
    // Implement API call to mark all as read
    // await api.markAllAlertsAsRead()
    setTimeout(() => {
      setMarkingAllAsRead(false)
    }, 1000)
  }

  // Clear all alerts
  const handleClearAll = async () => {
    // Implement API call to clear all alerts
    // await api.clearAllAlerts()
  }

  // Render alert item
  const renderAlertItem = (alert: any) => {
    const config = getAlertConfig(alert.type)
    const strategyName = getStrategyName(alert.strategyId)

    return (
      <List.Item
        key={alert.id}
        style={{
          backgroundColor: alert.read ? 'transparent' : config.bgColor,
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '8px',
        }}
        actions={[
          !alert.read && (
            <Tooltip title="标记为已读">
              <Button
                type="text"
                size="small"
                icon={<CheckOutlined />}
                onClick={() => {
                  // Implement mark as read
                  console.log('Mark as read:', alert.id)
                }}
              />
            </Tooltip>
          ),
          <Tooltip title="删除">
            <Button
              type="text"
              size="small"
              icon={<DeleteOutlined />}
              danger
              onClick={() => {
                // Implement delete alert
                console.log('Delete alert:', alert.id)
              }}
            />
          </Tooltip>
        ].filter(Boolean)}
      >
        <List.Item.Meta
          avatar={
            <Avatar
              style={{
                backgroundColor: config.color,
                color: 'white',
              }}
              icon={config.icon}
            />
          }
          title={
            <Space>
              <Text strong={!alert.read}>{alert.title}</Text>
              {!alert.read && <Badge dot />}
              {strategyName && (
                <Tag color="blue" size="small">
                  {strategyName}
                </Tag>
              )}
            </Space>
          }
          description={
            <Space direction="vertical" size={4}>
              <Text type="secondary">{alert.message}</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {dayjs(alert.timestamp).fromNow()}
              </Text>
            </Space>
          }
        />
      </List.Item>
    )
  }

  return (
    <Drawer
      title={
        <Space>
          <BellOutlined />
          通知中心
          {unreadCount > 0 && (
            <Badge count={unreadCount} size="small" />
          )}
        </Space>
      }
      placement="right"
      width={400}
      open={visible}
      onClose={onClose}
      extra={
        <Space>
          <Button
            size="small"
            onClick={handleMarkAllAsRead}
            loading={markingAllAsRead}
            disabled={unreadCount === 0}
          >
            全部已读
          </Button>
          <Button
            size="small"
            onClick={handleClearAll}
            disabled={alerts.length === 0}
          >
            清空
          </Button>
        </Space>
      }
    >
      {/* Filter Tabs */}
      <Space style={{ marginBottom: 16, width: '100%' }} wrap>
        <Button
          size="small"
          type={selectedFilter === 'all' ? 'primary' : 'default'}
          onClick={() => setSelectedFilter('all')}
        >
          全部 ({alerts.length})
        </Button>
        <Button
          size="small"
          type={selectedFilter === 'error' ? 'primary' : 'default'}
          onClick={() => setSelectedFilter('error')}
        >
          错误 ({alerts.filter(a => a.type === 'error').length})
        </Button>
        <Button
          size="small"
          type={selectedFilter === 'warning' ? 'primary' : 'default'}
          onClick={() => setSelectedFilter('warning')}
        >
          警告 ({alerts.filter(a => a.type === 'warning').length})
        </Button>
        <Button
          size="small"
          type={selectedFilter === 'success' ? 'primary' : 'default'}
          onClick={() => setSelectedFilter('success')}
        >
          成功 ({alerts.filter(a => a.type === 'success').length})
        </Button>
        <Button
          size="small"
          type={selectedFilter === 'info' ? 'primary' : 'default'}
          onClick={() => setSelectedFilter('info')}
        >
          信息 ({alerts.filter(a => a.type === 'info').length})
        </Button>
      </Space>

      <Divider style={{ margin: '12px 0' }} />

      {/* Alerts List */}
      {filteredAlerts.length > 0 ? (
        <List
          dataSource={filteredAlerts}
          renderItem={renderAlertItem}
          style={{ padding: 0 }}
        />
      ) : (
        <Empty
          description={
            selectedFilter === 'all' ? '暂无通知' : `暂无${selectedFilter}类型通知`
          }
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      )}

      {/* Strategy Status Summary */}
      {strategies.length > 0 && (
        <>
          <Divider />
          <div style={{ marginTop: 16 }}>
            <Title level={5} style={{ marginBottom: 12 }}>
              <RocketOutlined /> 策略状态概览
            </Title>
            <Space wrap>
              <Tag color="green">
                运行中: {strategies.filter(s => s.status === 'active').length}
              </Tag>
              <Tag color="default">
                已停止: {strategies.filter(s => s.status === 'inactive').length}
              </Tag>
              <Tag color="blue">
                测试中: {strategies.filter(s => s.status === 'testing').length}
              </Tag>
              <Tag color="orange">
                需要关注: {strategies.filter(s => s.status === 'attention_needed').length}
              </Tag>
            </Space>
          </div>
        </>
      )}
    </Drawer>
  )
}

export default NotificationCenter