// Square-UI Base Component Template
import React from 'react';
import { cn } from '../utils/square-utils';

export interface SquareComponentProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
}

export const SquareComponent: React.FC<SquareComponentProps> = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  ...props
}) => {
  const baseClasses = cn(
    'inline-flex items-center justify-center rounded-square font-medium transition-all duration-200',
    'focus:outline-none focus:ring-2 focus:ring-square-500 focus:ring-offset-2',
    {
      'shadow-square hover:shadow-square-lg': !disabled,
      'opacity-50 cursor-not-allowed': disabled,
      'animate-pulse': loading,
    },
    className
  );

  const variantClasses = {
    primary: 'bg-gradient-to-r from-square-500 to-purple-600 text-white',
    secondary: 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-900',
    success: 'bg-gradient-to-r from-green-400 to-emerald-500 text-white',
    warning: 'bg-gradient-to-r from-yellow-400 to-orange-500 text-white',
    error: 'bg-gradient-to-r from-red-500 to-pink-500 text-white',
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      className={cn(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size]
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      )}
      {children}
    </button>
  );
};

export default SquareComponent;
