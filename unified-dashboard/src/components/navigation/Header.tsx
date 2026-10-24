import React, { HTMLAttributes, forwardRef } from 'react'
import { cn } from '@/utils/cn'

export interface HeaderProps extends HTMLAttributes<HTMLElement> {
  sticky?: boolean
  transparent?: boolean
  bordered?: boolean
}

const Header = forwardRef<HTMLElement, HeaderProps>(
  ({ className, sticky = false, transparent = false, bordered = false, children, ...props }, ref) => {
    return (
      <header
        ref={ref}
        className={cn(
          'top-0 z-50 w-full border-b border-gray-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60',
          sticky && 'sticky top-0 z-50',
          transparent && 'border-transparent bg-transparent',
          bordered && 'border-gray-200',
          className
        )}
        {...props}
      >
        <div className="container mx-auto flex h-16 items-center justify-between px-6">
          {children}
        </div>
      </header>
    )
  }
)

Header.displayName = 'Header'

const HeaderBrand = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center space-x-4', className)}
      {...props}
    >
      {children}
    </div>
  )
)

HeaderBrand.displayName = 'HeaderBrand'

const HeaderNav = forwardRef<HTMLElement, HTMLAttributes<HTMLElement>>(
  ({ className, children, ...props }, ref) => (
    <nav
      ref={ref}
      className={cn('flex items-center space-x-1', className)}
      {...props}
    >
      {children}
    </nav>
  )
)

HeaderNav.displayName = 'HeaderNav'

const HeaderActions = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center space-x-4', className)}
      {...props}
    >
      {children}
    </div>
  )
)

HeaderActions.displayName = 'HeaderActions'

export { Header, HeaderBrand, HeaderNav, HeaderActions }