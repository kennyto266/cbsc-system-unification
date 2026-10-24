// Square-UI Utility Functions
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Enhanced cn function with square-ui support
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Square color utilities
export const squareColors = {
  primary: {
    50: '#f0f4ff',
    100: '#e0e7ff',
    200: '#c7d2fe',
    300: '#a5b4fc',
    400: '#818cf8',
    500: '#667eea',
    600: '#5a67d8',
    700: '#4c51bf',
    800: '#434190',
    900: '#3c366b',
    950: '#312e81',
  },
  gradient: {
    primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    secondary: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    success: 'linear-gradient(135deg, #13B497 0%, #59D4A4 100%)',
    warning: 'linear-gradient(135deg, #F7B500 0%, #F5A623 100%)',
    error: 'linear-gradient(135deg, #FF5252 0%, #FF3838 100%)',
  }
};

// Theme utilities
export const getThemeClasses = (variant: 'primary' | 'secondary' | 'success' | 'warning' | 'error') => {
  const variants = {
    primary: 'bg-gradient-to-r from-square-500 to-purple-600 text-white shadow-square',
    secondary: 'bg-gradient-to-r from-purple-100 to-pink-100 text-purple-900',
    success: 'bg-gradient-to-r from-green-400 to-emerald-500 text-white',
    warning: 'bg-gradient-to-r from-yellow-400 to-orange-500 text-white',
    error: 'bg-gradient-to-r from-red-500 to-pink-500 text-white',
  };
  return variants[variant] || variants.primary;
};

// Animation utilities
export const animations = {
  fadeIn: 'animate-fade-in',
  slideUp: 'animate-slide-up',
  slideDown: 'animate-slide-down',
  scaleIn: 'animate-scale-in',
  float: 'animate-float',
  pulseSlow: 'animate-pulse-slow',
};
