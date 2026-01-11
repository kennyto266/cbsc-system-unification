/**
 * Grid Provider - Provides grid context to all grid components
 */

import React, { createContext, useContext, ReactNode } from 'react'

export interface GridContextType {
  cols: number
  rowHeight: number
  margin: [number, number]
  containerPadding: [number, number]
  containerWidth: number
  gridSpacing: number
  isDraggable: boolean
  isResizable: boolean
}

export const GridContext = createContext<GridContextType | undefined>(undefined)

interface GridProviderProps {
  children: ReactNode
  value: GridContextType
}

export const GridProvider: React.FC<GridProviderProps> = ({ children, value }) => {
  return (
    <GridContext.Provider value={value}>
      {children}
    </GridContext.Provider>
  )
}

export const useGridContext = (): GridContextType => {
  const context = useContext(GridContext)
  if (!context) {
    throw new Error('useGridContext must be used within a GridProvider')
  }
  return context
}