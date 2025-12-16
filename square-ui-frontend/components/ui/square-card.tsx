'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface SquareCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'bordered' | 'elevated' | 'outlined';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  header?: React.ReactNode;
  footer?: React.ReactNode;
  loading?: boolean;
}

const SquareCard = React.forwardRef<HTMLDivElement, SquareCardProps>(
  ({ className, variant = 'default', padding = 'md', header, footer, loading, children, ...props }, ref) => {
    const variantClasses = {
      default: 'bg-white border border-gray-200',
      bordered: 'bg-white border-2 border-gray-200',
      elevated: 'bg-white shadow-md border border-gray-100',
      outlined: 'bg-white border-2 border-gray-300 shadow-sm',
    };

    const paddingClasses = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    };

    return (
      <div
        className={cn(
          'rounded-lg transition-all duration-200',
          variantClasses[variant],
          paddingClasses[padding],
          loading && 'opacity-50 pointer-events-none',
          className
        )}
        ref={ref}
        {...props}
      >
        {header && (
          <div className="border-b border-gray-200 pb-4 mb-4">
            {header}
          </div>
        )}
        {children}
        {footer && (
          <div className="border-t border-gray-200 pt-4 mt-4">
            {footer}
          </div>
        )}
      </div>
    );
  }
);

SquareCard.displayName = 'SquareCard';

export { SquareCard };
export type { SquareCardProps };