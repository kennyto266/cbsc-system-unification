/**
 * Non-Price Strategy Management Page
 * 非價格策略管理頁面
 */

import React, { useState, useEffect, useMemo } from 'react'
import {
  Plus,
  Search,
  Filter,
  Play,
  Pause,
  Square,
  Settings,
  Download,
  TrendingUp,
  AlertCircle,
  Clock,
  CheckCircle,
  XCircle,
  RefreshCw,
  Eye,
  Edit,
  Trash2,
  Copy,
  ArrowUpRight,
  ArrowDownRight,
  Target,
  Activity
} from 'lucide-react'
import { format } from 'date-fns'
import NonPriceStrategyCard from '../components/NonPriceStrategyCard'
import StrategyForm from '../components/StrategyForm'
import StrategyStatusCard from '../components/StrategyStatusCard'
import StrategyHistory from '../components/StrategyHistory'
import { useEconomicStrategy } from '../hooks/useEconomicStrategy'
import { economicStrategyApi } from '../services/economicStrategyApi'

// Mock API response for development
const mockApiCall = async (method: string, data?: any) => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 500))

  if (method === 'getAllStrategies') {
    return {
      success: true,
      data: [] // Empty for now, will be populated by backend
    }
  }

  return {
    success: true,
    message: 'Operation successful'
  }
}

// Mock API if real API is not available
const safeApiCall = async (fn: () => Promise<any>) => {
  try {
    return await fn()
  } catch (error) {
    console.warn('API call failed, using mock response:', error)
    return mockApiCall('mock')
  }
}

interface NonPriceStrategy {
  id: string
  name: string
  type: 'interest_rate_arbitrage' | 'economic_data_correlation' | 'multi_indicator_momentum' | 'volatility_based' | 'seasonal_patterns'
  status: 'active' | 'paused' | 'stopped' | 'error' | 'testing'
  description: string
  parameters: Record<string, any>
  indicators: string[]
  createdAt: string
  updatedAt: string
  lastRun?: string
  nextRun?: string
  performance?: {
    totalReturn: number
    winRate: number
    sharpeRatio: number
    maxDrawdown: number
    totalTrades: number
    profitableTrades: number
  }
  error?: string
  configuration?: {
    autoRestart: boolean
    riskLimits: {
      maxPositionSize: number
      maxDailyLoss: number
      maxDrawdown: number
    }
    executionSettings: {
      slippageTolerance: number
      executionDelay: number
      retryAttempts: number
    }
  }
}

interface StrategyFormData {
  name: string
  type: NonPriceStrategy['type']
  description: string
  parameters: Record<string, any>
  indicators: string[]
  configuration: {
    autoRestart: boolean
    riskLimits: NonPriceStrategy['configuration']['riskLimits']
    executionSettings: NonPriceStrategy['configuration']['executionSettings']
  }
}

const STRATEGY_TYPES = [
  {
    value: 'interest_rate_arbitrage',
    label: '利率套利',
    description: '利用跨市場利率差異進行套利',
    icon: TrendingUp,
    color: 'blue'
  },
  {
    value: 'economic_data_correlation',
    label: '經濟數據相關性',
    description: '利用經濟指標與市場波動的相關性',
    icon: Filter,
    color: 'green'
  },
  {
    value: 'multi_indicator_momentum',
    label: '多指標動量',
    description: '結合多個經濟指標進行動量交易',
    icon: Activity,
    color: 'purple'
  },
  {
    value: 'volatility_based',
    label: '波動率策略',
    description: '基於經濟波動率模式生成信號',
    icon: AlertCircle,
    color: 'orange'
  },
  {
    value: 'seasonal_patterns',
    label: '季節性模式',
    description: '識別並交易季節性經濟模式',
    icon: Clock,
    color: 'pink'
  }
]

