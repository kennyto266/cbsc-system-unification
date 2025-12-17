import React, { useState, useCallback } from 'react'
import {
  Button,
  Space,
  Dropdown,
  Modal,
  Form,
  Input,
  Select,
  Upload,
  message,
  Tooltip,
  Divider,
  Popconfirm,
  Switch,
  Slider,
  Typography
} from 'antd'
import {
  PlusOutlined,
  SaveOutlined,
  UploadOutlined,
  DownloadOutlined,
  SettingOutlined,
  DeleteOutlined,
  CopyOutlined,
  AppstoreOutlined,
  LayoutOutlined,
  ReloadOutlined,
  FullscreenOutlined,
  EyeOutlined,
  EditOutlined,
  LockOutlined,
  UnlockOutlined,
  AlignLeftOutlined,
  AlignCenterOutlined,
  AlignRightOutlined,
  VerticalAlignTopOutlined,
  VerticalAlignMiddleOutlined,
  VerticalAlignBottomOutlined
} from '@ant-design/icons'
import { useResponsiveGrid, GridWidget, WidgetType } from './ResponsiveGridProvider'

const { Option } = Select
const { Text } = Typography

interface GridToolbarProps {
  selectedWidgets: Set<string>
  onSelectionChange: (selection: Set<string>) => void
  editable?: boolean
}

// Layout presets
const LAYOUT_PRESETS = [
  {
    name: '默认布局',
    description: '标准的仪表板布局',
    icon: <LayoutOutlined />,
    layouts: {
      lg: [
        { i: 'market-overview', x: 0, y: 0, w: 6, h: 2 },
        { i: 'strategy-performance', x: 6, y: 0, w: 6, h: 4 },
        { i: 'asset-allocation', x: 0, y: 2, w: 6, h: 3 },
        { i: 'system-health', x: 0, y: 5, w: 6, h: 3 },
        { i: 'recent-signals', x: 6, y: 4, w: 6, h: 4 },
        { i: 'quick-actions', x: 0, y: 8, w: 12, h: 2 }
      ]
    }
  },
  {
    name: '交易布局',
    description: '专注于交易的布局',
    icon: <AppstoreOutlined />,
    layouts: {
      lg: [
        { i: 'market-overview', x: 0, y: 0, w: 12, h: 2 },
        { i: 'strategy-performance', x: 0, y: 2, w: 8, h: 5 },
        { i: 'quick-actions', x: 8, y: 2, w: 4, h: 5 },
        { i: 'recent-signals', x: 0, y: 7, w: 12, h: 3 }
      ]
    }
  },
  {
    name: '监控布局',
    description: '系统监控为主',
    icon: <EyeOutlined />,
    layouts: {
      lg: [
        { i: 'system-health', x: 0, y: 0, w: 4, h: 4 },
        { i: 'market-overview', x: 4, y: 0, w: 8, h: 2 },
        { i: 'asset-allocation', x: 4, y: 2, w: 4, h: 4 },
        { i: 'strategy-performance', x: 8, y: 2, w: 4, h: 4 },
        { i: 'recent-signals', x: 0, y: 4, w: 12, h: 4 }
      ]
    }
  }
]

