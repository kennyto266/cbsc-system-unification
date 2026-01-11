// Export real-time chart components
export { default as TimeSeriesChart } from './components/TimeSeriesChart'
export { default as HeatmapChart } from './components/HeatmapChart'
export { default as DistributionChart } from './components/DistributionChart'

// Export Advanced Charts
export { default as ScatterPlot } from './advanced/ScatterPlot'
export { default as RadarChart } from './advanced/RadarChart'
export { default as AdvancedHeatmapChart } from './advanced/HeatmapChart'
export type { ScatterDataPoint, ScatterDataset, ScatterPlotProps } from './advanced/ScatterPlot'
export type { RadarDataPoint, RadarDataset, RadarChartProps } from './advanced/RadarChart'
export type { HeatmapDataPoint, HeatmapDataset, HeatmapChartProps } from './advanced/HeatmapChart'

// Export Financial Charts
export { default as CandlestickChart } from './financial/CandlestickChart'
export type { OHLCData, CandlestickChartProps } from './financial/CandlestickChart'

// Export Dashboard Components
export { default as PerformanceGauge } from './dashboard/PerformanceGauge'
export type { GaugeThreshold, PerformanceGaugeProps } from './dashboard/PerformanceGauge'

// Export Shared Components
export { default as AdvancedChartContainer, type ChartRef } from './shared/ChartContainer'
export type { ChartContainerProps } from './shared/ChartContainer'

// Export Data Components
export { default as DataTable, type DataTableRef } from '../data/DataTable'
export type { TableColumn, DataTableProps } from '../data/DataTable'

// Export shared components
export { default as ChartContainer } from './components/shared/ChartContainer'
export { default as ChartTooltip } from './components/shared/ChartTooltip'
export { default as ChartLegend } from './components/shared/ChartLegend'
export { default as ChartControls } from './components/shared/ChartControls'

// Export hooks
export { default as useRealTimeData } from './hooks/useRealTimeData'
export { default as useChartInteraction } from './hooks/useChartInteraction'
export { default as useChartPerformance } from './hooks/useChartPerformance'
export { useChartData, useChartSubscription, useMultipleChartSubscriptions } from './providers/ChartDataProvider'

// Export providers
export { default as ChartDataProvider } from './providers/ChartDataProvider'

// Export types
export * from './types/chart.types'
export * from './types/data.types'

// Export utils
export * from './utils/chartUtils'
export * from './utils/dataTransform'
export * from './utils/performanceUtils'
export {
  transformTimeSeriesData,
  aggregateTimeSeries,
  resampleData,
  calculateMovingAverage,
  calculateStandardDeviation,
  calculatePercentiles,
  detectOutliers,
  generateColorPalette,
  formatNumber,
  formatPercentage,
  formatDate,
  debounce,
  throttle,
  memoize
} from '../../utils/chartUtils'

// Export styles and themes
export * from './styles/chartThemes'

// 統一導出所有圖表組件
export { default as StrategyPerformanceChart } from './StrategyPerformanceChart'
export { default as AssetAllocationChart } from './AssetAllocationChart'
export { default as StrategyComparisonChart } from './StrategyComparisonChart'
export { default as RiskReturnScatterChart } from './RiskReturnScatterChart'
export { default as RealTimePriceChart } from './RealTimePriceChart'

// Real-time Chart Components - Task #65 Implementation
// Note: Remove duplicate exports that are already exported above
export {
  TechnicalIndicatorChart,
  DepthChart,
  TechnicalIndicatorsManager,
  RealTimeChartProvider,
  useRealTimeChart,
  useChart,
  type ChartDataPoint as RealTimeChartDataPoint,
  type IndicatorData,
  type IndicatorConfig,
  type ChartType,
  type TimeframeOption,
  type OrderBookLevel,
  type OrderBookData
} from './RealTime'

// Performance Monitor
export { default as ChartPerformanceMonitor, type PerformanceMetrics } from './RealTime/ChartPerformanceMonitor'

// 圖表相關的工具函數和類型定義
export interface ChartTheme {
  primaryColor: string
  backgroundColor: string
  gridColor: string
  textColor: string
  successColor: string
  dangerColor: string
  warningColor: string
  infoColor: string
}

export interface ChartExportOptions {
  format: 'png' | 'jpg' | 'svg'
  quality?: number
  backgroundColor?: string
}

export const defaultChartTheme: ChartTheme = {
  primaryColor: '#3B82F6',
  backgroundColor: '#ffffff',
  gridColor: 'rgba(0, 0, 0, 0.05)',
  textColor: '#374151',
  successColor: '#10B981',
  dangerColor: '#EF4444',
  warningColor: '#F59E0B',
  infoColor: '#06B6D4'
}

