import { Breakpoint, GridLayout, GridItem } from '../../types/dashboard/grid'

// Responsive breakpoint configurations
export const BREAKPOINTS: Record<Breakpoint, { min: number; max?: number }> = {
  xs: { min: 0, max: 640 },
  sm: { min: 640, max: 768 },
  md: { min: 768, max: 1024 },
  lg: { min: 1024, max: 1280 },
  xl: { min: 1280, max: 1536 },
  '2xl': { min: 1536, max: 2560 },
  '4xl': { min: 2560 },
}

// Default grid configurations for each breakpoint
export const DEFAULT_GRID_CONFIG = {
  xs: { cols: 1, rowHeight: 120, margin: [4, 4], containerPadding: [8, 8] },
  sm: { cols: 2, rowHeight: 100, margin: [8, 8], containerPadding: [12, 12] },
  md: { cols: 3, rowHeight: 100, margin: [12, 12], containerPadding: [16, 16] },
  lg: { cols: 4, rowHeight: 80, margin: [16, 16], containerPadding: [20, 20] },
  xl: { cols: 6, rowHeight: 80, margin: [20, 20], containerPadding: [24, 24] },
  '2xl': { cols: 8, rowHeight: 80, margin: [24, 24], containerPadding: [32, 32] },
  '4xl': { cols: 12, rowHeight: 80, margin: [32, 32], containerPadding: [40, 40] },
}

/**
 * Get current breakpoint based on window width
 */
export const getCurrentBreakpoint = (width: number): Breakpoint => {
  const sortedBreakpoints = Object.entries(BREAKPOINTS)
    .filter(([_, config]) => width >= config.min && (!config.max || width < config.max))
    .sort(([_, a], [__, b]) => b.min - a.min)

  return sortedBreakpoints[0]?.[0] as Breakpoint || 'lg'
}

/**
 * Get responsive grid configuration
 */
export const getResponsiveGridConfig = (width: number, customConfig?: Partial<typeof DEFAULT_GRID_CONFIG>) => {
  const breakpoint = getCurrentBreakpoint(width)
  const defaultConfig = DEFAULT_GRID_CONFIG[breakpoint]

  return {
    breakpoint,
    ...defaultConfig,
    ...customConfig,
  }
}

/**
 * Adjust widget size for different breakpoints
 */
export const adjustWidgetForBreakpoint = (
  item: GridItem,
  fromBreakpoint: Breakpoint,
  toBreakpoint: Breakpoint
): GridItem => {
  const scaleFactor = DEFAULT_GRID_CONFIG[fromBreakpoint].cols / DEFAULT_GRID_CONFIG[toBreakpoint].cols

  // Adjust width and position
  const newWidth = Math.max(1, Math.round(item.size.w * scaleFactor))
  const newHeight = item.size.h // Keep height the same
  const newX = Math.round(item.position.x * scaleFactor)
  const newY = item.position.y // Keep Y position the same

  return {
    ...item,
    position: { x: newX, y: newY },
    size: {
      ...item.size,
      w: newWidth,
      h: newHeight,
    },
  }
}

/**
 * Optimize layout for mobile devices
 */
export const optimizeForMobile = (items: GridItem[]): GridItem[] => {
  // Sort by Y position, then X position
  const sortedItems = [...items].sort((a, b) => {
    if (a.position.y !== b.position.y) return a.position.y - b.position.y
    return a.position.x - b.position.x
  })

  // Arrange in single column
  let currentY = 0
  return sortedItems.map(item => ({
    ...item,
    position: { x: 0, y: currentY },
    size: {
      ...item.size,
      w: 1, // Full width
    },
  }))
}

/**
 * Optimize layout for tablet devices
 */
export const optimizeForTablet = (items: GridItem[]): GridItem[] => {
  const cols = DEFAULT_GRID_CONFIG.md.cols
  const sortedItems = [...items].sort((a, b) => {
    if (a.position.y !== b.position.y) return a.position.y - b.position.y
    return a.position.x - b.position.x
  })

  let currentY = 0
  let currentX = 0

  return sortedItems.map(item => {
    const itemWidth = Math.min(item.size.w, cols - currentX)

    if (currentX + itemWidth > cols) {
      currentX = 0
      currentY += 1
    }

    const newItem = {
      ...item,
      position: { x: currentX, y: currentY },
      size: {
        ...item.size,
        w: Math.min(item.size.w, cols - currentX),
      },
    }

    currentX += itemWidth

    return newItem
  })
}

/**
 * Generate CSS media queries for breakpoints
 */
export const generateMediaQueries = () => {
  return Object.entries(BREAKPOINTS)
    .map(([key, config]) => {
      if (config.max) {
        return `@media (min-width: ${config.min}px) and (max-width: ${config.max - 1}px)`
      }
      return `@media (min-width: ${config.min}px)`
    })
    .join('\n')
}

/**
 * Check if widget should be visible at breakpoint
 */
export const isWidgetVisible = (
  item: GridItem,
  breakpoint: Breakpoint,
  customRules?: Record<WidgetType, Breakpoint[]>
): boolean => {
  const defaultVisibleBreakpoints: Breakpoint[] = ['md', 'lg', 'xl', '2xl', '4xl']

  if (customRules?.[item.type]) {
    return customRules[item.type].includes(breakpoint)
  }

  return defaultVisibleBreakpoints.includes(breakpoint)
}

/**
 * Calculate optimal widget dimensions
 */
export const calculateOptimalDimensions = (
  widgetType: string,
  breakpoint: Breakpoint,
  containerWidth: number,
  containerHeight: number
) => {
  const config = DEFAULT_GRID_CONFIG[breakpoint]
  const cellWidth = (containerWidth - config.margin[0] * (config.cols + 1)) / config.cols
  const cellHeight = config.rowHeight

  // Define optimal sizes for different widget types
  const widgetOptimalSizes: Record<string, { w: number; h: number }> = {
    'market-overview': { w: 2, h: 2 },
    'strategy-monitor': { w: 3, h: 3 },
    'portfolio-summary': { w: 2, h: 3 },
    'risk-metrics': { w: 2, h: 2 },
    'trading-panel': { w: 3, h: 4 },
    'news-feed': { w: 2, h: 3 },
    'system-status': { w: 1, h: 2 },
    'performance-chart': { w: 4, h: 3 },
    'order-book': { w: 2, h: 4 },
    'alert-center': { w: 1, h: 2 },
  }

  const optimal = widgetOptimalSizes[widgetType] || { w: 2, h: 2 }

  // Adjust for breakpoint
  const scaleFactor = Math.min(config.cols / 6, 1) // Normalize to 6 columns as base

  return {
    w: Math.max(1, Math.round(optimal.w * scaleFactor)),
    h: Math.max(1, optimal.h),
  }
}

/**
 * Debounce function for responsive handling
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout | null = null

  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

/**
 * Throttle function for performance optimization
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}