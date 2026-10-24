/**
 * useDragDrop Hook - Manages drag and drop functionality for widgets
 */

import { useState, useCallback } from 'react'
import { useDraggable, useDroppable } from '@dnd-kit/core'

interface UseDragDropProps {
  id: string
  type: string
  isDraggable?: boolean
  isDroppable?: boolean
}

export const useDragDrop = ({ id, type, isDraggable = true, isDroppable = true }: UseDragDropProps) => {
  const [isDraggingOver, setIsDraggingOver] = useState(false)

  // Draggable configuration
  const {
    attributes,
    listeners,
    setNodeRef: setDraggableRef,
    transform,
    isDragging,
  } = useDraggable({
    id,
    data: {
      type,
      id,
    },
    disabled: !isDraggable,
  })

  // Droppable configuration
  const {
    setNodeRef: setDroppableRef,
    isOver,
  } = useDroppable({
    id,
    disabled: !isDroppable,
  })

  // Combined ref for both draggable and droppable
  const setNodeRef = useCallback((node: HTMLElement | null) => {
    setDraggableRef(node)
    setDroppableRef(node)
  }, [setDraggableRef, setDroppableRef])

  // Update dragging state
  useState(() => {
    setIsDraggingOver(isOver)
  }, [isOver])

  return {
    attributes,
    listeners,
    setNodeRef,
    transform,
    isDragging,
    isDraggingOver: isOver,
    canDrag: isDraggable,
    canDrop: isDroppable,
  }
}