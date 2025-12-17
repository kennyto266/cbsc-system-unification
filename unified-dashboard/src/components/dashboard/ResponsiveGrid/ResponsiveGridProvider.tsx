import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { Layout, Layouts } from 'react-grid-layout'
import { toast } from 'react-hot-toast'

// Grid configuration types
export interface GridConfig {
  cols: number
  rowHeight: number
  margin: [number, number]
  containerPadding: [number, number]
  breakpoint: string
}

// Default grid configurations for different screen sizes
export const GRID_CONFIGS: Record<string, GridConfig> = {
  lg: { cols: 12, rowHeight: 100, margin: [16, 16], containerPadding: [16, 16], breakpoint: 'lg' },
  md: { cols: 10, rowHeight: 100, margin: [12, 12], containerPadding: [12, 12], breakpoint: 'md' },
  sm: { cols: 6, rowHeight: 100, margin: [8, 8], containerPadding: [8, 8], breakpoint: 'sm' },
  xs: { cols: 4, rowHeight: 100, margin: [8, 8], containerPadding: [8, 8], breakpoint: 'xs' },
  xxs: { cols: 2, rowHeight: 100, margin: [4, 4], containerPadding: [4, 4], breakpoint: 'xxs' }
}

// Widget type definitions
export interface WidgetType {
  id: string
  type: string
  name: string
  category: 'chart' | 'metric' | 'table' | 'control' | 'custom'
  icon?: ReactNode
  defaultSize: { w: number; h: number }
  minSize: { w: number; h: number }
  maxSize: { w: number; h: number }
  configurable: boolean
  resizable: boolean
  draggable: boolean
}

// Widget instance on the grid
export interface GridWidget extends Layout {
  id: string
  type: string
  name: string
  category: string
  config?: Record<string, any>
  data?: any
  lastUpdated?: string
}

// Grid context interface
interface GridContextType {
  // Layout management
  layouts: Layouts
  currentBreakpoint: string
  gridConfig: GridConfig

  // Widget management
  widgets: GridWidget[]
  widgetTypes: Record<string, WidgetType>

  // Actions
  updateLayout: (layout: Layout[], breakpoint: string) => void
  addWidget: (widget: GridWidget) => void
  removeWidget: (widgetId: string) => void
  updateWidget: (widgetId: string, updates: Partial<GridWidget>) => void
  moveWidget: (widgetId: string, layout: Layout) => void
  resizeWidget: (widgetId: string, layout: Layout) => void

  // Utility functions
  resetLayout: () => void
  saveLayout: (name: string) => void
  loadLayout: (name: string) => void
  exportLayout: () => string
  importLayout: (layoutJson: string) => void

  // Breakpoint management
  setBreakpoint: (breakpoint: string) => void
  getBreakpointFromWidth: (width: number) => string

  // State access for external use
  getState: () => GridContextType
}

// Create context
const GridContext = createContext<GridContextType | undefined>(undefined)

