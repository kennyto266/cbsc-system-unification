// Square-UI Input Component
import React, { forwardRef } from 'react';
import { cn } from '../utils/square-utils';

export interface SquareInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  variant?: 'default' | 'filled' | 'outlined';
}

export const SquareInput = forwardRef<HTMLInputElement, SquareInputProps>(
  (
    {
      className,
      type = 'text',
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      variant = 'default',
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

    const baseClasses = cn(
      'w-full px-4 py-2 rounded-square transition-all duration-200',
      'focus:outline-none focus:ring-2 focus:ring-square-500 focus:ring-offset-2',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      {
        'shadow-square-sm': variant === 'default',
        'border-2 border-gray-300 bg-transparent': variant === 'outlined',
        'bg-gray-100 border-2 border-transparent focus:bg-white focus:border-gray-300': variant === 'filled',
      }
    );

    const errorClasses = error
      ? 'border-red-500 focus:ring-red-500'
      : 'border-transparent';

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
              {leftIcon}
            </div>
          )}
          <input
            type={type}
            id={inputId}
            className={cn(
              baseClasses,
              errorClasses,
              {
                'pl-10': leftIcon,
                'pr-10': rightIcon,
              },
              className
            )}
            ref={ref}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <p className="mt-2 text-sm text-red-600">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p className="mt-2 text-sm text-gray-500">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

SquareInput.displayName = 'SquareInput';

export default SquareInput;