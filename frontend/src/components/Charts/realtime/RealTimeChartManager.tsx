import React, { useState, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  RealTimeLineChart,
  RealTimeBarChart,
  RealTimeRadarChart,
  RealTimeHeatmap
} from './index'
import type {
  RealTimeLineChartProps,
  RealTimeBarChartProps,
  RealTimeRadarChartProps,
  RealTimeHeatmapProps
} from './index'
import { useRealTimeDataProcessor } from '../../../hooks/useRealTimeDataProcessor'

// Chart types
export type ChartType = 'line' | 'bar' | 'radar' | 'heatmap'

// Chart configuration
export interface ChartConfig {
  id: string
  type: ChartType
  title: string
  enabled: boolean
  position: {
    x: number
    y: number
    w: number
    h: number
  }
  websocketUrl?: string
  channel?: string
  config?: any
}

// Props for RealTimeChartManager
export interface RealTimeChartManagerProps {
  charts: ChartConfig[]
  layout?: 'grid' | 'flex' | 'absolute'
  theme?: 'light' | 'dark'
  className?: string
  height?: number
  onChartUpdate?: (chartId: string, data: any) => void
  onChartError?: (chartId: string, error: string) => void
  onLayoutChange?: (charts: ChartConfig[]) => void
}

const RealTimeChartManager: React.FC<RealTimeChartManagerProps> = ({
  charts,
  layout = 'grid',
  theme = 'light',
  className = '',
  height = 800,
  onChartUpdate,
  onChartError,
  onLayoutChange
}) => {
  const [activeCharts, setActiveCharts] = useState<Set<string>>(new Set(charts.map(c => c.id)))
  const [chartStates, setChartStates] = useState<Record<string, any>>({})

  // Toggle chart visibility
  const toggleChart = useCallback((chartId: string) => {
    setActiveCharts(prev => {
      const newSet = new Set(prev)
      if (newSet.has(chartId)) {
        newSet.delete(chartId)
      } else {
        newSet.add(chartId)
      }
      return newSet
    })
  }, [])

  // Update chart state
  const updateChartState = useCallback((chartId: string, state: any) => {
    setChartStates(prev => ({
      ...prev,
      [chartId]: state
    }))
    onChartUpdate?.(chartId, state)
  }, [onChartUpdate])

  // Handle chart error
  const handleChartError = useCallback((chartId: string, error: string) => {
    setChartStates(prev => ({
      ...prev,
      [chartId]: { ...prev[chartId], error }
    }))
    onChartError?.(chartId, error)
  }, [onChartError])

  // Render individual chart based on type
  const renderChart = useCallback((chart: ChartConfig) => {
    if (!activeCharts.has(chart.id)) return null

    const commonProps = {
      key: chart.id,
      websocketUrl: chart.websocketUrl,
      channel: chart.channel,
      theme,
      onDataUpdate: (data: any) => updateChartState(chart.id, { data, lastUpdate: Date.now() }),
      className: 'w-full h-full'
    }

    switch (chart.type) {
      case 'line':
        return (
          <RealTimeLineChart
            {...commonProps}
            {...(chart.config as RealTimeLineChartProps)}
            height={chart.position.h}
          />
        )
      case 'bar':
        return (
          <RealTimeBarChart
            {...commonProps}
            {...(chart.config as RealTimeBarChartProps)}
            height={chart.position.h}
          />
        )
      case 'radar':
        const radarConfig = chart.config as RealTimeRadarChartProps
        return (
          <RealTimeRadarChart
            {...commonProps}
            dimensions={radarConfig.dimensions || []}
            {...radarConfig}
            height={chart.position.h}
          />
        )
      case 'heatmap':
        const heatmapConfig = chart.config as RealTimeHeatmapProps
        return (
          <RealTimeHeatmap
            {...commonProps}
            xLabels={heatmapConfig.xLabels || []}
            yLabels={heatmapConfig.yLabels || []}
            {...heatmapConfig}
            height={chart.position.h}
          />
        )
      default:
        return null
    }
  }, [activeCharts, theme, updateChartState])

  // Grid layout
  if (layout === 'grid') {
    const gridCols = Math.ceil(Math.sqrt(charts.filter(c => activeCharts.has(c.id)).length))

    return (
      <div className={`w-full ${className}`}>
        {/* Chart Controls */}
        <div className="mb-4 flex flex-wrap gap-2">
          {charts.map(chart => (
            <motion.button
              key={chart.id}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => toggleChart(chart.id)}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                activeCharts.has(chart.id)
                  ? 'bg-blue-500 text-white shadow-lg'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
              }`}
            >
              {chart.title}
            </motion.button>
          ))}
        </div>

        {/* Charts Grid */}
        <div
          className="grid gap-4"
          style={{
            gridTemplateColumns: `repeat(${gridCols}, minmax(0, 1fr))`,
            height: `${height}px`
          }}
        >
          <AnimatePresence>
            {charts
              .filter(chart => activeCharts.has(chart.id))
              .map(chart => (
                <motion.div
                  key={chart.id}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  transition={{ duration: 0.3 }}
                  className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4"
                >
                  {/* Chart Header */}
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold">{chart.title}</h3>
                    <div className="flex items-center space-x-2">
                      {chartStates[chart.id]?.lastUpdate && (
                        <span className="text-xs text-gray-500">
                          {new Date(chartStates[chart.id].lastUpdate).toLocaleTimeString()}
                        </span>
                      )}
                      {chartStates[chart.id]?.error && (
                        <span className="text-xs text-red-500">⚠ 錯誤</span>
                      )}
                    </div>
                  </div>

                  {/* Chart Content */}
                  <div className="relative" style={{ height: 'calc(100% - 2rem)' }}>
                    {renderChart(chart)}
                  </div>

                  {/* Error Display */}
                  <AnimatePresence>
                    {chartStates[chart.id]?.error && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="absolute top-0 left-0 right-0 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-b-lg"
                      >
                        <p className="text-xs text-red-600 dark:text-red-400">
                          {chartStates[chart.id].error}
                        </p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
          </AnimatePresence>
        </div>
      </div>
    )
  }

  // Flex layout
  if (layout === 'flex') {
    return (
      <div className={`w-full flex flex-col space-y-4 ${className}`} style={{ height: `${height}px` }}>
        {charts
          .filter(chart => activeCharts.has(chart.id))
          .map(chart => (
            <motion.div
              key={chart.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 flex-shrink-0"
              style={{ height: chart.position.h }}
            >
              {renderChart(chart)}
            </motion.div>
          ))}
      </div>
    )
  }

  // Absolute layout (dashboard style)
  return (
    <div className={`w-full relative ${className}`} style={{ height: `${height}px` }}>
      {charts
        .filter(chart => activeCharts.has(chart.id))
        .map(chart => (
          <motion.div
            key={chart.id}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4"
            style={{
              left: chart.position.x,
              top: chart.position.y,
              width: chart.position.w,
              height: chart.position.h
            }}
          >
            {/* Drag Handle */}
            <div className="absolute top-0 left-0 right-0 h-8 cursor-move flex items-center justify-between px-2">
              <h4 className="text-sm font-medium truncate">{chart.title}</h4>
              <button
                onClick={() => toggleChart(chart.id)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>

            {/* Chart Content */}
            <div className="pt-10 h-full">
              {renderChart(chart)}
            </div>
          </motion.div>
        ))}
    </div>
  )
}

export default RealTimeChartManager