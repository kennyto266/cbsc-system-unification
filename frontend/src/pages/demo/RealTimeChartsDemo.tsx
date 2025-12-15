import React, { useState } from 'react'
import {
  RealTimeLineChart,
  RealTimeBarChart,
  RealTimeRadarChart,
  RealTimeHeatmap,
  RealTimeChartManager,
  type ChartConfig
} from '../../components/Charts'

const RealTimeChartsDemo: React.FC = () => {
  const [selectedView, setSelectedView] = useState<'individual' | 'manager'>('individual')
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  // Configuration for each chart type
  const lineChartConfig = {
    websocketUrl: 'ws://localhost:3003',
    channel: 'strategy-netvalue',
    maxDataPoints: 1000,
    showStats: true,
    showAlerts: true,
    alertThresholds: {
      upper: 1.5,
      lower: 0.5
    },
    compareMode: true,
    enableCrosshair: true,
    enableZoom: true
  }

  const barChartConfig = {
    websocketUrl: 'ws://localhost:3003',
    channel: 'strategy-returns',
    maxDataPoints: 50,
    dynamicSorting: true,
    sortBy: 'value' as const,
    sortOrder: 'desc' as const,
    showChange: true,
    colorByValue: true,
    showTopN: 10,
    showValuesOnBars: true
  }

  const radarChartConfig = {
    websocketUrl: 'ws://localhost:3003',
    channel: 'strategy-metrics',
    dimensions: [
      { key: 'sharpeRatio', label: '夏普比率', min: 0, max: 3, unit: '' },
      { key: 'maxDrawdown', label: '最大回撤', min: 0, max: 50, unit: '%' },
      { key: 'winRate', label: '勝率', min: 0, max: 100, unit: '%' },
      { key: 'profitFactor', label: '盈利因子', min: 0, max: 5, unit: '' },
      { key: 'calmarRatio', label: '卡瑪比率', min: 0, max: 10, unit: '' },
      { key: 'var95', label: 'VaR (95%)', min: -20, max: 0, unit: '%' }
    ],
    aggregationMethod: 'average' as const,
    showAlerts: true,
    showValues: true,
    showPercentage: true,
    normalizeValues: true
  }

  const heatmapConfig = {
    websocketUrl: 'ws://localhost:3003',
    channel: 'strategy-correlations',
    xLabels: ['策略A', '策略B', '策略C', '策略D', '策略E'],
    yLabels: ['策略A', '策略B', '策略C', '策略D', '策略E'],
    colorScale: {
      min: '#3b82f6',
      mid: '#ffffff',
      max: '#ef4444'
    },
    diverging: true,
    centerValue: 0,
    showLegend: true,
    showValues: true,
    valueFormat: (v: number) => v.toFixed(3)
  }

  // Configuration for chart manager
  const chartConfigs: ChartConfig[] = [
    {
      id: 'netvalue',
      type: 'line',
      title: '策略淨值曲線',
      enabled: true,
      position: { x: 0, y: 0, w: 6, h: 4 },
      websocketUrl: 'ws://localhost:3003',
      channel: 'strategy-netvalue',
      config: lineChartConfig
    },
    {
      id: 'returns',
      type: 'bar',
      title: '策略收益率排行',
      enabled: true,
      position: { x: 6, y: 0, w: 6, h: 4 },
      websocketUrl: 'ws://localhost:3003',
      channel: 'strategy-returns',
      config: barChartConfig
    },
    {
      id: 'metrics',
      type: 'radar',
      title: '策略評分雷達圖',
      enabled: true,
      position: { x: 0, y: 4, w: 6, h: 4 },
      websocketUrl: 'ws://localhost:3003',
      channel: 'strategy-metrics',
      config: radarChartConfig
    },
    {
      id: 'correlations',
      type: 'heatmap',
      title: '策略相關性熱力圖',
      enabled: true,
      position: { x: 6, y: 4, w: 6, h: 4 },
      websocketUrl: 'ws://localhost:3003',
      channel: 'strategy-correlations',
      config: heatmapConfig
    }
  ]

  const handleChartUpdate = (chartId: string, data: any) => {
    console.log(`Chart ${chartId} updated:`, data)
  }

  const handleChartError = (chartId: string, error: string) => {
    console.error(`Chart ${chartId} error:`, error)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            實時圖表組件演示
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            展示基於Chart.js的高性能實時圖表組件
          </p>
        </div>

        {/* Controls */}
        <div className="mb-6 flex flex-wrap gap-4">
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              查看模式:
            </label>
            <select
              value={selectedView}
              onChange={(e) => setSelectedView(e.target.value as 'individual' | 'manager')}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            >
              <option value="individual">獨立圖表</option>
              <option value="manager">圖表管理器</option>
            </select>
          </div>

          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              主題:
            </label>
            <select
              value={theme}
              onChange={(e) => setTheme(e.target.value as 'light' | 'dark')}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            >
              <option value="light">淺色</option>
              <option value="dark">深色</option>
            </select>
          </div>
        </div>

        {/* Individual Charts View */}
        {selectedView === 'individual' && (
          <div className="space-y-8">
            {/* Line Chart */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4">實時折線圖 - 策略淨值</h2>
              <RealTimeLineChart
                {...lineChartConfig}
                theme={theme}
                height={400}
                onDataPointClick={(point) => {
                  console.log('Data point clicked:', point)
                }}
                onAlertTriggered={(type, value) => {
                  console.log(`Alert triggered: ${type} threshold breached with value ${value}`)
                }}
              />
            </div>

            {/* Bar Chart */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4">實時柱狀圖 - 收益率排行</h2>
              <RealTimeBarChart
                {...barChartConfig}
                theme={theme}
                height={400}
                onBarClick={(data, index) => {
                  console.log('Bar clicked:', data, index)
                }}
                onThresholdBreached={(item, threshold) => {
                  console.log('Threshold breached:', item, threshold)
                }}
              />
            </div>

            {/* Radar Chart */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4">實時雷達圖 - 策略評分</h2>
              <RealTimeRadarChart
                {...radarChartConfig}
                theme={theme}
                height={400}
                onScoreUpdate={(scores) => {
                  console.log('Scores updated:', scores)
                }}
                onOverallScoreChange={(score) => {
                  console.log('Overall score changed:', score)
                }}
                onDimensionAlert={(dimension, value, threshold) => {
                  console.log('Dimension alert:', dimension, value, threshold)
                }}
              />
            </div>

            {/* Heatmap */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4">實時熱力圖 - 策略相關性</h2>
              <RealTimeHeatmap
                {...heatmapConfig}
                theme={theme}
                height={400}
                onCellClick={(x, y, value) => {
                  console.log('Cell clicked:', x, y, value)
                }}
                onCellAlert={(x, y, value) => {
                  console.log('Cell alert:', x, y, value)
                }}
                onCorrelationChange={(correlations) => {
                  console.log('Correlations changed:', correlations)
                }}
              />
            </div>
          </div>
        )}

        {/* Chart Manager View */}
        {selectedView === 'manager' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">圖表管理器視圖</h2>
            <RealTimeChartManager
              charts={chartConfigs}
              layout="grid"
              theme={theme}
              height={800}
              onChartUpdate={handleChartUpdate}
              onChartError={handleChartError}
              onLayoutChange={(charts) => {
                console.log('Layout changed:', charts)
              }}
            />
          </div>
        )}

        {/* Feature List */}
        <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">功能特性</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="font-semibold mb-2">高性能渲染</h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                <li>• 支持1000+數據點流暢渲染</li>
                <li>• LTTB數據抽樣算法</li>
                <li>• 批量數據處理</li>
                <li>• 內存優化管理</li>
              </ul>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="font-semibold mb-2">實時更新</h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                <li>• WebSocket數據連接</li>
                <li>• 自動重連機制</li>
                <li>• 數據更新延遲 &lt; 100ms</li>
                <li>• 暫停/恢復控制</li>
              </ul>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="font-semibold mb-2">交互功能</h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                <li>• 縮放和平移</li>
                <li>• 懸停提示</li>
                <li>• 數據點選擇</li>
                <li>• 跨線標識器</li>
              </ul>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="font-semibold mb-2">可視化類型</h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                <li>• 實時折線圖</li>
                <li>• 動態柱狀圖</li>
                <li>• 多維雷達圖</li>
                <li>• 相關性熱力圖</li>
              </ul>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="font-semibold mb-2">警報系統</h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                <li>• 閾值警報</li>
                <li>• 視覺標記</li>
                <li>• 回調通知</li>
                <li>• 異常檢測</li>
              </ul>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="font-semibold mb-2">響應式設計</h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                <li>• 自適應佈局</li>
                <li>• 主題切換</li>
                <li>• 移動端支持</li>
                <li>• 高DPI顯示</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RealTimeChartsDemo