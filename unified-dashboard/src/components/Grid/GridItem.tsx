/**
 * Grid Item Component - Represents a single widget container in the grid
 * Provides resizing and dragging capabilities
 */

import React, { useRef, useCallback } from 'react'
import { Rnd } from 'react-rnd'
import { Widget } from '../Widget/Widget'
import { GridItem as GridItemType } from '../../types/grid'
import { useWidgetManager } from '../../hooks/useWidgetManager'

interface GridItemProps {
  item: GridItemType
  isDragging: boolean
  onDragStart: (id: string) => void
  onDrag: (id: string, x: number, y: number) => void
  onDragStop: (id: string, x: number, y: number) => void
  onResizeStart: (id: string) => void
  onResize: (id: string, direction: string, ref: HTMLElement, delta: any, position: any) => void
  onResizeStop: (id: string, x: number, y: number, width: number, height: number) => void
  gridSpacing: number
  containerWidth: number
  cols: number
  rowHeight: number
}

export const GridItem: React.FC<GridItemProps> = ({
  item,
  isDragging,
  onDragStart,
  onDrag,
  onDragStop,
  onResizeStart,
  onResize,
  onResizeStop,
  gridSpacing,
  containerWidth,
  cols,
  rowHeight,
}) => {
  const { removeWidget, updateWidget } = useWidgetManager()
  const itemRef = useRef<HTMLDivElement>(null)

  // Convert grid coordinates to pixels
  const gridToPixels = useCallback((gridUnits: number) => {
    return Math.round((gridUnits / cols) * (containerWidth - (cols - 1) * gridSpacing))
  }, [containerWidth, cols, gridSpacing])

  // Convert pixels to grid coordinates
  const pixelsToGrid = useCallback((pixels: number) => {
    return Math.round((pixels / containerWidth) * cols)
  }, [containerWidth, cols])

  // Calculate pixel dimensions from grid coordinates
  const width = gridToPixels(item.w)
  const height = item.h * rowHeight
  const x = gridToPixels(item.x)
  const y = item.y * rowHeight

  const handleDragStart = useCallback(() => {
    onDragStart(item.id)
  }, [item.id, onDragStart])

  const handleDrag = useCallback((e: any, data: any) => {
    const gridX = Math.round((data.x / containerWidth) * cols)
    const gridY = Math.round(data.y / rowHeight)
    onDrag(item.id, gridX, gridY)
  }, [item.id, onDrag, containerWidth, cols, rowHeight])

  const handleDragStop = useCallback((e: any, data: any) => {
    const gridX = Math.round((data.x / containerWidth) * cols)
    const gridY = Math.round(data.y / rowHeight)
    onDragStop(item.id, gridX, gridY)
  }, [item.id, onDragStop, containerWidth, cols, rowHeight])

  const handleResizeStart = useCallback(() => {
    onResizeStart(item.id)
  }, [item.id, onResizeStart])

  const handleResize = useCallback((direction: string, ref: HTMLElement, delta: any, position: any) => {
    const newWidth = pixelsToGrid(ref.offsetWidth)
    const newHeight = Math.round(ref.offsetHeight / rowHeight)
    onResize(item.id, direction, ref, delta, position)

    // Update item dimensions during resize for immediate visual feedback
    updateWidget(item.id, {
      ...item,
      w: Math.max(item.minW || 1, newWidth),
      h: Math.max(item.minH || 1, newHeight),
    })
  }, [item.id, item, onResize, pixelsToGrid, rowHeight, updateWidget])

  const handleResizeStop = useCallback((e: any, direction: string, ref: HTMLElement, delta: any, position: any) => {
    const gridX = Math.round((position.x / containerWidth) * cols)
    const gridY = Math.round(position.y / rowHeight)
    const newWidth = pixelsToGrid(ref.offsetWidth)
    const newHeight = Math.round(ref.offsetHeight / rowHeight)

    onResizeStop(item.id, gridX, gridY, newWidth, newHeight)
  }, [item.id, onResizeStop, containerWidth, cols, rowHeight, pixelsToGrid])

  const handleClose = useCallback(() => {
    removeWidget(item.id)
  }, [item.id, removeWidget])

  return (
    <Rnd
      ref={itemRef}
      size={{
        width,
        height,
      }}
      position={{
        x,
        y,
      }}
      onDragStart={handleDragStart}
      onDrag={handleDrag}
      onDragStop={handleDragStop}
      onResizeStart={handleResizeStart}
      onResize={handleResize}
      onResizeStop={handleResizeStop}
      dragHandleClassName="widget-drag-handle"
      enableResizing={{
        top: false,
        right: true,
        bottom: true,
        left: false,
        topRight: false,
        bottomRight: true,
        bottomLeft: false,
        topLeft: false,
      }}
      minWidth={gridToPixels(item.minW || 1)}
      minHeight={item.minH ? item.minH * rowHeight : rowHeight}
      maxWidth={gridToPixels(item.maxW || cols)}
      maxHeight={item.maxH ? item.maxH * rowHeight : Infinity}
      bounds="parent"
      dragAxis="both"
      resizeGrid={[gridSpacing, rowHeight]}
      dragGrid={[gridSpacing, rowHeight]}
      className={`grid-item ${isDragging ? 'dragging' : ''}`}
      style={{
        zIndex: isDragging ? 1000 : item.z || 1,
      }}
    >
      <Widget
        id={item.id}
        type={item.type}
        title={item.title}
        isResizable={true}
        isDraggable={true}
        onClose={handleClose}
        onMinimize={() => updateWidget(item.id, { ...item, isMinimized: true })}
        onMaximize={() => updateWidget(item.id, {
          ...item,
          isMaximized: !item.isMaximized,
          w: item.isMaximized ? item.prevW || item.w : cols,
          h: item.isMaximized ? item.prevH || item.h : 12,
          prevW: item.w,
          prevH: item.h,
        })}
        isMinimized={item.isMinimized}
        isMaximized={item.isMaximized}
      />
    </Rnd>
  )
}