import React, { useState, useRef, useEffect } from 'react'
import { Chart, ChartConfiguration, ChartEvent, ActiveElement, Point } from 'chart.js'

// Annotation types
export type AnnotationType =
  | 'line'
  | 'rectangle'
  | 'ellipse'
  | 'text'
  | 'arrow'
  | 'trendline'
  | 'fibonacci'
  | 'support'
  | 'resistance'

// Annotation interface
export interface ChartAnnotation {
  id: string
  type: AnnotationType
  startX: number
  startY: number
  endX?: number
  endY?: number
  label?: string
  color: string
  strokeWidth?: number
  fill?: boolean
  fillColor?: string
  dashPattern?: number[]
  arrow?: {
    headSize: number
    headAngle: number
  }
  text?: {
    content: string
    fontSize: number
    fontFamily: string
    fontWeight: string
    align: 'left' | 'center' | 'right'
    baseline: 'top' | 'middle' | 'bottom'
  }
  fibonacci?: {
    levels: number[]
    colors: string[]
  }
}

// Chart annotation props
export interface ChartAnnotationProps {
  chart: Chart
  annotations: ChartAnnotation[]
  enabled?: boolean
  activeTool?: AnnotationType
  defaultColor?: string
  onAnnotationAdd?: (annotation: ChartAnnotation) => void
  onAnnotationUpdate?: (id: string, annotation: Partial<ChartAnnotation>) => void
  onAnnotationDelete?: (id: string) => void
  className?: string
}

