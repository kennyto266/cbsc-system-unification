import React, { useMemo, useRef, useEffect, useState, useCallback, lazy, Suspense } from 'react'
import { chartUtils } from '../../utils/charts'
import { forwardRef, useImperativeHandle } from 'react'

// Vite-compatible lazy import of Plotly (no next/dynamic needed)
const Plot = lazy(() => import('react-plotly.js'))

export interface Point3D {
  x: number
  y: number
  z: number
  color?: string
  size?: number
  label?: string
  metadata?: Record<string, any>
}

export interface SurfaceData {
  x: number[]
  y: number[]
  z: number[][]
  type: 'surface' | 'heatmap'
  colorscale?: string
}

export interface ThreeDChartProps {
  data: Point3D[] | SurfaceData
  width?: number
  height?: number
  title?: string
  subtitle?: string
  loading?: boolean
  error?: string
  chartType?: 'scatter3d' | 'surface' | 'mesh3d' | 'heatmap3d'
  showGrid?: boolean
  showLegend?: boolean
  showTooltip?: boolean
  theme?: 'light' | 'dark'
  colors?: {
    background?: string
    grid?: string
    surface?: string
  }
  camera?: {
    eye: { x: number; y: number; z: number }
    center: { x: number; y: number; z: number }
    up: { x: number; y: number; z: number }
  }
  axes?: {
    x?: { title?: string; range?: [number, number] }
    y?: { title?: string; range?: [number, number] }
    z?: { title?: string; range?: [number, number] }
  }
  onPointClick?: (point: Point3D) => void
  onSurfaceClick?: (x: number, y: number, z: number) => void
  animationEnabled?: boolean
  colorScale?: string[] | string
  markerSize?: number
  lineWidth?: number
  opacity?: number
}

export interface ThreeDChartRef {
  exportChart: (format: 'png' | 'svg' | 'pdf') => Promise<void>
  getCamera: () => any
  setCamera: (camera: any) => void
  resetCamera: () => void
  spin: (duration?: number) => void
}

