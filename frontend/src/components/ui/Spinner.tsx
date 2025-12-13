import React from 'react';
import { LoadingSpinner } from './LoadingSpinner';

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className = '' }) => {
  return <LoadingSpinner size={size} className={className} />;
};