/**
 * useWidgetManager Hook - Manages widget instances and operations
 */

import { useState, useCallback } from 'react'
import { Widget, WidgetType } from '../types/widget'

interface UseWidgetManagerProps {
  initialWidgets?: Widget[]
  maxWidgets?: number
}

const DEFAULT_WIDGETS: Widget[] = [
  {
    id: 'strategy-overview',
    type: 'strategy-overview',
    title: '策略概览',
    isMinimized: false,
    isMaximized: false,
    config: {},
  },
  {
    id: 'performance-metrics',
    type: 'performance-metrics',
    title: '性能指标',
    isMinimized: false,
    isMaximized: false,
    config: {},
  },
  {
    id: 'real-time-monitor',
    type: 'real-time-monitor',
    title: '实时监控',
    isMinimized: false,
    isMaximized: false,
    config: {
      symbols: ['BTC/USDT', 'ETH/USDT'],
    },
  },
]

export const useWidgetManager = ({
  initialWidgets = DEFAULT_WIDGETS,
  maxWidgets = 50,
}: UseWidgetManagerProps = {}) => {
  const [widgets, setWidgets] = useState<Widget[]>(initialWidgets)

  // Generate unique ID for new widgets
  const generateId = useCallback((type: WidgetType) => {
    return `${type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }, [])

  // Get default widget configuration by type
  const getDefaultWidgetConfig = useCallback((type: WidgetType): Partial<Widget> => {
    const configs: Record<WidgetType, Partial<Widget>> = {
      'strategy-overview': {
        title: '策略概览',
        minW: 3,
        minH: 3,
        defaultW: 4,
        defaultH: 4,
      },
      'performance-metrics': {
        title: '性能指标',
        minW: 3,
        minH: 4,
        defaultW: 6,
        defaultH: 5,
      },
      'backtest-results': {
        title: '回测结果',
        minW: 4,
        minH: 4,
        defaultW: 8,
        defaultH: 6,
      },
      'real-time-monitor': {
        title: '实时监控',
        minW: 3,
        minH: 3,
        defaultW: 6,
        defaultH: 4,
        config: {
          symbols: ['BTC/USDT', 'ETH/USDT', 'AAPL', 'TSLA'],
        },
      },
      'news-announcement': {
        title: '新闻公告',
        minW: 2,
        minH: 3,
        defaultW: 3,
        defaultH: 5,
      },
    }

    return configs[type] || {}
  }, [])

  // Add new widget
  const addWidget = useCallback((
    type: WidgetType,
    customConfig?: Partial<Widget>
  ) => {
    if (widgets.length >= maxWidgets) {
      console.warn(`Maximum number of widgets (${maxWidgets}) reached`)
      return null
    }

    const id = generateId(type)
    const defaultConfig = getDefaultWidgetConfig(type)
    const newWidget: Widget = {
      id,
      type,
      title: defaultConfig.title || type,
      isMinimized: false,
      isMaximized: false,
      config: defaultConfig.config || {},
      ...customConfig,
    }

    setWidgets(prev => [...prev, newWidget])
    return id
  }, [widgets.length, maxWidgets, generateId, getDefaultWidgetConfig])

  // Remove widget
  const removeWidget = useCallback((id: string) => {
    setWidgets(prev => prev.filter(widget => widget.id !== id))
  }, [])

  // Update widget
  const updateWidget = useCallback((id: string, updates: Partial<Widget>) => {
    setWidgets(prev => prev.map(widget =>
      widget.id === id ? { ...widget, ...updates } : widget
    ))
  }, [])

  // Toggle widget minimized state
  const toggleMinimized = useCallback((id: string) => {
    setWidgets(prev => prev.map(widget =>
      widget.id === id ? { ...widget, isMinimized: !widget.isMinimized } : widget
    ))
  }, [])

  // Toggle widget maximized state
  const toggleMaximized = useCallback((id: string) => {
    setWidgets(prev => prev.map(widget => {
      if (widget.id !== id) return widget

      const isMaximized = !widget.isMaximized

      // Save current dimensions when maximizing
      if (isMaximized) {
        return {
          ...widget,
          isMaximized,
          prevW: widget.w,
          prevH: widget.h,
        }
      }

      // Restore previous dimensions when unmaximizing
      return {
        ...widget,
        isMaximized,
        w: widget.prevW || widget.w,
        h: widget.prevH || widget.h,
      }
    }))
  }, [])

  // Get widget by ID
  const getWidget = useCallback((id: string) => {
    return widgets.find(widget => widget.id === id)
  }, [widgets])

  // Get widgets by type
  const getWidgetsByType = useCallback((type: WidgetType) => {
    return widgets.filter(widget => widget.type === type)
  }, [widgets])

  // Get available widget types
  const getAvailableWidgetTypes = useCallback((): WidgetType[] => {
    const existingTypes = new Set(widgets.map(w => w.type))
    const allTypes: WidgetType[] = [
      'strategy-overview',
      'performance-metrics',
      'backtest-results',
      'real-time-monitor',
      'news-announcement',
    ]

    // Show all types but indicate which ones are already used
    return allTypes
  }, [widgets])

  // Duplicate widget
  const duplicateWidget = useCallback((id: string) => {
    const widget = getWidget(id)
    if (!widget || widgets.length >= maxWidgets) return null

    const newId = generateId(widget.type)
    const duplicatedWidget: Widget = {
      ...widget,
      id: newId,
      title: `${widget.title} (副本)`,
      isMinimized: false,
      isMaximized: false,
    }

    setWidgets(prev => [...prev, duplicatedWidget])
    return newId
  }, [getWidget, widgets.length, maxWidgets, generateId])

  // Clear all widgets
  const clearWidgets = useCallback(() => {
    setWidgets([])
  }, [])

  // Reset to default widgets
  const resetToDefaults = useCallback(() => {
    setWidgets(DEFAULT_WIDGETS)
  }, [])

  // Export widget configuration
  const exportWidgets = useCallback(() => {
    return JSON.stringify(widgets, null, 2)
  }, [widgets])

  // Import widget configuration
  const importWidgets = useCallback((config: string) => {
    try {
      const parsedWidgets = JSON.parse(config)
      if (Array.isArray(parsedWidgets)) {
        // Validate each widget
        const validWidgets = parsedWidgets.filter(w =>
          w.id && w.type && Object.values(getAvailableWidgetTypes()).includes(w.type)
        )
        setWidgets(validWidgets)
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to import widgets:', error)
      return false
    }
  }, [getAvailableWidgetTypes])

  return {
    widgets,
    addWidget,
    removeWidget,
    updateWidget,
    toggleMinimized,
    toggleMaximized,
    getWidget,
    getWidgetsByType,
    getAvailableWidgetTypes,
    duplicateWidget,
    clearWidgets,
    resetToDefaults,
    exportWidgets,
    importWidgets,
    generateId,
    getDefaultWidgetConfig,
  }
}