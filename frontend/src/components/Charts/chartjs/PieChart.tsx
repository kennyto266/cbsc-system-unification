import React, { useRef, useCallback } from 'react'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js'
import { Pie, Doughnut } from 'react-chartjs-2'
import type { ChartData, ChartOptions } from 'chart.js'
import { BaseChartProps } from '../../../types/chart'
import { getTheme, getChartJsDefaults } from '../../Charts/utils/chartThemes'

// Register Chart.js components
ChartJS.register(
  ArcElement,
  Tooltip,
  Legend
)

// Extended props for PieChart
export interface PieChartProps extends Omit<BaseChartProps<'pie'>, 'type'> {
  // Chart type
  doughnut?: boolean

  // Display props
  showPercentage?: boolean
  percentagePosition?: 'label' | 'tooltip' | 'both'

  // Legend props
  legendPosition?: 'top' | 'bottom' | 'left' | 'right'

  // Style props
  borderWidth?: number
  hoverOffset?: number
  spacing?: number

  // Animation props
  animationDuration?: number
  animateRotate?: boolean
  animateScale?: boolean

  // Center text for doughnut charts
  centerText?: {
    text: string
    subtext?: string
    fontSize?: number
    subFontSize?: number
  }
}

const PieChart: React.FC<PieChartProps> = ({
  data,
  options = {},
  width,
  height,
  className = '',
  theme = 'light',
  onDataPointClick,
  onLegendClick,
  doughnut = false,
  showPercentage = true,
  percentagePosition = 'both',
  legendPosition = 'right',
  borderWidth = 2,
  hoverOffset = 4,
  spacing = 0,
  animationDuration = 300,
  animateRotate = true,
  animateScale = false,
  centerText
}) => {
  const chartRef = useRef<ChartJS<'pie' | 'doughnut'>>(null)
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

  // Calculate total for percentage calculations
  const total = data.datasets[0]?.data.reduce((sum, val) => sum + val, 0) || 0

  // Default options with theme
  const defaultOptions: ChartOptions<'pie' | 'doughnut'> = {
    ...getChartJsDefaults(currentTheme),
    animation: {
      animateRotate,
      animateScale,
      duration: animationDuration,
      easing: 'easeInOutQuad'
    },
    responsive: true,
    maintainAspectRatio: false,
    onClick: handleClick,
    plugins: {
      ...getChartJsDefaults(currentTheme).plugins,
      legend: {
        ...getChartJsDefaults(currentTheme).plugins.legend,
        display: true,
        position: legendPosition,
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
        },
        labels: {
          ...getChartJsDefaults(currentTheme).plugins.legend.labels,
          generateLabels: (chart) => {
            const dataset = chart.data.datasets[0]
            return (chart.data.labels || []).map((label, i) => {
              const value = dataset.data[i]
              const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0'
              const displayLabel = showPercentage && (percentagePosition === 'label' || percentagePosition === 'both')
                ? `${label} (${percentage}%)`
                : label

              return {
                text: displayLabel,
                fillStyle: dataset.backgroundColor[i] as string,
                strokeStyle: dataset.borderColor[i] as string,
                lineWidth: dataset.borderWidth,
                hidden: false,
                index: i
              }
            })
          }
        }
      },
      tooltip: {
        ...getChartJsDefaults(currentTheme).plugins.tooltip,
        callbacks: {
          label: (context) => {
            let label = context.label || ''
            if (label) {
              label += ': '
            }

            const value = context.parsed
            label += new Intl.NumberFormat('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2
            }).format(value)

            if (showPercentage && (percentagePosition === 'tooltip' || percentagePosition === 'both')) {
              const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0'
              label += ` (${percentage}%)`
            }

            return label
          }
        }
      },
      // Center text plugin for doughnut charts
      ...(doughnut && centerText && {
        beforeDraw: (chart) => {
          const ctx = chart.ctx
          const width = chart.width
          const height = chart.height

          ctx.restore()
          const mainFontSize = centerText.fontSize || Math.round(height / 16)
          const subFontSize = centerText.subFontSize || Math.round(height / 24)

          ctx.font = `${mainFontSize}px ${currentTheme.fontFamily || 'sans-serif'}`
          ctx.textBaseline = 'middle'
          ctx.textAlign = 'center'
          ctx.fillStyle = currentTheme.textColor

          const text = centerText.text
          const textY = height / 2 - (centerText.subtext ? subFontSize / 2 : 0)
          ctx.fillText(text, width / 2, textY)

          if (centerText.subtext) {
            ctx.font = `${subFontSize}px ${currentTheme.fontFamily || 'sans-serif'}`
            ctx.fillStyle = currentTheme.textColor + '80'
            const subtext = centerText.subtext
            const subtextY = height / 2 + mainFontSize / 2
            ctx.fillText(subtext, width / 2, subtextY)
          }

          ctx.save()
        }
      })
    },
    spacing,
    cutout: doughnut ? '50%' : '0%'
  }

  // Process datasets with default values
  const processedData = {
    ...data,
    datasets: data.datasets.map((dataset, datasetIndex) => ({
      ...dataset,
      borderWidth,
      hoverOffset,
      borderColor: dataset.borderColor || (theme === 'dark' ? '#1f2937' : '#ffffff'),
      // Apply theme colors if not provided
      backgroundColor: dataset.backgroundColor || data.labels?.map((_, i) =>
        currentTheme.colors[i % currentTheme.colors.length]
      ) || currentTheme.colors
    }))
  }

  // Merge options
  const mergedOptions = {
    ...defaultOptions,
    ...options,
    plugins: {
      ...defaultOptions.plugins,
      ...options.plugins
    }
  }

  const ChartComponent = doughnut ? Doughnut : Pie

  return (
    <div className={`w-full ${className}`} style={{ width, height }}>
      <ChartComponent
        ref={chartRef}
        data={processedData}
        options={mergedOptions}
      />
    </div>
  )
}

export default PieChart