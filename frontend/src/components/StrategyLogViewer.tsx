/**
 * Strategy Log Viewer Component
 * 策略日誌查看器組件
 */

import React, { useState, useEffect, useMemo, useRef } from 'react'
import {
  Search,
  Filter,
  Download,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle,
  XCircle,
  Info,
  Clock,
  Zap,
  Settings,
  Play,
  Pause,
  SkipForward,
  Calendar,
  Tag,
  FileText,
  Eye,
  EyeOff,
  Terminal,
  Bug,
  Activity,
  Database,
  Shield,
  Bell,
  MessageSquare,
  Cpu,
  HardDrive,
  Wifi,
  TrendingUp
} from 'lucide-react'

// Types
interface LogEntry {
  id: string
  timestamp: string
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical'
  category: 'execution' | 'performance' | 'risk' | 'data' | 'system' | 'trading' | 'api' | 'websocket'
  message: string
  details?: Record<string, any>
  source?: string
  userId?: string
  strategyId?: string
  correlationId?: string
  stackTrace?: string
  metrics?: {
    duration?: number
    memory?: number
    cpu?: number
    requests?: number
  }
}

interface LogFilter {
  levels: string[]
  categories: string[]
  sources: string[]
  timeRange: {
    start?: Date
    end?: Date
  }
  search: string
}

interface LogViewerProps {
  strategyId?: string
  className?: string
  logs?: LogEntry[]
  maxEntries?: number
  autoRefresh?: boolean
  refreshInterval?: number
  showLevels?: boolean
  showCategories?: boolean
  showMetrics?: boolean
  compactMode?: boolean
  enableSearch?: boolean
  enableExport?: boolean
  enableLiveMode?: boolean
  onLogClick?: (log: LogEntry) => void
  onExport?: (format: 'csv' | 'json' | 'txt') => void
}

const LOG_LEVELS = {
  debug: { label: '調試', color: '#6b7280', icon: Bug, priority: 0 },
  info: { label: '信息', color: '#3b82f6', icon: Info, priority: 1 },
  warning: { label: '警告', color: '#f59e0b', icon: AlertCircle, priority: 2 },
  error: { label: '錯誤', color: '#ef4444', icon: XCircle, priority: 3 },
  critical: { label: '嚴重', color: '#dc2626', icon: Shield, priority: 4 }
}

const LOG_CATEGORIES = {
  execution: { label: '執行', color: '#8b5cf6', icon: Play },
  performance: { label: '性能', color: '#f59e0b', icon: Activity },
  risk: { label: '風險', color: '#ef4444', icon: Shield },
  data: { label: '數據', color: '#10b981', icon: Database },
  system: { label: '系統', color: '#6b7280', icon: Cpu },
  trading: { label: '交易', color: '#3b82f6', icon: TrendingUp },
  api: { label: 'API', color: '#ec4899', icon: MessageSquare },
  websocket: { label: 'WebSocket', color: '#14b8a6', icon: Wifi }
}

