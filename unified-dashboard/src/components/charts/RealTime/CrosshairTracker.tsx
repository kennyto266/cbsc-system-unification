import React, { useEffect, useRef, useState, useCallback } from 'react'
import { Chart, ChartEvent, ActiveElement, Point } from 'chart.js'

// Crosshair data
export interface CrosshairData {
  x: number
  y: number
  xValue: any
  yValue: any
  dataIndex: number
  datasetIndex: number
}

// Crosshair tracker props
export interface CrosshairTrackerProps {
  chart: Chart
  enabled?: boolean
  showXLine?: boolean
  showYLine?: boolean
  showTooltip?: boolean
  showDataLabels?: boolean
  snapToData?: boolean
  lineColor?: string
  lineWidth?: number
  lineStyle?: 'solid' | 'dashed' | 'dotted'
  labelFormat?: (value: any, axis: 'x' | 'y') => string
  onDataPoint?: (data: CrosshairData) => void
  className?: string
}

// Crosshair tracker component
export const CrosshairTracker: React.FC<CrosshairTrackerProps> = ({
  chart,
  enabled = true,
  showXLine = true,
  showYLine = true,
  showTooltip = true,
  showDataLabels = true,
  snapToData = true,
  lineColor = 'rgba(0, 0, 0, 0.3)',
  lineWidth = 1,
  lineStyle = 'dashed',
  labelFormat = (value, axis) => typeof value === 'number' ? value.toFixed(2) : String(value),
  onDataPoint,
  className = ''
}) => {
  const [crosshairData, setCrosshairData] = useState<CrosshairData | null>(null)
  const [isVisible, setIsVisible] = useState(false)
  const canvasRef = useRef<HTMLCanvasElement>(chart.canvas)
  const overlayRef = useRef<HTMLCanvasElement>(null)

  // Initialize overlay canvas
  useEffect(() => {
    if (!canvasRef.current || !overlayRef.current) return

    const overlay = overlayRef.current
    overlay.width = canvasRef.current.width
    overlay.height = canvasRef.current.height
  }, [chart])

  // Draw crosshair
  const drawCrosshair = useCallback((data: CrosshairData) => {
    const canvas = overlayRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Get pixel coordinates
    const xPixel = data.x
    const yPixel = data.y

    // Set line style
    ctx.strokeStyle = lineColor
    ctx.lineWidth = lineWidth

    if (lineStyle === 'dashed') {
      ctx.setLineDash([5, 5])
    } else if (lineStyle === 'dotted') {
      ctx.setLineDash([2, 2])
    } else {
      ctx.setLineDash([])
    }

    // Draw vertical line
    if (showXLine) {
      ctx.beginPath()
      ctx.moveTo(xPixel, 0)
      ctx.lineTo(xPixel, canvas.height)
      ctx.stroke()
    }

    // Draw horizontal line
    if (showYLine) {
      ctx.beginPath()
      ctx.moveTo(0, yPixel)
      ctx.lineTo(canvas.width, yPixel)
      ctx.stroke()
    }

    // Draw data labels
    if (showDataLabels) {
      ctx.setLineDash([])
      ctx.fillStyle = 'rgba(0, 0, 0, 0.8)'
      ctx.fillRect(xPixel + 10, yPixel - 20, 80, 30)

      ctx.fillStyle = 'white'
      ctx.font = '12px Arial'
      ctx.fillText(`X: ${labelFormat(data.xValue, 'x')}`, xPixel + 15, yPixel - 5)
      ctx.fillText(`Y: ${labelFormat(data.yValue, 'y')}`, xPixel + 15, yPixel + 10)
    }

    // Draw tooltip
    if (showTooltip && data.dataIndex >= 0 && data.datasetIndex >= 0) {
      const dataset = chart.data.datasets[data.datasetIndex]
      if (dataset) {
        const label = dataset.label || ''
        const value = dataset.data[data.dataIndex]

        // Draw tooltip background
        const tooltipWidth = 150
        const tooltipHeight = 50
        const tooltipX = Math.min(xPixel + 10, canvas.width - tooltipWidth - 10)
        const tooltipY = Math.max(yPixel - tooltipHeight - 10, 10)

        ctx.fillStyle = 'rgba(0, 0, 0, 0.9)'
        ctx.fillRect(tooltipX, tooltipY, tooltipWidth, tooltipHeight)

        // Draw tooltip text
        ctx.fillStyle = 'white'
        ctx.font = 'bold 12px Arial'
        ctx.fillText(label, tooltipX + 10, tooltipY + 20)
        ctx.font = '12px Arial'
        ctx.fillText(`Value: ${labelFormat(value, 'y')}`, tooltipX + 10, tooltipY + 40)
      }
    }
  }, [chart, showXLine, showYLine, showTooltip, showDataLabels, lineColor, lineWidth, lineStyle, labelFormat])

  // Find nearest data point
  const findNearestDataPoint = useCallback((clientX: number, clientY: number): CrosshairData | null => {
    if (!snapToData) {
      // Return raw coordinates
      const rect = canvasRef.current!.getBoundingClientRect()
      const x = clientX - rect.left
      const y = clientY - rect.top

      return {
        x,
        y,
        xValue: chart.scales.x.getValueForPixel(x),
        yValue: chart.scales.y.getValueForPixel(y),
        dataIndex: -1,
        datasetIndex: -1
      }
    }

    // Find nearest data point
    const rect = canvasRef.current!.getBoundingClientRect()
    const x = clientX - rect.left
    const y = clientY - rect.top

    let nearestPoint: CrosshairData | null = null
    let minDistance = Infinity

    chart.data.datasets.forEach((dataset, datasetIndex) => {
      if (dataset.hidden) return

      dataset.data.forEach((point, index) => {
        if (!point || typeof point !== 'object') return

        const pointX = chart.scales.x.getPixelForValue((point as any).x || index)
        const pointY = chart.scales.y.getPixelForValue((point as any).y)

        const distance = Math.sqrt(Math.pow(x - pointX, 2) + Math.pow(y - pointY, 2))

        if (distance < minDistance && distance < 20) { // 20px threshold
          minDistance = distance
          nearestPoint = {
            x: pointX,
            y: pointY,
            xValue: (point as any).x,
            yValue: (point as any).y,
            dataIndex: index,
            datasetIndex
          }
        }
      })
    })

    return nearestPoint
  }, [chart, snapToData])

  // Handle mouse move
  const handleMouseMove = useCallback((event: MouseEvent) => {
    if (!enabled) return

    const data = findNearestDataPoint(event.clientX, event.clientY)
    setCrosshairData(data)
    setIsVisible(true)

    if (data) {
      drawCrosshair(data)
      onDataPoint?.(data)
    }
  }, [enabled, findNearestDataPoint, drawCrosshair, onDataPoint])

  // Handle mouse leave
  const handleMouseLeave = useCallback(() => {
    setIsVisible(false)
    setCrosshairData(null)

    // Clear overlay
    const canvas = overlayRef.current
    if (canvas) {
      const ctx = canvas.getContext('2d')
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height)
      }
    }
  }, [])

  // Set up event listeners
  useEffect(() => {
    if (!enabled) return

    const canvas = canvasRef.current
    if (!canvas) return

    canvas.addEventListener('mousemove', handleMouseMove)
    canvas.addEventListener('mouseleave', handleMouseLeave)

    return () => {
      canvas.removeEventListener('mousemove', handleMouseMove)
      canvas.removeEventListener('mouseleave', handleMouseLeave)
    }
  }, [enabled, handleMouseMove, handleMouseLeave])

  // Sync with chart events
  useEffect(() => {
    if (!enabled) return

    const handleChartEvent = (event: ChartEvent) => {
      if (event.type === 'mousemove' && event.native) {
        const mouseEvent = event.native as MouseEvent
        handleMouseMove(mouseEvent)
      } else if (event.type === 'mouseout') {
        handleMouseLeave()
      }
    }

    chart.options.onHover = handleChartEvent
    chart.update('none')

    return () => {
      chart.options.onHover = undefined
    }
  }, [chart, enabled, handleMouseMove, handleMouseLeave])

  return (
    <div className={`crosshair-tracker ${className}`}>
      <canvas
        ref={overlayRef}
        className="absolute inset-0 pointer-events-none"
        style={{ zIndex: 5 }}
      />
      {/* Crosshair info display */}
      {isVisible && crosshairData && (
        <div className="absolute top-4 right-4 bg-black bg-opacity-75 text-white px-3 py-2 rounded text-xs">
          <div>X: {labelFormat(crosshairData.xValue, 'x')}</div>
          <div>Y: {labelFormat(crosshairData.yValue, 'y')}</div>
          {crosshairData.dataIndex >= 0 && (
            <div>Index: {crosshairData.dataIndex}</div>
          )}
        </div>
      )}
    </div>
  )
}

export default CrosshairTracker