// Chart annotation component
export const ChartAnnotation: React.FC<ChartAnnotationProps> = ({
  chart,
  annotations,
  enabled = true,
  activeTool,
  defaultColor = '#FF6B6B',
  onAnnotationAdd,
  onAnnotationUpdate,
  onAnnotationDelete,
  className = ''
}) => {
  const [isDrawing, setIsDrawing] = useState(false)
  const [currentAnnotation, setCurrentAnnotation] = useState<Partial<ChartAnnotation> | null>(null)
  const [selectedAnnotation, setSelectedAnnotation] = useState<string | null>(null)
  const canvasRef = useRef<HTMLCanvasElement>(chart.canvas)
  const overlayRef = useRef<HTMLCanvasElement>(null)

  // Initialize overlay canvas
  useEffect(() => {
    if (!canvasRef.current || !overlayRef.current) return

    const overlay = overlayRef.current
    overlay.width = canvasRef.current.width
    overlay.height = canvasRef.current.height

    // Draw existing annotations
    drawAnnotations()
  }, [chart, annotations])

  // Draw all annotations
  const drawAnnotations = useCallback(() => {
    const canvas = overlayRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Draw each annotation
    annotations.forEach(annotation => {
      drawAnnotation(ctx, annotation, annotation.id === selectedAnnotation)
    })
  }, [annotations, selectedAnnotation])

  // Draw single annotation
  const drawAnnotation = (ctx: CanvasRenderingContext2D, annotation: ChartAnnotation, isSelected: boolean) => {
    ctx.save()

    // Get chart coordinates
    const startX = chart.scales.x.getPixelForValue(annotation.startX)
    const startY = chart.scales.y.getPixelForValue(annotation.startY)
    const endX = annotation.endX ? chart.scales.x.getPixelForValue(annotation.endX) : startX
    const endY = annotation.endY ? chart.scales.y.getPixelForValue(annotation.endY) : startY

    // Set styles
    ctx.strokeStyle = annotation.color
    ctx.lineWidth = annotation.strokeWidth || 2
    ctx.fillStyle = annotation.fillColor || annotation.color + '20'

    if (annotation.dashPattern) {
      ctx.setLineDash(annotation.dashPattern)
    }

    // Draw based on type
    switch (annotation.type) {
      case 'line':
        ctx.beginPath()
        ctx.moveTo(startX, startY)
        ctx.lineTo(endX, endY)
        ctx.stroke()
        break

      case 'trendline':
        // Extended line beyond end points
        const dx = endX - startX
        const dy = endY - startY
        const extension = 1000 // Extend by this amount
        ctx.beginPath()
        ctx.moveTo(startX - dx * extension, startY - dy * extension)
        ctx.lineTo(endX + dx * extension, endY + dy * extension)
        ctx.stroke()
        break

      case 'rectangle':
        ctx.beginPath()
        ctx.rect(startX, startY, endX - startX, endY - startY)
        if (annotation.fill) {
          ctx.fill()
        }
        ctx.stroke()
        break

      case 'ellipse':
        const centerX = (startX + endX) / 2
        const centerY = (startY + endY) / 2
        const radiusX = Math.abs(endX - startX) / 2
        const radiusY = Math.abs(endY - startY) / 2
        ctx.beginPath()
        ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI)
        if (annotation.fill) {
          ctx.fill()
        }
        ctx.stroke()
        break

      case 'text':
        if (annotation.text) {
          ctx.font = `${annotation.text.fontWeight} ${annotation.text.fontSize}px ${annotation.text.fontFamily}`
          ctx.fillStyle = annotation.color
          ctx.textAlign = annotation.text.align
          ctx.textBaseline = annotation.text.baseline
          ctx.fillText(annotation.text.content, startX, startY)
        }
        break

      case 'arrow':
        // Draw line
        ctx.beginPath()
        ctx.moveTo(startX, startY)
        ctx.lineTo(endX, endY)
        ctx.stroke()

        // Draw arrowhead
        const angle = Math.atan2(endY - startY, endX - startX)
        const headLength = annotation.arrow?.headSize || 10
        const headAngle = annotation.arrow?.headAngle || Math.PI / 6

        ctx.beginPath()
        ctx.moveTo(endX, endY)
        ctx.lineTo(
          endX - headLength * Math.cos(angle - headAngle),
          endY - headLength * Math.sin(angle - headAngle)
        )
        ctx.moveTo(endX, endY)
        ctx.lineTo(
          endX - headLength * Math.cos(angle + headAngle),
          endY - headLength * Math.sin(angle + headAngle)
        )
        ctx.stroke()
        break

      case 'fibonacci':
        const fibLevels = annotation.fibonacci?.levels || [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
        const fibColors = annotation.fibonacci?.colors || [
          '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8'
        ]

        fibLevels.forEach((level, index) => {
          const y = startY + (endY - startY) * level
          ctx.strokeStyle = fibColors[index % fibColors.length]
          ctx.setLineDash([5, 5])
          ctx.beginPath()
          ctx.moveTo(startX, y)
          ctx.lineTo(endX, y)
          ctx.stroke()

          // Label
          ctx.fillStyle = fibColors[index % fibColors.length]
          ctx.font = '12px Arial'
          ctx.textAlign = 'left'
          ctx.fillText(`${(level * 100).toFixed(1)}%`, startX + 5, y - 5)
        })
        break

      case 'support':
      case 'resistance':
        ctx.setLineDash([10, 5])
        ctx.beginPath()
        ctx.moveTo(startX, startY)
        ctx.lineTo(endX, startY)
        ctx.stroke()

        // Label
        ctx.fillStyle = annotation.color
        ctx.font = 'bold 12px Arial'
        ctx.textAlign = 'center'
        ctx.fillText(
          annotation.type.toUpperCase(),
          (startX + endX) / 2,
          startY - 5
        )
        break
    }

    // Draw selection indicator
    if (isSelected) {
      ctx.strokeStyle = '#000000'
      ctx.lineWidth = 1
      ctx.setLineDash([5, 5])
      ctx.strokeRect(startX - 5, startY - 5, endX - startX + 10, endY - startY + 10)
    }

    ctx.restore()
  }

  // Handle mouse down
  const handleMouseDown = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!enabled || !activeTool) return

    const rect = overlayRef.current!.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    // Convert to chart values
    const chartX = chart.scales.x.getValueForPixel(x)
    const chartY = chart.scales.y.getValueForPixel(y)

    setIsDrawing(true)
    setCurrentAnnotation({
      id: `annotation-${Date.now()}`,
      type: activeTool,
      startX: chartX,
      startY: chartY,
      color: defaultColor,
      strokeWidth: 2
    })
  }

  // Handle mouse move
  const handleMouseMove = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !currentAnnotation) return

    const rect = overlayRef.current!.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    // Convert to chart values
    const chartX = chart.scales.x.getValueForPixel(x)
    const chartY = chart.scales.y.getValueForPixel(y)

    // Update current annotation
    const updated = {
      ...currentAnnotation,
      endX: chartX,
      endY: chartY
    }

    setCurrentAnnotation(updated)

    // Draw temporary annotation
    const canvas = overlayRef.current!
    const ctx = canvas.getContext('2d')!

    // Clear and redraw
    drawAnnotations()

    // Draw current annotation being drawn
    if (updated.id && updated.startX !== undefined && updated.startY !== undefined) {
      drawAnnotation(ctx, updated as ChartAnnotation, false)
    }
  }

  // Handle mouse up
  const handleMouseUp = () => {
    if (!isDrawing || !currentAnnotation) return

    setIsDrawing(false)

    // Add annotation if valid
    if (currentAnnotation.endX !== undefined && currentAnnotation.endY !== undefined) {
      const newAnnotation = currentAnnotation as ChartAnnotation
      onAnnotationAdd?.(newAnnotation)
    }

    setCurrentAnnotation(null)
  }

  // Handle annotation click
  const handleAnnotationClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!enabled) return

    const rect = overlayRef.current!.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    // Check if clicking on an annotation
    const clickedAnnotation = annotations.find(annotation => {
      const startX = chart.scales.x.getPixelForValue(annotation.startX)
      const startY = chart.scales.y.getPixelForValue(annotation.startY)
      const endX = annotation.endX ? chart.scales.x.getPixelForValue(annotation.endX) : startX
      const endY = annotation.endY ? chart.scales.y.getPixelForValue(annotation.endY) : startY

      // Simple bounding box check
      return x >= Math.min(startX, endX) - 5 &&
             x <= Math.max(startX, endX) + 5 &&
             y >= Math.min(startY, endY) - 5 &&
             y <= Math.max(startY, endY) + 5
    })

    if (clickedAnnotation) {
      setSelectedAnnotation(clickedAnnotation.id)
    } else {
      setSelectedAnnotation(null)
    }
  }

  // Delete selected annotation
  const deleteSelectedAnnotation = useCallback(() => {
    if (selectedAnnotation) {
      onAnnotationDelete?.(selectedAnnotation)
      setSelectedAnnotation(null)
    }
  }, [selectedAnnotation, onAnnotationDelete])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Delete' || e.key === 'Backspace') {
        deleteSelectedAnnotation()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [deleteSelectedAnnotation])

  return (
    <div className={`chart-annotation ${className}`}>
      <canvas
        ref={overlayRef}
        className="absolute inset-0 pointer-events-auto"
        style={{ zIndex: 10 }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onClick={handleAnnotationClick}
      />
      {/* Annotation toolbar */}
      {enabled && (
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-2 flex space-x-2">
          {/* Tool selection */}
          <select
            value={activeTool || ''}
            onChange={(e) => {
              // Tool selection logic would be handled by parent
            }}
            className="text-sm px-2 py-1 border rounded"
          >
            <option value="">Select Tool</option>
            <option value="line">Line</option>
            <option value="trendline">Trendline</option>
            <option value="rectangle">Rectangle</option>
            <option value="ellipse">Ellipse</option>
            <option value="text">Text</option>
            <option value="arrow">Arrow</option>
            <option value="fibonacci">Fibonacci</option>
            <option value="support">Support</option>
            <option value="resistance">Resistance</option>
          </select>

          {/* Color picker */}
          <input
            type="color"
            value={defaultColor}
            onChange={(e) => {
              // Color change logic would be handled by parent
            }}
            className="w-8 h-8 border rounded cursor-pointer"
          />

          {/* Delete button */}
          {selectedAnnotation && (
            <button
              onClick={deleteSelectedAnnotation}
              className="text-sm px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Delete
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default ChartAnnotation