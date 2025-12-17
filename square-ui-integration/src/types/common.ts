/**
 * Common types used across the application
 */

// Pagination
export interface PaginationParams {
  page?: number
  pageSize?: number
  sort?: string
  order?: 'asc' | 'desc'
}

export interface PaginationResponse<T> {
  data: T[]
  pagination: {
    page: number
    pageSize: number
    total: number
    totalPages: number
    hasNext: boolean
    hasPrev: boolean
  }
}

// API Response
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: {
    code: string
    message: string
    details?: any
  }
  timestamp: string
}

// Select Options
export interface SelectOption {
  label: string
  value: string | number
  disabled?: boolean
  description?: string
}

// Table Column
export interface TableColumn<T = any> {
  key: keyof T
  title: string
  dataIndex?: keyof T
  width?: number | string
  fixed?: 'left' | 'right'
  sortable?: boolean
  filterable?: boolean
  render?: (value: any, record: T, index: number) => React.ReactNode
  align?: 'left' | 'center' | 'right'
}

// Form Field
export interface FormField {
  name: string
  label: string
  type: 'text' | 'number' | 'email' | 'password' | 'select' | 'checkbox' | 'radio' | 'textarea' | 'date' | 'file'
  required?: boolean
  placeholder?: string
  options?: SelectOption[]
  validation?: {
    min?: number
    max?: number
    pattern?: RegExp
    custom?: (value: any) => string | undefined
  }
  defaultValue?: any
  description?: string
  disabled?: boolean
}

// Time Range
export interface TimeRange {
  start: Date | string
  end: Date | string
}

// Date Range Preset
export interface DateRangePreset {
  label: string
  value: TimeRange
  key: string
}

// Chart Data Point
export interface ChartDataPoint {
  x: string | number | Date
  y: number
  label?: string
  color?: string
}

// Chart Config
export interface ChartConfig {
  type: 'line' | 'bar' | 'area' | 'pie' | 'scatter' | 'candlestick'
  title?: string
  height?: number
  showLegend?: boolean
  showTooltip?: boolean
  showGrid?: boolean
  colors?: string[]
}

// Notification
export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
  timestamp: Date
  read?: boolean
  actions?: {
    label: string
    action: () => void
  }[]
}

// Filter State
export interface FilterState {
  search?: string
  dateRange?: TimeRange
  status?: string[]
  category?: string
  [key: string]: any
}

// Sort State
export interface SortState {
  field: string
  direction: 'asc' | 'desc'
}

// Loading State
export interface LoadingState {
  isLoading: boolean
  message?: string
}

// Error State
export interface ErrorState {
  hasError: boolean
  error?: Error | string
  message?: string
}

// Route Config
export interface RouteConfig {
  path: string
  component: React.ComponentType
  exact?: boolean
  protected?: boolean
  title?: string
  icon?: React.ReactNode
  children?: RouteConfig[]
}

// Menu Item
export interface MenuItem {
  key: string
  label: string
  icon?: React.ReactNode
  path?: string
  children?: MenuItem[]
  badge?: {
    count: number
    color?: 'default' | 'primary' | 'success' | 'warning' | 'error'
  }
  disabled?: boolean
}

// Breadcrumb Item
export interface BreadcrumbItem {
  title: string
  path?: string
}

// Export Options
export interface ExportOptions {
  format: 'csv' | 'xlsx' | 'json' | 'pdf'
  filename?: string
  filters?: FilterState
  columns?: string[]
}

// Theme Mode
export type ThemeMode = 'light' | 'dark' | 'system'

// Color Scheme
export type ColorScheme = 'blue' | 'green' | 'purple' | 'orange' | 'red' | 'gray'

// Language
export type Language = 'zh-CN' | 'en-US'

// Device Type
export type DeviceType = 'desktop' | 'tablet' | 'mobile'

// File Upload
export interface FileUpload {
  file: File
  id: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress?: number
  url?: string
  error?: string
}

// Search Suggestion
export interface SearchSuggestion {
  type: 'strategy' | 'market' | 'news' | 'help'
  title: string
  description?: string
  url?: string
  icon?: React.ReactNode
}