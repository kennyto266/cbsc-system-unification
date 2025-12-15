// UI State related types

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  duration?: number
  timestamp: number
  action?: {
    label: string
    handler: () => void
  }
  persistent?: boolean
}

export interface UIState {
  theme: 'light' | 'dark'
  sidebarOpen: boolean
  notifications: Notification[]
  loading: Record<string, boolean>
  modals: Record<string, boolean>
  drawers: Record<string, boolean>
  pageSize: number
  language: 'zh-CN' | 'en-US'
  layout: {
    headerHeight: number
    sidebarWidth: number
    footerHeight: number
  }
  breadcrumbs: BreadcrumbItem[]
}

export interface BreadcrumbItem {
  key: string
  title: string
  path?: string
  icon?: string
}

// Modal types
export interface ModalConfig {
  title: string
  content: React.ReactNode
  width?: number | string
  height?: number | string
  closable?: boolean
  maskClosable?: boolean
  okText?: string
  cancelText?: string
  onOk?: () => void | Promise<void>
  onCancel?: () => void
  footer?: React.ReactNode
}

export interface DrawerConfig {
  title: string
  content: React.ReactNode
  width?: number | string
  height?: number | string
  placement: 'left' | 'right' | 'top' | 'bottom'
  closable?: boolean
  maskClosable?: boolean
  onClose?: () => void
  extra?: React.ReactNode
}

// Layout types
export interface MenuItem {
  key: string
  label: string
  icon?: React.ReactNode
  path?: string
  children?: MenuItem[]
  badge?: {
    count: number
    color?: string
  }
  disabled?: boolean
  hidden?: boolean
  permission?: string
}

export interface MenuConfig {
  items: MenuItem[]
  selectedKeys: string[]
  openKeys: string[]
}

// Loading states
export interface LoadingState {
  [key: string]: boolean
}

// Table types
export interface TableColumn<T = any> {
  key: string
  title: string
  dataIndex: keyof T
  width?: number | string
  align?: 'left' | 'center' | 'right'
  sorter?: boolean | ((a: T, b: T) => number)
  filterable?: boolean
  render?: (value: any, record: T, index: number) => React.ReactNode
  fixed?: 'left' | 'right'
  ellipsis?: boolean
  hidden?: boolean
}

export interface TableProps<T = any> {
  columns: TableColumn<T>[]
  dataSource: T[]
  loading?: boolean
  pagination?: {
    current: number
    pageSize: number
    total: number
    showSizeChanger?: boolean
    showQuickJumper?: boolean
    showTotal?: (total: number, range: [number, number]) => string
  }
  rowSelection?: {
    selectedRowKeys: (string | number)[]
    onChange: (selectedRowKeys: (string | number)[], selectedRows: T[]) => void
    getCheckboxProps?: (record: T) => { disabled?: boolean }
  }
  scroll?: {
    x?: number
    y?: number
  }
  size?: 'small' | 'middle' | 'large'
  bordered?: boolean
}

// Form types
export interface FormField {
  name: string
  label: string
  type: 'input' | 'textarea' | 'select' | 'radio' | 'checkbox' | 'date' | 'upload' | 'custom'
  required?: boolean
  rules?: ValidationRule[]
  options?: SelectOption[]
  placeholder?: string
  disabled?: boolean
  hidden?: boolean
  render?: (form: any) => React.ReactNode
}

export interface ValidationRule {
  required?: boolean
  min?: number
  max?: number
  pattern?: RegExp
  message?: string
  validator?: (rule: any, value: any) => Promise<void>
}

export interface SelectOption {
  label: string
  value: string | number
  disabled?: boolean
  description?: string
  icon?: React.ReactNode
  group?: string
}

// Search and filter types
export interface SearchParams {
  query?: string
  filters?: Record<string, any>
  sort?: {
    field: string
    order: 'asc' | 'desc'
  }
  page?: number
  pageSize?: number
}

export interface FilterOption {
  key: string
  label: string
  field: string
  type: 'select' | 'range' | 'date' | 'custom'
  options?: SelectOption[]
  value?: any
  render?: (value: any, onChange: (value: any) => void) => React.ReactNode
}

// File upload types
export interface FileUpload {
  id: string
  name: string
  size: number
  type: string
  status: 'uploading' | 'success' | 'error'
  progress?: number
  url?: string
  error?: string
  response?: any
}

export interface UploadConfig {
  accept?: string
  multiple?: boolean
  maxSize?: number
  maxCount?: number
  action: string
  headers?: Record<string, string>
  data?: Record<string, any>
  beforeUpload?: (file: File) => boolean | Promise<boolean>
  onProgress?: (event: ProgressEvent, file: FileUpload) => void
  onSuccess?: (response: any, file: FileUpload) => void
  onError?: (error: Error, file: FileUpload) => void
}

// Chart types
export interface ChartDataPoint {
  x: number | string
  y: number
  label?: string
  color?: string
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'area' | 'pie' | 'scatter' | 'candlestick'
  title?: string
  subtitle?: string
  xAxis?: {
    label: string
    type: 'category' | 'value' | 'time'
  }
  yAxis?: {
    label: string
    min?: number
    max?: number
  }
  legend?: boolean
  grid?: boolean
  tooltip?: boolean
  zoom?: boolean
}

// Theme types
export interface Theme {
  mode: 'light' | 'dark'
  colors: {
    primary: string
    secondary: string
    success: string
    warning: string
    error: string
    info: string
    background: string
    surface: string
    text: {
      primary: string
      secondary: string
      disabled: string
    }
  }
  typography: {
    fontFamily: string
    fontSize: {
      xs: string
      sm: string
      base: string
      lg: string
      xl: string
      '2xl': string
      '3xl': string
    }
  }
  spacing: {
    xs: string
    sm: string
    base: string
    lg: string
    xl: string
    '2xl': string
  }
  borderRadius: {
    sm: string
    base: string
    lg: string
    xl: string
  }
  shadows: {
    sm: string
    base: string
    lg: string
    xl: string
  }
}