const GridToolbar: React.FC<GridToolbarProps> = ({
  selectedWidgets,
  onSelectionChange,
  editable = true
}) => {
  const {
    widgets,
    widgetTypes,
    addWidget,
    removeWidget,
    resetLayout,
    saveLayout,
    loadLayout,
    exportLayout,
    importLayout
  } = useResponsiveGrid()

  const [addWidgetModalVisible, setAddWidgetModalVisible] = useState(false)
  const [saveLayoutModalVisible, setSaveLayoutModalVisible] = useState(false)
  const [loadLayoutModalVisible, setLoadLayoutModalVisible] = useState(false)
  const [settingsModalVisible, setSettingsModalVisible] = useState(false)
  const [form] = Form.useForm()

  // Handle adding a new widget
  const handleAddWidget = useCallback((values: any) => {
    const widgetType = widgetTypes[values.type]
    if (!widgetType) return

    const newWidget: GridWidget = {
      id: `${values.type}-${Date.now()}`,
      type: values.type,
      name: values.name || widgetType.name,
      category: widgetType.category,
      x: 0,
      y: 0,
      w: widgetType.defaultSize.w,
      h: widgetType.defaultSize.h,
      minW: widgetType.minSize.w,
      minH: widgetType.minSize.h,
      maxW: widgetType.maxSize.w,
      maxH: widgetType.maxSize.h,
      isDraggable: widgetType.draggable,
      isResizable: widgetType.resizable,
      config: values.config || {}
    }

    addWidget(newWidget)
    setAddWidgetModalVisible(false)
    form.resetFields()
  }, [widgetTypes, addWidget, form])

  // Handle saving layout
  const handleSaveLayout = useCallback((values: any) => {
    saveLayout(values.name)
    setSaveLayoutModalVisible(false)
    form.resetFields()
  }, [saveLayout, form])

  // Handle loading layout
  const handleLoadLayout = useCallback((values: any) => {
    loadLayout(values.name)
    setLoadLayoutModalVisible(false)
    form.resetFields()
  }, [loadLayout, form])

  // Handle applying preset layout
  const handleApplyPreset = useCallback((preset: any) => {
    Modal.confirm({
      title: '应用预设布局',
      content: `确定要应用 "${preset.name}" 布局吗？这将替换当前的布局设置。`,
      onOk: () => {
        // Clear current widgets and apply preset
        widgets.forEach(widget => removeWidget(widget.id))

        // Add widgets from preset
        Object.values(preset.layouts).flat().forEach((layout: any) => {
          const widgetType = widgetTypes[layout.i]
          if (widgetType) {
            const newWidget: GridWidget = {
              id: `${layout.i}-${Date.now()}`,
              type: layout.i,
              name: widgetType.name,
              category: widgetType.category,
              x: layout.x,
              y: layout.y,
              w: layout.w,
              h: layout.h,
              minW: widgetType.minSize.w,
              minH: widgetType.minSize.h,
              maxW: widgetType.maxSize.w,
              maxH: widgetType.maxSize.h,
              isDraggable: widgetType.draggable,
              isResizable: widgetType.resizable
            }
            addWidget(newWidget)
          }
        })

        message.success(`已应用 "${preset.name}" 布局`)
      }
    })
  }, [widgets, widgetTypes, removeWidget, addWidget])

  // Handle deleting selected widgets
  const handleDeleteSelected = useCallback(() => {
    selectedWidgets.forEach(widgetId => {
      removeWidget(widgetId)
    })
    onSelectionChange(new Set())
  }, [selectedWidgets, removeWidget, onSelectionChange])

  // Handle duplicating selected widgets
  const handleDuplicateSelected = useCallback(() => {
    selectedWidgets.forEach(widgetId => {
      const widget = widgets.find(w => w.id === widgetId)
      if (widget) {
        const duplicate: GridWidget = {
          ...widget,
          id: `${widget.type}-copy-${Date.now()}-${Math.random()}`,
          name: `${widget.name} (副本)`,
          x: (widget.x || 0) + 1,
          y: (widget.y || 0) + 1
        }
        addWidget(duplicate)
      }
    })
    onSelectionChange(new Set())
  }, [selectedWidgets, widgets, addWidget, onSelectionChange])

  // Handle exporting layout
  const handleExportLayout = useCallback(() => {
    const layoutJson = exportLayout()
    const blob = new Blob([layoutJson], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `dashboard-layout-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
    message.success('布局已导出')
  }, [exportLayout])

  // Handle importing layout
  const handleImportLayout = useCallback((file: any) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string
        importLayout(content)
        message.success('布局导入成功')
      } catch (error) {
        message.error('布局文件格式错误')
      }
    }
    reader.readAsText(file)
    return false
  }, [importLayout])

  // Widget type options for dropdown
  const widgetTypeOptions = Object.values(widgetTypes).map(type => (
    <Option key={type.id} value={type.id}>
      <Space>
        <span>{type.name}</span>
        <Text type="secondary" className="text-xs">
          {type.category}
        </Text>
      </Space>
    </Option>
  ))

  // Preset layout menu items
  const presetMenuItems = LAYOUT_PRESETS.map((preset, index) => ({
    key: index,
    label: (
      <div className="flex items-center justify-between">
        <div>
          <div className="font-medium">{preset.name}</div>
          <div className="text-xs text-gray-500">{preset.description}</div>
        </div>
        {preset.icon}
      </div>
    ),
    onClick: () => handleApplyPreset(preset)
  }))

  return (
    <div className="grid-toolbar">
      <Space size="small" wrap>
        {/* Add Widget */}
        <Tooltip title="添加组件">
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setAddWidgetModalVisible(true)}
            disabled={!editable}
          >
            添加组件
          </Button>
        </Tooltip>

        {/* Layout Presets */}
        <Dropdown
          menu={{ items: presetMenuItems }}
          placement="bottomLeft"
          disabled={!editable}
        >
          <Button icon={<LayoutOutlined />}>
            预设布局
          </Button>
        </Dropdown>

        <Divider type="vertical" />

        {/* Save/Load Layout */}
        <Tooltip title="保存布局">
          <Button
            icon={<SaveOutlined />}
            onClick={() => setSaveLayoutModalVisible(true)}
          >
            保存
          </Button>
        </Tooltip>

        <Tooltip title="加载布局">
          <Button
            icon={<UploadOutlined />}
            onClick={() => setLoadLayoutModalVisible(true)}
          >
            加载
          </Button>
        </Tooltip>

        {/* Import/Export */}
        <Tooltip title="导出布局">
          <Button
            icon={<DownloadOutlined />}
            onClick={handleExportLayout}
          >
            导出
          </Button>
        </Tooltip>

        <Upload
          accept=".json"
          showUploadList={false}
          beforeUpload={handleImportLayout}
        >
          <Tooltip title="导入布局">
            <Button icon={<UploadOutlined />}>
              导入
            </Button>
          </Tooltip>
        </Upload>

        <Divider type="vertical" />

        {/* Selection Actions */}
        {selectedWidgets.size > 0 && (
          <>
            <Text type="secondary">已选择 {selectedWidgets.size} 个组件</Text>

            {editable && (
              <>
                <Tooltip title="复制选中组件">
                  <Button
                    icon={<CopyOutlined />}
                    onClick={handleDuplicateSelected}
                  >
                    复制
                  </Button>
                </Tooltip>

                <Popconfirm
                  title="确定要删除选中的组件吗？"
                  onConfirm={handleDeleteSelected}
                  okText="确定"
                  cancelText="取消"
                >
                  <Tooltip title="删除选中组件">
                    <Button
                      danger
                      icon={<DeleteOutlined />}
                    >
                      删除
                    </Button>
                  </Tooltip>
                </Popconfirm>
              </>
            )}
          </>
        )}

        <Divider type="vertical" />

        {/* Layout Actions */}
        {editable && (
          <>
            <Tooltip title="重置布局">
              <Button
                icon={<ReloadOutlined />}
                onClick={() => {
                  Modal.confirm({
                    title: '重置布局',
                    content: '确定要重置所有组件布局吗？',
                    onOk: resetLayout
                  })
                }}
              >
                重置
              </Button>
            </Tooltip>

            <Tooltip title="网格设置">
              <Button
                icon={<SettingOutlined />}
                onClick={() => setSettingsModalVisible(true)}
              />
            </Tooltip>
          </>
        )}

        {/* View Mode Toggle */}
        <Tooltip title={editable ? '切换到查看模式' : '切换到编辑模式'}>
          <Button
            icon={editable ? <EyeOutlined /> : <EditOutlined />}
            onClick={() => {
              // Toggle edit mode
              console.log('Toggle edit mode')
            }}
          />
        </Tooltip>
      </Space>

      {/* Add Widget Modal */}
      <Modal
        title="添加新组件"
        open={addWidgetModalVisible}
        onCancel={() => setAddWidgetModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAddWidget}
        >
          <Form.Item
            name="type"
            label="组件类型"
            rules={[{ required: true, message: '请选择组件类型' }]}
          >
            <Select placeholder="选择组件类型" showSearch>
              {widgetTypeOptions}
            </Select>
          </Form.Item>

          <Form.Item
            name="name"
            label="组件名称"
          >
            <Input placeholder="自定义组件名称（可选）" />
          </Form.Item>

          <Form.Item
            name="config"
            label="配置参数"
          >
            <Input.TextArea
              rows={4}
              placeholder="JSON格式的配置参数（可选）"
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Save Layout Modal */}
      <Modal
        title="保存布局"
        open={saveLayoutModalVisible}
        onCancel={() => setSaveLayoutModalVisible(false)}
        onOk={() => form.submit()}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveLayout}
        >
          <Form.Item
            name="name"
            label="布局名称"
            rules={[{ required: true, message: '请输入布局名称' }]}
          >
            <Input placeholder="输入布局名称" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Load Layout Modal */}
      <Modal
        title="加载布局"
        open={loadLayoutModalVisible}
        onCancel={() => setLoadLayoutModalVisible(false)}
        onOk={() => form.submit()}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleLoadLayout}
        >
          <Form.Item
            name="name"
            label="布局名称"
            rules={[{ required: true, message: '请输入要加载的布局名称' }]}
          >
            <Input placeholder="输入布局名称" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Settings Modal */}
      <Modal
        title="网格设置"
        open={settingsModalVisible}
        onCancel={() => setSettingsModalVisible(false)}
        onOk={() => setSettingsModalVisible(false)}
        width={800}
      >
        <div className="space-y-6">
          <div>
            <h4>显示选项</h4>
            <Space direction="vertical">
              <div className="flex items-center justify-between">
                <Text>显示网格线</Text>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <Text>显示组件边框</Text>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <Text>吸附到网格</Text>
                <Switch defaultChecked />
              </div>
            </Space>
          </div>

          <div>
            <h4>网格大小</h4>
            <Form layout="vertical">
              <Form.Item label="行高">
                <Slider
                  min={50}
                  max={200}
                  defaultValue={100}
                  marks={{
                    50: '50px',
                    100: '100px',
                    150: '150px',
                    200: '200px'
                  }}
                />
              </Form.Item>
              <Form.Item label="间距">
                <Slider
                  min={0}
                  max={32}
                  defaultValue={16}
                  marks={{
                    0: '0px',
                    8: '8px',
                    16: '16px',
                    24: '24px',
                    32: '32px'
                  }}
                />
              </Form.Item>
            </Form>
          </div>

          <div>
            <h4>对齐方式</h4>
            <Space>
              <Tooltip title="左对齐">
                <Button icon={<AlignLeftOutlined />} />
              </Tooltip>
              <Tooltip title="居中">
                <Button icon={<AlignCenterOutlined />} />
              </Tooltip>
              <Tooltip title="右对齐">
                <Button icon={<AlignRightOutlined />} />
              </Tooltip>
              <Divider type="vertical" />
              <Tooltip title="顶部对齐">
                <Button icon={<VerticalAlignTopOutlined />} />
              </Tooltip>
              <Tooltip title="中部对齐">
                <Button icon={<VerticalAlignMiddleOutlined />} />
              </Tooltip>
              <Tooltip title="底部对齐">
                <Button icon={<VerticalAlignBottomOutlined />} />
              </Tooltip>
            </Space>
          </div>
        </div>
      </Modal>

      <style jsx>{`
        .grid-toolbar {
          padding: 12px;
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(0, 0, 0, 0.06);
          border-radius: 8px;
          margin-bottom: 16px;
        }

        .dark .grid-toolbar {
          background: rgba(0, 0, 0, 0.95);
          border-color: rgba(255, 255, 255, 0.1);
        }
      `}</style>
    </div>
  )
}

export default GridToolbar