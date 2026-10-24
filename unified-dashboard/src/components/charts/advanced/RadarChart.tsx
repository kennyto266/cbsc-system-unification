import React, { useEffect, useRef, useMemo } from 'react'
import { Chart, registerables, RadialLinearScale } from 'chart.js'
import { BaseChartProps } from '../types/chart.types'

// Register Chart.js components
Chart.register(...registerables, RadialLinearScale)

export interface RadarDataPoint {
  label: string
  value: number
  max?: number
  benchmark?: number
}

export interface RadarDataset {
  label: string
  data: number[]
  backgroundColor?: string | string[]
  borderColor?: string
  borderWidth?: number
  pointBackgroundColor?: string
  pointBorderColor?: string
  pointRadius?: number
  pointHoverRadius?: number
  fill?: boolean
}

export interface RadarChartProps extends BaseChartProps {
  labels: string[]
  datasets: RadarDataset[]
  scales?: {
    r: {
      min?: number
      max?: number
      beginAtZero?: boolean
      ticks?: {
        stepSize?: number
        backdropColor?: string
        color?: string
      }
      grid?: {
        color?: string | string[]
        circular?: boolean
      }
      pointLabels?: {
        font?: {
          family?: string
          size?: number
          weight?: string
        }
        color?: string | string[]
      }
    }
  }
  showBenchmark?: boolean
  benchmarkData?: number[]
  benchmarkLabel?: string
  fillArea?: boolean
  startAngle?: number
  animationDuration?: number
  onDatasetClick?: (datasetIndex: number) => void
  onPointClick?: (datasetIndex: number, pointIndex: number, value: number) => void
}

