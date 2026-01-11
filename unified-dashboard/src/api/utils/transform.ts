/**
 * API Data Transformation Utilities
 * Provides functions to transform API data for frontend consumption
 */

// Snake case to camel case conversion
export const toCamelCase = (str: string): string => {
  return str.replace(/([-_][a-z])/g, (group) =>
    group.toUpperCase().replace('-', '').replace('_', '')
  )
}

// Camel case to snake case conversion
export const toSnakeCase = (str: string): string => {
  return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`)
}

// Convert object keys from snake_case to camelCase
export const keysToCamel = (obj: any): any => {
  if (obj === null || obj === undefined) return obj

  if (Array.isArray(obj)) {
    return obj.map((item) => keysToCamel(item))
  }

  if (typeof obj === 'object') {
    const result: any = {}
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        const camelKey = toCamelCase(key)
        result[camelKey] = keysToCamel(obj[key])
      }
    }
    return result
  }

  return obj
}

// Convert object keys from camelCase to snake_case
export const keysToSnake = (obj: any): any => {
  if (obj === null || obj === undefined) return obj

  if (Array.isArray(obj)) {
    return obj.map((item) => keysToSnake(item))
  }

  if (typeof obj === 'object') {
    const result: any = {}
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        const snakeKey = toSnakeCase(key)
        result[snakeKey] = keysToSnake(obj[key])
      }
    }
    return result
  }

  return obj
}

// Transform API date strings to Date objects
export const transformDates = (obj: any, dateFields: string[]): any => {
  if (!obj || typeof obj !== 'object') return obj

  const result = { ...obj }

  dateFields.forEach((field) => {
    if (result[field]) {
      const date = new Date(result[field])
      if (!isNaN(date.getTime())) {
        result[field] = date
      }
    }
  })

  return result
}

// Transform date to ISO string
export const dateToISOString = (date: Date | string | null): string | null => {
  if (!date) return null

  if (typeof date === 'string') {
    return date
  }

  return date.toISOString()
}

// Transform strategy status
export const transformStrategyStatus = (status: string): 'active' | 'paused' | 'stopped' | 'draft' => {
  const statusMap: Record<string, 'active' | 'paused' | 'stopped' | 'draft'> = {
    'running': 'active',
    'executing': 'active',
    'paused': 'paused',
    'stopped': 'stopped',
    'draft': 'draft',
  }

  return statusMap[status.toLowerCase()] || 'draft'
}

// Transform market data for charts
export const transformMarketData = (data: any[], options?: {
  xKey?: string
  yKey?: string
  volumeKey?: string
}) => {
  const {
    xKey = 'timestamp',
    yKey = 'close',
    volumeKey = 'volume',
  } = options || {}

  return {
    labels: data.map((item) => {
      const timestamp = item[xKey]
      return typeof timestamp === 'number'
        ? new Date(timestamp).toLocaleString()
        : new Date(timestamp).toLocaleString()
    }),
    datasets: [
      {
        label: 'Price',
        data: data.map((item) => item[yKey]),
        borderColor: '#1890ff',
        backgroundColor: 'rgba(24, 144, 255, 0.1)',
        fill: true,
        tension: 0.4,
      },
      ...(volumeKey ? [{
        label: 'Volume',
        data: data.map((item) => item[volumeKey] || 0),
        borderColor: '#52c41a',
        backgroundColor: 'rgba(82, 196, 26, 0.1)',
        fill: true,
        tension: 0.4,
        yAxisID: 'y1',
      }] : []),
    ],
  }
}

// Transform strategy performance data
export const transformStrategyPerformance = (performance: any) => {
  return {
    totalReturn: performance.totalReturn * 100, // Convert to percentage
    annualizedReturn: performance.annualizedReturn * 100,
    sharpeRatio: performance.sharpeRatio,
    maxDrawdown: Math.abs(performance.maxDrawdown) * 100, // Make positive
    winRate: performance.winRate * 100,
    profitFactor: performance.profitFactor,
    totalTrades: performance.totalTrades,
    winningTrades: performance.winningTrades,
    losingTrades: performance.losingTrades,
  }
}

// Transform portfolio data for pie chart
export const transformPortfolioData = (data: Array<{ name: string; value: number; color?: string }>) => {
  return {
    labels: data.map((item) => item.name),
    datasets: [
      {
        data: data.map((item) => item.value),
        backgroundColor: data.map((item) => item.color || '#1890ff'),
        borderWidth: 2,
        borderColor: '#fff',
      },
    ],
  }
}

// Transform table data for Ant Design Table
export const transformTableData = (
  data: any[],
  columns: Array<{ key: string; title: string; dataIndex: string; render?: (value: any) => any }>,
  options?: {
    pagination?: {
      current: number
      pageSize: number
      total: number
    }
  }
) => {
  return {
    columns,
    dataSource: data.map((item, index) => ({
      key: item.id || index,
      ...keysToCamel(item),
    })),
    pagination: options?.pagination || {
      current: 1,
      pageSize: 10,
      total: data.length,
    },
  }
}

// Transform error message for display
export const transformErrorMessage = (error: any): string => {
  if (typeof error === 'string') {
    return error
  }

  if (error?.response?.data?.message) {
    return error.response.data.message
  }

  if (error?.message) {
    return error.message
  }

  if (error?.error?.message) {
    return error.error.message
  }

  return '发生未知错误，请稍后重试'
}

// Transform validation errors
export const transformValidationErrors = (error: any): Record<string, string> => {
  const errors: Record<string, string> = {}

  if (error?.response?.data?.details) {
    const details = error.response.data.details
    if (Array.isArray(details)) {
      details.forEach((detail: any) => {
        const field = detail.field || detail.path || 'unknown'
        errors[field] = detail.message || '验证失败'
      })
    } else if (typeof details === 'object') {
      Object.entries(details).forEach(([field, message]) => {
        errors[field] = Array.isArray(message) ? message[0] : String(message)
      })
    }
  }

  return errors
}

// Transform API response to match expected format
export const transformApiResponse = <T>(response: any): T => {
  if (response?.data) {
    return keysToCamel(response.data)
  }
  return keysToCamel(response)
}

// Transform paginated response
export const transformPaginatedResponse = <T>(response: any) => {
  const transformed = keysToCamel(response)

  return {
    data: transformed.data || [],
    pagination: {
      current: transformed.pagination?.page || 1,
      pageSize: transformed.pagination?.limit || 10,
      total: transformed.pagination?.total || 0,
      showTotal: (total: number, range: [number, number]) =>
        `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
      showSizeChanger: true,
      showQuickJumper: true,
    },
  }
}