// 圖表工具函數
export const chartUtils = {
  // 格式化數字
  formatNumber: (value: number, decimals: number = 2): string => {
    return new Intl.NumberFormat('zh-TW', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(value)
  },

  // 格式化百分比
  formatPercentage: (value: number, decimals: number = 2): string => {
    return `${chartUtils.formatNumber(value * 100, decimals)}%`
  },

  // 格式化貨幣
  formatCurrency: (value: number, currency: string = 'USD'): string => {
    return new Intl.NumberFormat('zh-TW', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value)
  },

  // 生成顏色數組
  generateColors: (count: number, baseColors?: string[]): string[] => {
    const colors = baseColors || [
      '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
      '#EC4899', '#06B6D4', '#84CC16', '#6366F1', '#14B8A6'
    ]

    const result: string[] = []
    for (let i = 0; i < count; i++) {
      result.push(colors[i % colors.length])
    }
    return result
  },

  // 計算移動平均
  calculateSMA: (data: number[], period: number): number[] => {
    const result: number[] = []
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push(NaN)
      } else {
        const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0)
        result.push(sum / period)
      }
    }
    return result
  },

  // 計算指數移動平均
  calculateEMA: (data: number[], period: number): number[] => {
    const result: number[] = []
    const multiplier = 2 / (period + 1)

    if (data.length === 0) return result

    result[0] = data[0]
    for (let i = 1; i < data.length; i++) {
      result[i] = (data[i] - result[i - 1]) * multiplier + result[i - 1]
    }
    return result
  },

  // 計算RSI
  calculateRSI: (data: number[], period: number = 14): number[] => {
    const result: number[] = []

    for (let i = 0; i < data.length; i++) {
      if (i < period) {
        result.push(NaN)
      } else {
        let gains = 0
        let losses = 0
        for (let j = i - period + 1; j <= i; j++) {
          const change = data[j] - data[j - 1]
          if (change > 0) gains += change
          else losses -= change
        }
        const avgGain = gains / period
        const avgLoss = losses / period
        const rs = avgGain / avgLoss
        result.push(100 - (100 / (1 + rs)))
      }
    }
    return result
  },

  // 導出圖表為圖片
  exportChart: (canvas: HTMLCanvasElement, options: ChartExportOptions): Promise<void> => {
    return new Promise((resolve, reject) => {
      try {
        const { format, quality = 1, backgroundColor = '#ffffff' } = options

        // 設置背景色
        const ctx = canvas.getContext('2d')
        if (ctx && backgroundColor) {
          const originalBg = canvas.style.backgroundColor
          canvas.style.backgroundColor = backgroundColor

          setTimeout(() => {
            const url = canvas.toDataURL(`image/${format}`, quality)
            const link = document.createElement('a')
            link.download = `chart-${Date.now()}.${format}`
            link.href = url
            link.click()

            canvas.style.backgroundColor = originalBg
            resolve()
          }, 100)
        } else {
          const url = canvas.toDataURL(`image/${format}`, quality)
          const link = document.createElement('a')
          link.download = `chart-${Date.now()}.${format}`
          link.href = url
          link.click()
          resolve()
        }
      } catch (error) {
        reject(error)
      }
    })
  },

  // 調整圖表主題
  applyTheme: (theme: ChartTheme): ChartTheme => {
    return { ...defaultChartTheme, ...theme }
  }
}

// 圖表響應式配置
export const responsiveChartConfig = {
  // 移動端配置
  mobile: {
    aspectRatio: 1,
    height: 300,
    fontSize: 10,
    pointRadius: 2,
    legendPosition: 'bottom' as const
  },

  // 平板配置
  tablet: {
    aspectRatio: 16/9,
    height: 400,
    fontSize: 12,
    pointRadius: 3,
    legendPosition: 'top' as const
  },

  // 桌面配置
  desktop: {
    aspectRatio: 21/9,
    height: 500,
    fontSize: 14,
    pointRadius: 4,
    legendPosition: 'top' as const
  }
}

// 圖表動畫配置
export const chartAnimationConfig = {
  duration: 1000,
  easing: 'easeInOutQuart' as const,
  delay: (context: any) => {
    let delay = 0
    if (context.type === 'data' && context.mode === 'default') {
      delay = context.dataIndex * 300 + context.datasetIndex * 100
    }
    return delay
  }
}

// 圖表類型枚舉
export enum ChartType {
  LINE = 'line',
  BAR = 'bar',
  PIE = 'pie',
  DOUGHNUT = 'doughnut',
  RADAR = 'radar',
  POLAR_AREA = 'polarArea',
  SCATTER = 'scatter',
  BUBBLE = 'bubble'
}

// 圖表更新頻率枚舉
export enum UpdateFrequency {
  REAL_TIME = 'real_time',
  MINUTELY = 'minutely',
  HOURLY = 'hourly',
  DAILY = 'daily',
  WEEKLY = 'weekly',
  MONTHLY = 'monthly'
}

// 圖表狀態接口
export interface ChartState {
  isLoading: boolean
  hasError: boolean
  errorMessage?: string
  lastUpdate?: Date
  updateFrequency: UpdateFrequency
  isRealTime: boolean
}

// 圖表數據接口
export interface ChartDataPoint {
  x: number | string | Date
  y: number
  label?: string
  metadata?: Record<string, any>
}

// 圖表數據集接口
export interface ChartDataset {
  label: string
  data: ChartDataPoint[]
  backgroundColor?: string | string[]
  borderColor?: string | string[]
  borderWidth?: number
  pointRadius?: number
  pointHoverRadius?: number
  tension?: number
  fill?: boolean | string
}

// 完整的圖表配置接口
export interface ChartConfig {
  type: ChartType
  data: {
    labels: string[]
    datasets: ChartDataset[]
  }
  options: any
  theme?: ChartTheme
  responsive?: boolean
  maintainAspectRatio?: boolean
  animation?: any
  plugins?: any
}