const ThreeDChart = forwardRef<ThreeDChartRef, ThreeDChartProps>(({
  data,
  width = 800,
  height = 600,
  title,
  subtitle,
  loading,
  error,
  chartType = 'scatter3d',
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  theme = 'light',
  colors = {
    background: '#ffffff',
    grid: 'rgba(0, 0, 0, 0.1)',
    surface: 'Viridis',
  },
  camera = {
    eye: { x: 1.5, y: 1.5, z: 1.5 },
    center: { x: 0, y: 0, z: 0 },
    up: { x: 0, y: 0, z: 1 },
  },
  axes = {},
  onPointClick,
  onSurfaceClick,
  animationEnabled = true,
  colorScale = 'Viridis',
  markerSize = 8,
  lineWidth = 2,
  opacity = 0.8,
}, ref) => {
  const plotRef = useRef<any>(null)
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  // Transform data based on chart type
  const plotlyData = useMemo(() => {
    if (!data) return []

    if (Array.isArray(data)) {
      // Point3D data for scatter3d
      if (chartType === 'scatter3d') {
        return [{
          type: 'scatter3d',
          mode: 'markers',
          x: data.map(p => p.x),
          y: data.map(p => p.y),
          z: data.map(p => p.z),
          marker: {
            size: data.map(p => p.size || markerSize),
            color: data.map(p => p.color || p.z),
            colorscale: colorScale,
            showscale: showLegend,
            opacity,
          },
          text: data.map(p => p.label || ''),
          hovertemplate: data.map(p => {
            const labels = []
            if (p.label) labels.push(`Label: ${p.label}`)
            labels.push(`X: ${chartUtils.formatNumber(p.x)}`)
            labels.push(`Y: ${chartUtils.formatNumber(p.y)}`)
            labels.push(`Z: ${chartUtils.formatNumber(p.z)}`)
            if (p.metadata) {
              Object.entries(p.metadata).forEach(([key, value]) => {
                labels.push(`${key}: ${value}`)
              })
            }
            return labels.join('<br>') + '<extra></extra>'
          }),
        }]
      } else if (chartType === 'mesh3d') {
        // Convert points to mesh (requires triangulation)
        const x = data.map(p => p.x)
        const y = data.map(p => p.y)
        const z = data.map(p => p.z)

        // Simple triangulation (for demonstration)
        const i: number[] = []
        const j: number[] = []
        const k: number[] = []
        for (let idx = 0; idx < data.length - 2; idx += 3) {
          i.push(idx)
          j.push(idx + 1)
          k.push(idx + 2)
        }

        return [{
          type: 'mesh3d',
          x,
          y,
          z,
          i,
          j,
          k,
          opacity,
          color: colors.surface || colorScale,
        }]
      }
    } else {
      // SurfaceData for surface or heatmap
      if (chartType === 'surface' || chartType === 'heatmap3d') {
        return [{
          type: chartType === 'heatmap3d' ? 'heatmap' : 'surface',
          x: data.x,
          y: data.y,
          z: data.z,
          colorscale: data.colorscale || colorScale,
          showscale: showLegend,
          opacity,
          contours: {
            z: {
              show: showGrid,
              usecolormap: true,
              highlightcolor: colors.grid,
              project: { z: true },
            },
          },
        }]
      }
    }

    return []
  }, [data, chartType, colorScale, showLegend, showGrid, colors, markerSize, opacity])

  // Plotly layout
  const layout = useMemo(() => {
    const isDark = theme === 'dark'
    const bgColor = isDark ? '#1a1a1a' : colors.background
    const textColor = isDark ? '#ffffff' : '#000000'
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : colors.grid

    return {
      title: {
        text: title,
        font: {
          size: 18,
          color: textColor,
        },
      },
      scene: {
        camera: camera,
        xaxis: {
          title: axes.x?.title || 'X Axis',
          range: axes.x?.range,
          gridcolor: gridColor,
          showbackground: showGrid,
          backgroundcolor: bgColor,
          color: textColor,
        },
        yaxis: {
          title: axes.y?.title || 'Y Axis',
          range: axes.y?.range,
          gridcolor: gridColor,
          showbackground: showGrid,
          backgroundcolor: bgColor,
          color: textColor,
        },
        zaxis: {
          title: axes.z?.title || 'Z Axis',
          range: axes.z?.range,
          gridcolor: gridColor,
          showbackground: showGrid,
          backgroundcolor: bgColor,
          color: textColor,
        },
      },
      paper_bgcolor: bgColor,
      plot_bgcolor: bgColor,
      font: {
        color: textColor,
      },
      showlegend: showLegend,
      hovermode: showTooltip ? 'closest' : false,
      margin: {
        l: 0,
        r: 0,
        t: title ? 40 : 0,
        b: 0,
      },
      annotations: subtitle ? [
        {
          text: subtitle,
          xref: 'paper',
          yref: 'paper',
          x: 0,
          y: 1,
          xanchor: 'left',
          yanchor: 'bottom',
          font: {
            size: 12,
            color: textColor,
          },
          showarrow: false,
        },
      ] : [],
    }
  }, [title, subtitle, theme, colors, camera, axes, showGrid, showLegend, showTooltip])

  // Plotly config
  const config = useMemo(() => ({
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['toImage'],
    toImageButtonOptions: {
      format: 'png',
      filename: '3d-chart',
      height: height,
      width: width,
      scale: 2,
    },
    responsive: true,
  }), [width, height])

  // Chart ref methods
  useImperativeHandle(ref, () => ({
    exportChart: async (format: 'png' | 'svg' | 'pdf' = 'png') => {
      if (plotRef.current) {
        await plotRef.current.downloadImage(format, `3d-chart-${Date.now()}`)
      }
    },
    getCamera: () => {
      return plotRef.current?.getLayout()?.scene?.camera || camera
    },
    setCamera: (newCamera: any) => {
      if (plotRef.current) {
        plotRef.current.updateLayout({
          scene: { camera: newCamera },
        })
      }
    },
    resetCamera: () => {
      if (plotRef.current) {
        plotRef.current.updateLayout({
          scene: { camera },
        })
      }
    },
    spin: (duration = 5000) => {
      if (plotRef.current && animationEnabled) {
        const startCamera = plotRef.current.getLayout()?.scene?.camera || camera
        const startTime = Date.now()
        const animate = () => {
          const elapsed = Date.now() - startTime
          if (elapsed < duration) {
            const angle = (elapsed / duration) * Math.PI * 2
            const newCamera = {
              ...startCamera,
              eye: {
                x: Math.cos(angle) * startCamera.eye.x - Math.sin(angle) * startCamera.eye.z,
                y: startCamera.eye.y,
                z: Math.sin(angle) * startCamera.eye.x + Math.cos(angle) * startCamera.eye.z,
              },
            }
            plotRef.current.updateLayout({
              scene: { camera: newCamera },
            })
            requestAnimationFrame(animate)
          }
        }
        animate()
      }
    },
  }), [camera, animationEnabled])

  // Handle click events
  const handleClick = useCallback((event: any) => {
    if (!event.points || event.points.length === 0) return

    const point = event.points[0]
    if (chartType === 'scatter3d' && onPointClick) {
      const index = point.pointNumber
      const pointData = (data as Point3D[])[index]
      if (pointData) {
        onPointClick(pointData)
      }
    } else if ((chartType === 'surface' || chartType === 'heatmap3d') && onSurfaceClick) {
      onSurfaceClick(point.x, point.y, point.z)
    }
  }, [chartType, data, onPointClick, onSurfaceClick])

  if (!isClient) {
    return (
      <div style={{ width, height }} className="flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="relative" style={{ width, height }}>
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            <span className="text-sm text-gray-600">Loading 3D chart...</span>
          </div>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 bg-opacity-90 z-10">
          <div className="text-center">
            <div className="text-red-500 text-sm mb-2">Error loading 3D chart</div>
            <div className="text-red-400 text-xs">{error}</div>
          </div>
        </div>
      )}

      <Suspense fallback={<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>}>
        <Plot
          ref={plotRef}
          data={plotlyData}
          layout={layout}
          config={config}
          style={{ width: '100%', height: '100%' }}
          onClick={handleClick}
        />
      </Suspense>
    </div>
  )
})

ThreeDChart.displayName = 'ThreeDChart'

export default ThreeDChart