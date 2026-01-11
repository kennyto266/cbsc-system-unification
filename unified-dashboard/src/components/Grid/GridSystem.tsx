/**
 * Grid System Component - Responsive 12-column grid layout for widgets
 * Manages the overall grid container and provides context for grid items
 */

import React, { useCallback, useRef, useState, useEffect } from 'react'
import { GridItem } from './GridItem'
import { GridProvider } from './GridProvider'
import { GridLayout, GridItem as GridItemType } from '../../types/grid'
import { useGridLayout } from '../../hooks/useGridLayout'
import { useWidgetManager } from '../../hooks/useWidgetManager'

interface GridSystemProps {
  layout: GridLayout
  onLayoutChange?: (layout: GridLayout) => void
  className?: string
  children?: React.ReactNode
  isDraggable?: boolean
  isResizable?: boolean
  cols?: number
  rowHeight?: number
  margin?: [number, number]
  containerPadding?: [number, number]
  onDragStart?: (layout: GridItemType[], oldItem: GridItemType, newItem: GridItemType, placeholder: GridItemType, e: MouseEvent, element: HTMLElement) => void
  onDrag?: (layout: GridItemType[], oldItem: GridItemType, newItem: GridItemType, placeholder: GridItemType, e: MouseEvent, element: HTMLElement) => void
  onDragEnd?: (layout: GridItemType[], oldItem: GridItemType, newItem: GridItemType, placeholder: GridItemType, e: MouseEvent, element: HTMLElement) => void
  onResizeStart?: (layout: GridItemType[], oldItem: GridItemType, newItem: GridItemType, placeholder: GridItemType, e: MouseEvent, element: HTMLElement) => void
  onResize?: (layout: GridItemType[], oldItem: GridItemType, newItem: GridItemType, placeholder: GridItemType, e: MouseEvent, element: HTMLElement) => void
  onResizeEnd?: (layout: GridItemType[], oldItem: GridItemType, newItem: GridItemType, placeholder: GridItemType, e: MouseEvent, element: HTMLElement) => void
}

