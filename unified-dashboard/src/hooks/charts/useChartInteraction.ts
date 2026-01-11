import { useState, useCallback, useRef, useEffect } from 'react'
import { Chart as ChartJS, ChartEvent, ActiveElement } from 'chart.js'

export interface ChartInteractionState {
  hoveredElement: ActiveElement | null
  selectedElements: ActiveElement[]
  clickedPoint: { x: number; y: number } | null
  brushSelection: { startX: number; startY: number; endX: number; endY: number } | null
  zoomLevel: number
  panOffset: { x: number; y: number }
}

export interface UseChartInteractionOptions {
  enableHover?: boolean
  enableSelection?: boolean
  enableBrush?: boolean
  enableZoom?: boolean
  enablePan?: boolean
  onHover?: (element: ActiveElement | null) => void
  onSelect?: (elements: ActiveElement[]) => void
  onBrush?: (selection: { startX: number; startY: number; endX: number; endY: number }) => void
  onZoom?: (level: number, center?: { x: number; y: number }) => void
  onPan?: (offset: { x: number; y: number }) => void
  multiSelect?: boolean
  brushThreshold?: number
  zoomSpeed?: number
  panSpeed?: number
}

export const useChartInteraction = (options: UseChartInteractionOptions = {}) => {
  const {
    enableHover = true,
    enableSelection = true,
    enableBrush = false,
    enableZoom = true,
    enablePan = true,
    onHover,
    onSelect,
    onBrush,
    onZoom,
    onPan,
    multiSelect = false,
    brushThreshold = 5,
    zoomSpeed = 0.1,
    panSpeed = 1,
  } = options

  const [state, setState] = useState<ChartInteractionState>({
    hoveredElement: null,
    selectedElements: [],
    clickedPoint: null,
    brushSelection: null,
    zoomLevel: 1,
    panOffset: { x: 0, y: 0 },
  })

  const chartRef = useRef<ChartJS | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const isBrushing = useRef(false)
  const isPanning = useRef(false)
  const lastPanPosition = useRef({ x: 0, y: 0 })

  // Handle hover
  const handleHover = useCallback((event: ChartEvent, elements: ActiveElement[]) => {
    if (!enableHover) return

    const hoveredElement = elements.length > 0 ? elements[0] : null
    setState(prev => ({ ...prev, hoveredElement }))
    onHover?.(hoveredElement)
  }, [enableHover, onHover])

  // Handle click
  const handleClick = useCallback((event: ChartEvent, elements: ActiveElement[]) => {
    if (!enableSelection) return

    const point = { x: event.x || 0, y: event.y || 0 }

    if (enableBrush && !isBrushing.current) {
      // Start brush selection
      isBrushing.current = true
      setState(prev => ({
        ...prev,
        clickedPoint: point,
        brushSelection: { startX: point.x, startY: point.y, endX: point.x, endY: point.y },
      }))
    } else if (enableSelection) {
      // Handle element selection
      let newSelectedElements: ActiveElement[]

      if (multiSelect) {
        // Toggle selection
        const elementIndex = elements[0]?.index
        if (elementIndex !== undefined) {
          const isSelected = state.selectedElements.some(el => el.index === elementIndex)
          newSelectedElements = isSelected
            ? state.selectedElements.filter(el => el.index !== elementIndex)
            : [...state.selectedElements, elements[0]]
        } else {
          newSelectedElements = []
        }
      } else {
        // Single selection
        newSelectedElements = elements.length > 0 ? [elements[0]] : []
      }

      setState(prev => ({ ...prev, selectedElements: newSelectedElements }))
      onSelect?.(newSelectedElements)
    }
  }, [
    enableSelection,
    enableBrush,
    multiSelect,
    state.selectedElements,
    onSelect,
  ])

  // Handle mouse move
  const handleMouseMove = useCallback((event: MouseEvent) => {
    if (!canvasRef.current) return

    const rect = canvasRef.current.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    if (isBrushing.current && state.clickedPoint) {
      // Update brush selection
      setState(prev => ({
        ...prev,
        brushSelection: {
          startX: prev.clickedPoint!.x,
          startY: prev.clickedPoint!.y,
          endX: x,
          endY: y,
        },
      }))
    } else if (isPanning.current) {
      // Handle panning
      const deltaX = x - lastPanPosition.current.x
      const deltaY = y - lastPanPosition.current.y

      setState(prev => ({
        ...prev,
        panOffset: {
          x: prev.panOffset.x + deltaX * panSpeed,
          y: prev.panOffset.y + deltaY * panSpeed,
        },
      }))

      onPan?.(state.panOffset)
      lastPanPosition.current = { x, y }
    }
  }, [
    state.clickedPoint,
    state.panOffset,
    panSpeed,
    onPan,
  ])

  // Handle mouse up
  const handleMouseUp = useCallback((event: MouseEvent) => {
    if (isBrushing.current && state.brushSelection) {
      // End brush selection
      isBrushing.current = false
      const { startX, startY, endX, endY } = state.brushSelection

      // Check if brush selection is significant
      const width = Math.abs(endX - startX)
      const height = Math.abs(endY - startY)

      if (width > brushThreshold || height > brushThreshold) {
        onBrush?.({
          startX: Math.min(startX, endX),
          startY: Math.min(startY, endY),
          endX: Math.max(startX, endX),
          endY: Math.max(startY, endY),
        })
      } else {
        // Clear brush if too small
        setState(prev => ({ ...prev, brushSelection: null }))
      }
    }

    isPanning.current = false
  }, [state.brushSelection, brushThreshold, onBrush])

  // Handle wheel for zoom
  const handleWheel = useCallback((event: WheelEvent) => {
    if (!enableZoom || !canvasRef.current) return

    event.preventDefault()

    const rect = canvasRef.current.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    const delta = event.deltaY > 0 ? -zoomSpeed : zoomSpeed
    const newZoomLevel = Math.max(0.1, Math.min(5, state.zoomLevel + delta))

    setState(prev => ({ ...prev, zoomLevel: newZoomLevel }))
    onZoom?.(newZoomLevel, { x, y })
  }, [enableZoom, zoomSpeed, state.zoomLevel, onZoom])

  // Setup event listeners
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    canvas.addEventListener('mousemove', handleMouseMove)
    canvas.addEventListener('mouseup', handleMouseUp)
    canvas.addEventListener('wheel', handleWheel, { passive: false })

    // Handle right mouse button for panning
    const handleContextMenu = (event: MouseEvent) => {
      event.preventDefault()
      if (enablePan) {
        isPanning.current = true
        lastPanPosition.current = { x: event.offsetX, y: event.offsetY }
      }
    }

    canvas.addEventListener('contextmenu', handleContextMenu)

    return () => {
      canvas.removeEventListener('mousemove', handleMouseMove)
      canvas.removeEventListener('mouseup', handleMouseUp)
      canvas.removeEventListener('wheel', handleWheel)
      canvas.removeEventListener('contextmenu', handleContextMenu)
    }
  }, [handleMouseMove, handleMouseUp, handleWheel, enablePan])

  // Chart event handlers
  const chartOptions = useMemo(() => ({
    onHover: handleHover,
    onClick: handleClick,
  }), [handleHover, handleClick])

  // Clear selections
  const clearSelection = useCallback(() => {
    setState(prev => ({
      ...prev,
      selectedElements: [],
      brushSelection: null,
    }))
  }, [])

  // Reset zoom and pan
  const resetView = useCallback(() => {
    setState(prev => ({
      ...prev,
      zoomLevel: 1,
      panOffset: { x: 0, y: 0 },
    }))
  }, [])

  // Set chart reference
  const setChart = useCallback((chart: ChartJS) => {
    chartRef.current = chart
    canvasRef.current = chart.canvas
  }, [])

  return {
    state,
    chartOptions,
    setChart,
    clearSelection,
    resetView,
  }
}