import React, { useState } from 'react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Link } from 'react-router-dom'
import {
  ArrowLeftIcon,
  PlusIcon,
  PlayIcon,
  StopIcon,
  TrashIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'

// Mock backtest data
const MOCK_BACKTESTS = [
  {
    id: '1',
    name: 'RSI策略回測-2024',
    strategy: 'RSI策略',
    symbols: ['AAPL', 'MSFT', 'GOOGL'],
    status: 'completed',
    totalReturn: 15.4,
    sharpeRatio: 1.80,
    maxDrawdown: -8.2,
    createdAt: '2025-12-01T10:00:00Z',
  },
  {
    id: '2',
    name: '動量策略測試',
    strategy: '動量策略',
    symbols: ['TSLA', 'NVDA'],
    status: 'running',
    totalReturn: undefined,
    sharpeRatio: undefined,
    maxDrawdown: undefined,
    createdAt: '2025-12-05T09:30:00Z',
  },
  {
    id: '3',
    name: '多因子組合回測',
    strategy: '多因子策略',
    symbols: ['SPY', 'QQQ', 'IWM'],
    status: 'pending',
    totalReturn: undefined,
    sharpeRatio: undefined,
    maxDrawdown: undefined,
    createdAt: '2025-12-04T14:20:00Z',
  },
  {
    id: '4',
    name: '套利策略驗證',
    strategy: '套利策略',
    symbols: ['GLD', 'SLV'],
    status: 'failed',
    totalReturn: undefined,
    sharpeRatio: undefined,
    maxDrawdown: undefined,
    createdAt: '2025-12-03T16:45:00Z',
  },
]

const STATUS_CONFIG = {
  pending: {
    label: '等待中',
    color: 'gray',
    icon: ClockIcon,
  },
  running: {
    label: '運行中',
    color: 'blue',
    icon: PlayIcon,
  },
  completed: {
    label: '已完成',
    color: 'green',
    icon: CheckCircleIcon,
  },
  failed: {
    label: '失敗',
    color: 'red',
    icon: XCircleIcon,
  },
}

const BacktestMockPage: React.FC = () => {
  const [backtests, setBacktests] = useState(MOCK_BACKTESTS)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    strategy: '',
    symbols: '',
    startDate: '',
    endDate: '',
    initialCapital: 100000,
  })

  const getStatusBadge = (status: string) => {
    const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.pending
    const Icon = config.icon
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-${config.color}-100 text-${config.color}-800`}>
        <Icon className="h-3 w-3" />
        {config.label}
      </span>
    )
  }

  const handleCreateBacktest = (e: React.FormEvent) => {
    e.preventDefault()
    const newBacktest = {
      id: String(backtests.length + 1),
      name: formData.name || `${formData.strategy}回測-${new Date().getFullYear()}`,
      strategy: formData.strategy,
      symbols: formData.symbols.split(',').map(s => s.trim()),
      status: 'pending' as const,
      totalReturn: undefined,
      sharpeRatio: undefined,
      maxDrawdown: undefined,
      createdAt: new Date().toISOString(),
    }
    setBacktests([newBacktest, ...backtests])
    setShowCreateForm(false)
    setFormData({
      name: '',
      strategy: '',
      symbols: '',
      startDate: '',
      endDate: '',
      initialCapital: 100000,
    })
    alert('回測任務創建成功！')
  }

  const handleRunBacktest = (id: string) => {
    setBacktests(backtests.map(b =>
      b.id === id ? { ...b, status: 'running' as const } : b
    ))
    alert(`回測任務 ${id} 已開始運行`)
  }

  const handleStopBacktest = (id: string) => {
    setBacktests(backtests.map(b =>
      b.id === id ? { ...b, status: 'pending' as const } : b
    ))
    alert(`回測任務 ${id} 已停止`)
  }

  const handleDeleteBacktest = (id: string) => {
    if (confirm('確定要刪除此回測任務嗎？')) {
      setBacktests(backtests.filter(b => b.id !== id))
      alert(`回測任務 ${id} 已刪除`)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/">
          <Button variant="outline" size="sm">
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            返回首頁
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            回測分析
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            創建和管理策略回測任務
          </p>
        </div>
        <div className="flex gap-3">
          <Button onClick={() => setShowCreateForm(true)}>
            <PlusIcon className="h-5 w-5 mr-2" />
            新建回測
          </Button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">總任務數</div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{backtests.length}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">已完成</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {backtests.filter(b => b.status === 'completed').length}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">運行中</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">
            {backtests.filter(b => b.status === 'running').length}
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">失敗</div>
          <div className="text-2xl font-bold text-red-600 mt-1">
            {backtests.filter(b => b.status === 'failed').length}
          </div>
        </Card>
      </div>

      {/* Create Form Dialog */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="p-6 max-w-md w-full">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              創建回測任務
            </h2>
            <form onSubmit={handleCreateBacktest} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  任務名稱
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                  placeholder="例如：RSI策略回測-2024"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  選擇策略
                </label>
                <select
                  value={formData.strategy}
                  onChange={(e) => setFormData({ ...formData, strategy: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                  required
                >
                  <option value="">請選擇策略</option>
                  <option value="RSI策略">RSI策略</option>
                  <option value="動量策略">動量策略</option>
                  <option value="多因子策略">多因子策略</option>
                  <option value="套利策略">套利策略</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  交易品种
                </label>
                <input
                  type="text"
                  value={formData.symbols}
                  onChange={(e) => setFormData({ ...formData, symbols: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                  placeholder="AAPL, MSFT, GOOGL"
                  required
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  用逗號分隔多個股票代碼
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    開始日期
                  </label>
                  <input
                    type="date"
                    value={formData.startDate}
                    onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    結束日期
                  </label>
                  <input
                    type="date"
                    value={formData.endDate}
                    onChange={(e) => setFormData({ ...formData, endDate: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  初始資本
                </label>
                <input
                  type="number"
                  value={formData.initialCapital}
                  onChange={(e) => setFormData({ ...formData, initialCapital: Number(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                  placeholder="100000"
                />
              </div>

              <div className="flex gap-4 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowCreateForm(false)}
                  className="flex-1"
                >
                  取消
                </Button>
                <Button
                  type="submit"
                  className="flex-1"
                  disabled={!formData.strategy || !formData.symbols}
                >
                  創建
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Backtest List */}
      <Card className="overflow-hidden">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            回測任務列表
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            共 {backtests.length} 個任務
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  任務名稱
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  策略
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  交易品种
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  狀態
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  總收益
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  夏普比率
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  最大回撤
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  創建時間
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {backtests.map((backtest) => (
                <tr key={backtest.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {backtest.name}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900 dark:text-white">
                      {backtest.strategy}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-1">
                      {backtest.symbols.slice(0, 2).map((symbol) => (
                        <span
                          key={symbol}
                          className="inline-flex items-center px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-800"
                        >
                          {symbol}
                        </span>
                      ))}
                      {backtest.symbols.length > 2 && (
                        <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-800">
                          +{backtest.symbols.length - 2}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {getStatusBadge(backtest.status)}
                  </td>
                  <td className="px-6 py-4">
                    {backtest.totalReturn !== undefined ? (
                      <span className={`text-sm font-medium ${
                        backtest.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {backtest.totalReturn >= 0 ? '+' : ''}{backtest.totalReturn.toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-sm text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {backtest.sharpeRatio !== undefined ? (
                      <span className="text-sm text-gray-900 dark:text-white">
                        {backtest.sharpeRatio.toFixed(2)}
                      </span>
                    ) : (
                      <span className="text-sm text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {backtest.maxDrawdown !== undefined ? (
                      <span className="text-sm font-medium text-red-600">
                        {backtest.maxDrawdown.toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-sm text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {new Date(backtest.createdAt).toLocaleDateString('zh-CN')}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2 justify-end">
                      {backtest.status === 'running' && (
                        <button
                          onClick={() => handleStopBacktest(backtest.id)}
                          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                          title="停止"
                        >
                          <StopIcon className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                        </button>
                      )}
                      {(backtest.status === 'pending' || backtest.status === 'failed') && (
                        <button
                          onClick={() => handleRunBacktest(backtest.id)}
                          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                          title="運行"
                        >
                          <PlayIcon className="h-4 w-4 text-green-600 dark:text-green-400" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteBacktest(backtest.id)}
                        className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                        title="刪除"
                      >
                        <TrashIcon className="h-4 w-4 text-red-600 dark:text-red-400" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {backtests.length === 0 && (
          <div className="text-center py-12">
            <ChartBarIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500 dark:text-gray-400">暫無回測任務</p>
            <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
              點擊「新建回測」創建您的第一個回測任務
            </p>
          </div>
        )}
      </Card>

      {/* API Note */}
      <Card className="p-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-3">
          <SparklesIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>API集成：</strong> 回測功能將連接到以下API端點：
              POST /api/backtest/create (創建回測)、POST /api/backtest/{'{'}id{'}'}/run (運行回測)、
              POST /api/backtest/{'{'}id{'}'}/stop (停止回測)、GET /api/backtest (獲取列表)。
              當前顯示模擬數據。實際部署時將從後端獲取真實數據。
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default BacktestMockPage
