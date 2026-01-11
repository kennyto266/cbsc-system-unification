import React from 'react';
import { motion } from 'framer-motion';
import { Spinner } from '../ui/Spinner';
import { ChartToolbar } from './ChartToolbar';

interface ChartContainerProps {
  title?: string;
  subtitle?: string;
  loading?: boolean;
  error?: string;
  children: React.ReactNode;
  className?: string;
  toolbar?: {
    onExport?: (format: 'png' | 'svg' | 'csv') => void;
    onRefresh?: () => void;
    onFullscreen?: () => void;
    showExport?: boolean;
    showRefresh?: boolean;
    showFullscreen?: boolean;
  };
  actions?: React.ReactNode;
}

export const ChartContainer: React.FC<ChartContainerProps> = ({
  title,
  subtitle,
  loading = false,
  error,
  children,
  className = '',
  toolbar,
  actions
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 ${className}`}
    >
      {/* Header */}
      {(title || subtitle || toolbar || actions) && (
        <div className="flex items-center justify-between mb-6">
          <div className="flex-1">
            {title && (
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {subtitle}
              </p>
            )}
          </div>

          <div className="flex items-center gap-4">
            {actions}
            {toolbar && (
              <ChartToolbar
                onExport={toolbar.onExport}
                onRefresh={toolbar.onRefresh}
                onFullscreen={toolbar.onFullscreen}
                showExport={toolbar.showExport}
                showRefresh={toolbar.showRefresh}
                showFullscreen={toolbar.showFullscreen}
              />
            )}
          </div>
        </div>
      )}

      {/* Chart Content */}
      <div className="relative min-h-[300px]">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white dark:bg-gray-800 bg-opacity-75 dark:bg-opacity-75 z-10">
            <div className="flex flex-col items-center">
              <Spinner size="lg" />
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                加载中...
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center z-10">
            <div className="text-center">
              <div className="text-red-500 dark:text-red-400 mb-2">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-sm text-red-600 dark:text-red-400">
                {error}
              </p>
            </div>
          </div>
        )}

        <div className={`transition-opacity duration-300 ${loading || error ? 'opacity-50' : 'opacity-100'}`}>
          {children}
        </div>
      </div>
    </motion.div>
  );
};