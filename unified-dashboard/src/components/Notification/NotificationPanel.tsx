import React from 'react'
import {
  CheckCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  CloseCircleOutlined,
  CheckOutlined,
  DeleteOutlined
} from '@ant-design/icons'
import { Button, List, Typography, Space, Divider, Empty } from 'antd'
import { motion, AnimatePresence } from 'framer-motion'

const { Text, Title } = Typography

interface Notification {
  id: number
  type: 'success' | 'warning' | 'info' | 'error'
  title: string
  message: string
  time: string
  read?: boolean
}

interface NotificationPanelProps {
  notifications: Notification[]
  onClose: () => void
  onMarkAllRead: () => void
}

const NotificationPanel: React.FC<NotificationPanelProps> = ({
  notifications,
  onClose,
  onMarkAllRead,
}) => {
  const getNotificationIcon = (type: string) => {
    const iconProps = { className: 'text-lg' }
    switch (type) {
      case 'success':
        return <CheckCircleOutlined {...iconProps} className="text-green-500" />
      case 'warning':
        return <WarningOutlined {...iconProps} className="text-yellow-500" />
      case 'error':
        return <CloseCircleOutlined {...iconProps} className="text-red-500" />
      default:
        return <InfoCircleOutlined {...iconProps} className="text-blue-500" />
    }
  }

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'border-l-green-500 bg-green-50 dark:bg-green-900/20'
      case 'warning':
        return 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
      case 'error':
        return 'border-l-red-500 bg-red-50 dark:bg-red-900/20'
      default:
        return 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/20'
    }
  }

  return (
    <div className="max-h-96 overflow-hidden flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <Title level={5} className="!mb-0">
          通知中心
        </Title>
        <Space>
          <Button
            type="text"
            size="small"
            icon={<CheckOutlined />}
            onClick={onMarkAllRead}
          >
            全部已读
          </Button>
          <Button
            type="text"
            size="small"
            icon={<DeleteOutlined />}
            className="text-red-500 hover:text-red-600"
          >
            清空
          </Button>
        </Space>
      </div>

      {/* Notification List */}
      <div className="flex-1 overflow-y-auto">
        {notifications.length > 0 ? (
          <List
            dataSource={notifications}
            renderItem={(item) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2 }}
                className={`border-l-4 ${getNotificationColor(item.type)}
                  hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer`}
              >
                <List.Item className="px-4 py-3 !border-none">
                  <div className="flex items-start space-x-3 w-full">
                    {getNotificationIcon(item.type)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <Text strong className="text-gray-900 dark:text-white">
                          {item.title}
                        </Text>
                        <Text type="secondary" className="text-xs">
                          {item.time}
                        </Text>
                      </div>
                      <Text type="secondary" className="text-sm block">
                        {item.message}
                      </Text>
                    </div>
                  </div>
                </List.Item>
              </motion.div>
            )}
          />
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无通知"
            className="py-8"
          />
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-200 dark:border-gray-700">
        <Button
          type="link"
          block
          className="text-blue-500 hover:text-blue-600"
          onClick={() => {
            // Navigate to notifications page
            console.log('Navigate to all notifications')
            onClose()
          }}
        >
          查看所有通知
        </Button>
      </div>
    </div>
  )
}

export default NotificationPanel