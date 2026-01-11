/**
 * Grid Calculation Utilities - Helper functions for grid layout calculations
 */

import { GridItem } from '../types/grid'

// Convert grid coordinates to pixels
export const gridToPixels = (
  gridUnits: number,
  containerWidth: number,
  cols: number,
  gridSpacing: number
): number => {
  const columnWidth = (containerWidth - (cols - 1) * gridSpacing) / cols
  return gridUnits * columnWidth + (gridUnits - 1) * gridSpacing
}

// Convert pixels to grid coordinates
export const pixelsToGrid = (
  pixels: number,
  containerWidth: number,
  cols: number,
  gridSpacing: number
): number => {
  const columnWidth = (containerWidth - (cols - 1) * gridSpacing) / cols
  const columnWidthWithSpacing = columnWidth + gridSpacing
  return Math.round(pixels / columnWidthWithSpacing)
}

// Constrain value within range
export const constrainValue = (value: number, min: number, max: number): number => {
  return Math.max(min, Math.min(value, max))
}

// Check if two rectangles overlap
export const rectanglesOverlap = (
  rect1: { x: number; y: number; w: number; h: number },
  rect2: { x: number; y: number; w: number; h: number }
): boolean => {
  return !(
    rect1.x + rect1.w <= rect2.x || // rect1 is to the left of rect2
    rect1.x >= rect2.x + rect2.w || // rect1 is to the right of rect2
    rect1.y + rect1.h <= rect2.y || // rect1 is above rect2
    rect1.y >= rect2.y + rect2.h // rect1 is below rect2
  )
}

// Check if position is valid for a grid item
export const isValidPosition = (
  x: number,
  y: number,
  w: number,
  h: number,
  cols: number,
  layout: GridItem[],
  excludeId?: string
): boolean => {
  // Check if within grid bounds
  if (x < 0 || y < 0 || x + w > cols) {
    return false
  }

  // Check for collisions with other items
  const itemRect = { x, y, w, h }
  for (const layoutItem of layout) {
    if (layoutItem.id === excludeId) continue

    const layoutRect = {
      x: layoutItem.x,
      y: layoutItem.y,
      w: layoutItem.w,
      h: layoutItem.h,
    }

    if (rectanglesOverlap(itemRect, layoutRect)) {
      return false
    }
  }

  return true
}

// Find valid position for a new item
export const findValidPosition = (
  w: number,
  h: number,
  cols: number,
  layout: GridItem[],
  excludeId?: string,
  startY = 0
): { x: number; y: number } => {
  // Try to find position at specified Y coordinate first
  for (let x = 0; x <= cols - w; x++) {
    if (isValidPosition(x, startY, w, h, cols, layout, excludeId)) {
      return { x, y: startY }
    }
  }

  // Search entire grid
  for (let y = 0; y < 100; y++) {
    for (let x = 0; x <= cols - w; x++) {
      if (isValidPosition(x, y, w, h, cols, layout, excludeId)) {
        return { x, y }
      }
    }
  }

  // Fallback: place at the bottom
  const maxY = Math.max(...layout.map(item => item.y + item.h), 0)
  return { x: 0, y: maxY }
}

// Compact layout vertically
export const compactVertical = (layout: GridItem[]): GridItem[] => {
  const sortedLayout = [...layout].sort((a, b) => a.y - b.y || a.x - b.x)
  const compactedLayout: GridItem[] = []

  for (const item of sortedLayout) {
    let placed = false
    let y = 0

    while (!placed) {
      const canPlace = compactedLayout.every(placedItem => {
        return !rectanglesOverlap(
          { x: item.x, y, w: item.w, h: item.h },
          { x: placedItem.x, y: placedItem.y, w: placedItem.w, h: placedItem.h }
        )
      })

      if (canPlace) {
        compactedLayout.push({ ...item, y })
        placed = true
      } else {
        y += 1
      }
    }
  }

  return compactedLayout
}

// Compact layout horizontally
export const compactHorizontal = (layout: GridItem[], cols: number): GridItem[] => {
  const sortedLayout = [...layout].sort((a, b) => a.x - b.x || a.y - b.y)
  const compactedLayout: GridItem[] = []

  for (const item of sortedLayout) {
    let placed = false
    let x = 0

    while (!placed && x <= cols - item.w) {
      const canPlace = compactedLayout.every(placedItem => {
        return !rectanglesOverlap(
          { x, y: item.y, w: item.w, h: item.h },
          { x: placedItem.x, y: placedItem.y, w: placedItem.w, h: placedItem.h }
        )
      })

      if (canPlace) {
        compactedLayout.push({ ...item, x })
        placed = true
      } else {
        x += 1
      }
    }

    if (!placed) {
      // If couldn't place horizontally, place in next row
      const maxY = Math.max(...compactedLayout.map(item => item.y + item.h), 0)
      compactedLayout.push({ ...item, x: 0, y: maxY })
    }
  }

  return compactedLayout
}

// Move item to closest valid position
export const moveItemToValidPosition = (
  layout: GridItem[],
  id: string,
  targetX: number,
  targetY: number,
  cols: number
): GridItem => {
  const item = layout.find(i => i.id === id)
  if (!item) return { id, x: targetX, y: targetY, w: 1, h: 1, isDraggable: true, isResizable: true }

  // Constrain within bounds
  const constrainedX = constrainValue(targetX, 0, cols - item.w)
  const constrainedY = Math.max(0, targetY)

  // Check if position is valid
  if (isValidPosition(constrainedX, constrainedY, item.w, item.h, cols, layout, id)) {
    return { ...item, x: constrainedX, y: constrainedY }
  }

  // Find nearest valid position
  const validPosition = findValidPosition(item.w, item.h, cols, layout, id)
  return { ...item, x: validPosition.x, y: validPosition.y }
}

// Calculate grid height based on items
export const calculateGridHeight = (
  layout: GridItem[],
  rowHeight: number,
  gridSpacing: number
): number => {
  if (layout.length === 0) return 0

  const maxY = Math.max(...layout.map(item => item.y + item.h))
  return maxY * rowHeight + (maxY - 1) * gridSpacing
}

// Get item bounds in pixels
export const getItemBounds = (
  item: GridItem,
  containerWidth: number,
  cols: number,
  rowHeight: number,
  gridSpacing: number
) => {
  const left = gridToPixels(item.x, containerWidth, cols, gridSpacing)
  const top = item.y * rowHeight
  const width = gridToPixels(item.w, containerWidth, cols, gridSpacing)
  const height = item.h * rowHeight

  return { left, top, width, height }
}

// Calculate distance between two points
export const calculateDistance = (x1: number, y1: number, x2: number, y2: number): number => {
  return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2))
}

// Snap value to grid
export const snapToGrid = (value: number, gridSize: number): number => {
  return Math.round(value / gridSize) * gridSize
}