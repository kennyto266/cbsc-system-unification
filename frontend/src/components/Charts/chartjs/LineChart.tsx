import React, { useRef, useEffect, useCallback, useMemo } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TimeScale
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import type { ChartData, ChartOptions } from 'chart.js'
import { BaseChartProps } from '../../../types/chart'
import { getTheme, getChartJsDefaults } from '../../Charts/utils/chartThemes'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TimeScale
)

// Extended props for LineChart
export interface LineChartProps extends Omit<BaseChartProps<'line'>, 'type'> {
  // Data props
  timeSeries?: boolean
  areaFill?: boolean
  stepped?: 'before' | 'after' | 'middle' | boolean

  // Style props
  tension?: number
  pointRadius?: number
  pointHoverRadius?: number
  borderWidth?: number

  // Grid props
  showGrid?: boolean
  gridColor?: string

  // Animation props
  animationDuration?: number
}

const LineChart: React.FC<LineChartProps> = ({
  data,
  options = {},
  width,
  height,
  className = '',
  theme = 'light',
  tabIndex,
  onDataPointClick,
  onLegendClick,
  timeSeries = false,
  areaFill = false,
  stepped = false,
  tension = 0.4,
  pointRadius = 3,
  pointHoverRadius = 5,
  borderWidth = 2,
  showGrid = true,
  gridColor,
  animationDuration = 300
}) => {
  const chartRef = useRef<ChartJS<'line'>>(null)
  const currentTheme = getTheme(theme)

  // Handle click events
  const handleClick = useCallback((event: any, elements: any[]) => {
    if (elements.length > 0 && onDataPointClick) {
      const { datasetIndex, index } = elements[0]
      const dataset = data.datasets[datasetIndex]
      const point = {
        dataset,
        value: dataset.data[index],
        label: data.labels?.[index],
        datasetIndex,
        index
      }
      onDataPointClick(point, elements[0])
    }
  }, [data, onDataPointClick])

  // Default options with theme
  const defaultOptions: ChartOptions<'line'> = {
    ...getChartJsDefaults(currentTheme),
    animation: {
      duration: animationDuration,
      easing: 'easeInOutQuad'
    },
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false
    },
    onClick: handleClick,
    plugins: {
      ...getChartJsDefaults(currentTheme).plugins,
      legend: {
        ...getChartJsDefaults(currentTheme).plugins.legend,
        onClick: (e, legendItem, legend) => {
          if (onLegendClick) {
            onLegendClick(legendItem, legend)
          } else {
            // Default toggle behavior
            const index = legendItem.datasetIndex
            const chart = legend.chart
            const meta = chart.getDatasetMeta(index)
            meta.hidden = meta.hidden === null ? !chart.data.datasets[index].hidden : null
            chart.update()
          }
        }
      },
      tooltip: {
        ...getChartJsDefaults(currentTheme).plugins.tooltip,
        callbacks: {
          title: (context) => {
            if (timeSeries && context[0].label) {
              return new Date(context[0].label).toLocaleString()
            }
            return context[0].label
          },
          label: (context) => {
            let label = context.dataset.label || ''
            if (label) {
              label += ': '
            }
            if (context.parsed.y !== null) {
              label += new Intl.NumberFormat('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
              }).format(context.parsed.y)
            }
            return label
          }
        }
      }
    },
    scales: {
      x: {
        type: timeSeries ? 'time' : 'category',
        time: timeSeries ? {
          displayFormats: {
            quarter: 'MMM yyyy',
            month: 'MMM yyyy',
            week: 'MMM dd',
            day: 'MMM dd',
            hour: 'HH:mm'
          }
        } : undefined,
        grid: {
          display: showGrid,
          color: gridColor || currentTheme.gridColor,
          borderDash: [2, 2]
        },
        ticks: {
          color: currentTheme.textColor,
          font: {
            size: currentTheme.fontSize,
            family: currentTheme.fontFamily
          }
        },
        border: {
          color: currentTheme.borderColor
        }
      },
      y: {
        grid: {
          display: showGrid,
          color: gridColor || currentTheme.gridColor,
          borderDash: [2, 2]
        },
        ticks: {
          color: currentTheme.textColor,
          font: {
            size: currentTheme.fontSize,
            family: currentTheme.fontFamily
          },
          callback: (value) => {
            return new Intl.NumberFormat('en-US', {
              minimumFractionDigits: 0,
              maximumFractionDigits: 2
            }).format(value as number)
          }
        },
        border: {
          color: currentTheme.borderColor
        }
      }
    }
  }

  // Process datasets with default values
  const processedData = {
    ...data,
    datasets: data.datasets.map((dataset, index) => ({
      ...dataset,
      fill: areaFill,
      tension,
      stepped,
      pointRadius,
      pointHoverRadius,
      borderWidth,
      borderColor: dataset.borderColor || currentTheme.colors[index % currentTheme.colors.length],
      backgroundColor: areaFill
        ? (dataset.backgroundColor || currentTheme.colors[index % currentTheme.colors.length] + '20')
        : dataset.backgroundColor,
      pointBackgroundColor: dataset.pointBackgroundColor || currentTheme.colors[index % currentTheme.colors.length],
      pointBorderColor: dataset.pointBorderColor || '#fff',
      pointHoverBackgroundColor: dataset.pointHoverBackgroundColor || '#fff',
      pointHoverBorderColor: dataset.pointHoverBorderColor || currentTheme.colors[index % currentTheme.colors.length]
    }))
  }

  // Merge options
  const mergedOptions = {
    ...defaultOptions,
    ...options,
    plugins: {
      ...defaultOptions.plugins,
      ...options.plugins
    },
    scales: {
      ...defaultOptions.scales,
      ...options.scales
    }
  }

  return (
    <div className={`w-full ${className}`} style={{ width, height }}>
      <Line
        ref={chartRef}
        data={processedData}
        options={mergedOptions}
        {...(tabIndex !== undefined && { tabIndex })}
      />
    </div>
  )
}

export default LineChart