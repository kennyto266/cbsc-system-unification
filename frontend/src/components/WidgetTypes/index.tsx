import React from 'react'
import { WidgetConfig, WidgetRegistry } from '../../types/grid'

// 导入所有Widget组件
import StrategyOverview from './StrategyOverview'
import PerformanceMetrics from './PerformanceMetrics'
import RealTimeMonitor from './RealTimeMonitor'
import QuickActions from './QuickActions'

// 创建Widget注册表
export const widgetRegistry: WidgetRegistry = {
  'strategy-overview': {
    component: StrategyOverview,
    defaultProps: {
      title: '策略概览',
      isDraggable: true,
      isResizable: true
    },
    defaultSize: { w: 6, h: 4 },
    minSize: { w: 4, minH: 3 },
    maxSize: { w: 12, h: 8 },
    category: '策略',
    description: '显示所有策略的概览信息，包括运行状态、收益统计等',
    icon: '📊'
  },
  'performance-metrics': {
    component: PerformanceMetrics,
    defaultProps: {
      title: '性能指标',
      isDraggable: true,
      isResizable: true
    },
    defaultSize: { w: 4, h: 3 },
    minSize: { w: 3, minH: 2 },
    maxSize: { w: 8, h: 6 },
    category: '分析',
    description: '显示策略组合的性能指标，包括收益率、夏普比率等',
    icon: '📈'
  },
  'realtime-monitor': {
    component: RealTimeMonitor,
    defaultProps: {
      title: '实时监控',
      isDraggable: true,
      isResizable: true
    },
    defaultSize: { w: 6, h: 4 },
    minSize: { w: 4, minH: 3 },
    maxSize: { w: 12, h: 8 },
    category: '监控',
    description: '实时显示市场数据和系统状态',
    icon: '👁'
  },
  'quick-actions': {
    component: QuickActions,
    defaultProps: {
      title: '快捷操作',
      isDraggable: true,
      isResizable: false
    },
    defaultSize: { w: 4, h: 2 },
    minSize: { w: 3, minH: 2 },
    maxSize: { w: 6, h: 3 },
    category: '工具',
    description: '提供快速操作按钮和批量管理功能',
    icon: '⚡'
  }
}

// 获取Widget组件
export const getWidgetComponent = (type: string) => {
  const widgetConfig = widgetRegistry[type]
  return widgetConfig?.component || null
}

// 获取Widget默认配置
export const getWidgetDefaultConfig = (type: string): Partial<WidgetConfig> => {
  const widgetConfig = widgetRegistry[type]
  return widgetConfig?.defaultProps || {}
}

// 获取Widget默认大小
export const getWidgetDefaultSize = (type: string) => {
  const widgetConfig = widgetRegistry[type]
  return widgetConfig?.defaultSize || { w: 4, h: 3 }
}

// 获取Widget最小尺寸
export const getWidgetMinSize = (type: string) => {
  const widgetConfig = widgetRegistry[type]
  return widgetConfig?.minSize || { w: 2, minH: 2 }
}

// 获取Widget最大尺寸
export const getWidgetMaxSize = (type: string) => {
  const widgetConfig = widgetRegistry[type]
  return widgetConfig?.maxSize || { w: 12, h: 20 }
}

// 按类别分组Widget
export const getWidgetsByCategory = () => {
  const categorized: Record<string, Array<{ type: string; config: any }>> = {}

  Object.entries(widgetRegistry).forEach(([type, config]) => {
    const category = config.category || '其他'
    if (!categorized[category]) {
      categorized[category] = []
    }
    categorized[category].push({ type, config })
  })

  return categorized
}

// 获取所有可用Widget类型
export const getAvailableWidgetTypes = () => {
  return Object.keys(widgetRegistry)
}

// 导出所有Widget组件
export {
  StrategyOverview,
  PerformanceMetrics,
  RealTimeMonitor,
  QuickActions
}

// 默认导出
export default {
  StrategyOverview,
  PerformanceMetrics,
  RealTimeMonitor,
  QuickActions
}