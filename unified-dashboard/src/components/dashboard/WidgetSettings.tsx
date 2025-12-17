/**
 * Widget Settings Component - Dashboard layout and widget settings
 */

import React from 'react'
import { Card, Switch, Space, Button, Typography, Divider, Alert } from 'antd'
import {
  SaveOutlined,
  ReloadOutlined,
  DeleteOutlined,
  CompressOutlined,
} from '@ant-design/icons'

const { Title, Text } = Typography

interface WidgetSettingsProps {
  isAutoSaveEnabled: boolean
  isLayoutLocked: boolean
  onToggleAutoSave: () => void
  onToggleLock: () => void
  onCompactLayout: () => void
  onResetLayout: () => void
}

export const WidgetSettings: React.FC<WidgetSettingsProps> = ({
  isAutoSaveEnabled,
  isLayoutLocked,
  onToggleAutoSave,
  onToggleLock,
  onCompactLayout,
  onResetLayout,
}) => {
  return (
    <div className="widget-settings space-y-6">
      <div>
        <Title level={4}>布局设置</Title>
        <Text type="secondary">
          配置仪表板的布局和行为选项
        </Text>
      </div>

      {/* Auto Save Setting */}
      <Card size="small" title="自动保存">
        <Space direction="vertical" className="w-full">
          <div className="flex items-center justify-between">
            <div>
              <Text strong>启用自动保存</Text>
              <br />
              <Text type="secondary" className="text-xs">
                布局更改将自动保存到本地存储
              </Text>
            </div>
            <Switch
              checked={isAutoSaveEnabled}
              onChange={onToggleAutoSave}
            />
          </div>
        </Space>
      </Card>

      {/* Layout Lock Setting */}
      <Card size="small" title="布局锁定">
        <Space direction="vertical" className="w-full">
          <div className="flex items-center justify-between">
            <div>
              <Text strong>锁定布局</Text>
              <br />
              <Text type="secondary" className="text-xs">
                锁定后无法移动或调整组件大小
            </div>
            <Switch
              checked={isLayoutLocked}
              onChange={onToggleLock}
            />
          </div>
          {isLayoutLocked && (
            <Alert
              message="布局已锁定"
              description="解锁后才能重新排列组件"
              type="info"
              showIcon
              size="small"
            />
          )}
        </Space>
      </Card>

      <Divider />

      {/* Layout Actions */}
      <Card size="small" title="布局操作">
        <Space direction="vertical" className="w-full">
          <Button
            icon={<CompressOutlined />}
            onClick={onCompactLayout}
            className="w-full"
          >
            整理布局
          </Button>

          <Button
            icon={<ReloadOutlined />}
            onClick={onResetLayout}
            danger
            className="w-full"
          >
            重置为默认布局
          </Button>

          <Alert
            message="注意"
            description="重置布局将清除所有自定义配置并恢复默认设置"
            type="warning"
            showIcon
            size="small"
          />
        </Space>
      </Card>

      <Divider />

      {/* Tips */}
      <Card size="small" title="使用提示">
        <Space direction="vertical" className="w-full">
          <div>
            <Text strong>快捷操作：</Text>
            <ul className="text-sm text-gray-600 mt-2 space-y-1">
              <li>• 拖拽组件标题栏可移动位置</li>
              <li>• 拖拽组件右下角可调整大小</li>
              <li>• 双击组件标题栏可快速最大化</li>
              <li>• 右键组件可显示更多选项</li>
            </ul>
          </div>
          <div>
            <Text strong>性能建议：</Text>
            <ul className="text-sm text-gray-600 mt-2 space-y-1">
              <li>• 避免同时显示过多组件</li>
              <li>• 定期清理不需要的组件</li>
              <li>• 使用导出功能备份布局</li>
            </ul>
          </div>
        </Space>
      </Card>
    </div>
  )
}