/**
 * useGridLayout Hook - Manages grid layout state and operations
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { GridLayout, GridItem } from '../types/grid'

interface UseGridLayoutProps {
  initialLayout?: GridLayout
  cols?: number
  rowHeight?: number
  autoArrange?: boolean
  compactType?: 'vertical' | 'horizontal' | null
  preventCollision?: boolean
}

export const useGridLayout = ({
  initialLayout = [],
  cols = 12,
  rowHeight = 100,
  autoArrange = true,
  compactType = 'vertical',
  preventCollision = false,
}: UseGridLayoutProps = {}) => {
  const [layout, setLayout] = useState<GridLayout>(initialLayout)
  const [activeDraggingId, setActiveDraggingId] = useState<string | null>(null)
  const [activeResizingId, setActiveResizingId] = useState<string | null>(null)
  const layoutRef = useRef(layout)

  // Update ref when layout changes
  useEffect(() => {
    layoutRef.current = layout
  }, [layout])

  // Generate unique ID for new items
  const generateId = useCallback(() => {
    return `widget_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }, [])

  // Check if position is occupied
  const isPositionOccupied = useCallback((x: number, y: number, w: number, h: number, excludeId?: string) => {
    return layout.some(item => {
      if (item.id === excludeId) return false

      // Check if rectangles overlap
      return !(
        x + w <= item.x || // Item is to the left
        x >= item.x + item.w || // Item is to the right
        y + h <= item.y || // Item is above
        y >= item.y + item.h // Item is below
      )
    })
  }, [layout])

  // Find first available position
  const findAvailablePosition = useCallback((w: number, h: number, excludeId?: string) => {
    if (!autoArrange) {
      // If auto-arrange is disabled, return a default position
      return { x: 0, y: 0 }
    }

    for (let y = 0; y < 100; y++) {
      for (let x = 0; x <= cols - w; x++) {
        if (!isPositionOccupied(x, y, w, h, excludeId)) {
          return { x, y }
        }
      }
    }

    // If no position found, place at the bottom
    const maxY = Math.max(...layout.map(item => item.y + item.h), 0)
    return { x: 0, y: maxY }
  }, [autoArrange, cols, isPositionOccupied, layout])

  // Add new item to layout
  const addItem = useCallback((
    item: Omit<GridItem, 'id'> & { id?: string }
  ) => {
    const id = item.id || generateId()
    const newItem: GridItem = {
      id,
      x: 0,
      y: 0,
      w: item.w || 4,
      h: item.h || 4,
      minW: item.minW || 1,
      minH: item.minH || 1,
      maxW: item.maxW || cols,
      maxH: item.maxH || Infinity,
      isDraggable: item.isDraggable ?? true,
      isResizable: item.isResizable ?? true,
      ...item,
    }

    // Find available position
    const position = findAvailablePosition(newItem.w, newItem.h)
    newItem.x = position.x
    newItem.y = position.y

    setLayout(prev => [...prev, newItem])
    return id
  }, [generateId, cols, findAvailablePosition])

  // Remove item from layout
  const removeItem = useCallback((id: string) => {
    setLayout(prev => prev.filter(item => item.id !== id))
  }, [])

  // Update item in layout
  const updateItem = useCallback((id: string, updates: Partial<GridItem>) => {
    setLayout(prev => prev.map(item =>
      item.id === id ? { ...item, ...updates } : item
    ))
  }, [])

  // Move item to new position
  const moveItem = useCallback((id: string, x: number, y: number) => {
    const item = layout.find(i => i.id === id)
    if (!item || !item.isDraggable) return

    // Constrain position within grid
    const constrainedX = Math.max(0, Math.min(x, cols - item.w))
    const constrainedY = Math.max(0, y)

    updateItem(id, { x: constrainedX, y: constrainedY })
  }, [layout, cols, updateItem])

  // Resize item
  const resizeItem = useCallback((
    id: string,
    w: number,
    h: number,
    x?: number,
    y?: number
  ) => {
    const item = layout.find(i => i.id === id)
    if (!item || !item.isResizable) return

    // Constrain size within limits
    const constrainedW = Math.max(item.minW || 1, Math.min(w, item.maxW || cols))
    const constrainedH = Math.max(item.minH || 1, Math.min(h, item.maxH || Infinity))

    // Constrain position if size changed and position provided
    let constrainedX = x
    let constrainedY = y
    if (x !== undefined && y !== undefined) {
      constrainedX = Math.max(0, Math.min(x, cols - constrainedW))
      constrainedY = Math.max(0, y)
    }

    updateItem(id, {
      w: constrainedW,
      h: constrainedH,
      ...(constrainedX !== undefined && { x: constrainedX }),
      ...(constrainedY !== undefined && { y: constrainedY }),
    })
  }, [layout, cols, updateItem])

  // Compact layout to remove empty spaces
  const compactLayout = useCallback((type: 'vertical' | 'horizontal' = 'vertical') => {
    const newLayout = [...layout]
    const sortedLayout = type === 'vertical'
      ? newLayout.sort((a, b) => a.y - b.y || a.x - b.x)
      : newLayout.sort((a, b) => a.x - b.x || a.y - b.y)

    const compactedLayout: GridItem[] = []
    const occupiedPositions = new Set<string>()

    for (const item of sortedLayout) {
      let placed = false
      let newX = 0
      let newY = 0

      // Try to place item at the earliest possible position
      while (!placed) {
        if (!isPositionOccupied(newX, newY, item.w, item.h, item.id)) {
          // Check if this position conflicts with already placed items
          let hasConflict = false
          for (const placedItem of compactedLayout) {
            if (
              newX < placedItem.x + placedItem.w &&
              newX + item.w > placedItem.x &&
              newY < placedItem.y + placedItem.h &&
              newY + item.h > placedItem.y
            ) {
              hasConflict = true
              break
            }
          }

          if (!hasConflict) {
            compactedLayout.push({ ...item, x: newX, y: newY })
            placed = true
          }
        }

        if (!placed) {
          if (type === 'vertical') {
            newX += 1
            if (newX > cols - item.w) {
              newX = 0
              newY += 1
            }
          } else {
            newY += 1
          }
        }
      }
    }

    setLayout(compactedLayout)
  }, [layout, cols, isPositionOccupied])

  // Reset layout to initial state
  const resetLayout = useCallback(() => {
    setLayout(initialLayout)
  }, [initialLayout])

  // Clear all items
  const clearLayout = useCallback(() => {
    setLayout([])
  }, [])

  // Get layout as JSON for persistence
  const getLayoutAsJSON = useCallback(() => {
    return JSON.stringify(layout)
  }, [layout])

  // Load layout from JSON
  const loadLayoutFromJSON = useCallback((jsonString: string) => {
    try {
      const parsedLayout = JSON.parse(jsonString)
      if (Array.isArray(parsedLayout)) {
        setLayout(parsedLayout)
      }
    } catch (error) {
      console.error('Failed to load layout from JSON:', error)
    }
  }, [])

  return {
    layout,
    activeDraggingId,
    activeResizingId,
    setActiveDraggingId,
    setActiveResizingId,
    addItem,
    removeItem,
    updateItem,
    moveItem,
    resizeItem,
    compactLayout,
    resetLayout,
    clearLayout,
    getLayoutAsJSON,
    loadLayoutFromJSON,
    isPositionOccupied,
    findAvailablePosition,
  }
}