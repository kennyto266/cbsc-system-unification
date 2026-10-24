import React from 'react'
import { Space, Button, Tooltip, Dropdown, Badge } from 'antd'
import {
  PlusOutlined,
  LayoutOutlined,
  SaveOutlined,
  ReloadOutlined,
  SettingOutlined,
  AppstoreOutlined,
  EyeOutlined,
  EditOutlined,
  FullscreenOutlined,
  DownloadOutlined,
  UploadOutlined
} from '@ant-design/icons'

interface DashboardToolbarProps {
  onPresetClick?: () => void
  onSaveLayout?: () => void
  onAddWidget?: () => void
  editable?: boolean
  widgetCount?: number
  isFullscreen?: boolean
  onToggleFullscreen?: () => void
}

const DashboardToolbar: React.FC<DashboardToolbarProps> = ({
  onPresetClick,
  onSaveLayout,
  onAddWidget,
  editable = true,
  widgetCount = 0,
  isFullscreen = false,
  onToggleFullscreen
}) => {
  // Toolbar menu items
  const viewMenuItems = [
    {
      key: 'compact',
      label: '紧凑视图',
      onClick: () => console.log('Compact view')
    },
    {
      key: 'comfortable',
      label: '舒适视图',
      onClick: () => console.log('Comfortable view')
    },
    {
      key: 'spacious',
      label: '宽松视图',
      onClick: () => console.log('Spacious view')
    }
  ]

  const layoutMenuItems = [
    {
      key: 'auto',
      label: '自动排列',
      onClick: () => console.log('Auto arrange')
    },
    {
      key: 'align-left',
      label: '左对齐',
      onClick: () => console.log('Align left')
    },
    {
      key: 'align-center',
      label: '居中对齐',
      onClick: () => console.log('Align center')
    },
    {
      key: 'align-right',
      label: '右对齐',
      onClick: () => console.log('Align right')
    }
  ]

  return (
    <div className="dashboard-toolbar p-3 bg-white dark:bg-gray-800 border-b dark:border-gray-700">
      <div className="flex items-center justify-between">
        {/* Left side actions */}
        <Space size="small">
          {editable && (
            <>
              <Tooltip title="添加组件">
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={onAddWidget}
                >
                  添加组件
                </Button>
              </Tooltip>

              <Tooltip title="预设布局">
                <Button
                  icon={<AppstoreOutlined />}
                  onClick={onPresetClick}
                >
                  预设布局
                </Button>
              </Tooltip>

              <Tooltip title="保存布局">
                <Button
                  icon={<SaveOutlined />}
                  onClick={onSaveLayout}
                >
                  保存
                </Button>
              </Tooltip>

              <Dropdown
                menu={{ items: viewMenuItems }}
                placement="bottomLeft"
              >
                <Button icon={<EyeOutlined />}>
                  视图
                </Button>
              </Dropdown>

              <Dropdown
                menu={{ items: layoutMenuItems }}
                placement="bottomLeft"
              >
                <Button icon={<LayoutOutlined />}>
                  排列
                </Button>
              </Dropdown>
            </>
          )}
        </Space>

        {/* Center info */}
        <div className="flex items-center space-x-4">
          <Badge count={widgetCount} showZero color="#1890ff">
            <span className="text-sm text-gray-500">组件数量</span>
          </Badge>

          {editable && (
            <Badge
              count="编辑中"
              status="processing"
              className="cursor-pointer"
            />
          )}
        </div>

        {/* Right side actions */}
        <Space size="small">
          <Tooltip title="刷新数据">
            <Button
              icon={<ReloadOutlined />}
              onClick={() => window.location.reload()}
            >
              刷新
            </Button>
          </Tooltip>

          {editable && (
            <Tooltip title="网格设置">
              <Button
                icon={<SettingOutlined />}
                onClick={() => console.log('Grid settings')}
              />
            </Tooltip>
          )}

          <Tooltip title={isFullscreen ? '退出全屏' : '全屏显示'}>
            <Button
              icon={<FullscreenOutlined />}
              onClick={onToggleFullscreen}
            />
          </Tooltip>

          <Dropdown
            menu={{
              items: [
                {
                  key: 'export',
                  label: '导出布局',
                  icon: <DownloadOutlined />,
                  onClick: () => console.log('Export layout')
                },
                {
                  key: 'import',
                  label: '导入布局',
                  icon: <UploadOutlined />,
                  onClick: () => console.log('Import layout')
                }
              ]
            }}
            placement="bottomRight"
          >
            <Button icon={<SettingOutlined />} />
          </Dropdown>
        </Space>
      </div>

      <style jsx>{`
        .dashboard-toolbar {
          backdrop-filter: blur(10px);
          background: rgba(255, 255, 255, 0.95);
        }

        .dark .dashboard-toolbar {
          background: rgba(0, 0, 0, 0.95);
        }
      `}</style>
    </div>
  )
}

export default DashboardToolbar