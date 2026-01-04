/**
 * Grid - Responsive Grid Layout Component
 * Migrated from unified-dashboard square-ui
 *
 * Features:
 * - Responsive column configuration (xs, sm, md, lg, xl)
 * - Auto-fit mode for flexible layouts
 * - GridItem for individual item control
 * - Preset grids for common layouts
 */

import React from 'react'
import { cn } from '@/lib/utils'

interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  cols?: number | string | { xs?: number; sm?: number; md?: number; lg?: number; xl?: number }
  gap?: number | string
  className?: string
  autoFit?: boolean
  minColWidth?: string
  maxColWidth?: string
}

interface GridItemProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  span?: number | string
  start?: number | string
  end?: number | string
  className?: string
}

export const Grid: React.FC<GridProps> = ({
  children,
  cols = 1,
  gap = 4,
  className,
  autoFit = false,
  minColWidth = '250px',
  maxColWidth,
  ...props
}) => {
  // Build grid template columns
  const getGridCols = () => {
    if (autoFit) {
      const maxWidth = maxColWidth ? `max(${maxColWidth}, ` : ''
      const closeMaxWidth = maxColWidth ? ')' : ''
      return `repeat(auto-fit, ${maxWidth}minmax(${minColWidth}, 1fr)${closeMaxWidth})`
    }

    if (typeof cols === 'number') {
      return `repeat(${cols}, minmax(0, 1fr))`
    }

    if (typeof cols === 'string') {
      return cols
    }

    // Responsive columns object
    const responsiveCols = []
    if (cols.xs) responsiveCols.push(cols.xs)
    if (cols.sm) responsiveCols.push(cols.sm)
    if (cols.md) responsiveCols.push(cols.md)
    if (cols.lg) responsiveCols.push(cols.lg)
    if (cols.xl) responsiveCols.push(cols.xl)

    return responsiveCols.length > 0
      ? `repeat(${responsiveCols[responsiveCols.length - 1]}, minmax(0, 1fr))`
      : 'repeat(1, minmax(0, 1fr))'
  }

  const gridStyles: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: getGridCols(),
    gap: typeof gap === 'number' ? `${gap * 0.25}rem` : gap,
  }

  // Add responsive styles if cols is an object
  const responsiveClasses = []
  if (typeof cols === 'object' && cols !== null) {
    if (cols.xs) responsiveClasses.push(`grid-cols-${cols.xs}`)
    if (cols.sm) responsiveClasses.push(`sm:grid-cols-${cols.sm}`)
    if (cols.md) responsiveClasses.push(`md:grid-cols-${cols.md}`)
    if (cols.lg) responsiveClasses.push(`lg:grid-cols-${cols.lg}`)
    if (cols.xl) responsiveClasses.push(`xl:grid-cols-${cols.xl}`)
  }

  return (
    <div
      className={cn(
        'grid',
        typeof gap === 'number' && `gap-${gap}`,
        ...responsiveClasses,
        className
      )}
      style={gridStyles}
      {...props}
    >
      {children}
    </div>
  )
}

export const GridItem: React.FC<GridItemProps> = ({
  children,
  span,
  start,
  end,
  className,
  ...props
}) => {
  const itemStyles: React.CSSProperties = {}

  if (span) {
    itemStyles.gridColumn = typeof span === 'number' ? `span ${span}` : span
  }

  if (start) {
    itemStyles.gridColumnStart = typeof start === 'number' ? start : start
  }

  if (end) {
    itemStyles.gridColumnEnd = typeof end === 'number' ? end : end
  }

  const spanClass = typeof span === 'number' ? `col-span-${span}` : ''
  const startClass = typeof start === 'number' ? `col-start-${start}` : ''
  const endClass = typeof end === 'number' ? `col-end-${end}` : ''

  return (
    <div
      className={cn(
        spanClass,
        startClass,
        endClass,
        className
      )}
      style={itemStyles}
      {...props}
    >
      {children}
    </div>
  )
}

// Responsive grid presets
export const ResponsiveGrid: React.FC<{
  children: React.ReactNode
  gap?: number
  className?: string
}> = ({ children, gap = 4, className }) => {
  return (
    <Grid
      cols={{ xs: 1, sm: 2, md: 3, lg: 4 }}
      gap={gap}
      className={className}
    >
      {children}
    </Grid>
  )
}

export const DashboardGrid: React.FC<{
  children: React.ReactNode
  className?: string
}> = ({ children, className }) => {
  return (
    <Grid
      cols={{ xs: 1, sm: 1, md: 2, lg: 3, xl: 4 }}
      gap={6}
      className={cn('w-full', className)}
    >
      {children}
    </Grid>
  )
}

// Metrics grid - optimized for metric cards
export const MetricsGrid: React.FC<{
  children: React.ReactNode
  className?: string
}> = ({ children, className }) => {
  return (
    <Grid
      cols={{ xs: 1, sm: 2, lg: 4 }}
      gap={4}
      className={cn('w-full mb-6', className)}
    >
      {children}
    </Grid>
  )
}

// Chart grid - optimized for charts and larger components
export const ChartGrid: React.FC<{
  children: React.ReactNode
  className?: string
}> = ({ children, className }) => {
  return (
    <Grid
      cols={{ xs: 1, lg: 2 }}
      gap={6}
      className={cn('w-full', className)}
    >
      {children}
    </Grid>
  )
}

// Flexible grid with auto-fit
export const FlexibleGrid: React.FC<{
  children: React.ReactNode
  minColWidth?: string
  maxColWidth?: string
  gap?: number
  className?: string
}> = ({
  children,
  minColWidth = '280px',
  maxColWidth,
  gap = 4,
  className
}) => {
  return (
    <Grid
      autoFit
      minColWidth={minColWidth}
      maxColWidth={maxColWidth}
      gap={gap}
      className={cn('w-full', className)}
    >
      {children}
    </Grid>
  )
}

export default Grid
