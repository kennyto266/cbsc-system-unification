/**
 * Chart Utilities
 * Common utilities for chart operations
 */

import { ChartData, ChartOptions } from 'chart.js'

// Color palettes
export const COLORS = {
  primary: '#1890ff',
  success: '#52c41a',
  warning: '#faad14',
  danger: '#f5222d',
  info: '#13c2c2',

  // Extended palette
  blue: '#1890ff',
  cyan: '#13c2c2',
  teal: '#13c2c2',
  green: '#52c41a',
  magenta: '#eb2f96',
  red: '#f5222d',
  orange: '#fa8c16',
  yellow: '#fadb14',
  volcano: '#fa541c',
  gold: '#faad14',
  lime: '#a0d911',
  purple: '#722ed1',
  antdesign: '#1890ff',

  // Gradients
  gradients: {
    blue: ['#1890ff', '#096dd9'],
    green: ['#52c41a', '#389e0d'],
    red: ['#f5222d', '#cf1322'],
    orange: ['#fa8c16', '#d46b08'],
    purple: ['#722ed1', '#531dab'],
  },

  // Opacity variants
  withOpacity: (color: string, opacity: number): string => {
    const hex = color.replace('#', '')
    const r = parseInt(hex.substring(0, 2), 16)
    const g = parseInt(hex.substring(2, 4), 16)
    const b = parseInt(hex.substring(4, 6), 16)
    return `rgba(${r}, ${g}, ${b}, ${opacity})`
  }
}

// Chart themes
export const CHART_THEMES = {
  light: {
    background: '#ffffff',
    text: '#000000',
    grid: '#e8e8e8',
  },
  dark: {
    background: '#1f1f1f',
    text: '#ffffff',
    grid: '#434343',
  },
}

// Default chart options
export const DEFAULT_CHART_OPTIONS: Partial<ChartOptions> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top' as const,
    },
    tooltip: {
      enabled: true,
      mode: 'index' as const,
      intersect: false,
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
    },
    y: {
      beginAtZero: true,
    },
  },
}

// Color generator for datasets
export const generateColors = (count: number, baseColor?: string): string[] => {
  if (baseColor) {
    // Generate shades of base color
    return Array.from({ length: count }, (_, i) => {
      const opacity = 1 - (i * 0.7 / count)
      return COLORS.withOpacity(baseColor, opacity)
    })
  }

  // Use predefined colors
  const colorPalette = [
    COLORS.blue,
    COLORS.green,
    COLORS.orange,
    COLORS.red,
    COLORS.purple,
    COLORS.cyan,
    COLORS.yellow,
    COLORS.magenta,
  ]

  return Array.from({ length: count }, (_, i) => colorPalette[i % colorPalette.length])
}

// Format chart data
export const formatChartData = (
  labels: string[],
  datasets: Array<{
    label: string
    data: number[]
    color?: string
  }>
): ChartData => {
  return {
    labels,
    datasets: datasets.map((dataset, index) => ({
      label: dataset.label,
      data: dataset.data,
      backgroundColor: dataset.color || generateColors(1)[index],
      borderColor: dataset.color || generateColors(1)[index],
      borderWidth: 2,
      tension: 0.4,
    })),
  }
}

// Calculate min/max for axis
export const calculateAxisRange = (data: number[]): { min: number; max: number } => {
  const min = Math.min(...data)
  const max = Math.max(...data)
  const padding = (max - min) * 0.1

  return {
    min: min - padding,
    max: max + padding,
  }
}

// Format large numbers
export const formatNumber = (num: number, decimals: number = 2): string => {
  if (num >= 1e9) return `${(num / 1e9).toFixed(decimals)}B`
  if (num >= 1e6) return `${(num / 1e6).toFixed(decimals)}M`
  if (num >= 1e3) return `${(num / 1e3).toFixed(decimals)}K`
  return num.toFixed(decimals)
}

// Date formatting
export const formatDate = (date: Date | string, format: 'short' | 'long' = 'short'): string => {
  const d = typeof date === 'string' ? new Date(date) : date

  if (format === 'short') {
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

// Export chart as image
export const exportChart = async (
  canvas: HTMLCanvasElement,
  filename: string = 'chart.png'
): Promise<void> => {
  const link = document.createElement('a')
  link.download = filename
  link.href = canvas.toDataURL('image/png')
  link.click()
}

// Debounce function for chart updates
export const debounceChartUpdate = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout | null = null

  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

// Merge chart options
export const mergeChartOptions = (
  defaultOptions: ChartOptions,
  customOptions?: Partial<ChartOptions>
): ChartOptions => {
  return {
    ...defaultOptions,
    ...customOptions,
    plugins: {
      ...defaultOptions.plugins,
      ...customOptions?.plugins,
    },
    scales: {
      ...defaultOptions.scales,
      ...customOptions?.scales,
    },
  }
}
