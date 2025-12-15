import React, { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { debounce } from 'lodash-es'

// UI Components
import { Card, Button, Input, Select, Badge, Pagination } from '../../../components/ui'
import {
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  PlayIcon,
  PauseIcon,
  StopIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  ChevronUpDownIcon,
  CheckIcon,
  XMarkIcon,
  Squares2X2Icon,
  TableCellsIcon
} from '@heroicons/react/24/outline'

// Hooks and API
import { useGetStrategiesQuery } from '../../../api/endpoints/strategyApi'
import { useToast } from '../../../hooks/useToast'
import { useTheme } from '../../../hooks/useTheme'

// Components
import BatchOperations from './BatchOperations'

// Types
import type { Strategy, StrategyFilter } from '../../../types/strategy'

// Strategy status configuration
const STRATEGY_STATUS_CONFIG = {
  active: { label: '运行中', color: 'green' },
  inactive: { label: '未激活', color: 'gray' },
  testing: { label: '测试中', color: 'blue' },
  archived: { label: '已归档', color: 'gray' },
  error: { label: '错误', color: 'red' },
  processing: { label: '处理中', color: 'yellow' }
} as const

// Strategy category configuration
const STRATEGY_CATEGORY_CONFIG = {
  core_cbsc: { label: '核心CBSC', color: 'blue' },
  multi_factor: { label: '多因子', color: 'purple' },
  multi_strategy: { label: '多策略', color: 'indigo' },
  monthly: { label: '月度策略', color: 'cyan' },
  other: { label: '其他', color: 'gray' }
} as const

// Columns for the strategy table
const STRATEGY_COLUMNS = [
  { key: 'name', label: '策略名称', sortable: true },
  { key: 'category', label: '类别', sortable: true },
  { key: 'status', label: '状态', sortable: true },
  { key: 'annual_return', label: '年化收益率', sortable: true },
  { key: 'sharpe_ratio', label: '夏普比率', sortable: true },
  { key: 'max_drawdown', label: '最大回撤', sortable: true },
  { key: 'createdAt', label: '创建时间', sortable: true },
  { key: 'actions', label: '操作', sortable: false }
] as const

// Strategy List Component
const StrategyList: React.FC = () => {
  const navigate = useNavigate()
  const { theme } = useTheme()
  const { addToast } = useToast()

  // State management
  const [filters, setFilters] = useState<StrategyFilter>({})
  const [pagination, setPagination] = useState({ page: 1, pageSize: 20 })
  const [sortBy, setSortBy] = useState('createdAt')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [viewMode, setViewMode] = useState<'table' | 'card'>('table')
  const [showFilters, setShowFilters] = useState(false)

  // API call with memoized parameters
  const queryParams = useMemo(() => ({
    page: pagination.page,
    pageSize: pagination.pageSize,
    search: filters.search,
    category: filters.category,
    status: filters.status,
    sortBy,
    sortOrder
  }), [pagination, filters, sortBy, sortOrder])

  const {
    data: strategiesData,
    error,
    isLoading,
    refetch
  } = useGetStrategiesQuery(queryParams)

  // Debounced search
  const debouncedSearch = useMemo(
    () => debounce((searchTerm: string) => {
      setFilters(prev => ({ ...prev, search: searchTerm }))
      setPagination(prev => ({ ...prev, page: 1 }))
    }, 300),
    []
  )

  // Handle search input
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    debouncedSearch(event.target.value)
  }

  // Handle filter changes
  const handleFilterChange = (key: keyof StrategyFilter, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  // Handle sorting
  const handleSort = (column: string) => {
    if (column === sortBy) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('desc')
    }
  }

  // Handle selection
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(strategiesData?.items?.map(s => s.id) || [])
    } else {
      setSelectedIds([])
    }
  }

  const handleSelectStrategy = (id: string, checked: boolean) => {
    if (checked) {
      setSelectedIds(prev => [...prev, id])
    } else {
      setSelectedIds(prev => prev.filter(selectedId => selectedId !== id))
    }
  }

  // Handle strategy actions
  const handleCreateStrategy = () => {
    navigate('/strategies/create')
  }

  const handleEditStrategy = (id: string) => {
    navigate(`/strategies/${id}/edit`)
  }

  const handleViewAnalysis = (id: string) => {
    navigate(`/strategies/${id}/analysis`)
  }

  const handleQuickAction = async (id: string, action: 'start' | 'stop' | 'pause') => {
    try {
      // TODO: Implement quick action API call
      addToast({
        type: 'success',
        message: `策略${action === 'start' ? '启动' : action === 'stop' ? '停止' : '暂停'}成功`
      })
      refetch()
    } catch (error) {
      addToast({
        type: 'error',
        message: `操作失败: ${error instanceof Error ? error.message : '未知错误'}`
      })
    }
  }

  // Render status badge
  const renderStatusBadge = (status: string) => {
    const config = STRATEGY_STATUS_CONFIG[status as keyof typeof STRATEGY_STATUS_CONFIG]
    return (
      <Badge variant={config?.color as any} size="sm">
        {config?.label || status}
      </Badge>
    )
  }

  // Render category badge
  const renderCategoryBadge = (category: string) => {
    const config = STRATEGY_CATEGORY_CONFIG[category as keyof typeof STRATEGY_CATEGORY_CONFIG]
    return (
      <Badge variant={config?.color as any} size="sm">
        {config?.label || category}
      </Badge>
    )
  }

  // Render loading skeleton
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="h-12 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Render error state
  if (error) {
    return (
      <Card className="text-center py-12">
        <div className="text-red-500 mb-4">加载策略列表失败</div>
        <Button onClick={() => refetch()}>重试</Button>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          策略管理
        </h1>
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
          >
            <FunnelIcon className="h-5 w-5 mr-2" />
            筛选
          </Button>
          <Button onClick={handleCreateStrategy}>
            <PlusIcon className="h-5 w-5 mr-2" />
            创建策略
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <Card className="p-4">
        <div className="space-y-4">
          {/* Search Bar */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="搜索策略名称、描述或标签..."
                onChange={handleSearchChange}
                className="w-full"
                startAdornment={<MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />}
              />
            </div>
            <div className="flex gap-2">
              <Select
                placeholder="类别"
                value={filters.category}
                onChange={(value) => handleFilterChange('category', value)}
                className="w-32"
              >
                <option value="">全部</option>
                {Object.entries(STRATEGY_CATEGORY_CONFIG).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
                ))}
              </Select>
              <Select
                placeholder="状态"
                value={filters.status}
                onChange={(value) => handleFilterChange('status', value)}
                className="w-32"
              >
                <option value="">全部</option>
                {Object.entries(STRATEGY_STATUS_CONFIG).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
                ))}
              </Select>
            </div>
          </div>

          {/* Advanced Filters (collapsible) */}
          {showFilters && (
            <div className="border-t pt-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* TODO: Add advanced filters */}
                <div className="text-sm text-gray-500">
                  高级筛选功能开发中...
                </div>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Batch Operations */}
      <BatchOperations
        selectedIds={selectedIds}
        onSelectionChange={setSelectedIds}
        onOperationComplete={() => refetch()}
      />

      {/* View Mode Toggle and Stats */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setViewMode('table')}
              className={`flex items-center px-3 py-1 rounded text-sm font-medium transition-colors ${
                viewMode === 'table'
                  ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
              }`}
            >
              <TableCellsIcon className="h-4 w-4 mr-2" />
              表格
            </button>
            <button
              onClick={() => setViewMode('card')}
              className={`flex items-center px-3 py-1 rounded text-sm font-medium transition-colors ${
                viewMode === 'card'
                  ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
              }`}
            >
              <Squares2X2Icon className="h-4 w-4 mr-2" />
              卡片
            </button>
          </div>
        </div>

        {/* Pagination Info */}
        <div className="text-sm text-gray-500">
          共 {strategiesData?.total || 0} 个策略
        </div>
      </div>

      {/* Strategy Table */}
      {viewMode === 'table' ? (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="w-12 p-4">
                    <input
                      type="checkbox"
                      checked={selectedIds.length === strategiesData?.items?.length}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </th>
                  {STRATEGY_COLUMNS.map(column => (
                    <th
                      key={column.key}
                      className="p-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                    >
                      {column.sortable ? (
                        <button
                          onClick={() => handleSort(column.key)}
                          className="flex items-center space-x-1 hover:text-gray-700 dark:hover:text-gray-300"
                        >
                          <span>{column.label}</span>
                          <ChevronUpDownIcon className="h-4 w-4" />
                        </button>
                      ) : (
                        column.label
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                {strategiesData?.items?.map((strategy: Strategy) => (
                  <tr key={strategy.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="p-4">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(strategy.id)}
                        onChange={(e) => handleSelectStrategy(strategy.id, e.target.checked)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </td>
                    <td className="p-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {strategy.name}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {strategy.description}
                        </div>
                      </div>
                    </td>
                    <td className="p-4">
                      {renderCategoryBadge(strategy.category)}
                    </td>
                    <td className="p-4">
                      {renderStatusBadge(strategy.status)}
                    </td>
                    <td className="p-4">
                      <div className={`text-sm font-medium ${
                        (strategy.annual_return || 0) >= 0
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {strategy.annual_return
                          ? `${strategy.annual_return.toFixed(2)}%`
                          : '-'
                        }
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="text-sm text-gray-900 dark:text-white">
                        {strategy.sharpe_ratio?.toFixed(2) || '-'}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className={`text-sm font-medium ${
                        (strategy.max_drawdown || 0) <= 0.1
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {strategy.max_drawdown
                          ? `${(strategy.max_drawdown * 100).toFixed(2)}%`
                          : '-'
                        }
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="text-sm text-gray-900 dark:text-white">
                        {new Date(strategy.createdAt).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewAnalysis(strategy.id)}
                        >
                          <EyeIcon className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditStrategy(strategy.id)}
                        >
                          <PencilIcon className="h-4 w-4" />
                        </Button>
                        <div className="relative">
                          <Button variant="ghost" size="sm">
                            <PlayIcon className="h-4 w-4" />
                          </Button>
                          {/* TODO: Add dropdown menu for more actions */}
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <>
          {/* Card View */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {strategiesData?.items?.map((strategy: Strategy) => (
            <Card key={strategy.id} className="hover:shadow-lg transition-shadow cursor-pointer">
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">
                      {strategy.name}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
                      {strategy.description}
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(strategy.id)}
                    onChange={(e) => handleSelectStrategy(strategy.id, e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center space-x-2 mb-4">
                  {renderCategoryBadge(strategy.category)}
                  {renderStatusBadge(strategy.status)}
                </div>

                {(strategy.annual_return !== undefined || strategy.sharpe_ratio !== undefined || strategy.max_drawdown !== undefined) && (
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="text-center">
                      <div className={`text-lg font-semibold ${
                        (strategy.annual_return || 0) >= 0
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {(strategy.annual_return || 0).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">年化收益</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold text-gray-900 dark:text-white">
                        {(strategy.sharpe_ratio || 0).toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">夏普比率</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-lg font-semibold ${
                        (strategy.max_drawdown || 0) <= 0.1
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {(strategy.max_drawdown || 0).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">最大回撤</div>
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    创建于 {new Date(strategy.createdAt).toLocaleDateString()}
                  </div>
                  <div className="flex items-center space-x-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleViewAnalysis(strategy.id)}
                    >
                      <EyeIcon className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditStrategy(strategy.id)}
                    >
                      <PencilIcon className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleQuickAction(strategy.id, 'start')}
                    >
                      <PlayIcon className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
        </>
      )}

      {/* Pagination */}
      {strategiesData && strategiesData.total > pagination.pageSize && (
        <div className="flex justify-center">
          <Pagination
            currentPage={pagination.page}
            totalPages={strategiesData.totalPages}
            onPageChange={(page) => setPagination(prev => ({ ...prev, page }))}
            onPageSizeChange={(pageSize) => setPagination(prev => ({ ...prev, pageSize, page: 1 }))}
          />
        </div>
      )}

      {/* Empty State */}
      {!isLoading && strategiesData?.items?.length === 0 && (
        <Card className="text-center py-12">
          <div className="text-gray-500 mb-4">暂无策略</div>
          <Button onClick={handleCreateStrategy}>创建第一个策略</Button>
        </Card>
      )}
    </div>
  )
}

export default StrategyList;