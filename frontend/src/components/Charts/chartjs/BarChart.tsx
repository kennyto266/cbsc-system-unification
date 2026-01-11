import React, { useRef, useCallback } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Bar } from 'react-chartjs-2'
import type { ChartData, ChartOptions } from 'chart.js'
import { BaseChartProps } from '../../../types/chart'
import { getTheme, getChartJsDefaults } from '../../Charts/utils/chartThemes'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
)

// Extended props for BarChart
export interface BarChartProps extends Omit<BaseChartProps<'bar'>, 'type'> {
  // Orientation props
  horizontal?: boolean

  // Stacking props
  stacked?: boolean
  groupMode?: 'grouped' | 'stacked'

  // Style props
  barPercentage?: number
  categoryPercentage?: number
  borderWidth?: number
  borderRadius?: number

  // Value display props
  showValues?: boolean
  valuePosition?: 'top' | 'bottom' | 'inside' | 'outside'
  valueFormat?: Intl.NumberFormatOptions

  // Grid props
  showGrid?: boolean
  gridColor?: string

  // Animation props
  animationDuration?: number
}

const BarChart: React.FC<BarChartProps> = ({
  data,
  options = {},
  width,
  height,
  className = '',
  theme = 'light',
  onDataPointClick,
  onLegendClick,
  horizontal = false,
  stacked = false,
  groupMode = 'grouped',
  barPercentage = 0.8,
  categoryPercentage = 0.9,
  borderWidth = 1,
  borderRadius = 0,
  showValues = false,
  valuePosition = 'top',
  valueFormat,
  showGrid = true,
  gridColor,
  animationDuration = 300
}) => {
  const chartRef = useRef<ChartJS<'bar'>>(null)
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

  // Determine if stacking is enabled
  const isStacked = stacked || groupMode === 'stacked'

  // Default options with theme
  const defaultOptions: ChartOptions<'bar'> = {
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
          label: (context) => {
            let label = context.dataset.label || ''
            if (label) {
              label += ': '
            }
            if (context.parsed.y !== null) {
              const formatOptions = valueFormat || {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
              }
              label += new Intl.NumberFormat('en-US', formatOptions).format(context.parsed.y)
            }
            return label
          }
        }
      }
    },
    scales: {
      x: {
        stacked: isStacked,
        grid: {
          display: false,
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
        stacked: isStacked,
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
            const formatOptions = valueFormat || {
              minimumFractionDigits: 0,
              maximumFractionDigits: 2
            }
            return new Intl.NumberFormat('en-US', formatOptions).format(value as number)
          }
        },
        border: {
          color: currentTheme.borderColor
        }
      }
    },
    indexAxis: horizontal ? 'y' as const : 'x' as const
  }

  // Process datasets with default values
  const processedData = {
    ...data,
    datasets: data.datasets.map((dataset, index) => {
      // Handle both single color and color array
      const backgroundColor = Array.isArray(dataset.backgroundColor)
        ? dataset.backgroundColor
        : [dataset.backgroundColor || currentTheme.colors[index % currentTheme.colors.length]]

      const borderColor = Array.isArray(dataset.borderColor)
        ? dataset.borderColor
        : [dataset.borderColor || currentTheme.colors[index % currentTheme.colors.length]]

      return {
        ...dataset,
        backgroundColor,
        borderColor,
        borderWidth,
        borderRadius,
        barPercentage,
        categoryPercentage
      }
    })
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
      <Bar
        ref={chartRef}
        data={processedData}
        options={mergedOptions}
      />
    </div>
  )
}

export default BarChart