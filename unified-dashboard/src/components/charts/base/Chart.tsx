import React, { useRef, useEffect, useCallback, forwardRef, useImperativeHandle } from 'react'
import { Chart as ChartJS, ChartConfiguration, ChartEvent, ChartTypeRegistry, Plugin } from 'chart.js'
import { Line, Bar, Pie, Doughnut, Radar, PolarArea, Scatter, Bubble } from 'react-chartjs-2'
import { ChartTheme, ChartExportOptions, chartUtils } from '../../../utils/charts'
import { cn } from '@/lib/utils'

// Register Chart.js components
import {
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ArcElement,
  RadialLinearScale,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ArcElement,
  RadialLinearScale
)

// Chart type mapping
const chartComponents = {
  line: Line,
  bar: Bar,
  pie: Pie,
  doughnut: Doughnut,
  radar: Radar,
  polarArea: PolarArea,
  scatter: Scatter,
  bubble: Bubble,
}

export interface ChartProps extends Omit<ChartConfiguration, 'type'> {
  type: keyof ChartTypeRegistry
  data: any
  options?: any
  theme?: ChartTheme
  responsive?: boolean
  maintainAspectRatio?: boolean
  width?: number
  height?: number
  className?: string
  loading?: boolean
  error?: string
  onDataPointClick?: (event: ChartEvent, elements: any[], dataset: any, index: number) => void
  onLegendClick?: (legendItem: any, legend: any) => void
  exportOptions?: ChartExportOptions
  showExportButton?: boolean
  animationDuration?: number
  redraw?: boolean
  plugins?: Plugin[]
}

export interface ChartRef {
  exportChart: (options?: ChartExportOptions) => Promise<void>
  getChartInstance: () => ChartJS | null
  update: () => void
  resetZoom: () => void
  zoomIn: () => void
  zoomOut: () => void
}

const Chart = forwardRef<ChartRef, ChartProps>(({
  type,
  data,
  options = {},
  theme,
  responsive = true,
  maintainAspectRatio = false,
  width,
  height,
  className,
  loading = false,
  error,
  onDataPointClick,
  onLegendClick,
  exportOptions,
  showExportButton = false,
  animationDuration = 1000,
  redraw = false,
  plugins = [],
  ...props
}, ref) => {
  const chartRef = useRef<ChartJS>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Apply theme to chart options
  const getThemedOptions = useCallback(() => {
    const defaultTheme = chartUtils.applyTheme(theme || {})

    return {
      responsive,
      maintainAspectRatio,
      animation: {
        duration: animationDuration,
        easing: 'easeInOutQuart',
        delay: (context: any) => {
          let delay = 0
          if (context.type === 'data' && context.mode === 'default') {
            delay = context.dataIndex * 50 + context.datasetIndex * 100
          }
          return delay
        },
      },
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            usePointStyle: true,
            padding: 20,
            color: defaultTheme.textColor,
            font: {
              size: 12,
            },
          },
          onClick: onLegendClick,
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: defaultTheme.primaryColor,
          borderWidth: 1,
          cornerRadius: 8,
          padding: 12,
          displayColors: true,
          callbacks: {
            label: (context: any) => {
              let label = context.dataset.label || ''
              if (label) {
                label += ': '
              }
              if (context.parsed.y !== null) {
                label += chartUtils.formatNumber(context.parsed.y)
              }
              return label
            },
          },
        },
        ...plugins,
      },
      scales: type !== 'pie' && type !== 'doughnut' && type !== 'radar' && type !== 'polarArea' ? {
        x: {
          grid: {
            color: defaultTheme.gridColor,
            drawBorder: false,
          },
          ticks: {
            color: defaultTheme.textColor,
            font: {
              size: 11,
            },
          },
        },
        y: {
          grid: {
            color: defaultTheme.gridColor,
            drawBorder: false,
          },
          ticks: {
            color: defaultTheme.textColor,
            font: {
              size: 11,
            },
          },
        },
      } : undefined,
      onClick: (event: ChartEvent, elements: any[]) => {
        if (elements.length > 0 && onDataPointClick) {
          const { datasetIndex, index } = elements[0]
          const dataset = data.datasets[datasetIndex]
          onDataPointClick(event, elements, dataset, index)
        }
      },
      ...options,
    }
  }, [theme, responsive, maintainAspectRatio, type, data, onDataPointClick, onLegendClick, plugins, options, animationDuration])

  // Apply theme to data
  const getThemedData = useCallback(() => {
    const defaultTheme = chartUtils.applyTheme(theme || {})

    return {
      ...data,
      datasets: data.datasets?.map((dataset: any) => ({
        ...dataset,
        backgroundColor: dataset.backgroundColor || defaultTheme.primaryColor,
        borderColor: dataset.borderColor || defaultTheme.primaryColor,
      })) || [],
    }
  }, [data, theme])

  // Chart ref methods
  useImperativeHandle(ref, () => ({
    exportChart: async (options?: ChartExportOptions) => {
      if (chartRef.current) {
        const canvas = chartRef.current.canvas
        await chartUtils.exportChart(canvas, options || exportOptions)
      }
    },
    getChartInstance: () => chartRef.current,
    update: () => {
      if (chartRef.current) {
        chartRef.current.update()
      }
    },
    resetZoom: () => {
      if (chartRef.current) {
        chartRef.current.resetZoom()
      }
    },
    zoomIn: () => {
      if (chartRef.current) {
        chartRef.current.zoom(1.1)
      }
    },
    zoomOut: () => {
      if (chartRef.current) {
        chartRef.current.zoom(0.9)
      }
    },
  }), [exportOptions])

  // Handle export button click
  const handleExport = useCallback(async () => {
    if (chartRef.current) {
      try {
        const canvas = chartRef.current.canvas
        await chartUtils.exportChart(canvas, exportOptions)
      } catch (error) {
        console.error('Export failed:', error)
      }
    }
  }, [exportOptions])

  // Update chart when data or options change
  useEffect(() => {
    if (chartRef.current && !redraw) {
      chartRef.current.update()
    }
  }, [getThemedData, getThemedOptions, redraw])

  const ChartComponent = chartComponents[type as keyof typeof chartComponents]

  if (!ChartComponent) {
    return (
      <div className="flex items-center justify-center h-full text-red-500">
        Unsupported chart type: {type}
      </div>
    )
  }

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            <span className="text-sm text-gray-600">Loading...</span>
          </div>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 bg-opacity-90 z-10">
          <div className="text-center">
            <div className="text-red-500 text-sm mb-2">Error loading chart</div>
            <div className="text-red-400 text-xs">{error}</div>
          </div>
        </div>
      )}

      {showExportButton && (
        <button
          onClick={handleExport}
          className="absolute top-2 right-2 z-20 px-3 py-1 text-xs bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Export
        </button>
      )}

      <div style={{ width, height }} className="w-full h-full">
        <ChartComponent
          ref={chartRef}
          data={getThemedData()}
          options={getThemedOptions()}
          {...props}
        />
      </div>
    </div>
  )
})

Chart.displayName = 'Chart'

export default Chart