'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';
import { squareTheme } from '@/lib/square-theme';

// Square 風格的變體
interface SquareButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'link';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
}

const SquareButton = React.forwardRef<HTMLButtonElement, SquareButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, icon, iconPosition = 'left', children, disabled, onClick, ...props }, ref) => {
    const baseClasses = 'relative inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

    const variantClasses = {
      primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 shadow-sm hover:shadow-md',
      secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200 focus:ring-gray-500 border border-gray-300',
      outline: 'bg-transparent text-gray-700 hover:bg-gray-50 focus:ring-gray-500 border border-gray-300',
      ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-500',
      destructive: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 shadow-sm hover:shadow-md',
      link: 'bg-transparent text-blue-600 hover:text-blue-800 hover:underline focus:ring-blue-500 p-0 h-auto',
    };

    const sizeClasses = {
      sm: 'h-8 px-3 text-xs rounded-md',
      md: 'h-10 px-4 text-sm rounded-md',
      lg: 'h-12 px-6 text-base rounded-lg',
    };

    // 處理點擊事件
    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      console.log('SquareButton clicked, loading:', loading, 'disabled:', disabled);
      if (loading || disabled) {
        e.preventDefault();
        return;
      }

      if (onClick) {
        console.log('Calling onClick handler');
        onClick(e);
      }
    };

    return (
      <button
        className={cn(
          baseClasses,
          variantClasses[variant],
          sizeClasses[size],
          icon && !children && 'px-3',
          className
        )}
        ref={ref}
        disabled={disabled || loading}
        onClick={handleClick}
        {...props}
      >
        {loading && <Loader2 className={cn('animate-spin', children && 'mr-2')} size={16} />}
        {!loading && icon && iconPosition === 'left' && (
          <span className={cn(children && 'mr-2')}>{icon}</span>
        )}
        {children}
        {!loading && icon && iconPosition === 'right' && (
          <span className={cn(children && 'ml-2')}>{icon}</span>
        )}
      </button>
    );
  }
);

SquareButton.displayName = 'SquareButton';

export { SquareButton };
export type { SquareButtonProps };