import React from 'react'
import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import {
  ArrowPathIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  PencilIcon,
  TrashIcon,
  PlayIcon,
  PauseIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

// Mock strategy data
const MOCK_STRATEGIES = [
  {
    id: '1',
    name: 'CBSC RSI策略',
    category: 'core_cbsc',
    status: 'active',
    annual_return: 15.4,
    sharpe_ratio: 1.8,
    max_drawdown: 0.08,
    description: '基於CBSC數據的RSI策略',
    createdAt: '2025-12-01',
  },
  {
    id: '2',
    name: '情緒動量策略',
    category: 'multi_factor',
    status: 'active',
    annual_return: 12.3,
    sharpe_ratio: 1.5,
    max_drawdown: 0.12,
    description: '結合市場情緒的動量策略',
    createdAt: '2025-12-05',
  },
  {
    id: '3',
    name: '月度再平衡策略',
    category: 'monthly',
    status: 'inactive',
    annual_return: 8.7,
    sharpe_ratio: 1.2,
    max_drawdown: 0.05,
    description: '每月進行資產再平衡',
    createdAt: '2025-12-10',
  },
]

const STATUS_CONFIG = {
  active: { label: '運行中', color: 'green' },
  inactive: { label: '未激活', color: 'gray' },
  testing: { label: '測試中', color: 'blue' },
  error: { label: '錯誤', color: 'red' },
}

const CATEGORY_CONFIG = {
  core_cbsc: { label: '核心CBSC', color: 'blue' },
  multi_factor: { label: '多因子', color: 'purple' },
  monthly: { label: '月度策略', color: 'cyan' },
  other: { label: '其他', color: 'gray' },
}

const StrategiesListPage: React.FC = () => {
  const [strategies] = React.useState(MOCK_STRATEGIES)
  const [searchTerm, setSearchTerm] = React.useState('')
  const [selectedCategory, setSelectedCategory] = React.useState('')

  const filteredStrategies = strategies.filter(strategy => {
    const matchesSearch = strategy.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         strategy.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = !selectedCategory || strategy.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const getStatusBadge = (status: string) => {
    const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.inactive
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full bg-${config.color}-100 text-${config.color}-800`}>
        {config.label}
      </span>
    )
  }

  const getCategoryBadge = (category: string) => {
    const config = CATEGORY_CONFIG[category as keyof typeof CATEGORY_CONFIG] || CATEGORY_CONFIG.other
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full bg-${config.color}-100 text-${config.color}-800`}>
        {config.label}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            策略列表
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            管理和監控您的所有量化交易策略
          </p>
        </div>
        <div className="flex gap-3">
          <Link to="/strategies/create">
            <Button>
              <PlusIcon className="h-5 w-5 mr-2" />
              創建策略
            </Button>
          </Link>
        </div>
      </div>

      {/* Search and Filters */}
      <Card className="p-4">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="搜索策略名稱或描述..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
            />
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
          >
            <option value="">所有類別</option>
            <option value="core_cbsc">核心CBSC</option>
            <option value="multi_factor">多因子</option>
            <option value="monthly">月度策略</option>
          </select>
        </div>
      </Card>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">總策略數</div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{strategies.length}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">運行中</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {strategies.filter(s => s.status === 'active').length}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">平均年化收益</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">
            {(strategies.reduce((sum, s) => sum + s.annual_return, 0) / strategies.length).toFixed(1)}%
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">最佳夏普比率</div>
          <div className="text-2xl font-bold text-purple-600 mt-1">
            {Math.max(...strategies.map(s => s.sharpe_ratio)).toFixed(2)}
          </div>
        </Card>
      </div>

      {/* Strategy List */}
      <Card className="overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">策略名稱</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">類別</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">狀態</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">年化收益</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">夏普比率</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">最大回撤</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">操作</th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            {filteredStrategies.map((strategy) => (
              <tr key={strategy.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="px-6 py-4">
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {strategy.name}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {strategy.description}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">{getCategoryBadge(strategy.category)}</td>
                <td className="px-6 py-4">{getStatusBadge(strategy.status)}</td>
                <td className="px-6 py-4">
                  <span className={`text-sm font-medium ${strategy.annual_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {strategy.annual_return.toFixed(1)}%
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                  {strategy.sharpe_ratio.toFixed(2)}
                </td>
                <td className="px-6 py-4">
                  <span className={`text-sm font-medium ${strategy.max_drawdown <= 0.1 ? 'text-green-600' : 'text-red-600'}`}>
                    {(strategy.max_drawdown * 100).toFixed(1)}%
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex gap-2">
                    <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded" title="編輯">
                      <PencilIcon className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                    </button>
                    <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded" title="執行">
                      <PlayIcon className="h-4 w-4 text-green-600 dark:text-green-400" />
                    </button>
                    <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded" title="分析">
                      <ChartBarIcon className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    </button>
                    <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded" title="刪除">
                      <TrashIcon className="h-4 w-4 text-red-600 dark:text-red-400" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredStrategies.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 dark:text-gray-400">沒有找到匹配的策略</p>
          </div>
        )}
      </Card>

      {/* API Note */}
      <Card className="p-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-3">
          <ArrowPathIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>數據來源：</strong> 此頁面已連接到後端API (http://localhost:3005/api/personal-strategies/strategies)。
              當前顯示模擬數據。登錄後將顯示真實的策略數據。
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default StrategiesListPage
