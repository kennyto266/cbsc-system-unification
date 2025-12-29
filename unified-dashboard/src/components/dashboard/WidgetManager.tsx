/**
 * Widget Manager Component - Main dashboard widget management interface
 */

import React, { useState, useCallback, useEffect } from 'react'
import { Layout, Button, Dropdown, Space, Modal, Drawer, message } from 'antd'
import {
  AppstoreOutlined,
  SettingOutlined,
  SaveOutlined,
  ReloadOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  PlusOutlined,
  ImportOutlined,
  ExportOutlined,
  DeleteOutlined,
  UndoOutlined,
} from '@ant-design/icons'
import { GridSystem } from '../Grid/GridSystem'
import { useGridLayout } from '../../hooks/useGridLayout'
import { useWidgetManager } from '../../hooks/useWidgetManager'
import { createAutoSaver } from '../../utils/widgetPersistence'
import { WidgetType } from '../../types/widget'
import { WidgetLibrary } from './WidgetLibrary'
import { WidgetSettings } from './WidgetSettings'
import { GridItem } from '../../types/grid'

const { Content } = Layout

interface WidgetManagerProps {
  className?: string
  initialLayout?: GridItem[]
  onLayoutChange?: (layout: GridItem[]) => void
}

export const WidgetManager: React.FC<WidgetManagerProps> = ({
  className = '',
  initialLayout = [],
  onLayoutChange,
}) => {
  const [showLibrary, setShowLibrary] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isAutoSaveEnabled, setIsAutoSaveEnabled] = useState(true)
  const [isLayoutLocked, setIsLayoutLocked] = useState(false)

  const {
    layout,
    activeDraggingId,
    addItem,
    removeItem,
    updateItem,
    compactLayout,
    resetLayout,
    clearLayout,
    getLayoutAsJSON,
    loadLayoutFromJSON,
  } = useGridLayout({
    initialLayout,
    cols: 12,
    rowHeight: 100,
    autoArrange: true,
    compactType: 'vertical',
  })

  const {
    widgets,
    addWidget,
    removeWidget,
    updateWidget,
    getAvailableWidgetTypes,
    exportWidgets,
    importWidgets,
  } = useWidgetManager()

  // Initialize auto-saver
  const autoSaver = React.useMemo(
    () => createAutoSaver(async () => {
      try {
        await saveCurrentLayout()
      } catch (error) {
        console.error('Auto-save failed:', error)
      }
    }, 2000),
    []
  )

  // Save current layout
  const saveCurrentLayout = useCallback(async () => {
    const dashboardData = {
      layout,
      widgets,
      savedAt: new Date().toISOString(),
    }
    localStorage.setItem('cbsc-dashboard-layout', JSON.stringify(dashboardData))
  }, [layout, widgets])

  // Load saved layout on mount
  useEffect(() => {
    const loadSavedLayout = async () => {
      try {
        const saved = localStorage.getItem('cbsc-dashboard-layout')
        if (saved) {
          const { layout: savedLayout, widgets: savedWidgets } = JSON.parse(saved)
          if (savedLayout) {
            savedLayout.forEach(item => {
              addItem(item)
            })
          }
          // Load widgets if needed
        }
      } catch (error) {
        console.error('Failed to load saved layout:', error)
      }
    }

    loadSavedLayout()
  }, []) // Only run once on mount

  // Auto-save when layout changes
  useEffect(() => {
    if (isAutoSaveEnabled) {
      autoSaver.scheduleSave()
    }

    onLayoutChange?.(layout)

    return () => {
      autoSaver.cancelSave()
    }
  }, [layout, isAutoSaveEnabled, autoSaver, onLayoutChange])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      autoSaver.destroy()
    }
  }, [autoSaver])

  // Add widget to layout
  const handleAddWidget = useCallback((type: WidgetType, customConfig?: any) => {
    const widgetId = addWidget(type, customConfig)
    if (widgetId) {
      const item = {
        id: widgetId,
        x: 0,
        y: 0,
        w: 4,
        h: 4,
        isDraggable: !isLayoutLocked,
        isResizable: !isLayoutLocked,
      }
      addItem(item)
      message.success(`已添加 ${type} 组件`)
    }
  }, [addWidget, addItem, isLayoutLocked])

  // Remove widget from layout
  const handleRemoveWidget = useCallback((id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个组件吗？',
      onOk: () => {
        removeItem(id)
        removeWidget(id)
        message.success('组件已删除')
      },
    })
  }, [removeItem, removeWidget])

  // Export configuration
  const handleExport = useCallback(async () => {
    try {
      const config = {
        layout,
        widgets,
        exportedAt: new Date().toISOString(),
      }
      const blob = new Blob([JSON.stringify(config, null, 2)], {
        type: 'application/json',
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `dashboard-config-${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
      message.success('配置已导出')
    } catch (error) {
      message.error('导出失败')
    }
  }, [layout, widgets])

  // Import configuration
  const handleImport = useCallback(() => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.json'
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (!file) return

      try {
        const text = await file.text()
        const config = JSON.parse(text)

        if (config.layout) {
          clearLayout()
          config.layout.forEach((item: GridItem) => addItem(item))
        }

        if (config.widgets) {
          config.widgets.forEach((widget: any) => {
            addWidget(widget.type, widget)
          })
        }

        message.success('配置已导入')
      } catch (error) {
        message.error('导入失败，请检查文件格式')
      }
    }
    input.click()
  }, [clearLayout, addItem, addWidget])

  // Toggle fullscreen
  const toggleFullscreen = useCallback(() => {
    if (!isFullscreen) {
      document.documentElement.requestFullscreen?.()
    } else {
      document.exitFullscreen?.()
    }
    setIsFullscreen(!isFullscreen)
  }, [isFullscreen])

  // Layout actions menu
  const layoutActionsMenuItems = [
    {
      key: 'auto-save',
      label: isAutoSaveEnabled ? '禁用自动保存' : '启用自动保存',
      onClick: () => setIsAutoSaveEnabled(!isAutoSaveEnabled),
    },
    {
      key: 'lock',
      label: isLayoutLocked ? '解锁布局' : '锁定布局',
      onClick: () => setIsLayoutLocked(!isLayoutLocked),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'compact',
      label: '整理布局',
      onClick: () => {
        compactLayout('vertical')
        message.success('布局已整理')
      },
    },
    {
      key: 'reset',
      label: '重置布局',
      onClick: () => {
        Modal.confirm({
          title: '确认重置',
          content: '确定要重置为默认布局吗？这将清除所有自定义配置。',
          onOk: () => {
            resetLayout()
            message.success('布局已重置')
          },
        })
      },
    },
    {
      key: 'clear',
      label: '清空布局',
      onClick: () => {
        Modal.confirm({
          title: '确认清空',
          content: '确定要清空所有组件吗？',
          onOk: () => {
            clearLayout()
            message.success('布局已清空')
          },
        })
      },
    },
  ]

  return (
    <Layout className={`h-full ${className}`}>
      <Content className="h-full relative">
        {/* Toolbar */}
        <div className="absolute top-4 right-4 z-10 flex gap-2">
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setShowLibrary(true)}
              disabled={isLayoutLocked}
            >
              添加组件
            </Button>

            <Dropdown
              menu={{ items: layoutActionsMenuItems }}
              trigger={['click']}
            >
              <Button icon={<SettingOutlined />}>
                布局设置
              </Button>
            </Dropdown>

            <Button.Group>
              <Button
                icon={<ImportOutlined />}
                onClick={handleImport}
                title="导入配置"
              />
              <Button
                icon={<ExportOutlined />}
                onClick={handleExport}
                title="导出配置"
              />
              <Button
                icon={<SaveOutlined />}
                onClick={() => {
                  saveCurrentLayout()
                  message.success('布局已保存')
                }}
                title="保存布局"
              />
              <Button
                icon={<ReloadOutlined />}
                onClick={() => window.location.reload()}
                title="刷新页面"
              />
              <Button
                icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
                onClick={toggleFullscreen}
                title={isFullscreen ? '退出全屏' : '全屏'}
              />
            </Button.Group>
          </Space>
        </div>

        {/* Grid System */}
        <div className="h-full pt-16">
          <GridSystem
            layout={layout}
            onLayoutChange={newLayout => {
              // Update internal state
            }}
            isDraggable={!isLayoutLocked}
            isResizable={!isLayoutLocked}
            onDragStart={() => {}}
            onDrag={() => {}}
            onDragEnd={() => {
              if (isAutoSaveEnabled) {
                autoSaver.scheduleSave()
              }
            }}
            onResizeStart={() => {}}
            onResize={() => {}}
            onResizeEnd={() => {
              if (isAutoSaveEnabled) {
                autoSaver.scheduleSave()
              }
            }}
          />
        </div>

        {/* Widget Library Drawer */}
        <Drawer
          title="组件库"
          placement="right"
          onClose={() => setShowLibrary(false)}
          open={showLibrary}
          width={400}
        >
          <WidgetLibrary
            availableTypes={getAvailableWidgetTypes()}
            onAddWidget={handleAddWidget}
          />
        </Drawer>

        {/* Widget Settings Modal */}
        <Modal
          title="布局设置"
          open={showSettings}
          onCancel={() => setShowSettings(false)}
          footer={null}
          width={600}
        >
          <WidgetSettings
            isAutoSaveEnabled={isAutoSaveEnabled}
            isLayoutLocked={isLayoutLocked}
            onToggleAutoSave={() => setIsAutoSaveEnabled(!isAutoSaveEnabled)}
            onToggleLock={() => setIsLayoutLocked(!isLayoutLocked)}
            onCompactLayout={() => compactLayout('vertical')}
            onResetLayout={() => {
              resetLayout()
              setShowSettings(false)
            }}
          />
        </Modal>
      </Content>
    </Layout>
  )
}