export const RadarChart: React.FC<RadarChartProps> = ({
  labels,
  datasets,
  scales,
  showBenchmark = false,
  benchmarkData,
  benchmarkLabel = 'Benchmark',
  fillArea = true,
  startAngle = 0,
  animationDuration = 1000,
  width = 600,
  height = 600,
  className = '',
  theme = 'light',
  responsive = true,
  animation = true,
  onDatasetClick,
  onPointClick,
  dataTestId
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const chartRef = useRef<Chart<'radar'> | null>(null)

  // Theme colors
  const themeColors = useMemo(() => {
    return theme === 'dark'
      ? {
          grid: 'rgba(255, 255, 255, 0.1)',
          text: 'rgba(255, 255, 255, 0.8)',
          background: '#1f1f1f',
          primary: ['#00bcd4', '#4caf50', '#ff9800', '#e91e63', '#9c27b0']
        }
      : {
          grid: 'rgba(0, 0, 0, 0.1)',
          text: 'rgba(0, 0, 0, 0.8)',
          background: '#ffffff',
          primary: ['#2196f3', '#4caf50', '#ff9800', '#e91e63', '#9c27b0']
        }
  }, [theme])

  // Process datasets with theme colors
  const processedDatasets = useMemo(() => {
    const processed = datasets.map((dataset, index) => ({
      ...dataset,
      backgroundColor: dataset.backgroundColor || `${themeColors.primary[index % themeColors.primary.length]}33`,
      borderColor: dataset.borderColor || themeColors.primary[index % themeColors.primary.length],
      pointBackgroundColor: dataset.pointBackgroundColor || themeColors.primary[index % themeColors.primary.length],
      pointBorderColor: dataset.pointBorderColor || '#fff',
      borderWidth: dataset.borderWidth || 2,
      pointRadius: dataset.pointRadius || 4,
      pointHoverRadius: dataset.pointHoverRadius || 6,
      fill: fillArea
    }))

    // Add benchmark dataset if enabled
    if (showBenchmark && benchmarkData) {
      processed.push({
        label: benchmarkLabel,
        data: benchmarkData,
        backgroundColor: 'rgba(255, 99, 132, 0.1)',
        borderColor: 'rgba(255, 99, 132, 0.8)',
        borderWidth: 2,
        borderDash: [5, 5],
        pointRadius: 3,
        pointHoverRadius: 5,
        fill: false
      })
    }

    return processed
  }, [datasets, showBenchmark, benchmarkData, benchmarkLabel, fillArea, themeColors])

  // Chart configuration
  const chartConfig = useMemo(() => ({
    type: 'radar' as const,
    data: {
      labels,
      datasets: processedDatasets
    },
    options: {
      responsive,
      maintainAspectRatio: false,
      animation: animation ? {
        duration: animationDuration,
        easing: 'easeInOutQuart',
        animateRotate: true,
        animateScale: true
      } : false,
      elements: {
        line: {
          tension: 0.2
        }
      },
      scales: {
        r: {
          min: scales?.r?.min,
          max: scales?.r?.max,
          beginAtZero: scales?.r?.beginAtZero ?? true,
          angleLines: {
            color: themeColors.grid,
            borderDash: [5, 5]
          },
          grid: {
            color: themeColors.grid,
            circular: scales?.r?.grid?.circular ?? false
          },
          pointLabels: {
            font: {
              family: scales?.r?.pointLabels?.font?.family || 'Inter, sans-serif',
              size: scales?.r?.pointLabels?.font?.size || 12,
              weight: scales?.r?.pointLabels?.font?.weight || '500'
            },
            color: scales?.r?.pointLabels?.color || themeColors.text,
            padding: 15
          },
          ticks: {
            stepSize: scales?.r?.ticks?.stepSize,
            backdropColor: scales?.r?.ticks?.backdropColor || 'transparent',
            color: scales?.r?.ticks?.color || themeColors.text,
            font: {
              family: 'Inter, sans-serif',
              size: 10
            }
          }
        }
      },
      plugins: {
        legend: {
          position: 'top' as const,
          labels: {
            color: themeColors.text,
            font: {
              family: 'Inter, sans-serif',
              size: 12
            },
            padding: 20,
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          enabled: true,
          backgroundColor: theme === 'dark' ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.95)',
          titleColor: themeColors.text,
          bodyColor: themeColors.text,
          borderColor: themeColors.grid,
          borderWidth: 1,
          titleFont: {
            family: 'Inter, sans-serif',
            size: 14,
            weight: '600'
          },
          bodyFont: {
            family: 'Inter, sans-serif',
            size: 12
          },
          padding: 12,
          displayColors: true,
          callbacks: {
            label: (context: any) => {
              const datasetLabel = context.dataset.label || ''
              const value = context.raw
              const label = context.label || ''

              // Calculate percentage of max
              const maxValue = Math.max(...context.dataset.data)
              const percentage = ((value / maxValue) * 100).toFixed(1)

              return [
                `${datasetLabel}: ${value.toFixed(2)}`,
                `Percentage: ${percentage}%`
              ]
            },
            afterLabel: (context: any) => {
              // Show benchmark comparison if available
              if (showBenchmark && benchmarkData && context.datasetIndex < datasets.length) {
                const benchmark = benchmarkData[context.dataIndex]
                const actual = context.raw
                const diff = actual - benchmark
                const diffPercent = ((diff / benchmark) * 100).toFixed(1)

                return [
                  `Benchmark: ${benchmark.toFixed(2)}`,
                  `Difference: ${diff > 0 ? '+' : ''}${diff.toFixed(2)} (${diff > 0 ? '+' : ''}${diffPercent}%)`
                ]
              }
              return ''
            }
          }
        },
        datalabels: {
          display: false
        }
      },
      startAngle: startAngle
    },
    onClick: (event: any, elements: any[]) => {
        if (elements.length > 0) {
          const { datasetIndex, index } = elements[0]

          // Handle dataset click if clicking on legend area
          if (onDatasetClick && event.native.offsetX < 100) {
            onDatasetClick(datasetIndex)
            return
          }

          // Handle point click
          if (onPointClick) {
            const value = processedDatasets[datasetIndex].data[index]
            onPointClick(datasetIndex, index, value)
          }
        }
      },
    interaction: {
      mode: 'point' as const,
      intersect: false
    }
  }), [labels, processedDatasets, scales, themeColors, responsive, animation, animationDuration, showBenchmark, benchmarkData, datasets, onDatasetClick, onPointClick])

  // Initialize chart
  useEffect(() => {
    if (!canvasRef.current) return

    const chart = new Chart(canvasRef.current, chartConfig)
    chartRef.current = chart

    return () => {
      chart.destroy()
    }
  }, [chartConfig])

  return (
    <div
      className={`radar-chart-container ${className}`}
      data-testid={dataTestId}
      style={{ width, height }}
    >
      <canvas ref={canvasRef} />
    </div>
  )
}

export default RadarChart