const LogEntryCard: React.FC<{
  log: LogEntry
  expanded: boolean
  onToggle: () => void
  onClick?: () => void
  showMetrics?: boolean
  compactMode?: boolean
}> = ({ log, expanded, onToggle, onClick, showMetrics, compactMode }) => {
  const levelConfig = LOG_LEVELS[log.level]
  const categoryConfig = LOG_CATEGORIES[log.category]
  const LevelIcon = levelConfig.icon
  const CategoryIcon = categoryConfig.icon

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    })
  }

  return (
    <div
      className={`border border-gray-200 rounded-lg transition-all duration-200 ${
        compactMode ? 'p-3' : 'p-4'
      } ${expanded ? 'bg-gray-50' : 'bg-white hover:bg-gray-50'} cursor-pointer`}
      onClick={onClick}
    >
      <div className="flex items-start space-x-3">
        {/* Level Icon */}
        <div className="flex-shrink-0 mt-0.5">
          <LevelIcon
            className="w-4 h-4"
            style={{ color: levelConfig.color }}
          />
        </div>

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            {/* Header */}
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium" style={{ color: levelConfig.color }}>
                {levelConfig.label}
              </span>
              <span className="text-gray-300">•</span>
              <div className="flex items-center space-x-1">
                <CategoryIcon className="w-3 h-3" style={{ color: categoryConfig.color }} />
                <span className="text-xs text-gray-600">{categoryConfig.label}</span>
              </div>
              {log.source && (
                <>
                  <span className="text-gray-300">•</span>
                  <span className="text-xs text-gray-600">{log.source}</span>
                </>
              )}
            </div>

            {/* Timestamp */}
            <div className="flex items-center space-x-2">
              {!compactMode && showMetrics && log.metrics && (
                <div className="flex items-center space-x-1 text-xs text-gray-500">
                  {log.metrics.duration && (
                    <span>{log.metrics.duration}ms</span>
                  )}
                  {log.metrics.memory && (
                    <span>{(log.metrics.memory / 1024 / 1024).toFixed(1)}MB</span>
                  )}
                </div>
              )}
              <span className={`text-xs text-gray-500 font-mono ${
                compactMode ? 'hidden sm:block' : 'block'
              }`}>
                {formatTimestamp(log.timestamp)}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onToggle()
                }}
                className="p-1 hover:bg-gray-200 rounded transition-colors"
              >
                {expanded ? (
                  <ChevronUp className="w-4 h-4 text-gray-500" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                )}
              </button>
            </div>
          </div>

          {/* Message */}
          <p className={`mt-1 text-gray-900 ${compactMode ? 'text-sm line-clamp-1' : 'text-sm'}`}>
            {log.message}
          </p>

          {/* Expanded Details */}
          {expanded && (
            <div className="mt-3 space-y-2">
              {log.details && Object.keys(log.details).length > 0 && (
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h5 className="text-xs font-semibold text-gray-700 mb-2">詳細信息</h5>
                  <pre className="text-xs text-gray-600 overflow-x-auto">
                    {JSON.stringify(log.details, null, 2)}
                  </pre>
                </div>
              )}

              {log.stackTrace && (
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h5 className="text-xs font-semibold text-gray-700 mb-2">堆棧跟蹤</h5>
                  <pre className="text-xs text-gray-600 font-mono overflow-x-auto whitespace-pre-wrap">
                    {log.stackTrace}
                  </pre>
                </div>
              )}

              {log.correlationId && (
                <div className="flex items-center space-x-2 text-xs text-gray-500">
                  <span className="font-semibold">相關ID:</span>
                  <code className="bg-gray-100 px-2 py-1 rounded font-mono">
                    {log.correlationId}
                  </code>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function StrategyLogViewer({
  strategyId,
  className = '',
  logs,
  maxEntries = 1000,
  autoRefresh = false,
  refreshInterval = 5000,
  showLevels = true,
  showCategories = true,
  showMetrics = true,
  compactMode = false,
  enableSearch = true,
  enableExport = true,
  enableLiveMode = true,
  onLogClick,
  onExport
}: StrategyLogViewerProps) {
  const [filter, setFilter] = useState<LogFilter>({
    levels: ['info', 'warning', 'error', 'critical'],
    categories: [],
    sources: [],
    timeRange: {},
    search: ''
  })
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set())
  const [isLiveMode, setIsLiveMode] = useState(autoRefresh)
  const [isLoading, setIsLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const logContainerRef = useRef<HTMLDivElement>(null)

  // Mock data generation
  const mockLogs = useMemo(() => {
    if (logs) return logs

    const generatedLogs: LogEntry[] = []
    const levels: LogEntry['level'][] = ['debug', 'info', 'warning', 'error', 'critical']
    const categories: LogEntry['category'][] = ['execution', 'performance', 'risk', 'data', 'system', 'trading', 'api', 'websocket']
    const sources = ['strategy-engine', 'data-service', 'risk-monitor', 'websocket-server', 'api-gateway']

    const messages = [
      '策略開始執行',
      '獲取市場數據成功',
      '技術指標計算完成',
      '交易信號觸發',
      '訂單執行成功',
      '風險檢查通過',
      '持倉更新完成',
      '性能指標正常',
      '數據同步完成',
      'WebSocket連接建立',
      'API請求處理完成',
      '內存使用率正常',
      'CPU使用率較高',
      '響應時間超過預期',
      '數據庫連接異常',
      '網絡延遲較高',
      '認證成功',
      '權限驗證通過',
      '配置更新完成',
      '緩存刷新成功'
    ]

    const now = new Date()

    for (let i = 0; i < 500; i++) {
      const timestamp = new Date(now.getTime() - (499 - i) * 60000)
      const level = levels[Math.floor(Math.random() * levels.length)]
      const category = categories[Math.floor(Math.random() * categories.length)]
      const source = sources[Math.floor(Math.random() * sources.length)]
      const message = messages[Math.floor(Math.random() * messages.length)]

      const log: LogEntry = {
        id: `log-${i}`,
        timestamp: timestamp.toISOString(),
        level,
        category,
        message,
        source,
        strategyId,
        correlationId: `corr-${Math.floor(Math.random() * 1000)}`,
        metrics: Math.random() > 0.7 ? {
          duration: Math.floor(Math.random() * 1000),
          memory: Math.floor(Math.random() * 512 * 1024 * 1024),
          cpu: Math.random() * 100,
          requests: Math.floor(Math.random() * 100)
        } : undefined
      }

      if (level === 'error' || level === 'critical') {
        log.details = {
          errorCode: Math.floor(Math.random() * 1000),
          userId: Math.floor(Math.random() * 1000),
          requestId: `req-${Math.random().toString(36).substr(2, 9)}`,
          context: {
            module: source,
            action: 'process_request',
            parameters: {
              timeout: 30000,
              retryCount: 3
            }
          }
        }
        log.stackTrace = `
          at ${source}.process (${source}.js:${Math.floor(Math.random() * 1000)}:${Math.floor(Math.random() * 100)})
          at ${source}.execute (${source}.js:${Math.floor(Math.random() * 1000)}:${Math.floor(Math.random() * 100)})
          at main (${source}.js:${Math.floor(Math.random() * 1000)}:${Math.floor(Math.random() * 100)})
        `.trim()
      }

      generatedLogs.push(log)
    }

    return generatedLogs.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  }, [logs, strategyId])

  // Filter logs based on filter criteria
  const filteredLogs = useMemo(() => {
    let filtered = mockLogs

    // Apply time range filter
    if (filter.timeRange.start) {
      filtered = filtered.filter(log => new Date(log.timestamp) >= filter.timeRange.start!)
    }
    if (filter.timeRange.end) {
      filtered = filtered.filter(log => new Date(log.timestamp) <= filter.timeRange.end!)
    }

    // Apply level filter
    if (filter.levels.length > 0) {
      filtered = filtered.filter(log => filter.levels.includes(log.level))
    }

    // Apply category filter
    if (filter.categories.length > 0) {
      filtered = filtered.filter(log => filter.categories.includes(log.category))
    }

    // Apply source filter
    if (filter.sources.length > 0) {
      filtered = filtered.filter(log => log.source && filter.sources.includes(log.source))
    }

    // Apply search filter
    if (filter.search) {
      const searchLower = filter.search.toLowerCase()
      filtered = filtered.filter(log =>
        log.message.toLowerCase().includes(searchLower) ||
        log.source?.toLowerCase().includes(searchLower) ||
        log.correlationId?.toLowerCase().includes(searchLower)
      )
    }

    return filtered.slice(0, maxEntries)
  }, [mockLogs, filter, maxEntries])

  const toggleLogExpansion = (logId: string) => {
    setExpandedLogs(prev => {
      const newSet = new Set(prev)
      if (newSet.has(logId)) {
        newSet.delete(logId)
      } else {
        newSet.add(logId)
      }
      return newSet
    })
  }

  const toggleAllLogs = (expand: boolean) => {
    if (expand) {
      setExpandedLogs(new Set(filteredLogs.slice(0, 50).map(log => log.id)))
    } else {
      setExpandedLogs(new Set())
    }
  }

  const handleRefresh = async () => {
    setIsLoading(true)
    // Simulate refresh
    await new Promise(resolve => setTimeout(resolve, 1000))
    setIsLoading(false)
  }

  const handleExport = (format: 'csv' | 'json' | 'txt') => {
    if (onExport) {
      onExport(format)
    } else {
      // Default export logic
      let content = ''
      const filename = `strategy-logs-${new Date().toISOString().split('T')[0]}`

      switch (format) {
        case 'csv':
          const headers = ['Timestamp', 'Level', 'Category', 'Source', 'Message']
          const rows = filteredLogs.map(log => [
            log.timestamp,
            log.level,
            log.category,
            log.source || '',
            log.message.replace(/"/g, '""')
          ])
          content = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n')
          break
        case 'json':
          content = JSON.stringify(filteredLogs, null, 2)
          break
        case 'txt':
          content = filteredLogs.map(log =>
            `[${log.timestamp}] ${log.level.toUpperCase()} [${log.category}] ${log.source || ''}: ${log.message}`
          ).join('\n')
          break
      }

      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${filename}.${format}`
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  const handleLogClick = (log: LogEntry) => {
    if (onLogClick) {
      onLogClick(log)
    }
  }

  const updateFilter = (updates: Partial<LogFilter>) => {
    setFilter(prev => ({ ...prev, ...updates }))
  }

  useEffect(() => {
    if (searchTerm !== filter.search) {
      updateFilter({ search: searchTerm })
    }
  }, [searchTerm, filter.search])

  useEffect(() => {
    if (isLiveMode && refreshInterval > 0) {
      const interval = setInterval(handleRefresh, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [isLiveMode, refreshInterval])

  // Auto-scroll to bottom in live mode
  useEffect(() => {
    if (isLiveMode && logContainerRef.current) {
      logContainerRef.current.scrollTop = 0
    }
  }, [filteredLogs, isLiveMode])

  const logCounts = useMemo(() => {
    const counts = Object.fromEntries(
      Object.keys(LOG_LEVELS).map(level => [level, 0])
    )
    filteredLogs.forEach(log => {
      counts[log.level]++
    })
    return counts
  }, [filteredLogs])

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">策略日誌查看器</h2>
            <p className="mt-1 text-sm text-gray-600">
              顯示 {filteredLogs.length} 條日誌記錄
            </p>
          </div>
          <div className="flex items-center space-x-3 mt-4 sm:mt-0">
            {/* Search */}
            {enableSearch && (
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="搜索日誌..."
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                />
              </div>
            )}

            {/* Live Mode Toggle */}
            {enableLiveMode && (
              <button
                onClick={() => setIsLiveMode(!isLiveMode)}
                className={`p-2 rounded-lg transition-colors ${
                  isLiveMode
                    ? 'bg-blue-100 text-blue-600 hover:bg-blue-200'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                title={isLiveMode ? '關閉實時模式' : '開啟實時模式'}
              >
                {isLiveMode ? (
                  <Activity className="w-4 h-4" />
                ) : (
                  <Pause className="w-4 h-4" />
                )}
              </button>
            )}

            {/* Filter Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="p-2 bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
              title="過濾器"
            >
              <Filter className="w-4 h-4" />
            </button>

            {/* Export Menu */}
            {enableExport && (
              <div className="relative group">
                <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors" title="導出">
                  <Download className="w-4 h-4" />
                </button>
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                  <div className="p-2">
                    <button
                      onClick={() => handleExport('csv')}
                      className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                    >
                      導出 CSV
                    </button>
                    <button
                      onClick={() => handleExport('json')}
                      className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                    >
                      導出 JSON
                    </button>
                    <button
                      onClick={() => handleExport('txt')}
                      className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
                    >
                      導出 TXT
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Refresh */}
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="p-6 border-b border-gray-200 bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Level Filter */}
            {showLevels && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  日誌級別
                </label>
                <div className="space-y-2">
                  {Object.entries(LOG_LEVELS).map(([level, config]) => (
                    <label key={level} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filter.levels.includes(level)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            updateFilter({ levels: [...filter.levels, level] })
                          } else {
                            updateFilter({ levels: filter.levels.filter(l => l !== level) })
                          }
                        }}
                        className="mr-2 rounded border-gray-300"
                      />
                      <span className="text-sm text-gray-700">{config.label}</span>
                      <span className="ml-2 text-xs text-gray-500">({logCounts[level] || 0})</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Category Filter */}
            {showCategories && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  日誌分類
                </label>
                <div className="space-y-2">
                  {Object.entries(LOG_CATEGORIES).map(([category, config]) => (
                    <label key={category} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filter.categories.includes(category)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            updateFilter({ categories: [...filter.categories, category] })
                          } else {
                            updateFilter({ categories: filter.categories.filter(c => c !== category) })
                          }
                        }}
                        className="mr-2 rounded border-gray-300"
                      />
                      <span className="text-sm text-gray-700">{config.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Time Range Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                時間範圍
              </label>
              <div className="space-y-2">
                <div>
                  <label className="block text-xs text-gray-600">開始時間</label>
                  <input
                    type="datetime-local"
                    value={filter.timeRange.start ? filter.timeRange.start.toISOString().slice(0, 16) : ''}
                    onChange={(e) => {
                      updateFilter({
                        timeRange: {
                          ...filter.timeRange,
                          start: e.target.value ? new Date(e.target.value) : undefined
                        }
                      })
                    }}
                    className="w-full px-3 py-1 border border-gray-300 rounded-md text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600">結束時間</label>
                  <input
                    type="datetime-local"
                    value={filter.timeRange.end ? filter.timeRange.end.toISOString().slice(0, 16) : ''}
                    onChange={(e) => {
                      updateFilter({
                        timeRange: {
                          ...filter.timeRange,
                          end: e.target.value ? new Date(e.target.value) : undefined
                        }
                      })
                    }}
                    className="w-full px-3 py-1 border border-gray-300 rounded-md text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                快速操作
              </label>
              <div className="space-y-2">
                <button
                  onClick={() => toggleAllLogs(true)}
                  className="w-full px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                >
                  展開前50條
                </button>
                <button
                  onClick={() => toggleAllLogs(false)}
                  className="w-full px-3 py-1 text-sm text-gray-600 hover:bg-gray-50 rounded-md transition-colors"
                >
                  收起全部
                </button>
                <button
                  onClick={() => setFilter({
                    levels: ['info', 'warning', 'error', 'critical'],
                    categories: [],
                    sources: [],
                    timeRange: {},
                    search: ''
                  })}
                  className="w-full px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded-md transition-colors"
                >
                  重置過濾器
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Log Entries */}
      <div
        ref={logContainerRef}
        className={`overflow-y-auto ${compactMode ? 'max-h-96' : 'max-h-screen'}`}
        style={{ maxHeight: compactMode ? '24rem' : 'calc(100vh - 400px)' }}
      >
        {filteredLogs.length === 0 ? (
          <div className="p-8 text-center">
            <Terminal className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">沒有找到匹配的日誌記錄</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredLogs.map((log) => (
              <LogEntryCard
                key={log.id}
                log={log}
                expanded={expandedLogs.has(log.id)}
                onToggle={() => toggleLogExpansion(log.id)}
                onClick={() => handleLogClick(log)}
                showMetrics={showMetrics}
                compactMode={compactMode}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center space-x-4">
            <span>總計: {filteredLogs.length} 條</span>
            {isLiveMode && (
              <span className="flex items-center">
                <Activity className="w-4 h-4 mr-1 text-blue-600" />
                實時模式
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {Object.entries(logCounts).map(([level, count]) => (
              <span key={level} className="flex items-center" style={{ color: LOG_LEVELS[level as keyof typeof LOG_LEVELS].color }}>
                {LOG_LEVELS[level as keyof typeof LOG_LEVELS].label}: {count}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}