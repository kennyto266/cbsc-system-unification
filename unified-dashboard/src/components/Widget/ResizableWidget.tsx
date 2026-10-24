/**
 * Resizable Widget - Wrapper component that enables resize functionality
 */

import React, { useState, useCallback } from 'react'
import { ResizableBox } from 'react-resizable'
import { WidgetContainer } from './WidgetContainer'
import { WidgetType } from '../../types/widget'
import { useGridContext } from '../Grid/GridProvider'

interface ResizableWidgetProps {
  id: string
  type: WidgetType
  title: string
  children: React.ReactNode
  width: number
  height: number
  minConstraints?: [number, number]
  maxConstraints?: [number, number]
  isResizable?: boolean
  isDraggable?: boolean
  onClose?: () => void
  onMinimize?: () => void
  onMaximize?: () => void
  onSettings?: () => void
  isMinimized?: boolean
  isMaximized?: boolean
  className?: string
  extra?: React.ReactNode
  onResize?: (width: number, height: number) => void
  onResizeStop?: (width: number, height: number) => void
}

export const ResizableWidget: React.FC<ResizableWidgetProps> = ({
  id,
  type,
  title,
  children,
  width,
  height,
  minConstraints = [200, 150],
  maxConstraints = [Infinity, Infinity],
  isResizable = true,
  isDraggable = true,
  onClose,
  onMinimize,
  onMaximize,
  onSettings,
  isMinimized = false,
  isMaximized = false,
  className = '',
  extra,
  onResize,
  onResizeStop,
}) => {
  const [dimensions, setDimensions] = useState({ width, height })
  const { gridSpacing } = useGridContext()

  const handleResize = useCallback(
    (e: any, data: any) => {
      const newDimensions = {
        width: data.size.width,
        height: data.size.height,
      }
      setDimensions(newDimensions)
      onResize?.(newDimensions.width, newDimensions.height)
    },
    [onResize]
  )

  const handleResizeStop = useCallback(
    (e: any, data: any) => {
      const newDimensions = {
        width: data.size.width,
        height: data.size.height,
      }
      setDimensions(newDimensions)
      onResizeStop?.(newDimensions.width, newDimensions.height)
    },
    [onResizeStop]
  )

  if (!isResizable) {
    return (
      <WidgetContainer
        id={id}
        type={type}
        title={title}
        isResizable={isResizable}
        isDraggable={isDraggable}
        onClose={onClose}
        onMinimize={onMinimize}
        onMaximize={onMaximize}
        onSettings={onSettings}
        isMinimized={isMinimized}
        isMaximized={isMaximized}
        className={className}
        extra={extra}
      >
        {children}
      </WidgetContainer>
    )
  }

  return (
    <ResizableBox
      width={dimensions.width}
      height={dimensions.height}
      minConstraints={minConstraints}
      maxConstraints={maxConstraints}
      onResize={handleResize}
      onResizeStop={handleResizeStop}
      resizeHandles={['se']}
      handle={
        <div className="resize-handle absolute bottom-0 right-0 w-4 h-4 cursor-se-resize opacity-0 hover:opacity-50 transition-opacity">
          <div className="absolute bottom-1 right-1 w-2 h-2 border-r-2 border-b-2 border-gray-400" />
        </div>
      }
      style={{
        margin: gridSpacing,
      }}
      className={className}
    >
      <WidgetContainer
        id={id}
        type={type}
        title={title}
        isResizable={isResizable}
        isDraggable={isDraggable}
        onClose={onClose}
        onMinimize={onMinimize}
        onMaximize={onMaximize}
        onSettings={onSettings}
        isMinimized={isMinimized}
        isMaximized={isMaximized}
        className="h-full"
        extra={extra}
      >
        <div className="h-full overflow-auto">
          {children}
        </div>
      </WidgetContainer>
    </ResizableBox>
  )
}