// Default widget types registry
export const DEFAULT_WIDGET_TYPES: Record<string, WidgetType> = {
  // Technical Indicators
  'technical-indicator': {
    id: 'technical-indicator',
    type: 'technical-indicator',
    name: '技术指标图表',
    category: 'chart',
    defaultSize: { w: 4, h: 3 },
    minSize: { w: 2, h: 2 },
    maxSize: { w: 8, h: 6 },
    configurable: true,
    resizable: true,
    draggable: true
  },

  // Market Data
  'market-overview': {
    id: 'market-overview',
    type: 'market-overview',
    name: '市场概览',
    category: 'metric',
    defaultSize: { w: 6, h: 2 },
    minSize: { w: 3, h: 2 },
    maxSize: { w: 12, h: 4 },
    configurable: true,
    resizable: true,
    draggable: true
  },

  // Strategy Performance
  'strategy-performance': {
    id: 'strategy-performance',
    type: 'strategy-performance',
    name: '策略表现',
    category: 'chart',
    defaultSize: { w: 8, h: 4 },
    minSize: { w: 4, h: 3 },
    maxSize: { w: 12, h: 8 },
    configurable: true,
    resizable: true,
    draggable: true
  },

  // Asset Allocation
  'asset-allocation': {
    id: 'asset-allocation',
    type: 'asset-allocation',
    name: '资产配置',
    category: 'chart',
    defaultSize: { w: 4, h: 4 },
    minSize: { w: 3, h: 3 },
    maxSize: { w: 6, h: 6 },
    configurable: true,
    resizable: true,
    draggable: true
  },

  // System Health
  'system-health': {
    id: 'system-health',
    type: 'system-health',
    name: '系统健康度',
    category: 'metric',
    defaultSize: { w: 4, h: 3 },
    minSize: { w: 2, h: 2 },
    maxSize: { w: 6, h: 4 },
    configurable: false,
    resizable: true,
    draggable: true
  },

  // Recent Signals
  'recent-signals': {
    id: 'recent-signals',
    type: 'recent-signals',
    name: '最近信号',
    category: 'table',
    defaultSize: { w: 6, h: 4 },
    minSize: { w: 4, h: 3 },
    maxSize: { w: 12, h: 6 },
    configurable: true,
    resizable: true,
    draggable: true
  },

  // Quick Actions
  'quick-actions': {
    id: 'quick-actions',
    type: 'quick-actions',
    name: '快速操作',
    category: 'control',
    defaultSize: { w: 6, h: 2 },
    minSize: { w: 4, h: 2 },
    maxSize: { w: 12, h: 3 },
    configurable: true,
    resizable: true,
    draggable: true
  },

  // Custom Widget
  'custom-widget': {
    id: 'custom-widget',
    type: 'custom-widget',
    name: '自定义组件',
    category: 'custom',
    defaultSize: { w: 4, h: 3 },
    minSize: { w: 2, h: 2 },
    maxSize: { w: 12, h: 12 },
    configurable: true,
    resizable: true,
    draggable: true
  }
}

