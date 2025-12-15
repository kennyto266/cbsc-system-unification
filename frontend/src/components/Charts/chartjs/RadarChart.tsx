import React, { useRef, useCallback } from 'react'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Radar } from 'react-chartjs-2'
import type { ChartData, ChartOptions } from 'chart.js'
import { BaseChartProps } from '../../../types/chart'
import { getTheme, getChartJsDefaults } from '../../Charts/utils/chartThemes'

// Register Chart.js components
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Title,
  Tooltip,
  Legend
)

// Extended props for RadarChart
export interface RadarChartProps extends Omit<BaseChartProps<'radar'>, 'type'> {
  // Style props
  fillArea?: boolean
  fillOpacity?: number
  pointRadius?: number
  pointHoverRadius?: number
  lineWidth?: number
  tension?: number

  // Scale props
  min?: number
  max?: number
  ticks?: {
    stepSize?: number
    callback?: (value: number) => string
  }

  // Grid props
  showGrid?: boolean
  gridColor?: string
  angleLines?: boolean

  // Animation props
  animationDuration?: number
}

const RadarChart: React.FC<RadarChartProps> = ({
  data,
  options = {},
  width,
  height,
  className = '',
  theme = 'light',
  onDataPointClick,
  onLegendClick,
  fillArea = true,
  fillOpacity = 0.2,
  pointRadius = 3,
  pointHoverRadius = 5,
  lineWidth = 2,
  tension = 0.1,
  min,
  max,
  ticks,
  showGrid = true,
  gridColor,
  angleLines = true,
  animationDuration = 300
}) => {
  const chartRef = useRef<ChartJS<'radar'>>(null)
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

  // Process datasets with default values
  const processedData = {
    ...data,
    datasets: data.datasets.map((dataset, index) => {
      const baseColor = dataset.borderColor || currentTheme.colors[index % currentTheme.colors.length]

      return {
        ...dataset,
        fill: fillArea,
        tension,
        pointRadius,
        pointHoverRadius,
        borderWidth: lineWidth,
        borderColor: baseColor,
        backgroundColor: fillArea
          ? `${baseColor}${Math.round(fillOpacity * 255).toString(16).padStart(2, '0')}`
          : 'transparent',
        pointBackgroundColor: baseColor,
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: baseColor
      }
    })
  }

  // Default options with theme
  const defaultOptions: ChartOptions<'radar'> = {
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
            if (context.parsed.r !== null) {
              label += new Intl.NumberFormat('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
              }).format(context.parsed.r)
            }
            return label
          }
        }
      }
    },
    scales: {
      r: {
        min,
        max,
        grid: {
          display: showGrid,
          color: gridColor || currentTheme.gridColor,
          borderDash: [2, 2]
        },
        angleLines: {
          display: angleLines,
          color: gridColor || currentTheme.gridColor,
          borderDash: [2, 2]
        },
        pointLabels: {
          color: currentTheme.textColor,
          font: {
            size: currentTheme.fontSize,
            family: currentTheme.fontFamily
          }
        },
        ticks: {
          color: currentTheme.textColor,
          font: {
            size: currentTheme.fontSize,
            family: currentTheme.fontFamily
          },
          backdropColor: 'transparent',
          stepSize: ticks?.stepSize,
          callback: ticks?.callback || ((value) => {
            return new Intl.NumberFormat('en-US').format(value as number)
          })
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
      r: {
        ...defaultOptions.scales?.r,
        ...options.scales?.r
      }
    }
  }

  return (
    <div className={`w-full ${className}`} style={{ width, height }}>
      <Radar
        ref={chartRef}
        data={processedData}
        options={mergedOptions}
      />
    </div>
  )
}

export default RadarChart