const STRATEGY_STATUS_CONFIG = {
  active: {
    color: 'text-green-600',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-200',
    icon: Play,
    label: '運行中'
  },
  paused: {
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200',
    icon: Pause,
    label: '已暫停'
  },
  stopped: {
    color: 'text-red-600',
    bgColor: 'bg-red-100',
    borderColor: 'border-red-200',
    icon: Square,
    label: '已停止'
  },
  error: {
    color: 'text-red-600',
    bgColor: 'bg-red-100',
    borderColor: 'border-red-200',
    icon: XCircle,
    label: '錯誤'
  },
  testing: {
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200',
    icon: Clock,
    label: '測試中'
  }
}

export default function NonPriceStrategyManagement() {
  // State management
  const [strategies, setStrategies] = useState<NonPriceStrategy[]>([])
  const [filteredStrategies, setFilteredStrategies] = useState<NonPriceStrategy[]>([])
  const [selectedStrategy, setSelectedStrategy] = useState<NonPriceStrategy | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showEditForm, setShowEditForm] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState<string>('all')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [sortBy, setSortBy] = useState<string>('updatedAt')
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  // Economic strategy hook
  const {
    createStrategy,
    updateStrategy,
    deleteStrategy,
    startStrategy,
    stopStrategy,
    pauseStrategy,
    resumeStrategy,
    getStrategyHistory,
    getStrategyPerformance
  } = useEconomicStrategy()

  // Load strategies on component mount
  useEffect(() => {
    loadStrategies()
  }, [])

  // Filter and sort strategies
  useEffect(() => {
    let filtered = [...strategies]

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(strategy =>
        strategy.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        strategy.description.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Apply type filter
    if (filterType !== 'all') {
      filtered = filtered.filter(strategy => strategy.type === filterType)
    }

    // Apply status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(strategy => strategy.status === filterStatus)
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name)
        case 'status':
          return a.status.localeCompare(b.status)
        case 'performance':
          const aPerf = a.performance?.totalReturn || 0
          const bPerf = b.performance?.totalReturn || 0
          return bPerf - aPerf
        case 'createdAt':
          return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        case 'updatedAt':
        default:
          return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
      }
    })

    setFilteredStrategies(filtered)
  }, [strategies, searchTerm, filterType, filterStatus, sortBy])

  const loadStrategies = async () => {
    try {
      setLoading(true)
      const response = await safeApiCall(() => economicStrategyApi.getAllStrategies())
      if (response.success) {
        setStrategies(response.data || [])
      }
    } catch (error) {
      console.error('Error loading strategies:', error)
      setStrategies([])
    } finally {
      setLoading(false)
    }
  }

  const handleCreateStrategy = async (formData: StrategyFormData) => {
    try {
      setActionLoading(true)
      const response = await createStrategy(formData)
      if (response.success) {
        setShowCreateForm(false)
        await loadStrategies()
        return true
      }
      return false
    } catch (error) {
      console.error('Error creating strategy:', error)
      return false
    } finally {
      setActionLoading(false)
    }
  }

  const handleUpdateStrategy = async (formData: StrategyFormData) => {
    if (!selectedStrategy) return false

    try {
      setActionLoading(true)
      const response = await updateStrategy(selectedStrategy.id, formData)
      if (response.success) {
        setShowEditForm(false)
        setSelectedStrategy(null)
        await loadStrategies()
        return true
      }
      return false
    } catch (error) {
      console.error('Error updating strategy:', error)
      return false
    } finally {
      setActionLoading(false)
    }
  }

  const handleDeleteStrategy = async (strategyId: string) => {
    if (!confirm('確定要刪除此策略嗎？此操作無法撤銷。')) {
      return
    }

    try {
      setActionLoading(true)
      const response = await deleteStrategy(strategyId)
      if (response.success) {
        await loadStrategies()
      }
    } catch (error) {
      console.error('Error deleting strategy:', error)
    } finally {
      setActionLoading(false)
    }
  }

  const handleStartStrategy = async (strategyId: string) => {
    try {
      setActionLoading(true)
      const response = await startStrategy(strategyId)
      if (response.success) {
        await loadStrategies()
      }
    } catch (error) {
      console.error('Error starting strategy:', error)
    } finally {
      setActionLoading(false)
    }
  }

  const handleStopStrategy = async (strategyId: string) => {
    if (!confirm('確定要停止此策略嗎？')) {
      return
    }

    try {
      setActionLoading(true)
      const response = await stopStrategy(strategyId)
      if (response.success) {
        await loadStrategies()
      }
    } catch (error) {
      console.error('Error stopping strategy:', error)
    } finally {
      setActionLoading(false)
    }
  }

  const handlePauseStrategy = async (strategyId: string) => {
    try {
      setActionLoading(true)
      const response = await pauseStrategy(strategyId)
      if (response.success) {
        await loadStrategies()
      }
    } catch (error) {
      console.error('Error pausing strategy:', error)
    } finally {
      setActionLoading(false)
    }
  }

  const handleResumeStrategy = async (strategyId: string) => {
    try {
      setActionLoading(true)
      const response = await resumeStrategy(strategyId)
      if (response.success) {
        await loadStrategies()
      }
    } catch (error) {
      console.error('Error resuming strategy:', error)
    } finally {
      setActionLoading(false)
    }
  }

  const handleDuplicateStrategy = (strategy: NonPriceStrategy) => {
    const formData: StrategyFormData = {
      name: `${strategy.name} (副本)`,
      type: strategy.type,
      description: strategy.description,
      parameters: { ...strategy.parameters },
      indicators: [...strategy.indicators],
      configuration: strategy.configuration || {
        autoRestart: false,
        riskLimits: {
          maxPositionSize: 100000,
          maxDailyLoss: 0.05,
          maxDrawdown: 0.15
        },
        executionSettings: {
          slippageTolerance: 0.001,
          executionDelay: 1000,
          retryAttempts: 3
        }
      }
    }
    setSelectedStrategy(null)
    setShowCreateForm(true)
  }

  const getStatusConfig = (status: string) => {
    return STRATEGY_STATUS_CONFIG[status as keyof typeof STRATEGY_STATUS_CONFIG] || STRATEGY_STATUS_CONFIG.stopped
  }

  const getStrategyTypeConfig = (type: string) => {
    return STRATEGY_TYPES.find(t => t.value === type) || STRATEGY_TYPES[0]
  }

  const calculateOverallStats = () => {
    const activeStrategies = filteredStrategies.filter(s => s.status === 'active')
    const totalPerformance = filteredStrategies.reduce((sum, s) => {
      return sum + (s.performance?.totalReturn || 0)
    }, 0)
    const totalTrades = filteredStrategies.reduce((sum, s) => {
      return sum + (s.performance?.totalTrades || 0)
    }, 0)
    const totalWinRate = activeStrategies.length > 0
      ? activeStrategies.reduce((sum, s) => sum + (s.performance?.winRate || 0), 0) / activeStrategies.length
      : 0

    return {
      totalStrategies: filteredStrategies.length,
      activeStrategies: activeStrategies.length,
      totalPerformance,
      totalTrades,
      averageWinRate: totalWinRate
    }
  }

  const stats = calculateOverallStats()

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">載入策略中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">策略管理</h1>
                <p className="text-sm text-gray-500">管理和監控經濟交易策略</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowCreateForm(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="h-5 w-5" />
                <span>新建策略</span>
              </button>
              <button
                onClick={loadStrategies}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                title="重新整理"
              >
                <RefreshCw className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-blue-100 rounded-lg">
                <TrendingUp className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">總策略數</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.totalStrategies}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-green-100 rounded-lg">
                <Play className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">運行中策略</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.activeStrategies}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-purple-100 rounded-lg">
                <ArrowUpRight className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">總收益率</p>
                <p className={`text-2xl font-semibold ${
                  stats.totalPerformance >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {stats.totalPerformance >= 0 ? '+' : ''}{stats.totalPerformance.toFixed(2)}%
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <CheckCircle className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">總交易數</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.totalTrades.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 bg-pink-100 rounded-lg">
                <Target className="h-6 w-6 text-pink-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">平均勝率</p>
                <p className="text-2xl font-semibold text-gray-900">{(stats.averageWinRate * 100).toFixed(1)}%</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="搜尋策略..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">所有類型</option>
                {STRATEGY_TYPES.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>

              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">所有狀態</option>
                {Object.entries(STRATEGY_STATUS_CONFIG).map(([key, config]) => (
                  <option key={key} value={key}>
                    {config.label}
                  </option>
                ))}
              </select>

              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="updatedAt">最後更新</option>
                <option value="name">名稱</option>
                <option value="status">狀態</option>
                <option value="performance">績效</option>
                <option value="createdAt">創建日期</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Strategies Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
        {filteredStrategies.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <div className="text-gray-400 mb-4">
              <Filter className="h-12 w-12 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">未找到策略</h3>
            <p className="text-gray-500 mb-4">
              {searchTerm || filterType !== 'all' || filterStatus !== 'all'
                ? '請嘗試調整您的篩選條件或搜尋詞'
                : '開始創建您的第一個經濟交易策略'}
            </p>
            {!searchTerm && filterType === 'all' && filterStatus === 'all' && (
              <button
                onClick={() => setShowCreateForm(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                創建策略
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredStrategies.map(strategy => {
              const statusConfig = getStatusConfig(strategy.status)
              const typeConfig = getStrategyTypeConfig(strategy.type)
              const StatusIcon = statusConfig.icon
              const TypeIcon = typeConfig.icon

              return (
                <NonPriceStrategyCard
                  key={strategy.id}
                  strategy={strategy}
                  onStart={() => handleStartStrategy(strategy.id)}
                  onStop={() => handleStopStrategy(strategy.id)}
                  onPause={() => handlePauseStrategy(strategy.id)}
                  onResume={() => handleResumeStrategy(strategy.id)}
                  onEdit={() => {
                    setSelectedStrategy(strategy)
                    setShowEditForm(true)
                  }}
                  onDelete={() => handleDeleteStrategy(strategy.id)}
                  onDuplicate={() => handleDuplicateStrategy(strategy)}
                  onViewHistory={() => {
                    setSelectedStrategy(strategy)
                    setShowHistory(true)
                  }}
                  actionLoading={actionLoading}
                />
              )
            })}
          </div>
        )}
      </div>

      {/* Create Strategy Modal */}
      {showCreateForm && (
        <StrategyForm
          isOpen={showCreateForm}
          onClose={() => setShowCreateForm(false)}
          onSubmit={handleCreateStrategy}
          loading={actionLoading}
        />
      )}

      {/* Edit Strategy Modal */}
      {showEditForm && selectedStrategy && (
        <StrategyForm
          isOpen={showEditForm}
          onClose={() => {
            setShowEditForm(false)
            setSelectedStrategy(null)
          }}
          onSubmit={handleUpdateStrategy}
          loading={actionLoading}
          initialData={{
            name: selectedStrategy.name,
            type: selectedStrategy.type,
            description: selectedStrategy.description,
            parameters: selectedStrategy.parameters,
            indicators: selectedStrategy.indicators,
            configuration: selectedStrategy.configuration
          }}
          isEdit={true}
        />
      )}

      {/* Strategy History Modal */}
      {showHistory && selectedStrategy && (
        <StrategyHistory
          strategy={selectedStrategy}
          isOpen={showHistory}
          onClose={() => {
            setShowHistory(false)
            setSelectedStrategy(null)
          }}
        />
      )}
    </div>
  )
}
