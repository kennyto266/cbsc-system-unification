'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { getStatusColors } from '@/lib/square-theme';

interface SquareBadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md' | 'lg';
  status?: string; // For dynamic status-based styling
}

const SquareBadge = React.forwardRef<HTMLDivElement, SquareBadgeProps>(
  ({ className, variant = 'default', size = 'md', status, children, ...props }, ref) => {
    const baseClasses = 'inline-flex items-center font-medium rounded-full transition-colors duration-200';

    // 動態狀態顏色
    let statusColors;
    if (status) {
      statusColors = getStatusColors(status);
    }

    let variantClasses: { [key: string]: string };

    if (status && statusColors) {
      variantClasses = {
        default: `${statusColors.bg} ${statusColors.text} ${statusColors.border}`,
        primary: `${statusColors.bg} ${statusColors.text} ${statusColors.border}`,
        success: `${statusColors.bg} ${statusColors.text} ${statusColors.border}`,
        warning: `${statusColors.bg} ${statusColors.text} ${statusColors.border}`,
        error: `${statusColors.bg} ${statusColors.text} ${statusColors.border}`,
        info: `${statusColors.bg} ${statusColors.text} ${statusColors.border}`,
      };
    } else {
      variantClasses = {
        default: 'bg-gray-100 text-gray-800 border border-gray-200',
        primary: 'bg-blue-100 text-blue-800 border border-blue-200',
        success: 'bg-green-100 text-green-800 border border-green-200',
        warning: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
        error: 'bg-red-100 text-red-800 border border-red-200',
        info: 'bg-indigo-100 text-indigo-800 border border-indigo-200',
      };
    }

    const sizeClasses = {
      sm: 'px-2 py-0.5 text-xs',
      md: 'px-2.5 py-0.5 text-sm',
      lg: 'px-3 py-1 text-base',
    };

    return (
      <div
        className={cn(
          baseClasses,
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        ref={ref}
        {...props}
      >
        {children}
      </div>
    );
  }
);

SquareBadge.displayName = 'SquareBadge';

export { SquareBadge };
export type { SquareBadgeProps };