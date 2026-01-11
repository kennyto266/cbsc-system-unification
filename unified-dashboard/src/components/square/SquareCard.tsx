// Square-UI Card Component
import React from 'react';
import { cn } from '../utils/square-utils';

export interface SquareCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'elevated' | 'outlined';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  hover?: boolean;
  animated?: boolean;
}

export const SquareCard: React.FC<SquareCardProps> = ({
  children,
  className,
  variant = 'default',
  padding = 'md',
  hover = false,
  animated = false,
  ...props
}) => {
  const baseClasses = cn(
    'rounded-square transition-all duration-200',
    {
      'shadow-square': variant === 'elevated',
      'shadow-square-sm': variant === 'default',
      'shadow-none': variant === 'outlined',
      'glass-effect': variant === 'glass',
      'border-2 border-gray-200': variant === 'outlined',
      'hover:shadow-square-lg hover:-translate-y-1': hover,
      'animate-fade-in': animated,
    }
  );

  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
    xl: 'p-10',
  };

  return (
    <div
      className={cn(
        baseClasses,
        paddingClasses[padding],
        'bg-white',
        {
          'bg-gradient-to-br from-white to-gray-50': variant === 'glass' || variant === 'elevated',
        },
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

// Card Header Component
export const SquareCardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className,
  ...props
}) => {
  return (
    <div className={cn('mb-4 pb-4 border-b border-gray-200', className)} {...props}>
      {children}
    </div>
  );
};

// Card Title Component
export const SquareCardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  children,
  className,
  ...props
}) => {
  return (
    <h3 className={cn('text-lg font-semibold text-gray-900', className)} {...props}>
      {children}
    </h3>
  );
};

// Card Description Component
export const SquareCardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  children,
  className,
  ...props
}) => {
  return (
    <p className={cn('text-sm text-gray-600 mt-1', className)} {...props}>
      {children}
    </p>
  );
};

// Card Content Component
export const SquareCardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className,
  ...props
}) => {
  return (
    <div className={cn('', className)} {...props}>
      {children}
    </div>
  );
};

// Card Footer Component
export const SquareCardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className,
  ...props
}) => {
  return (
    <div className={cn('mt-4 pt-4 border-t border-gray-200 flex items-center justify-between', className)} {...props}>
      {children}
    </div>
  );
};

SquareCard.Header = SquareCardHeader;
SquareCard.Title = SquareCardTitle;
SquareCard.Description = SquareCardDescription;
SquareCard.Content = SquareCardContent;
SquareCard.Footer = SquareCardFooter;

export default SquareCard;