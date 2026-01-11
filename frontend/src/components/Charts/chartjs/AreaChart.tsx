import React, { useRef, useCallback, useMemo } from 'react'
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

// Extended props for AreaChart
export interface AreaChartProps extends Omit<BaseChartProps<'line'>, 'type'> {
  // Data props
  timeSeries?: boolean
  stacked?: boolean

  // Style props
  tension?: number
  fillOpacity?: number
  pointRadius?: number
  pointHoverRadius?: number
  showLine?: boolean
  lineWidth?: number

  // Gradient props
  useGradient?: boolean
  gradientDirection?: 'vertical' | 'horizontal'

  // Grid props
  showGrid?: boolean
  gridColor?: string

  // Animation props
  animationDuration?: number
}

const AreaChart: React.FC<AreaChartProps> = ({
  data,
  options = {},
  width,
  height,
  className = '',
  theme = 'light',
  onDataPointClick,
  onLegendClick,
  timeSeries = false,
  stacked = false,
  tension = 0.4,
  fillOpacity = 0.2,
  pointRadius = 0,
  pointHoverRadius = 5,
  showLine = true,
  lineWidth = 2,
  useGradient = true,
  gradientDirection = 'vertical',
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

  // Create gradient fills
  const createGradient = useCallback((ctx: CanvasRenderingContext2D, color: string) => {
    if (!useGradient) return color

    const gradient = gradientDirection === 'vertical'
      ? ctx.createLinearGradient(0, 0, 0, ctx.canvas.height)
      : ctx.createLinearGradient(0, 0, ctx.canvas.width, 0)

    // Parse the base color
    const hexColor = color.replace('#', '')
    const r = parseInt(hexColor.substr(0, 2), 16)
    const g = parseInt(hexColor.substr(2, 2), 16)
    const b = parseInt(hexColor.substr(4, 2), 16)

    gradient.addColorStop(0, `${r},${g},${b},${fillOpacity})`)
    gradient.addColorStop(1, `${r},${g},${b},0.0)`)

    return gradient
  }, [useGradient, fillOpacity, gradientDirection])

  // Process datasets with gradients and fills
  const processedData = useMemo(() => {
    // Create a temporary canvas to generate gradients
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    if (!ctx) return data

    return {
      ...data,
      datasets: data.datasets.map((dataset, index) => {
        const baseColor = dataset.borderColor || currentTheme.colors[index % currentTheme.colors.length]
        const backgroundColor = useGradient
          ? createGradient(ctx, baseColor)
          : `${baseColor}${Math.round(fillOpacity * 255).toString(16).padStart(2, '0')}`

        return {
          ...dataset,
          fill: {
            target: stacked ? 'origin' : 'origin',
            above: backgroundColor,
            below: backgroundColor
          },
          tension,
          pointRadius,
          pointHoverRadius,
          borderWidth: showLine ? lineWidth : 0,
          borderColor: showLine ? baseColor : 'transparent',
          pointBackgroundColor: baseColor,
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: baseColor,
          // Stacking configuration
          ...(stacked && {
            stack: 'stack0'
          })
        }
      })
    }
  }, [data, currentTheme, stacked, tension, pointRadius, pointHoverRadius, showLine, lineWidth, useGradient, fillOpacity, createGradient])

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
        stacked: true,
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
        stacked: true,
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
    },
    elements: {
      line: {
        tension,
        borderWidth: lineWidth
      },
      point: {
        radius: pointRadius,
        hoverRadius: pointHoverRadius
      }
    }
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
      />
    </div>
  )
}

export default AreaChart