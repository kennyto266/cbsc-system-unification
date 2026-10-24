/**
 * Widget Component - Base widget container with controls
 */

import React, { useState } from 'react'
import { Card, Button, Space, Dropdown, Tooltip } from 'antd'
import {
  CloseOutlined,
  MinusOutlined,
  ExpandOutlined,
  CompressOutlined,
  SettingOutlined,
  MoreOutlined,
  DragOutlined,
} from '@ant-design/icons'
import { motion, AnimatePresence } from 'framer-motion'
import { WidgetType } from '../../types/widget'
import { cn } from '../../utils/cn'

interface WidgetProps {
  id: string
  type: WidgetType
  title: string
  children?: React.ReactNode
  isResizable?: boolean
  isDraggable?: boolean
  onClose?: () => void
  onMinimize?: () => void
  onMaximize?: () => void
  onSettings?: () => void
  isMinimized?: boolean
  isMaximized?: boolean
  className?: string
  extra?: React.ReactNode
}

export const Widget: React.FC<WidgetProps> = ({
  id,
  type,
  title,
  children,
  isResizable = true,
  isDraggable = true,
  onClose,
  onMinimize,
  onMaximize,
  onSettings,
  isMinimized = false,
  isMaximized = false,
  className = '',
  extra,
}) => {
  const [isHovered, setIsHovered] = useState(false)

  const menuItems = [
    {
      key: 'settings',
      label: '设置',
      icon: <SettingOutlined />,
      onClick: onSettings,
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'minimize',
      label: isMinimized ? '还原' : '最小化',
      icon: <MinusOutlined />,
      onClick: onMinimize,
    },
    {
      key: 'maximize',
      label: isMaximized ? '还原' : '最大化',
      icon: isMaximized ? <CompressOutlined /> : <ExpandOutlined />,
      onClick: onMaximize,
    },
  ]

  const cardStyles = cn(
    'widget-container h-full transition-all duration-200',
    {
      'ring-2 ring-blue-400 ring-opacity-50': isHovered && isDraggable,
      'shadow-lg': !isMaximized,
      'shadow-xl fixed inset-4 z-50': isMaximized,
      'opacity-75': isMinimized,
    },
    className
  )

  const headerStyles = cn(
    'widget-header select-none cursor-default',
    {
      'cursor-move': isDraggable,
      'bg-gray-50': isDraggable,
    }
  )

  return (
    <AnimatePresence>
      {!isMinimized && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.2 }}
          className={cardStyles}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          <Card
            title={
              <div className="flex items-center gap-2">
                {isDraggable && (
                  <Tooltip title="拖拽移动">
                    <DragOutlined className="widget-drag-handle text-gray-400 hover:text-gray-600 transition-colors" />
                  </Tooltip>
                )}
                <span className="font-semibold text-gray-800">{title}</span>
              </div>
            }
            className={headerStyles}
            size="small"
            extra={
              <Space size="small">
                {extra}
                {isHovered && (
                  <>
                    {isResizable && (
                      <Tooltip title={isMaximized ? '还原' : '最大化'}>
                        <Button
                          type="text"
                          size="small"
                          icon={isMaximized ? <CompressOutlined /> : <ExpandOutlined />}
                          onClick={onMaximize}
                          className="opacity-70 hover:opacity-100 transition-opacity"
                        />
                      </Tooltip>
                    )}
                    <Dropdown
                      menu={{ items: menuItems.filter(item => item.onClick) }}
                      trigger={['click']}
                      placement="bottomRight"
                    >
                      <Button
                        type="text"
                        size="small"
                        icon={<MoreOutlined />}
                        className="opacity-70 hover:opacity-100 transition-opacity"
                      />
                    </Dropdown>
                    {onClose && (
                      <Tooltip title="关闭">
                        <Button
                          type="text"
                          size="small"
                          icon={<CloseOutlined />}
                          onClick={onClose}
                          className="opacity-70 hover:opacity-100 hover:text-red-500 transition-all"
                        />
                      </Tooltip>
                    )}
                  </>
                )}
              </Space>
            }
            styles={{
              body: {
                padding: isMaximized ? '16px' : '12px',
                height: '100%',
                overflow: 'auto',
              },
              header: {
                padding: '8px 12px',
                minHeight: '40px',
              },
            }}
          >
            <div className="h-full">
              {children}
            </div>
          </Card>
        </motion.div>
      )}
    </AnimatePresence>
  )
}