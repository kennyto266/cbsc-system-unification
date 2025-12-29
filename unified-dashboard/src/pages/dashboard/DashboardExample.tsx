import React, { useEffect } from 'react'
import { Button, Space, Card, Typography, Divider, Alert } from 'antd'
import {
  ResponsiveGridProvider,
  ResponsiveGrid,
  useResponsiveGrid,
  DEFAULT_WIDGET_TYPES
} from '../../components/dashboard/ResponsiveGrid'
import { GridWidget } from '../../components/dashboard/ResponsiveGrid/ResponsiveGridProvider'

const { Title, Text, Paragraph } = Typography

// Example component showing grid usage
const GridExample: React.FC = () => {
  const {
    widgets,
    addWidget,
    removeWidget,
    saveLayout,
    loadLayout,
    exportLayout,
    importLayout,
    resetLayout
  } = useResponsiveGrid()

  // Initialize with some example widgets
  useEffect(() => {
    // Add a few example widgets
    const exampleWidgets: GridWidget[] = [
      {
        id: 'example-metric',
        type: 'metric',
        name: '示例指标',
        category: 'metric',
        x: 0,
        y: 0,
        w: 3,
        h: 2,
        minW: 2,
        minH: 2,
        maxW: 6,
        maxH: 4,
        isDraggable: true,
        isResizable: true,
        config: {
          title: '总收益率',
          value: 12.5,
          suffix: '%',
          trend: 2.3,
          icon: '📈'
        }
      },
      {
        id: 'example-chart',
        type: 'technical-indicator',
        name: 'RSI指标示例',
        category: 'chart',
        x: 3,
        y: 0,
        w: 6,
        h: 4,
        minW: 4,
        minH: 3,
        maxW: 12,
        maxH: 8,
        isDraggable: true,
        isResizable: true,
        config: {
          indicator: 'RSI',
          symbol: 'BTC/USDT',
          timeFrame: '1h',
          params: { period: 14 }
        }
      },
      {
        id: 'example-custom',
        type: 'custom-widget',
        name: '自定义内容',
        category: 'custom',
        x: 9,
        y: 0,
        w: 3,
        h: 3,
        minW: 2,
        minH: 2,
        maxW: 6,
        maxH: 6,
        isDraggable: true,
        isResizable: true,
        config: {
          contentType: 'html',
          content: `
            <div style="padding: 20px; text-align: center;">
              <h3>自定义组件</h3>
              <p>这是一个自定义HTML内容的示例</p>
              <button onclick="alert('Hello from custom widget!')">点击我</button>
            </div>
          `
        }
      }
    ]

    // Only add if no widgets exist
    if (widgets.length === 0) {
      exampleWidgets.forEach(widget => {
        addWidget(widget)
      })
    }
  }, [])

  const handleAddRandomWidget = () => {
    const types = Object.keys(DEFAULT_WIDGET_TYPES)
    const randomType = types[Math.floor(Math.random() * types.length)]
    const widgetType = DEFAULT_WIDGET_TYPES[randomType]

    const newWidget: GridWidget = {
      id: `${randomType}-${Date.now()}`,
      type: randomType,
      name: widgetType.name,
      category: widgetType.category,
      x: Math.floor(Math.random() * 6),
      y: Math.floor(Math.random() * 4),
      w: widgetType.defaultSize.w,
      h: widgetType.defaultSize.h,
      minW: widgetType.minSize.w,
      minH: widgetType.minSize.h,
      maxW: widgetType.maxSize.w,
      maxH: widgetType.maxSize.h,
      isDraggable: widgetType.draggable,
      isResizable: widgetType.resizable
    }

    addWidget(newWidget)
  }

  const handleExport = () => {
    const layoutJson = exportLayout()
    const blob = new Blob([layoutJson], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `dashboard-layout-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      const content = e.target?.result as string
      importLayout(content)
    }
    reader.readAsText(file)
  }

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>響應式網格系統示例</Title>
      <Paragraph>
        這是一個使用響應式網格系統的示例，展示了拖拽、調整大小、持久化等功能。
      </Paragraph>

      <Alert
        message="操作提示"
        description="拖拽组件可以移动位置，拖拽右下角可以调整大小。双击组件可以打开配置面板。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* Control Panel */}
      <Card title="控制面板" style={{ marginBottom: 24 }}>
        <Space wrap>
          <Button type="primary" onClick={handleAddRandomWidget}>
            添加随机组件
          </Button>
          <Button onClick={() => saveLayout('example')}>
            保存布局
          </Button>
          <Button onClick={() => loadLayout('example')}>
            加载布局
          </Button>
          <Button onClick={handleExport}>
            导出布局
          </Button>
          <Button>
            <label htmlFor="import-layout" style={{ cursor: 'pointer' }}>
              导入布局
            </label>
            <input
              id="import-layout"
              type="file"
              accept=".json"
              style={{ display: 'none' }}
              onChange={handleImport}
            />
          </Button>
          <Button danger onClick={resetLayout}>
            重置布局
          </Button>
        </Space>
      </Card>

      {/* Grid Stats */}
      <Card title="網格狀態" style={{ marginBottom: 24 }}>
        <Space direction="vertical">
          <Text>組件數量: {widgets.length}</Text>
          <Text>可拖拽: {widgets.filter(w => w.isDraggable !== false).length}</Text>
          <Text>可調整大小: {widgets.filter(w => w.isResizable !== false).length}</Text>
          <Divider />
          <Text strong>組件列表:</Text>
          {widgets.map(widget => (
            <div key={widget.id} style={{ marginLeft: 16 }}>
              <Text>
                {widget.name} ({widget.type}) - 位置:({widget.x}, {widget.y}) 大小:({widget.w}x{widget.h})
                <Button
                  type="link"
                  danger
                  size="small"
                  onClick={() => removeWidget(widget.id)}
                >
                  刪除
                </Button>
              </Text>
            </div>
          ))}
        </Space>
      </Card>

      {/* Responsive Grid */}
      <Card title="響應式網格">
        <div style={{ height: '600px', border: '1px solid #d9d9d9', borderRadius: 4 }}>
          <ResponsiveGrid
            editable={true}
            showToolbar={true}
            onLayoutChange={(layout) => {
              console.log('Layout changed:', layout)
            }}
            onWidgetClick={(widget) => {
              console.log('Widget clicked:', widget)
            }}
            onWidgetDoubleClick={(widget) => {
              console.log('Widget double clicked:', widget)
            }}
          />
        </div>
      </Card>
    </div>
  )
}

// Main example component with provider
const DashboardExample: React.FC = () => {
  return (
    <ResponsiveGridProvider>
      <GridExample />
    </ResponsiveGridProvider>
  )
}

export default DashboardExample