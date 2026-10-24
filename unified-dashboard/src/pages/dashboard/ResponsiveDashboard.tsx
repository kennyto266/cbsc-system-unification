import React, { useState, useEffect } from 'react'
import { Button, Space, Typography, Card, Switch, Tooltip, Alert } from 'antd'
import {
  SettingOutlined,
  PlusOutlined,
  SaveOutlined,
  EyeOutlined,
  EditOutlined,
  FullscreenOutlined,
  AppstoreOutlined
} from '@ant-design/icons'
import Grid from '../../components/dashboard/Grid'
import { useGridLayout } from '../../hooks/dashboard/useGridLayout'
import { createGridItem } from '../../utils/dashboard/gridHelpers'

const { Title, Text } = Typography

const ResponsiveDashboard: React.FC = () => {
  const {
    layout,
    isEditMode,
    addNewWidget,
    toggleEditMode,
    resetLayout,
    lockLayout,
    unlockLayout,
    exportCurrentLayout,
    stats,
    setError,
  } = useGridLayout()

  // Initialize dashboard with default widgets
  useEffect(() => {
    if (layout.items.length === 0) {
      // Add default widgets to empty layout
      const defaultWidgets = [
        {
          type: 'market-overview',
          title: 'Market Overview',
          position: { x: 0, y: 0 },
          size: { w: 2, h: 3 },
        },
        {
          type: 'strategy-monitor',
          title: 'Strategy Monitor',
          position: { x: 2, y: 0 },
          size: { w: 2, h: 3 },
        },
        {
          type: 'portfolio-summary',
          title: 'Portfolio Summary',
          position: { x: 4, y: 0 },
          size: { w: 2, h: 3 },
        },
        {
          type: 'risk-metrics',
          title: 'Risk Metrics',
          position: { x: 0, y: 3 },
          size: { w: 3, h: 2 },
        },
        {
          type: 'trading-panel',
          title: 'Trading Panel',
          position: { x: 3, y: 3 },
          size: { w: 3, h: 2 },
        },
        {
          type: 'news-feed',
          title: 'News Feed',
          position: { x: 0, y: 5 },
          size: { w: 2, h: 2 },
        },
        {
          type: 'system-status',
          title: 'System Status',
          position: { x: 2, y: 5 },
          size: { w: 2, h: 2 },
        },
        {
          type: 'alert-center',
          title: 'Alert Center',
          position: { x: 4, y: 5 },
          size: { w: 2, h: 2 },
        },
      ]

      // Add widgets to layout
      defaultWidgets.forEach(widget => {
        addNewWidget(widget.type, widget.title, widget.position, widget.size)
      })
    }
  }, [layout.items.length, addNewWidget])

  // Available widget types to add
  const availableWidgets = [
    { type: 'market-overview', name: 'Market Overview', description: 'Real-time market data and metrics' },
    { type: 'strategy-monitor', name: 'Strategy Monitor', description: 'Monitor active trading strategies' },
    { type: 'portfolio-summary', name: 'Portfolio Summary', description: 'Portfolio value and allocation' },
    { type: 'risk-metrics', name: 'Risk Metrics', description: 'Risk analysis and indicators' },
    { type: 'trading-panel', name: 'Trading Panel', description: 'Quick trading interface' },
    { type: 'news-feed', name: 'News Feed', description: 'Latest market news' },
    { type: 'system-status', name: 'System Status', description: 'System health monitoring' },
    { type: 'performance-chart', name: 'Performance Chart', description: 'Performance visualization' },
    { type: 'order-book', name: 'Order Book', description: 'Live order book data' },
    { type: 'alert-center', name: 'Alert Center', description: 'Trading alerts and notifications' },
  ]

  const handleAddWidget = (type: string, name: string) => {
    const cols = layout.breakpoints[layout.activeBreakpoint || 'lg'].cols

    // Find empty space
    let y = 0
    let placed = false

    // Try to place widget in the first available spot
    for (let row = 0; row < 20 && !placed; row++) {
      for (let col = 0; col <= cols - 2 && !placed; col++) {
        const wouldOverlap = layout.items.some(item => {
          const itemRight = item.position.x + item.size.w
          const itemBottom = item.position.y + item.size.h
          const widgetRight = col + 2
          const widgetBottom = row + 2

          return !(
            col >= itemRight ||
            widgetRight <= item.position.x ||
            row >= itemBottom ||
            widgetBottom <= item.position.y
          )
        })

        if (!wouldOverlap) {
          addNewWidget(type, name, { x: col, y: row }, { w: 2, h: 2 })
          placed = true
          y = row
        }
      }
    }

    // If no space found, add to the bottom
    if (!placed) {
      const maxY = Math.max(...layout.items.map(item => item.position.y + item.size.h), 0)
      addNewWidget(type, name, { x: 0, y: maxY }, { w: 2, h: 2 })
    }
  }

  const handleExportLayout = () => {
    const layoutData = exportCurrentLayout()
    const blob = new Blob([layoutData], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `cbsc-dashboard-layout-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="h-screen w-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex justify-between items-center">
          <div>
            <Title level={3} className="!mb-0">
              CBSC Responsive Dashboard
            </Title>
            <Text type="secondary">
              Drag and resize widgets to customize your trading workspace
            </Text>
          </div>

          <Space size="middle">
            {/* Layout Stats */}
            <Space>
              <Text type="secondary" className="text-sm">
                {stats.totalWidgets} widgets
              </Text>
              <Text type="secondary" className="text-sm">
                {stats.utilizationRate.toFixed(0)}% utilized
              </Text>
            </Space>

            {/* Edit Mode Toggle */}
            <Space>
              <Text className="text-sm">Edit Mode</Text>
              <Switch
                checked={isEditMode}
                onChange={toggleEditMode}
                checkedChildren={<EditOutlined />}
                unCheckedChildren={<EyeOutlined />}
              />
            </Space>

            {/* Quick Actions */}
            <Tooltip title="Add Widget">
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => console.log('Open widget panel')}
              >
                Add Widget
              </Button>
            </Tooltip>

            <Tooltip title={layout.isLocked ? 'Unlock Layout' : 'Lock Layout'}>
              <Button
                type={layout.isLocked ? 'default' : 'dashed'}
                icon={layout.isLocked ? <SettingOutlined /> : <SettingOutlined />}
                onClick={layout.isLocked ? unlockLayout : lockLayout}
              >
                {layout.isLocked ? 'Locked' : 'Unlocked'}
              </Button>
            </Tooltip>

            <Tooltip title="Export Layout">
              <Button
                icon={<SaveOutlined />}
                onClick={handleExportLayout}
              >
                Export
              </Button>
            </Tooltip>

            <Tooltip title="Reset Layout">
              <Button
                onClick={resetLayout}
                danger
              >
                Reset
              </Button>
            </Tooltip>
          </Space>
        </div>
      </div>

      {/* Widget Panel (shown in edit mode) */}
      {isEditMode && (
        <div className="bg-blue-50 border-b border-blue-200 px-6 py-3">
          <div className="flex items-center gap-4">
            <Text strong className="text-blue-700">Available Widgets:</Text>
            <div className="flex flex-wrap gap-2">
              {availableWidgets.map(widget => (
                <Button
                  key={widget.type}
                  size="small"
                  className="text-left"
                  onClick={() => handleAddWidget(widget.type, widget.name)}
                  title={widget.description}
                >
                  <AppstoreOutlined className="mr-1" />
                  {widget.name}
                </Button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main Grid Container */}
      <div className="flex-1 p-4 overflow-hidden">
        {isEditMode && (
          <Alert
            message="Edit Mode Active"
            description="Drag widgets to move them. Use the corner handles to resize. Right-click for more options."
            type="info"
            showIcon
            closable
            className="mb-4"
          />
        )}

        <div className="h-full">
          <Grid
            className="bg-white rounded-lg shadow-sm"
            onWidgetClick={(widgetId) => console.log('Widget clicked:', widgetId)}
            onWidgetDoubleClick={(widgetId) => console.log('Widget double-clicked:', widgetId)}
          />
        </div>
      </div>

      {/* Footer */}
      <div className="bg-white border-t border-gray-200 px-6 py-2">
        <div className="flex justify-between items-center text-xs text-gray-500">
          <Text>
            Last updated: {new Date().toLocaleString()}
          </Text>
          <Text>
            Breakpoint: {layout.activeBreakpoint || 'lg'} |
            Columns: {layout.breakpoints[layout.activeBreakpoint || 'lg'].cols}
          </Text>
        </div>
      </div>

      {/* Custom styles */}
      <style jsx>{`
        .grid-container {
          height: 100%;
          position: relative;
        }
      `}</style>
    </div>
  )
}

export default ResponsiveDashboard