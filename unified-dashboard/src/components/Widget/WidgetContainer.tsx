/**
 * Widget Container - Manages widget rendering and provides common functionality
 */

import React from 'react'
import { Widget } from './Widget'
import { WidgetType } from '../../types/widget'

interface WidgetContainerProps {
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

export const WidgetContainer: React.FC<WidgetContainerProps> = ({
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
  return (
    <Widget
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
    </Widget>
  )
}