import React, { HTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/utils/cn'

const gridVariants = cva(
  'grid',
  {
    variants: {
      cols: {
        1: 'grid-cols-1',
        2: 'grid-cols-2',
        3: 'grid-cols-3',
        4: 'grid-cols-4',
        5: 'grid-cols-5',
        6: 'grid-cols-6',
        7: 'grid-cols-7',
        8: 'grid-cols-8',
        9: 'grid-cols-9',
        10: 'grid-cols-10',
        11: 'grid-cols-11',
        12: 'grid-cols-12',
        none: 'grid-cols-none',
      },
      gap: {
        none: '',
        xs: 'gap-1',
        sm: 'gap-2',
        default: 'gap-4',
        lg: 'gap-6',
        xl: 'gap-8',
        '2xl': 'gap-12',
      },
      responsive: {
        false: '',
        sm: 'sm:grid-cols-2',
        md: 'md:grid-cols-2',
        lg: 'lg:grid-cols-3',
        xl: 'xl:grid-cols-4',
        '2xl': '2xl:grid-cols-5',
        adaptive: 'sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4',
      },
    },
    defaultVariants: {
      cols: 1,
      gap: 'default',
      responsive: false,
    },
  }
)

export interface GridProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof gridVariants> {}

const Grid = forwardRef<HTMLDivElement, GridProps>(
  ({ className, cols, gap, responsive, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(gridVariants({ cols, gap, responsive, className }))}
      {...props}
    />
  )
)

Grid.displayName = 'Grid'

const GridItem = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement> & { span?: number }
>(({ className, span, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      span && `col-span-${span}`,
      className
    )}
    {...props}
  />
))

GridItem.displayName = 'GridItem'

export { Grid, GridItem, gridVariants }