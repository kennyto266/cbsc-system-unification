import React, { useEffect, useRef, useCallback, useMemo } from 'react'
import { Chart, registerables } from 'chart.js'
import { BaseChartProps, ChartInteractionState, ChartEventHandlers } from '../types/chart.types'

// Register Chart.js components
Chart.register(...registerables)

// Extended types for scatter plot
export interface ScatterDataPoint {
  x: number
  y: number
  z?: number // For bubble size
  label?: string
  category?: string
  color?: string
}

export interface ScatterDataset {
  label: string
  data: ScatterDataPoint[]
  backgroundColor?: string | string[]
  borderColor?: string | string[]
  borderWidth?: number
  pointRadius?: number | ((context: any) => number)
  pointHoverRadius?: number
  showLine?: boolean
  fill?: boolean
  tension?: number
}

export interface ScatterPlotProps extends BaseChartProps {
  datasets: ScatterDataset[]
  xAxis: {
    label: string
    min?: number
    max?: number
    scale?: 'linear' | 'logarithmic'
    format?: (value: number) => string
  }
  yAxis: {
    label: string
    min?: number
    max?: number
    scale?: 'linear' | 'logarithmic'
    format?: (value: number) => string
  }
  showRegression?: boolean
  regressionType?: 'linear' | 'polynomial' | 'exponential'
  clustering?: {
    enabled: boolean
    algorithm?: 'kmeans' | 'dbscan'
    clusters?: number
  }
  annotations?: {
    type: 'line' | 'box' | 'point'
    x?: number
    y?: number
    x2?: number
    y2?: number
    label?: string
    color?: string
  }[]
  onPointClick?: (point: ScatterDataPoint, dataset: ScatterDataset) => void
  onPointHover?: (point: ScatterDataPoint, dataset: ScatterDataset) => void
  eventHandlers?: ChartEventHandlers
}

// Regression line calculation
const calculateRegression = (data: ScatterDataPoint[], type: string) => {
  const validPoints = data.filter(p => !isNaN(p.x) && !isNaN(p.y))
  if (validPoints.length < 2) return null

  const n = validPoints.length
  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0

  validPoints.forEach(point => {
    sumX += point.x
    sumY += point.y
    sumXY += point.x * point.y
    sumX2 += point.x * point.x
    sumY2 += point.y * point.y
  })

  switch (type) {
    case 'linear':
      const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX)
      const intercept = (sumY - slope * sumX) / n
      return { slope, intercept, r2: calculateR2(validPoints, slope, intercept) }

    default:
      return null
  }
}

const calculateR2 = (data: ScatterDataPoint[], slope: number, intercept: number) => {
  const mean = data.reduce((sum, p) => sum + p.y, 0) / data.length
  const totalSumSquares = data.reduce((sum, p) => sum + Math.pow(p.y - mean, 2), 0)
  const residualSumSquares = data.reduce((sum, p) => {
    const predicted = slope * p.x + intercept
    return sum + Math.pow(p.y - predicted, 2)
  }, 0)
  return 1 - (residualSumSquares / totalSumSquares)
}

// Simple K-means clustering
const performClustering = (data: ScatterDataPoint[], k: number) => {
  const clusters = Array.from({ length: k }, (_, i) => ({
    center: data[i * Math.floor(data.length / k)] || data[0],
    points: [] as ScatterDataPoint[]
  }))

  // Assign points to nearest cluster
  data.forEach(point => {
    let minDist = Infinity
    let nearestCluster = 0

    clusters.forEach((cluster, i) => {
      const dist = Math.sqrt(
        Math.pow(point.x - cluster.center.x, 2) +
        Math.pow(point.y - cluster.center.y, 2)
      )
      if (dist < minDist) {
        minDist = dist
        nearestCluster = i
      }
    })

    clusters[nearestCluster].points.push(point)
  })

  // Update cluster centers
  clusters.forEach(cluster => {
    if (cluster.points.length > 0) {
      cluster.center = {
        x: cluster.points.reduce((sum, p) => sum + p.x, 0) / cluster.points.length,
        y: cluster.points.reduce((sum, p) => sum + p.y, 0) / cluster.points.length
      }
    }
  })

  return clusters
}

