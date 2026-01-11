import React, { createContext, useContext, useState, useCallback, useMemo } from 'react'
import { WidgetConfig, LayoutConfig, ResponsiveLayout, GRID_BREAKPOINTS, GRID_COLS } from '../../types/grid'
import { debounce } from 'lodash'

// 网格上下文接口
interface GridContextValue {
  widgets: WidgetConfig[]
  layout: ResponsiveLayout
  isEditing: boolean
  setIsEditing: (editing: boolean) => void
  addWidget: (widget: WidgetConfig) => void
  removeWidget: (widgetId: string) => void
  updateWidget: (widgetId: string, updates: Partial<WidgetConfig>) => void
  updateLayout: (layout: ResponsiveLayout) => void
  saveLayout: (name: string) => void
  loadLayout: (layoutId: string) => void
  resetLayout: () => void
  layouts: LayoutConfig[]
}

// 创建上下文
const GridContext = createContext<GridContextValue | undefined>(undefined)

// 导出hook
export const useGrid = () => {
  const context = useContext(GridContext)
  if (!context) {
    throw new Error('useGrid must be used within a GridProvider')
  }
  return context
}

// 网格提供者属性
interface GridProviderProps {
  children: React.ReactNode
  initialLayout?: ResponsiveLayout
  initialWidgets?: WidgetConfig[]
}

// 默认Widget配置
const createDefaultWidget = (type: string, id: string): WidgetConfig => {
  const widgetConfigs: Record<string, Partial<WidgetConfig>> = {
    'strategy-overview': { title: '策略概览', w: 6, h: 4, minW: 4, minH: 3 },
    'performance-metrics': { title: '性能指标', w: 4, h: 3, minW: 3, minH: 2 },
    'backtest-results': { title: '回测结果', w: 8, h: 5, minW: 6, minH: 4 },
    'realtime-monitor': { title: '实时监控', w: 6, h: 4, minW: 4, minH: 3 },
    'news-announcement': { title: '新闻公告', w: 4, h: 4, minW: 3, minH: 3 },
    'quick-actions': { title: '快捷操作', w: 4, h: 2, minW: 3, minH: 2 },
    'market-overview': { title: '市场概览', w: 6, h: 3, minW: 4, minH: 2 },
    'trade-history': { title: '交易历史', w: 8, h: 4, minW: 6, minH: 3 }
  }

  const config = widgetConfigs[type] || { title: '未知组件', w: 4, h: 3 }

  return {
    id,
    type: type as any,
    title: config.title!,
    x: 0,
    y: 0,
    w: config.w!,
    h: config.h!,
    minW: config.minW,
    minH: config.minH,
    isDraggable: true,
    isResizable: true,
    isMinimized: false,
    config: {}
  }
}

// 网格提供者组件
export const GridProvider: React.FC<GridProviderProps> = ({
  children,
  initialLayout,
  initialWidgets = []
}) => {
  const [widgets, setWidgets] = useState<WidgetConfig[]>(initialWidgets)
  const [layout, setLayout] = useState<ResponsiveLayout>(initialLayout || {})
  const [isEditing, setIsEditing] = useState(false)
  const [layouts, setLayouts] = useState<LayoutConfig[]>([])

  // 防抖处理布局变更
  const debouncedUpdateLayout = useMemo(
    () => debounce((newLayout: ResponsiveLayout) => {
      setLayout(newLayout)
      // 保存到localStorage
      try {
        localStorage.setItem('dashboard-layout', JSON.stringify(newLayout))
      } catch (error) {
        console.error('Failed to save layout to localStorage:', error)
      }
    }, 300),
    []
  )

  // 添加Widget
  const addWidget = useCallback((widget: WidgetConfig) => {
    setWidgets(prev => {
      // 找到下一个空位
      const maxY = Math.max(0, ...prev.map(w => w.y + w.h))
      const newWidget = {
        ...widget,
        y: maxY
      }
      return [...prev, newWidget]
    })
  }, [])

  // 移除Widget
  const removeWidget = useCallback((widgetId: string) => {
    setWidgets(prev => prev.filter(w => w.id !== widgetId))
  }, [])

  // 更新Widget
  const updateWidget = useCallback((widgetId: string, updates: Partial<WidgetConfig>) => {
    setWidgets(prev => prev.map(w =>
      w.id === widgetId ? { ...w, ...updates } : w
    ))
  }, [])

  // 更新布局
  const updateLayout = useCallback((newLayout: ResponsiveLayout) => {
    debouncedUpdateLayout(newLayout)
  }, [debouncedUpdateLayout])

  // 保存布局配置
  const saveLayout = useCallback((name: string) => {
    const newLayoutConfig: LayoutConfig = {
      id: Date.now().toString(),
      name,
      widgets,
      breakpoints: GRID_BREAKPOINTS,
      cols: GRID_COLS,
      rowHeight: 60,
      margin: [16, 16],
      containerPadding: [16, 16]
    }

    setLayouts(prev => [...prev, newLayoutConfig])

    // 保存到localStorage
    try {
      localStorage.setItem('dashboard-layouts', JSON.stringify([...layouts, newLayoutConfig]))
    } catch (error) {
      console.error('Failed to save layouts to localStorage:', error)
    }
  }, [widgets, layouts])

  // 加载布局配置
  const loadLayout = useCallback((layoutId: string) => {
    const layoutConfig = layouts.find(l => l.id === layoutId)
    if (layoutConfig) {
      setWidgets(layoutConfig.widgets)
    }
  }, [layouts])

  // 重置布局
  const resetLayout = useCallback(() => {
    const defaultWidgets: WidgetConfig[] = [
      createDefaultWidget('strategy-overview', 'widget-1'),
      createDefaultWidget('performance-metrics', 'widget-2'),
      createDefaultWidget('market-overview', 'widget-3'),
      createDefaultWidget('quick-actions', 'widget-4')
    ]

    setWidgets(defaultWidgets)
    setLayout({})

    // 清除localStorage
    localStorage.removeItem('dashboard-layout')
  }, [])

  // 从localStorage加载数据
  React.useEffect(() => {
    try {
      const savedLayout = localStorage.getItem('dashboard-layout')
      const savedLayouts = localStorage.getItem('dashboard-layouts')

      if (savedLayout) {
        setLayout(JSON.parse(savedLayout))
      }

      if (savedLayouts) {
        setLayouts(JSON.parse(savedLayouts))
      }
    } catch (error) {
      console.error('Failed to load data from localStorage:', error)
    }
  }, [])

  const value: GridContextValue = {
    widgets,
    layout,
    isEditing,
    setIsEditing,
    addWidget,
    removeWidget,
    updateWidget,
    updateLayout,
    saveLayout,
    loadLayout,
    resetLayout,
    layouts
  }

  return (
    <GridContext.Provider value={value}>
      {children}
    </GridContext.Provider>
  )
}

export default GridProvider