// Provider component
export const ResponsiveGridProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentBreakpoint, setCurrentBreakpoint] = useState<string>('lg')
  const [layouts, setLayouts] = useState<Layouts>({})
  const [widgets, setWidgets] = useState<GridWidget[]>([])
  const [widgetTypes] = useState<Record<string, WidgetType>>(DEFAULT_WIDGET_TYPES)

  const gridConfig = GRID_CONFIGS[currentBreakpoint]

  // Update layout for a specific breakpoint
  const updateLayout = useCallback((layout: Layout[], breakpoint: string) => {
    setLayouts(prev => ({
      ...prev,
      [breakpoint]: layout
    }))
  }, [])

  // Add new widget to the grid
  const addWidget = useCallback((widget: GridWidget) => {
    setWidgets(prev => {
      // Check if widget already exists
      if (prev.find(w => w.id === widget.id)) {
        toast.error(`组件 ${widget.name} 已存在`)
        return prev
      }

      toast.success(`已添加组件 ${widget.name}`)
      return [...prev, widget]
    })
  }, [])

  // Remove widget from the grid
  const removeWidget = useCallback((widgetId: string) => {
    setWidgets(prev => {
      const widget = prev.find(w => w.id === widgetId)
      if (!widget) return prev

      toast.success(`已移除组件 ${widget.name}`)
      return prev.filter(w => w.id !== widgetId)
    })

    // Also remove from layouts
    setLayouts(prev => {
      const newLayouts = { ...prev }
      Object.keys(newLayouts).forEach(breakpoint => {
        newLayouts[breakpoint] = newLayouts[breakpoint].filter(item => item.i !== widgetId)
      })
      return newLayouts
    })
  }, [])

  // Update widget properties
  const updateWidget = useCallback((widgetId: string, updates: Partial<GridWidget>) => {
    setWidgets(prev => prev.map(widget =>
      widget.id === widgetId
        ? { ...widget, ...updates, lastUpdated: new Date().toISOString() }
        : widget
    ))
  }, [])

  // Move widget to new position
  const moveWidget = useCallback((widgetId: string, layout: Layout) => {
    updateWidget(widgetId, {
      x: layout.x,
      y: layout.y,
      w: layout.w,
      h: layout.h
    })
  }, [updateWidget])

  // Resize widget
  const resizeWidget = useCallback((widgetId: string, layout: Layout) => {
    updateWidget(widgetId, {
      w: layout.w,
      h: layout.h
    })
  }, [updateWidget])

  // Reset layout to default
  const resetLayout = useCallback(() => {
    setLayouts({})
    setWidgets([])
    toast.success('布局已重置')
  }, [])

  // Save layout to localStorage
  const saveLayout = useCallback((name: string) => {
    const layoutData = {
      name,
      layouts,
      widgets,
      timestamp: new Date().toISOString()
    }

    localStorage.setItem(`grid-layout-${name}`, JSON.stringify(layoutData))
    toast.success(`布局 "${name}" 已保存`)
  }, [layouts, widgets])

  // Load layout from localStorage
  const loadLayout = useCallback((name: string) => {
    try {
      const savedLayout = localStorage.getItem(`grid-layout-${name}`)
      if (!savedLayout) {
        toast.error(`布局 "${name}" 不存在`)
        return
      }

      const layoutData = JSON.parse(savedLayout)
      setLayouts(layoutData.layouts || {})
      setWidgets(layoutData.widgets || [])
      toast.success(`已加载布局 "${name}"`)
    } catch (error) {
      console.error('Failed to load layout:', error)
      toast.error('加载布局失败')
    }
  }, [])

  // Export layout as JSON
  const exportLayout = useCallback(() => {
    const layoutData = {
      layouts,
      widgets,
      timestamp: new Date().toISOString()
    }

    return JSON.stringify(layoutData, null, 2)
  }, [layouts, widgets])

  // Import layout from JSON
  const importLayout = useCallback((layoutJson: string) => {
    try {
      const layoutData = JSON.parse(layoutJson)
      setLayouts(layoutData.layouts || {})
      setWidgets(layoutData.widgets || [])
      toast.success('布局导入成功')
    } catch (error) {
      console.error('Failed to import layout:', error)
      toast.error('布局导入失败')
    }
  }, [])

  // Set breakpoint based on screen width
  const setBreakpoint = useCallback((breakpoint: string) => {
    if (Object.keys(GRID_CONFIGS).includes(breakpoint)) {
      setCurrentBreakpoint(breakpoint)
    }
  }, [])

  // Get breakpoint from width
  const getBreakpointFromWidth = useCallback((width: number): string => {
    if (width >= 1200) return 'lg'
    if (width >= 992) return 'md'
    if (width >= 768) return 'sm'
    if (width >= 576) return 'xs'
    return 'xxs'
  }, [])

  // Get current state for external access
  const getState = useCallback(() => ({
    layouts,
    currentBreakpoint,
    gridConfig,
    widgets,
    widgetTypes,
    updateLayout,
    addWidget,
    removeWidget,
    updateWidget,
    moveWidget,
    resizeWidget,
    resetLayout,
    saveLayout,
    loadLayout,
    exportLayout,
    importLayout,
    setBreakpoint,
    getBreakpointFromWidth,
    getState
  }), [
    layouts,
    currentBreakpoint,
    gridConfig,
    widgets,
    widgetTypes,
    updateLayout,
    addWidget,
    removeWidget,
    updateWidget,
    moveWidget,
    resizeWidget,
    resetLayout,
    saveLayout,
    loadLayout,
    exportLayout,
    importLayout,
    setBreakpoint,
    getBreakpointFromWidth
  ])

  const value: GridContextType = {
    // Layout management
    layouts,
    currentBreakpoint,
    gridConfig,

    // Widget management
    widgets,
    widgetTypes,

    // Actions
    updateLayout,
    addWidget,
    removeWidget,
    updateWidget,
    moveWidget,
    resizeWidget,

    // Utility functions
    resetLayout,
    saveLayout,
    loadLayout,
    exportLayout,
    importLayout,

    // Breakpoint management
    setBreakpoint,
    getBreakpointFromWidth,

    // State access
    getState
  }

  return (
    <GridContext.Provider value={value}>
      {children}
    </GridContext.Provider>
  )
}

// Hook to use the grid context
export const useResponsiveGrid = () => {
  const context = useContext(GridContext)
  if (!context) {
    throw new Error('useResponsiveGrid must be used within ResponsiveGridProvider')
  }
  return context
}

// DEFAULT_WIDGET_TYPES is already exported as const above