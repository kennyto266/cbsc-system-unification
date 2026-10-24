// Grid and Widget type definitions for CBSC Dashboard

export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '4xl'

export type WidgetType =
  | 'market-overview'
  | 'strategy-monitor'
  | 'portfolio-summary'
  | 'risk-metrics'
  | 'trading-panel'
  | 'news-feed'
  | 'system-status'
  | 'performance-chart'
  | 'order-book'
  | 'alert-center'

export type WidgetSize = {
  w: number
  h: number
  minW?: number
  minH?: number
  maxW?: number
  maxH?: number
}

export type WidgetPosition = {
  x: number
  y: number
}

export type GridItem = {
  id: string
  type: WidgetType
  title: string
  position: WidgetPosition
  size: WidgetSize
  isResizable?: boolean
  isDraggable?: boolean
  isMinimized?: boolean
  isMaximized?: boolean
  isVisible?: boolean
  config?: Record<string, any>
  version?: string
  lastUpdated?: string
  dependencies?: string[]
}

export type GridLayout = {
  id: string
  name: string
  description?: string
  items: GridItem[]
  breakpoints: Record<Breakpoint, {
    cols: number
    rowHeight: number
    margin: [number, number]
    containerPadding: [number, number]
  }>
  activeBreakpoint?: Breakpoint
  isCompact?: boolean
  isLocked?: boolean
  theme?: 'light' | 'dark' | 'auto'
  createdAt: string
  updatedAt: string
}

export type WidgetRegistryItem = {
  type: WidgetType
  name: string
  description: string
  category: 'market' | 'strategy' | 'portfolio' | 'risk' | 'trading' | 'system'
  icon: string
  defaultSize: WidgetSize
  minSize: WidgetSize
  maxSize: WidgetSize
  component: React.ComponentType<any>
  config?: {
    schema?: any
    default?: Record<string, any>
  }
  permissions?: string[]
  dependencies?: string[]
  version: string
  changelog?: string[]
}

export type WidgetEvent = {
  type: 'add' | 'remove' | 'move' | 'resize' | 'update' | 'minimize' | 'maximize'
  widgetId: string
  data?: any
  timestamp: string
}

export type GridState = {
  layouts: Record<string, GridLayout>
  activeLayoutId: string
  isEditMode: boolean
  isLoading: boolean
  error?: string
  selectedWidgets: string[]
  clipboard?: GridItem
  history: {
    past: GridState[]
    present: GridState
    future: GridState[]
  }
}

export type GridConfig = {
  gridId: string
  autoSave: boolean
  saveInterval: number
  maxHistory: number
  responsive: boolean
  animateTransitions: boolean
  preventCollision: boolean
  useCSSTransforms: boolean
  compactType: 'vertical' | 'horizontal' | null
}