/**
 * Grid System Types
 */

export interface GridItem {
  id: string
  x: number
  y: number
  w: number
  h: number
  minW?: number
  minH?: number
  maxW?: number
  maxH?: number
  isDraggable?: boolean
  isResizable?: boolean
  isStatic?: boolean
  isMinimized?: boolean
  isMaximized?: boolean
  prevW?: number
  prevH?: number
  z?: number
  [key: string]: any
}

export type GridLayout = GridItem[]

export interface GridDropEvent {
  x: number
  y: number
  w: number
  h: number
  e: MouseEvent
}

export interface GridResizeEvent {
  x: number
  y: number
  w: number
  h: number
  e: MouseEvent
  node: HTMLElement
  size: {
    width: number
    height: number
  }
}

export interface GridDragEvent {
  x: number
  y: number
  e: MouseEvent
  node: HTMLElement
}

export type CompactType = 'vertical' | 'horizontal' | null

export interface GridOptions {
  cols: number
  rowHeight: number
  margin: [number, number]
  containerPadding: [number, number]
  isDraggable: boolean
  isResizable: boolean
  autoArrange: boolean
  compactType: CompactType
  preventCollision: boolean
}

export interface GridPosition {
  x: number
  y: number
}

export interface GridSize {
  w: number
  h: number
}

export interface GridBounds {
  left: number
  top: number
  width: number
  height: number
}