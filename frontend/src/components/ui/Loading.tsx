/**
 * Loading Component
 * 載入組件
 */

import React from 'react';
import { LoadingSpinner } from './LoadingSpinner';

interface LoadingProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  text?: string;
  className?: string;
}

export const Loading: React.FC<LoadingProps> = ({
  size = 'md',
  color = 'primary',
  text,
  className
}) => {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      <LoadingSpinner size={size} color={color} />
      {text && (
        <span className={`ml-2 text-${color === 'error' ? 'red' : color === 'warning' ? 'yellow' : color === 'success' ? 'green' : 'blue'}-600`}>
          {text}
        </span>
      )}
    </div>
  );
};