export const GridSystem: React.FC<GridSystemProps> = ({
  layout,
  onLayoutChange,
  className = '',
  children,
  isDraggable = true,
  isResizable = true,
  cols = 12,
  rowHeight = 100,
  margin = [16, 16],
  containerPadding = [16, 16],
  onDragStart,
  onDrag,
  onDragEnd,
  onResizeStart,
  onResize,
  onResizeEnd,
}) => {
  const gridRef = useRef<HTMLDivElement>(null)
  const [containerWidth, setContainerWidth] = useState(1200)
  const [gridSpacing] = useState(margin[0])
  const { activeDraggingId, setActiveDraggingId } = useGridLayout()
  const { widgets } = useWidgetManager()

  // Handle container resize
  useEffect(() => {
    const handleResize = () => {
      if (gridRef.current) {
        setContainerWidth(gridRef.current.offsetWidth)
      }
    }

    // Initial measurement
    handleResize()

    // Set up resize observer
    const resizeObserver = new ResizeObserver(handleResize)
    if (gridRef.current) {
      resizeObserver.observe(gridRef.current)
    }

    return () => {
      resizeObserver.disconnect()
    }
  }, [])

  // Handle layout change
  const handleLayoutChange = useCallback((newLayout: GridLayout) => {
    onLayoutChange?.(newLayout)
  }, [onLayoutChange])

  // Grid item event handlers
  const handleDragStart = useCallback((itemId: string) => {
    setActiveDraggingId(itemId)

    const item = layout.find(i => i.id === itemId)
    if (item && onDragStart) {
      const placeholder = { ...item }
      onDragStart(layout, item, item, placeholder, new MouseEvent('dragstart') as any, document.documentElement)
    }
  }, [layout, setActiveDraggingId, onDragStart])

  const handleDrag = useCallback((itemId: string, x: number, y: number) => {
    const itemIndex = layout.findIndex(i => i.id === itemId)
    if (itemIndex === -1) return

    const newLayout = [...layout]
    const oldItem = { ...newLayout[itemIndex] }
    newLayout[itemIndex] = {
      ...oldItem,
      x: Math.max(0, Math.min(x, cols - oldItem.w)),
      y: Math.max(0, y),
    }

    if (onDrag) {
      const placeholder = { ...newLayout[itemIndex] }
      onDrag(newLayout, oldItem, newLayout[itemIndex], placeholder, new MouseEvent('drag') as any, document.documentElement)
    }

    handleLayoutChange(newLayout)
  }, [layout, cols, onDrag, handleLayoutChange])

  const handleDragStop = useCallback((itemId: string, x: number, y: number) => {
    setActiveDraggingId(null)

    const itemIndex = layout.findIndex(i => i.id === itemId)
    if (itemIndex === -1) return

    const newLayout = [...layout]
    const oldItem = { ...newLayout[itemIndex] }
    newLayout[itemIndex] = {
      ...oldItem,
      x: Math.max(0, Math.min(x, cols - oldItem.w)),
      y: Math.max(0, y),
    }

    if (onDragEnd) {
      const placeholder = { ...newLayout[itemIndex] }
      onDragEnd(newLayout, oldItem, newLayout[itemIndex], placeholder, new MouseEvent('dragend') as any, document.documentElement)
    }

    handleLayoutChange(newLayout)
  }, [layout, cols, setActiveDraggingId, onDragEnd, handleLayoutChange])

  const handleResizeStart = useCallback((itemId: string) => {
    const item = layout.find(i => i.id === itemId)
    if (item && onResizeStart) {
      const placeholder = { ...item }
      onResizeStart(layout, item, item, placeholder, new MouseEvent('resizestart') as any, document.documentElement)
    }
  }, [layout, onResizeStart])

  const handleResize = useCallback((itemId: string, direction: string, ref: HTMLElement, delta: any, position: any) => {
    if (onResize) {
      const item = layout.find(i => i.id === itemId)
      if (item) {
        const placeholder = { ...item }
        onResize(layout, item, placeholder, placeholder, new MouseEvent('resize') as any, document.documentElement)
      }
    }
  }, [layout, onResize])

  const handleResizeStop = useCallback((itemId: string, x: number, y: number, width: number, height: number) => {
    const itemIndex = layout.findIndex(i => i.id === itemId)
    if (itemIndex === -1) return

    const newLayout = [...layout]
    const oldItem = { ...newLayout[itemIndex] }
    newLayout[itemIndex] = {
      ...oldItem,
      x: Math.max(0, Math.min(x, cols - width)),
      y: Math.max(0, y),
      w: Math.max(oldItem.minW || 1, Math.min(width, oldItem.maxW || cols)),
      h: Math.max(oldItem.minH || 1, height),
    }

    if (onResizeEnd) {
      const placeholder = { ...newLayout[itemIndex] }
      onResizeEnd(newLayout, oldItem, newLayout[itemIndex], placeholder, new MouseEvent('resizeend') as any, document.documentElement)
    }

    handleLayoutChange(newLayout)
  }, [layout, cols, onResizeEnd, handleLayoutChange])

  // Generate grid styles
  const gridStyles = {
    display: 'grid',
    gridTemplateColumns: `repeat(${cols}, 1fr)`,
    gap: `${gridSpacing}px`,
    padding: `${containerPadding[1]}px ${containerPadding[0]}px`,
    minHeight: '600px',
    position: 'relative' as const,
    width: '100%',
  }

  // Calculate grid height based on items
  const gridHeight = layout.reduce((maxY, item) => {
    return Math.max(maxY, item.y + item.h)
  }, 0)

  return (
    <GridProvider
      value={{
        cols,
        rowHeight,
        margin,
        containerPadding,
        containerWidth,
        gridSpacing,
        isDraggable,
        isResizable,
      }}
    >
      <div
        ref={gridRef}
        className={`grid-system ${className}`}
        style={{
          ...gridStyles,
          height: `${gridHeight * rowHeight + (gridHeight - 1) * gridSpacing + containerPadding[1] * 2}px`,
        }}
      >
        {layout.map((item) => {
          const widget = widgets.find(w => w.id === item.id)
          if (!widget || item.isMinimized) return null

          return (
            <GridItem
              key={item.id}
              item={item}
              isDragging={activeDraggingId === item.id}
              onDragStart={handleDragStart}
              onDrag={handleDrag}
              onDragStop={handleDragStop}
              onResizeStart={handleResizeStart}
              onResize={handleResize}
              onResizeStop={handleResizeStop}
              gridSpacing={gridSpacing}
              containerWidth={containerWidth}
              cols={cols}
              rowHeight={rowHeight}
            />
          )
        })}
        {children}
      </div>
    </GridProvider>
  )
}