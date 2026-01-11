import { ReactNode } from 'react'

// Widget类型枚举
export enum WidgetType {
  STRATEGY_OVERVIEW = 'strategy-overview',
  PERFORMANCE_METRICS = 'performance-metrics',
  BACKTEST_RESULTS = 'backtest-results',
  REALTIME_MONITOR = 'realtime-monitor',
  NEWS_ANNOUNCEMENT = 'news-announcement',
  QUICK_ACTIONS = 'quick-actions',
  MARKET_OVERVIEW = 'market-overview',
  TRADE_HISTORY = 'trade-history'
}

// Widget配置接口
export interface WidgetConfig {
  id: string
  type: WidgetType
  title: string
  x: number
  y: number
  w: number
  h: number
  minW?: number
  minH?: number
  maxW?: number
  maxH?: number
  isDraggable?: boolean
  isResizable?: boolean
  isMinimized?: boolean
  config?: Record<string, any>
  customData?: Record<string, any>
}

// 布局配置接口
export interface LayoutConfig {
  id: string
  name: string
  widgets: WidgetConfig[]
  breakpoints: {
    lg: number
    md: number
    sm: number
    xs: number
    xxs: number
  }
  cols: {
    lg: number
    md: number
    sm: number
    xs: number
    xxs: number
  }
  rowHeight?: number
  margin?: [number, number]
  containerPadding?: [number, number]
}

// 响应式布局接口
export interface ResponsiveLayout {
  lg?: LayoutItem[]
  md?: LayoutItem[]
  sm?: LayoutItem[]
  xs?: LayoutItem[]
  xxs?: LayoutItem[]
}

// 布局项接口
export interface LayoutItem {
  i: string
  x: number
  y: number
  w: number
  h: number
  minW?: number
  minH?: number
  maxW?: number
  maxH?: number
  static?: boolean
  isDraggable?: boolean
  isResizable?: boolean
}

// Widget组件属性
export interface WidgetProps {
  widget: WidgetConfig
  onEdit?: (widget: WidgetConfig) => void
  onDelete?: (widgetId: string) => void
  onResize?: (widgetId: string, size: { w: number; h: number }) => void
  onMove?: (widgetId: string, position: { x: number; y: number }) => void
  onMinimize?: (widgetId: string, minimized: boolean) => void
  children?: ReactNode
}

// 网格系统属性
export interface GridSystemProps {
  layout: ResponsiveLayout
  onLayoutChange?: (layout: ResponsiveLayout, allLayouts: ResponsiveLayout[]) => void
  widgets: WidgetConfig[]
  children?: ReactNode
  className?: string
  width?: number
  isDraggable?: boolean
  isResizable?: boolean
  compactType?: 'vertical' | 'horizontal' | null
  preventCollision?: boolean
  rowHeight?: number
  margin?: [number, number]
  containerPadding?: [number, number]
  onDragStart?: (layout: LayoutItem[], oldItem: LayoutItem?, newItem: LayoutItem, placeholder: LayoutItem, e: MouseEvent, element: HTMLElement) => void
  onDrag?: (layout: LayoutItem[], oldItem: LayoutItem, newItem: LayoutItem, placeholder: LayoutItem, e: MouseEvent, element: HTMLElement) => void
  onDragEnd?: (layout: LayoutItem[], oldItem: LayoutItem, newItem: LayoutItem, placeholder: LayoutItem, e: MouseEvent, element: HTMLElement) => void
}

// Widget注册接口
export interface WidgetRegistry {
  [widgetType: string]: {
    component: React.ComponentType<any>
    defaultProps: Partial<WidgetConfig>
    defaultSize: { w: number; h: number }
    minSize: { w: number; h: number }
    maxSize: { w: number; h: number }
    category: string
    description: string
    icon?: ReactNode
  }
}

// 网格断点
export const GRID_BREAKPOINTS = {
  lg: 1200,
  md: 996,
  sm: 768,
  xs: 480,
  xxs: 0
}

// 网格列数
export const GRID_COLS = {
  lg: 12,
  md: 10,
  sm: 6,
  xs: 4,
  xxs: 2
}

// 默认网格配置
export const DEFAULT_GRID_CONFIG = {
  breakpoints: GRID_BREAKPOINTS,
  cols: GRID_COLS,
  rowHeight: 60,
  margin: [16, 16] as [number, number],
  containerPadding: [16, 16] as [number, number]
}