// Transform file upload response
export const transformFileUpload = (response: any) => {
  return {
    url: response.url || response.downloadUrl,
    name: response.filename || response.name,
    size: response.size,
    type: response.mimeType || response.type,
  }
}

// Transform WebSocket message
export const transformWSMessage = (message: any) => {
  try {
    const data = typeof message.data === 'string' ? JSON.parse(message.data) : message.data
    return keysToCamel(data)
  } catch {
    return message.data
  }
}

// Format currency values
export const formatCurrency = (
  value: number,
  currency: string = 'CNY',
  locale: string = 'zh-CN'
): string => {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(value)
}

// Format percentage values
export const formatPercentage = (value: number, decimals: number = 2): string => {
  return `${value.toFixed(decimals)}%`
}

// Format large numbers
export const formatLargeNumber = (value: number): string => {
  if (value >= 1e9) {
    return `${(value / 1e9).toFixed(2)}B`
  }
  if (value >= 1e6) {
    return `${(value / 1e6).toFixed(2)}M`
  }
  if (value >= 1e3) {
    return `${(value / 1e3).toFixed(2)}K`
  }
  return value.toString()
}

// Transform time duration
export const formatDuration = (seconds: number): string => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (days > 0) {
    return `${days}天 ${hours}小时`
  }
  if (hours > 0) {
    return `${hours}小时 ${minutes}分钟`
  }
  if (minutes > 0) {
    return `${minutes}分钟 ${secs}秒`
  }
  return `${secs}秒`
}

// Deep clone object
export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj.getTime()) as unknown as T
  if (obj instanceof Array) return obj.map((item) => deepClone(item)) as unknown as T
  if (typeof obj === 'object') {
    const copy = {} as T
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        copy[key] = deepClone(obj[key])
      }
    }
    return copy
  }
  return obj
}