import { useState, useRef, useCallback, useEffect } from 'react'
import { ChartInteractionState, ChartEventHandlers } from '../types/chart.types'

interface UseChartInteractionOptions {
  enableZoom?: boolean
  enablePan?: boolean
  enableCrosshair?: boolean
  enableBrush?: boolean
  onStateChange?: (state: ChartInteractionState) => void
}

interface UseChartInteractionReturn {
  state: ChartInteractionState
  handlers: ChartEventHandlers
  containerRef: React.RefObject<HTMLDivElement>
  reset: () => void
  zoomTo: (range: { start: number; end: number }) => void
  panTo: (offset: { x: number; y: number }) => void
  setCrosshair: (position: { x: number; y: number }) => void
  selectPoints: (points: any[]) => void
  clearSelection: () => void
}

export function useChartInteraction(options: UseChartInteractionOptions = {}): UseChartInteractionReturn {
  const {
    enableZoom = true,
    enablePan = true,
    enableCrosshair = true,
    enableBrush = true,
    onStateChange
  } = options

  const [state, setState] = useState<ChartInteractionState>({
    isHovering: false,
    selectedPoints: [],
    zoomLevel: 1,
    panOffset: { x: 0, y: 0 }
  })

  const containerRef = useRef<HTMLDivElement>(null)
  const isDraggingRef = useRef(false)
  const dragStartRef = useRef({ x: 0, y: 0 })
  const lastPanOffsetRef = useRef({ x: 0, y: 0 })

  // Update state and trigger callback
  const updateState = useCallback((newState: Partial<ChartInteractionState>) => {
    const updatedState = { ...state, ...newState }
    setState(updatedState)
    onStateChange?.(updatedState)
  }, [state, onStateChange])

  // Handle mouse move
  const handleMouseMove = useCallback((event: MouseEvent) => {
    if (!containerRef.current) return

    const rect = containerRef.current.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    // Update crosshair position
    if (enableCrosshair) {
      updateState({
        crosshairPosition: { x, y },
        isHovering: true
      })
    }

    // Handle panning
    if (enablePan && isDraggingRef.current) {
      const deltaX = x - dragStartRef.current.x
      const deltaY = y - dragStartRef.current.y

      const newPanOffset = {
        x: lastPanOffsetRef.current.x + deltaX,
        y: lastPanOffsetRef.current.y + deltaY
      }

      updateState({ panOffset: newPanOffset })
    }
  }, [enableCrosshair, enablePan, updateState])

  // Handle mouse down
  const handleMouseDown = useCallback((event: MouseEvent) => {
    if (!containerRef.current || !enablePan) return

    const rect = containerRef.current.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    isDraggingRef.current = true
    dragStartRef.current = { x, y }
    lastPanOffsetRef.current = state.panOffset || { x: 0, y: 0 }

    // Add dragging class for cursor style
    containerRef.current.style.cursor = 'grabbing'
  }, [enablePan, state.panOffset])

  // Handle mouse up
  const handleMouseUp = useCallback(() => {
    if (isDraggingRef.current) {
      isDraggingRef.current = false
      if (containerRef.current) {
        containerRef.current.style.cursor = 'default'
      }
    }
  }, [])

  // Handle mouse click
  const handleMouseClick = useCallback((event: MouseEvent) => {
    // Custom click logic can be added here
    // For example, point selection or brush selection
  }, [])

  // Handle wheel for zoom
  const handleWheel = useCallback((event: WheelEvent) => {
    if (!enableZoom || !containerRef.current) return

    event.preventDefault()

    const rect = containerRef.current.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    // Calculate zoom factor
    const zoomSpeed = 0.1
    const delta = event.deltaY > 0 ? -zoomSpeed : zoomSpeed
    const newZoomLevel = Math.max(0.1, Math.min(10, (state.zoomLevel || 1) + delta))

    updateState({ zoomLevel: newZoomLevel })
  }, [enableZoom, state.zoomLevel, updateState])

  // Set up event listeners
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    container.addEventListener('mousemove', handleMouseMove)
    container.addEventListener('mousedown', handleMouseDown)
    container.addEventListener('mouseup', handleMouseUp)
    container.addEventListener('mouseleave', handleMouseUp)
    container.addEventListener('click', handleMouseClick)
    container.addEventListener('wheel', handleWheel, { passive: false })

    return () => {
      container.removeEventListener('mousemove', handleMouseMove)
      container.removeEventListener('mousedown', handleMouseDown)
      container.removeEventListener('mouseup', handleMouseUp)
      container.removeEventListener('mouseleave', handleMouseUp)
      container.removeEventListener('click', handleMouseClick)
      container.removeEventListener('wheel', handleWheel)
    }
  }, [handleMouseMove, handleMouseDown, handleMouseUp, handleMouseClick, handleWheel])

  // Reset interaction state
  const reset = useCallback(() => {
    isDraggingRef.current = false
    updateState({
      isHovering: false,
      hoveredPoint: undefined,
      selectedPoints: [],
      zoomLevel: 1,
      panOffset: { x: 0, y: 0 },
      crosshairPosition: undefined
    })
  }, [updateState])

  // Zoom to specific range
  const zoomTo = useCallback((range: { start: number; end: number }) => {
    // Calculate zoom level based on range
    // This is a simplified implementation
    const domain = end - start
    const newZoomLevel = Math.max(0.1, Math.min(10, 1000 / domain))

    updateState({ zoomLevel: newZoomLevel })
  }, [updateState])

  // Pan to specific offset
  const panTo = useCallback((offset: { x: number; y: number }) => {
    updateState({ panOffset: offset })
  }, [updateState])

  // Set crosshair position
  const setCrosshair = useCallback((position: { x: number; y: number }) => {
    updateState({
      crosshairPosition: position,
      isHovering: true
    })
  }, [updateState])

  // Select points
  const selectPoints = useCallback((points: any[]) => {
    updateState({ selectedPoints: points })
  }, [updateState])

  // Clear selection
  const clearSelection = useCallback(() => {
    updateState({ selectedPoints: [] })
  }, [updateState])

  return {
    state,
    handlers: {
      onMouseMove: handleMouseMove,
      onMouseClick: handleMouseClick,
      onZoom: (zoomLevel: number) => updateState({ zoomLevel }),
      onPan: (panOffset: { x: number; y: number }) => updateState({ panOffset }),
      onBrush: (range: { start: Date; end: Date }) => {
        // Handle brush selection
        console.log('Brush selection:', range)
      }
    },
    containerRef,
    reset,
    zoomTo,
    panTo,
    setCrosshair,
    selectPoints,
    clearSelection
  }
}