/**
 * Widget System Types
 */

export type WidgetType =
  | 'strategy-overview'
  | 'performance-metrics'
  | 'backtest-results'
  | 'real-time-monitor'
  | 'news-announcement'

export interface Widget {
  id: string
  type: WidgetType
  title: string
  isMinimized?: boolean
  isMaximized?: boolean
  config?: Record<string, any>
  createdAt?: string
  updatedAt?: string
}

export interface WidgetConfig {
  [key: string]: any
}

export interface WidgetDefinition {
  type: WidgetType
  title: string
  description: string
  icon: React.ComponentType
  component: React.ComponentType<any>
  defaultConfig: WidgetConfig
  defaultProps: {
    minW?: number
    minH?: number
    maxW?: number
    maxH?: number
    defaultW?: number
    defaultH?: number
  }
}

export interface WidgetLibrary {
  [type: string]: WidgetDefinition
}

export interface WidgetEvent {
  type: 'add' | 'remove' | 'update' | 'move' | 'resize' | 'minimize' | 'maximize'
  widgetId: string
  data?: any
}

export interface WidgetState {
  widgets: Widget[]
  activeWidgetId?: string
  layoutLocked: boolean
}

export interface WidgetAction {
  type: string
  payload: any
}