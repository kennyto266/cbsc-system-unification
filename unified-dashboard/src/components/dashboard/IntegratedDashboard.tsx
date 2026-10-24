/**
 * Integrated Dashboard Component
 * Combines Layout Navigation, Responsive Grid System, and Real-time Charts
 */

import React, { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { GridSystem } from '../Grid'
import { useGridLayout } from '../../hooks/useGridLayout'
import { useWidgetManager } from '../../hooks/useWidgetManager'
import { useWebSocket } from '../../hooks/useWebSocket'
import { RealTimeChartProvider } from '../charts/RealTime/RealTimeChartProvider'
import { GridLayout, GridItem } from '../../types/grid'
import { WidgetType } from '../../types/widget'

// Import widget components
import StrategyOverviewWidget from '../WidgetTypes/StrategyOverview'
import PerformanceMetricsWidget from '../WidgetTypes/PerformanceMetrics'
import BacktestResultsWidget from '../WidgetTypes/BacktestResults'
import RealTimeMonitorWidget from '../WidgetTypes/RealTimeMonitor'
import NewsAnnouncementWidget from '../WidgetTypes/NewsAnnouncement'

interface IntegratedDashboardProps {
  className?: string
}

const IntegratedDashboard: React.FC<IntegratedDashboardProps> = ({ className = '' }) => {
  const { isConnected } = useWebSocket()
  const { layout, updateLayout } = useGridLayout()
  const { widgets, addWidget, removeWidget, updateWidget } = useWidgetManager()
  const [isLoading, setIsLoading] = useState(true)

  // Initialize default layout
  useEffect(() => {
    const initializeLayout = async () => {
      setIsLoading(true)

      // Default widget configuration
      const defaultLayout: GridLayout = [
        { id: 'strategy-overview', x: 0, y: 0, w: 6, h: 3, minW: 4, minH: 2 },
        { id: 'performance-metrics', x: 6, y: 0, w: 6, h: 3, minW: 4, minH: 2 },
        { id: 'backtest-results', x: 0, y: 3, w: 8, h: 4, minW: 6, minH: 3 },
        { id: 'realtime-monitor', x: 8, y: 3, w: 4, h: 4, minW: 3, minH: 3 },
        { id: 'news-announcement', x: 0, y: 7, w: 12, h: 2, minW: 8, minH: 1 },
      ]

      // Initialize widgets
      const defaultWidgets = [
        { id: 'strategy-overview', type: WidgetType.STRATEGY_OVERVIEW, title: '策略概覽', config: {} },
        { id: 'performance-metrics', type: WidgetType.PERFORMANCE_METRICS, title: '性能指標', config: {} },
        { id: 'backtest-results', type: WidgetType.BACKTEST_RESULTS, title: '回測結果', config: {} },
        { id: 'realtime-monitor', type: WidgetType.REAL_TIME_MONITOR, title: '實時監控', config: {} },
        { id: 'news-announcement', type: WidgetType.NEWS_ANNOUNCEMENT, title: '新聞公告', config: {} },
      ]

      // Set initial layout if empty
      if (layout.length === 0) {
        updateLayout(defaultLayout)
      }

      // Add widgets if empty
      if (widgets.length === 0) {
        defaultWidgets.forEach(widget => addWidget(widget))
      }

      setIsLoading(false)
    }

    initializeLayout()
  }, [layout.length, widgets.length, updateLayout, addWidget])

  // Handle layout changes
  const handleLayoutChange = useCallback((newLayout: GridLayout) => {
    updateLayout(newLayout)
  }, [updateLayout])

  // Widget component renderer
  const renderWidget = (widget: any) => {
    switch (widget.type) {
      case WidgetType.STRATEGY_OVERVIEW:
        return <StrategyOverviewWidget widgetId={widget.id} config={widget.config} />
      case WidgetType.PERFORMANCE_METRICS:
        return <PerformanceMetricsWidget widgetId={widget.id} config={widget.config} />
      case WidgetType.BACKTEST_RESULTS:
        return <BacktestResultsWidget widgetId={widget.id} config={widget.config} />
      case WidgetType.REAL_TIME_MONITOR:
        return <RealTimeMonitorWidget widgetId={widget.id} config={widget.config} />
      case WidgetType.NEWS_ANNOUNCEMENT:
        return <NewsAnnouncementWidget widgetId={widget.id} config={widget.config} />
      default:
        return <div className="p-4 text-gray-500">Unknown widget type</div>
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
      </div>
    )
  }

  return (
    <div className={`integrated-dashboard ${className}`}>
      {/* Connection Status */}
      <div className="mb-4 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            CBSC 策略管理儀表板
          </h2>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-600 dark:text-gray-300">
              {isConnected ? '實時連接' : '連接斷開'}
            </span>
          </div>
        </div>
      </div>

      {/* Real-time Chart Provider */}
      <RealTimeChartProvider>
        {/* Grid System */}
        <GridSystem
          layout={layout}
          onLayoutChange={handleLayoutChange}
          isDraggable={true}
          isResizable={true}
          cols={12}
          rowHeight={80}
          margin={[16, 16]}
          className="dashboard-grid"
        >
          {layout.map((item) => {
            const widget = widgets.find(w => w.id === item.id)
            if (!widget) return null

            return (
              <motion.div
                key={item.id}
                layoutId={item.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.3 }}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-lg"
                style={{
                  gridColumn: `span ${item.w}`,
                  gridRow: `span ${item.h}`,
                }}
              >
                <div className="h-full flex flex-col">
                  {/* Widget Header */}
                  <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                      {widget.title}
                    </h3>
                    <div className="flex space-x-1">
                      <button
                        className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded"
                        onClick={() => {/* Minimize logic */}}
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                        </svg>
                      </button>
                      <button
                        className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded"
                        onClick={() => {/* Settings logic */}}
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                      </button>
                      <button
                        className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 rounded"
                        onClick={() => removeWidget(item.id)}
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  {/* Widget Content */}
                  <div className="flex-1 overflow-hidden">
                    {renderWidget(widget)}
                  </div>
                </div>
              </motion.div>
            )
          })}
        </GridSystem>
      </RealTimeChartProvider>
    </div>
  )
}

export default IntegratedDashboard