/**
 * Draggable Widget - Wrapper component that enables drag functionality
 */

import React from 'react'
import { useDraggable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import { WidgetContainer } from './WidgetContainer'
import { WidgetType } from '../../types/widget'

interface DraggableWidgetProps {
  id: string
  type: WidgetType
  title: string
  children: React.ReactNode
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
}

export const DraggableWidget: React.FC<DraggableWidgetProps> = ({
  id,
  type,
  title,
  children,
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
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    isDragging,
  } = useDraggable({
    id,
    disabled: !isDraggable,
  })

  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 1000 : undefined,
  }

  if (!isDraggable) {
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
    <div
      ref={setNodeRef}
      style={style}
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
        className={className}
        extra={extra}
      >
        <div
          {...attributes}
          {...listeners}
          className="widget-drag-area"
        >
          {children}
        </div>
      </WidgetContainer>
    </div>
  )
}