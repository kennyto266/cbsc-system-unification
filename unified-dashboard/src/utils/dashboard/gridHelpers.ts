import { GridItem, GridLayout, WidgetEvent, Breakpoint } from '../../types/dashboard/grid'

/**
 * Generate unique ID for grid items
 */
export const generateId = (): string => {
  return `widget_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Create new grid item
 */
export const createGridItem = (
  type: string,
  title: string,
  position: { x: number; y: number },
  size: { w: number; h: number }
): GridItem => {
  return {
    id: generateId(),
    type: type as any,
    title,
    position,
    size,
    isResizable: true,
    isDraggable: true,
    isMinimized: false,
    isMaximized: false,
    isVisible: true,
    config: {},
    version: '1.0.0',
    lastUpdated: new Date().toISOString(),
  }
}

/**
 * Validate grid layout
 */
export const validateGridLayout = (layout: GridLayout): string[] => => {
  const errors: string[] = []

  // Check for duplicate IDs
  const ids = layout.items.map(item => item.id)
  const duplicateIds = ids.filter((id, index) => ids.indexOf(id) !== index)
  if (duplicateIds.length > 0) {
    errors.push(`Duplicate widget IDs found: ${duplicateIds.join(', ')}`)
  }

  // Check for overlapping items
  for (let i = 0; i < layout.items.length; i++) {
    for (let j = i + 1; j < layout.items.length; j++) {
      if (isOverlapping(layout.items[i], layout.items[j])) {
        errors.push(`Widgets ${layout.items[i].id} and ${layout.items[j].id} are overlapping`)
      }
    }
  }

  // Check for out-of-bounds items
  const activeBreakpoint = layout.activeBreakpoint || 'lg'
  const config = layout.breakpoints[activeBreakpoint]

  layout.items.forEach(item => {
    if (item.position.x < 0 || item.position.y < 0) {
      errors.push(`Widget ${item.id} has negative position`)
    }
    if (item.position.x + item.size.w > config.cols) {
      errors.push(`Widget ${item.id} exceeds grid width`)
    }
  })

  return errors
}

/**
 * Check if two grid items are overlapping
 */
export const isOverlapping = (item1: GridItem, item2: GridItem): boolean => {
  return !(
    item1.position.x + item1.size.w <= item2.position.x ||
    item2.position.x + item2.size.w <= item1.position.x ||
    item1.position.y + item1.size.h <= item2.position.y ||
    item2.position.y + item2.size.h <= item1.position.y
  )
}

/**
 * Find empty space in grid
 */
export const findEmptySpace = (
  items: GridItem[],
  cols: number,
  width: number,
  height: number,
  startX = 0,
  startY = 0
): { x: number; y: number } | null => {
  // Simple grid search algorithm
  for (let y = startY; y < 100; y++) {
    for (let x = startX; x <= cols - width; x++) {
      const testItem = {
        id: 'test',
        type: 'market-overview' as any,
        title: 'test',
        position: { x, y },
        size: { w: width, h: height },
      }

      const hasOverlap = items.some(item => isOverlapping(item, testItem))

      if (!hasOverlap) {
        return { x, y }
      }
    }
  }

  return null
}

/**
 * Compact layout to remove empty spaces
 */
export const compactLayout = (
  items: GridItem[],
  cols: number,
  compactType: 'vertical' | 'horizontal' = 'vertical'
): GridItem[] => {
  const sorted = [...items].sort((a, b) => {
    if (compactType === 'vertical') {
      return a.position.y - b.position.y || a.position.x - b.position.x
    } else {
      return a.position.x - b.position.x || a.position.y - b.position.y
    }
  })

  const compacted: GridItem[] = []
  const occupied = new Set<string>()

  for (const item of sorted) {
    let newX = 0
    let newY = 0

    if (compactType === 'vertical') {
      // Find first available spot in vertical order
      for (let y = 0; y < 100; y++) {
        for (let x = 0; x <= cols - item.size.w; x++) {
          const fits = checkFit(item, x, y, compacted, cols)
          if (fits) {
            newX = x
            newY = y
            break
          }
        }
        if (newX !== 0 || newY !== 0) break
      }
    } else {
      // Find first available spot in horizontal order
      for (let x = 0; x <= cols - item.size.w; x++) {
        for (let y = 0; y < 100; y++) {
          const fits = checkFit(item, x, y, compacted, cols)
          if (fits) {
            newX = x
            newY = y
            break
          }
        }
        if (newX !== 0 || newY !== 0) break
      }
    }

    compacted.push({
      ...item,
      position: { x: newX, y: newY },
    })
  }

  return compacted
}

/**
 * Check if item fits at position
 */
const checkFit = (
  item: GridItem,
  x: number,
  y: number,
  placedItems: GridItem[],
  cols: number
): boolean => {
  // Check grid boundaries
  if (x < 0 || y < 0 || x + item.size.w > cols) {
    return false
  }

  // Check overlap with placed items
  const testItem = { ...item, position: { x, y } }
  return !placedItems.some(placed => isOverlapping(testItem, placed))
}

/**
 * Move widget to new position
 */
export const moveWidget = (
  items: GridItem[],
  widgetId: string,
  newPosition: { x: number; y: number }
): GridItem[] => {
  return items.map(item =>
    item.id === widgetId
      ? { ...item, position: newPosition, lastUpdated: new Date().toISOString() }
      : item
  )
}

/**
 * Resize widget
 */
export const resizeWidget = (
  items: GridItem[],
  widgetId: string,
  newSize: { w: number; h: number }
): GridItem[] => {
  return items.map(item =>
    item.id === widgetId
      ? { ...item, size: newSize, lastUpdated: new Date().toISOString() }
      : item
  )
}

/**
 * Add widget to layout
 */
export const addWidget = (
  items: GridItem[],
  newWidget: GridItem,
  cols: number
): GridItem[] => {
  // Find empty space for the widget
  const position = findEmptySpace(
    items,
    cols,
    newWidget.size.w,
    newWidget.size.h
  )

  if (!position) {
    // If no space found, add to the bottom
    const maxY = Math.max(...items.map(item => item.position.y + item.size.h), 0)
    newWidget.position = { x: 0, y: maxY }
  } else {
    newWidget.position = position
  }

  return [...items, newWidget]
}

/**
 * Remove widget from layout
 */
export const removeWidget = (items: GridItem[], widgetId: string): GridItem[] => {
  return items.filter(item => item.id !== widgetId)
}

/**
 * Duplicate widget
 */
export const duplicateWidget = (
  items: GridItem[],
  widgetId: string,
  cols: number
): GridItem[] => {
  const originalItem = items.find(item => item.id === widgetId)
  if (!originalItem) return items

  const duplicatedItem = {
    ...originalItem,
    id: generateId(),
    title: `${originalItem.title} (Copy)`,
  }

  return addWidget(items, duplicatedItem, cols)
}

/**
 * Get widget by ID
 */
export const getWidgetById = (items: GridItem[], widgetId: string): GridItem | null => {
  return items.find(item => item.id === widgetId) || null
}

/**
 * Update widget configuration
 */
export const updateWidgetConfig = (
  items: GridItem[],
  widgetId: string,
  config: Record<string, any>
): GridItem[] => {
  return items.map(item =>
    item.id === widgetId
      ? {
          ...item,
          config: { ...item.config, ...config },
          lastUpdated: new Date().toISOString(),
        }
      : item
  )
}

/**
 * Create widget event
 */
export const createWidgetEvent = (
  type: WidgetEvent['type'],
  widgetId: string,
  data?: any
): WidgetEvent => {
  return {
    type,
    widgetId,
    data,
    timestamp: new Date().toISOString(),
  }
}

/**
 * Export layout to JSON
 */
export const exportLayout = (layout: GridLayout): string => {
  return JSON.stringify(layout, null, 2)
}

/**
 * Import layout from JSON
 */
export const importLayout = (jsonString: string): GridLayout | null => {
  try {
    const layout = JSON.parse(jsonString)
    // Validate layout structure
    if (!layout.id || !layout.items || !Array.isArray(layout.items)) {
      throw new Error('Invalid layout structure')
    }
    return layout as GridLayout
  } catch (error) {
    console.error('Failed to import layout:', error)
    return null
  }
}

/**
 * Get layout statistics
 */
export const getLayoutStats = (layout: GridLayout) => {
  const totalWidgets = layout.items.length
  const visibleWidgets = layout.items.filter(item => item.isVisible !== false).length
  const minimizedWidgets = layout.items.filter(item => item.isMinimized).length
  const maximizedWidgets = layout.items.filter(item => item.isMaximized).length

  // Calculate total grid area used
  const activeBreakpoint = layout.activeBreakpoint || 'lg'
  const cols = layout.breakpoints[activeBreakpoint].cols
  const totalCells = layout.items.reduce((sum, item) => sum + (item.size.w * item.size.h), 0)
  const gridCells = cols * 100 // Assuming 100 rows max

  return {
    totalWidgets,
    visibleWidgets,
    minimizedWidgets,
    maximizedWidgets,
    totalCells,
    gridCells,
    utilizationRate: (totalCells / gridCells) * 100,
  }
}