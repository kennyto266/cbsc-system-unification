import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useToast } from '../../hooks/useToast';
import html2canvas from 'html2canvas';

interface ChartToolbarProps {
  onExport?: (format: 'png' | 'svg' | 'csv') => void;
  onRefresh?: () => void;
  onFullscreen?: () => void;
  showExport?: boolean;
  showRefresh?: boolean;
  showFullscreen?: boolean;
  chartRef?: React.RefObject<HTMLElement>;
}

export const ChartToolbar: React.FC<ChartToolbarProps> = ({
  onExport,
  onRefresh,
  onFullscreen,
  showExport = true,
  showRefresh = true,
  showFullscreen = true,
  chartRef
}) => {
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const { addToast } = useToast();

  const handleExport = async (format: 'png' | 'svg' | 'csv') => {
    setExportMenuOpen(false);

    if (format === 'png' && chartRef?.current) {
      try {
        const canvas = await html2canvas(chartRef.current, {
          backgroundColor: '#ffffff',
          scale: 2
        });

        const link = document.createElement('a');
        link.download = `chart-${Date.now()}.png`;
        link.href = canvas.toDataURL();
        link.click();

        addToast({
          type: 'success',
          message: '图表已导出为 PNG 格式'
        });
      } catch (error) {
        addToast({
          type: 'error',
          message: '导出失败，请重试'
        });
      }
    } else if (onExport) {
      onExport(format);
    }
  };

  return (
    <div className="flex items-center gap-2">
      {/* Refresh Button */}
      {showRefresh && onRefresh && (
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onRefresh}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          title="刷新图表"
        >
          <svg className="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </motion.button>
      )}

      {/* Export Menu */}
      {showExport && (
        <div className="relative">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setExportMenuOpen(!exportMenuOpen)}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title="导出图表"
          >
            <svg className="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </motion.button>

          <AnimatePresence>
            {exportMenuOpen && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -10 }}
                transition={{ duration: 0.2 }}
                className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-2 z-50"
              >
                <button
                  onClick={() => handleExport('png')}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  导出为 PNG
                </button>
                <button
                  onClick={() => handleExport('svg')}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  导出为 SVG
                </button>
                <button
                  onClick={() => handleExport('csv')}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  导出数据 (CSV)
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Fullscreen Button */}
      {showFullscreen && onFullscreen && (
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onFullscreen}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          title="全屏查看"
        >
          <svg className="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
          </svg>
        </motion.button>
      )}
    </div>
  );
};