export const ScatterPlot: React.FC<ScatterPlotProps> = ({
  datasets,
  xAxis,
  yAxis,
  showRegression = false,
  regressionType = 'linear',
  clustering,
  annotations = [],
  width = 800,
  height = 400,
  className = '',
  theme = 'light',
  responsive = true,
  animation = true,
  onPointClick,
  onPointHover,
  eventHandlers,
  dataTestId
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const chartRef = useRef<Chart<'scatter'> | null>(null)
  const interactionStateRef = useRef<ChartInteractionState>({
    isHovering: false
  })

  // Process data with clustering if enabled
  const processedDatasets = useMemo(() => {
    if (!clustering?.enabled) return datasets

    return datasets.map(dataset => {
      const clusters = performClustering(dataset.data, clustering.clusters || 3)
      const clusteredData = clusters.flatMap((cluster, i) =>
        cluster.points.map(point => ({
          ...point,
          category: `Cluster ${i + 1}`
        }))
      )

      return {
        ...dataset,
        data: clusteredData
      }
    })
  }, [datasets, clustering])

  // Chart configuration
  const chartConfig = useMemo(() => {
    const themeColors = theme === 'dark'
      ? {
          grid: 'rgba(255, 255, 255, 0.1)',
          text: 'rgba(255, 255, 255, 0.8)',
          background: '#1f1f1f'
        }
      : {
          grid: 'rgba(0, 0, 0, 0.1)',
          text: 'rgba(0, 0, 0, 0.8)',
          background: '#ffffff'
        }

    return {
      type: 'scatter' as const,
      data: {
        datasets: processedDatasets.map(dataset => ({
          ...dataset,
          backgroundColor: dataset.backgroundColor ||
            (clustering?.enabled
              ? ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
              : 'rgba(54, 162, 235, 0.6)'),
          borderColor: dataset.borderColor ||
            (clustering?.enabled
              ? ['#FF5252', '#26A69A', '#2196F3', '#FF7043', '#66BB6A']
              : 'rgba(54, 162, 235, 1)')
        }))
      },
      options: {
        responsive,
        maintainAspectRatio: false,
        animation: animation ? {
          duration: 1000,
          easing: 'easeInOutQuart'
        } : false,
        interaction: {
          intersect: false,
          mode: 'point'
        },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              color: themeColors.text,
              font: {
                family: 'Inter, sans-serif',
                size: 12
              }
            }
          },
          tooltip: {
            enabled: true,
            backgroundColor: theme === 'dark' ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.9)',
            titleColor: themeColors.text,
            bodyColor: themeColors.text,
            borderColor: themeColors.grid,
            borderWidth: 1,
            callbacks: {
              label: (context: any) => {
                const point = context.raw as ScatterDataPoint
                const labels = [
                  `${xAxis.label}: ${xAxis.format ? xAxis.format(point.x) : point.x}`,
                  `${yAxis.label}: ${yAxis.format ? yAxis.format(point.y) : point.y}`
                ]
                if (point.z) labels.push(`Size: ${point.z}`)
                if (point.label) labels.push(point.label)
                if (point.category) labels.push(`Category: ${point.category}`)
                return labels
              }
            }
          },
          annotation: {
            annotations: annotations.reduce((acc, ann, index) => {
              acc[`annotation_${index}`] = {
                type: ann.type,
                xMin: ann.x,
                xMax: ann.x2 || ann.x,
                yMin: ann.y,
                yMax: ann.y2 || ann.y,
                backgroundColor: ann.color || 'rgba(255, 99, 132, 0.25)',
                borderColor: ann.color || 'rgb(255, 99, 132)',
                borderWidth: 2,
                label: {
                  enabled: !!ann.label,
                  content: ann.label,
                  position: 'center'
                }
              }
              return acc
            }, {} as any)
          }
        },
        scales: {
          x: {
            type: xAxis.scale || 'linear',
            min: xAxis.min,
            max: xAxis.max,
            title: {
              display: true,
              text: xAxis.label,
              color: themeColors.text,
              font: {
                family: 'Inter, sans-serif',
                size: 14,
                weight: '500'
              }
            },
            grid: {
              color: themeColors.grid,
              drawBorder: false
            },
            ticks: {
              color: themeColors.text,
              font: {
                family: 'Inter, sans-serif',
                size: 11
              },
              callback: xAxis.format
            }
          },
          y: {
            type: yAxis.scale || 'linear',
            min: yAxis.min,
            max: yAxis.max,
            title: {
              display: true,
              text: yAxis.label,
              color: themeColors.text,
              font: {
                family: 'Inter, sans-serif',
                size: 14,
                weight: '500'
              }
            },
            grid: {
              color: themeColors.grid,
              drawBorder: false
            },
            ticks: {
              color: themeColors.text,
              font: {
                family: 'Inter, sans-serif',
                size: 11
              },
              callback: yAxis.format
            }
          }
        },
        onClick: (event, elements) => {
          if (elements.length > 0 && onPointClick) {
            const datasetIndex = elements[0].datasetIndex
            const index = elements[0].index
            const dataset = processedDatasets[datasetIndex]
            const point = dataset.data[index]
            onPointClick(point, dataset)
          }
        },
        onHover: (event, elements) => {
          interactionStateRef.current.isHovering = elements.length > 0
          if (elements.length > 0 && onPointHover) {
            const datasetIndex = elements[0].datasetIndex
            const index = elements[0].index
            const dataset = processedDatasets[datasetIndex]
            const point = dataset.data[index]
            onPointHover(point, dataset)
          }
        }
      }
    }
  }, [processedDatasets, xAxis, yAxis, theme, responsive, animation, annotations, onPointClick, onPointHover, clustering])

  // Add regression lines if enabled
  useEffect(() => {
    if (!chartRef.current || !showRegression) return

    const chart = chartRef.current
    const regressionDatasets = processedDatasets.map(dataset => {
      const regression = calculateRegression(dataset.data, regressionType)
      if (!regression) return null

      const xMin = Math.min(...dataset.data.map(d => d.x))
      const xMax = Math.max(...dataset.data.map(d => d.x))

      return {
        label: `${dataset.label} - Regression (R² = ${regression.r2.toFixed(3)})`,
        data: [
          { x: xMin, y: regression.slope * xMin + regression.intercept },
          { x: xMax, y: regression.slope * xMax + regression.intercept }
        ],
        type: 'line' as const,
        borderColor: dataset.borderColor || 'rgba(255, 99, 132, 0.8)',
        borderWidth: 2,
        borderDash: [5, 5],
        fill: false,
        pointRadius: 0,
        pointHoverRadius: 0
      }
    }).filter(Boolean) as any[]

    chart.data.datasets = [...chart.data.datasets, ...regressionDatasets]
    chart.update('none')
  }, [showRegression, regressionType, processedDatasets])

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
      className={`scatter-plot-container ${className}`}
      data-testid={dataTestId}
      style={{ width, height }}
    >
      <canvas ref={canvasRef} />
    </div>
  )
}

export default ScatterPlot