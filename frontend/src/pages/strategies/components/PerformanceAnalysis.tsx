import React, { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { useGetStrategyQuery, useGetPerformanceQuery } from '../../../store/api/apiSlice'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  ReferenceLine,
} from 'recharts'
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  DocumentArrowDownIcon,
  CalendarDaysIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  CurrencyDollarIcon,
  PercentBadgeIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline'
import { format } from 'date-fns'

// Type definitions
interface PerformanceMetrics {
  totalReturn: number
  annualizedReturn: number
  winRate: number
  profitFactor: number
  sharpeRatio: number
  maxDrawdown: number
  calmarRatio: number
  sortinoRatio: number
  totalTrades: number
  winningTrades: number
  losingTrades: number
  avgWin: number
  avgLoss: number
  largestWin: number
  largestLoss: number
  avgTradeDuration: string
  winRateByMonth: number[]
  monthlyReturns: Array<{ month: string; return: number }>
  equityCurve: Array<{ date: string; equity: number; drawdown: number }>
  tradeDistribution: Array<{ name: string; value: number; color: string }>
}

interface PeriodOption {
  label: string
  value: string
  days: number
}

const periodOptions: PeriodOption[] = [
  { label: '1天', value: '1D', days: 1 },
  { label: '1周', value: '1W', days: 7 },
  { label: '1月', value: '1M', days: 30 },
  { label: '3月', value: '3M', days: 90 },
  { label: '6月', value: '6M', days: 180 },
  { label: '1年', value: '1Y', days: 365 },
  { label: '全部', value: 'ALL', days: 0 },
]

// Mock data generator
const generateMockPerformanceData = (strategyId: string, period: string): PerformanceMetrics => {
  const days = periodOptions.find(p => p.value === period)?.days || 365
  const dataPoints = days === 0 ? 730 : Math.min(days * 2, 730)

  // Generate equity curve
  let equity = 100000
  const equityCurve = []
  const monthlyReturnsMap = new Map<string, number>()

  for (let i = 0; i < dataPoints; i++) {
    const date = new Date()
    date.setDate(date.getDate() - (dataPoints - i))
    const dateStr = format(date, 'yyyy-MM-dd')

    // Simulate daily returns
    const dailyReturn = (Math.random() - 0.45) * 0.04 // Slight positive bias
    equity *= (1 + dailyReturn)

    // Calculate drawdown
    const peak = Math.max(...equityCurve.map(d => d.equity), equity)
    const drawdown = ((peak - equity) / peak) * 100

    equityCurve.push({
      date: dateStr,
      equity: parseFloat(equity.toFixed(2)),
      drawdown: parseFloat(drawdown.toFixed(2)),
    })

    // Monthly returns
    const monthKey = format(date, 'yyyy-MM')
    if (!monthlyReturnsMap.has(monthKey)) {
      monthlyReturnsMap.set(monthKey, 0)
    }
    monthlyReturnsMap.set(monthKey, (monthlyReturnsMap.get(monthKey) || 0) + dailyReturn)
  }

  // Convert monthly returns to array
  const monthlyReturns = Array.from(monthlyReturnsMap.entries())
    .map(([month, returnVal]) => ({
      month: format(new Date(month + '-01'), 'MMM yyyy'),
      return: parseFloat((returnVal * 100).toFixed(2)),
    }))
    .slice(-12)

  // Calculate metrics
  const totalReturn = ((equity - 100000) / 100000) * 100
  const annualizedReturn = days === 0 ?
    (Math.pow(equity / 100000, 365 / dataPoints) - 1) * 100 :
    (Math.pow(equity / 100000, 365 / days) - 1) * 100

  const totalTrades = Math.floor(Math.random() * 500) + 100
  const winningTrades = Math.floor(totalTrades * (0.45 + Math.random() * 0.2))
  const losingTrades = totalTrades - winningTrades
  const winRate = (winningTrades / totalTrades) * 100

  const avgWin = parseFloat((Math.random() * 500 + 100).toFixed(2))
  const avgLoss = parseFloat((-(Math.random() * 200 + 50)).toFixed(2))
  const profitFactor = parseFloat(((avgWin * winningTrades) / Math.abs(avgLoss * losingTrades)).toFixed(2))

  const sharpeRatio = parseFloat((annualizedReturn / 15 + Math.random() * 2).toFixed(2))
  const maxDrawdown = Math.max(...equityCurve.map(d => d.drawdown))
  const calmarRatio = parseFloat((Math.abs(annualizedReturn / maxDrawdown) * 10).toFixed(2))
  const sortinoRatio = parseFloat((sharpeRatio * 1.2).toFixed(2))

  // Trade distribution
  const tradeDistribution = [
    { name: '盈利交易', value: winningTrades, color: '#10b981' },
    { name: '亏损交易', value: losingTrades, color: '#ef4444' },
  ]

  return {
    totalReturn: parseFloat(totalReturn.toFixed(2)),
    annualizedReturn: parseFloat(annualizedReturn.toFixed(2)),
    winRate: parseFloat(winRate.toFixed(2)),
    profitFactor,
    sharpeRatio,
    maxDrawdown: parseFloat(maxDrawdown.toFixed(2)),
    calmarRatio,
    sortinoRatio,
    totalTrades,
    winningTrades,
    losingTrades,
    avgWin,
    avgLoss,
    largestWin: parseFloat((avgWin * 3).toFixed(2)),
    largestLoss: parseFloat((avgLoss * 2).toFixed(2)),
    avgTradeDuration: `${Math.floor(Math.random() * 10 + 2)}天`,
    winRateByMonth: Array.from({ length: 12 }, () => Math.random() * 100),
    monthlyReturns,
    equityCurve,
    tradeDistribution,
  }
}

const PerformanceAnalysis: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [selectedPeriod, setSelectedPeriod] = useState<string>('1Y')

  // Fetch strategy data
  const { data: strategy, isLoading: strategyLoading, error: strategyError } = useGetStrategyQuery(id!)

  // Fetch performance data (using mock for now)
  const performanceData = useMemo(() => {
    if (!id) return null
    return generateMockPerformanceData(id, selectedPeriod)
  }, [id, selectedPeriod])

  // Export performance report
  const handleExportReport = () => {
    if (!performanceData || !strategy) return

    const report = {
      strategy: {
        name: strategy.name,
        id: strategy.id,
        category: strategy.category,
        createdAt: strategy.createdAt,
      },
      period: selectedPeriod,
      metrics: performanceData,
      generatedAt: new Date().toISOString(),
    }

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `performance-report-${strategy.name}-${selectedPeriod}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (strategyLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (strategyError || !strategy) {
    return (
      <div className="bg-error-50 border border-error-200 rounded-lg p-6">
        <div className="flex items-center">
          <ExclamationTriangleIcon className="h-5 w-5 text-error-600 mr-2" />
          <span className="text-error-800">加载策略失败</span>
        </div>
      </div>
    )
  }

  if (!performanceData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-neutral-500">暂无性能数据</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">{strategy.name}</h1>
            <p className="text-neutral-600 mt-1">性能分析报告</p>
          </div>
          <button
            onClick={handleExportReport}
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <DocumentArrowDownIcon className="h-5 w-5 mr-2" />
            导出报告
          </button>
        </div>

        {/* Period Selector */}
        <div className="mt-6 flex items-center space-x-2">
          <CalendarDaysIcon className="h-5 w-5 text-neutral-500" />
          <div className="flex space-x-1">
            {periodOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => setSelectedPeriod(option.value)}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  selectedPeriod === option.value
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-neutral-600 hover:bg-neutral-100'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Performance Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral-600">总回报</p>
              <p className={`text-2xl font-bold mt-1 ${
                performanceData.totalReturn >= 0 ? 'text-success-600' : 'text-error-600'
              }`}>
                {performanceData.totalReturn >= 0 ? '+' : ''}{performanceData.totalReturn.toFixed(2)}%
              </p>
            </div>
            <div className={`p-3 rounded-full ${
              performanceData.totalReturn >= 0 ? 'bg-success-100' : 'bg-error-100'
            }`}>
              {performanceData.totalReturn >= 0 ? (
                <ArrowTrendingUpIcon className="h-6 w-6 text-success-600" />
              ) : (
                <ArrowTrendingDownIcon className="h-6 w-6 text-error-600" />
              )}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral-600">年化回报</p>
              <p className="text-2xl font-bold mt-1 text-primary-600">
                {performanceData.annualizedReturn.toFixed(2)}%
              </p>
            </div>
            <div className="p-3 bg-primary-100 rounded-full">
              <PercentBadgeIcon className="h-6 w-6 text-primary-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral-600">胜率</p>
              <p className="text-2xl font-bold mt-1 text-primary-600">
                {performanceData.winRate.toFixed(1)}%
              </p>
            </div>
            <div className="p-3 bg-primary-100 rounded-full">
              <ChartBarIcon className="h-6 w-6 text-primary-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral-600">盈利因子</p>
              <p className="text-2xl font-bold mt-1 text-primary-600">
                {performanceData.profitFactor.toFixed(2)}
              </p>
            </div>
            <div className="p-3 bg-primary-100 rounded-full">
              <CurrencyDollarIcon className="h-6 w-6 text-primary-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Equity Curve & Drawdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">资金曲线</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={performanceData.equityCurve}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tickFormatter={(value) => format(new Date(value), 'MM/dd')}
                stroke="#6b7280"
                fontSize={12}
              />
              <YAxis
                tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                stroke="#6b7280"
                fontSize={12}
              />
              <Tooltip
                formatter={(value: number) => [`¥${value.toLocaleString()}`, '资金']}
                labelFormatter={(value) => format(new Date(value as string), 'yyyy-MM-dd')}
              />
              <Area
                type="monotone"
                dataKey="equity"
                stroke="#3b82f6"
                fill="#93c5fd"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">回撤分析</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={performanceData.equityCurve}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tickFormatter={(value) => format(new Date(value), 'MM/dd')}
                stroke="#6b7280"
                fontSize={12}
              />
              <YAxis
                tickFormatter={(value) => `${value.toFixed(0)}%`}
                stroke="#6b7280"
                fontSize={12}
              />
              <Tooltip
                formatter={(value: number) => [`${value.toFixed(2)}%`, '回撤']}
                labelFormatter={(value) => format(new Date(value as string), 'yyyy-MM-dd')}
              />
              <Area
                type="monotone"
                dataKey="drawdown"
                stroke="#ef4444"
                fill="#fca5a5"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Monthly Returns & Trade Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">月度回报</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={performanceData.monthlyReturns}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="month"
                stroke="#6b7280"
                fontSize={12}
              />
              <YAxis
                tickFormatter={(value) => `${value.toFixed(0)}%`}
                stroke="#6b7280"
                fontSize={12}
              />
              <Tooltip
                formatter={(value: number) => [`${value.toFixed(2)}%`, '回报率']}
              />
              <ReferenceLine y={0} stroke="#6b7280" />
              <Bar
                dataKey="return"
                fill={(entry: any) => entry >= 0 ? '#10b981' : '#ef4444'}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">交易分布</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={performanceData.tradeDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {performanceData.tradeDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => [value, '交易次数']} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Risk Metrics */}
      <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">风险指标</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg">
            <div>
              <p className="text-sm text-neutral-600">夏普比率</p>
              <p className="text-xl font-semibold text-neutral-900 mt-1">
                {performanceData.sharpeRatio.toFixed(2)}
              </p>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              performanceData.sharpeRatio > 1 ? 'bg-success-100 text-success-800' :
              performanceData.sharpeRatio > 0 ? 'bg-warning-100 text-warning-800' :
              'bg-error-100 text-error-800'
            }`}>
              {performanceData.sharpeRatio > 1 ? '优秀' : performanceData.sharpeRatio > 0 ? '一般' : '较差'}
            </div>
          </div>

          <div className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg">
            <div>
              <p className="text-sm text-neutral-600">最大回撤</p>
              <p className="text-xl font-semibold text-neutral-900 mt-1">
                -{performanceData.maxDrawdown.toFixed(2)}%
              </p>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              performanceData.maxDrawdown < 10 ? 'bg-success-100 text-success-800' :
              performanceData.maxDrawdown < 20 ? 'bg-warning-100 text-warning-800' :
              'bg-error-100 text-error-800'
            }`}>
              {performanceData.maxDrawdown < 10 ? '低风险' : performanceData.maxDrawdown < 20 ? '中风险' : '高风险'}
            </div>
          </div>

          <div className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg">
            <div>
              <p className="text-sm text-neutral-600">卡尔玛比率</p>
              <p className="text-xl font-semibold text-neutral-900 mt-1">
                {performanceData.calmarRatio.toFixed(2)}
              </p>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              performanceData.calmarRatio > 1 ? 'bg-success-100 text-success-800' :
              performanceData.calmarRatio > 0 ? 'bg-warning-100 text-warning-800' :
              'bg-error-100 text-error-800'
            }`}>
              {performanceData.calmarRatio > 1 ? '优秀' : performanceData.calmarRatio > 0 ? '一般' : '较差'}
            </div>
          </div>

          <div className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg">
            <div>
              <p className="text-sm text-neutral-600">索提诺比率</p>
              <p className="text-xl font-semibold text-neutral-900 mt-1">
                {performanceData.sortinoRatio.toFixed(2)}
              </p>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              performanceData.sortinoRatio > 1 ? 'bg-success-100 text-success-800' :
              performanceData.sortinoRatio > 0 ? 'bg-warning-100 text-warning-800' :
              'bg-error-100 text-error-800'
            }`}>
              {performanceData.sortinoRatio > 1 ? '优秀' : performanceData.sortinoRatio > 0 ? '一般' : '较差'}
            </div>
          </div>

          <div className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg">
            <div>
              <p className="text-sm text-neutral-600">总交易数</p>
              <p className="text-xl font-semibold text-neutral-900 mt-1">
                {performanceData.totalTrades}
              </p>
            </div>
            <div className="p-2 bg-primary-100 rounded-full">
              <FunnelIcon className="h-5 w-5 text-primary-600" />
            </div>
          </div>

          <div className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg">
            <div>
              <p className="text-sm text-neutral-600">平均持仓时间</p>
              <p className="text-xl font-semibold text-neutral-900 mt-1">
                {performanceData.avgTradeDuration}
              </p>
            </div>
            <div className="p-2 bg-primary-100 rounded-full">
              <ClockIcon className="h-5 w-5 text-primary-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Statistics Table */}
      <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">详细统计</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-neutral-200">
            <thead className="bg-neutral-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  指标
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  数值
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  指标
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  数值
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-neutral-200">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-900">盈利交易</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-900">
                  {performanceData.winningTrades}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-900">亏损交易</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-900">
                  {performanceData.losingTrades}
                </td>
              </tr>
              <tr className="bg-neutral-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-900">平均盈利</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-success-600">
                  ¥{performanceData.avgWin.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-900">平均亏损</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-error-600">
                  ¥{Math.abs(performanceData.avgLoss).toLocaleString()}
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-900">最大盈利</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-success-600">
                  ¥{performanceData.largestWin.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-900">最大亏损</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-error-600">
                  ¥{Math.abs(performanceData.largestLoss).toLocaleString()}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Analysis Summary */}
      <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">分析总结</h3>
        <div className="space-y-4">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <div className="flex items-center justify-center h-10 w-10 rounded-full bg-primary-100">
                <ShieldCheckIcon className="h-6 w-6 text-primary-600" />
              </div>
            </div>
            <div className="ml-4">
              <h4 className="text-sm font-medium text-neutral-900">风险评估</h4>
              <p className="mt-1 text-sm text-neutral-600">
                当前策略的风险水平为
                <span className={`font-semibold mx-1 ${
                  performanceData.maxDrawdown < 10 ? 'text-success-600' :
                  performanceData.maxDrawdown < 20 ? 'text-warning-600' :
                  'text-error-600'
                }`}>
                  {performanceData.maxDrawdown < 10 ? '低' : performanceData.maxDrawdown < 20 ? '中' : '高'}
                </span>
                风险，最大回撤为 {performanceData.maxDrawdown.toFixed(2)}%。
              </p>
            </div>
          </div>

          <div className="flex items-start">
            <div className="flex-shrink-0">
              <div className="flex items-center justify-center h-10 w-10 rounded-full bg-primary-100">
                <CheckCircleIcon className="h-6 w-6 text-primary-600" />
              </div>
            </div>
            <div className="ml-4">
              <h4 className="text-sm font-medium text-neutral-900">策略表现</h4>
              <p className="mt-1 text-sm text-neutral-600">
                策略在 {selectedPeriod} 期间的总回报为
                <span className={`font-semibold mx-1 ${
                  performanceData.totalReturn >= 0 ? 'text-success-600' : 'text-error-600'
                }`}>
                  {performanceData.totalReturn >= 0 ? '+' : ''}{performanceData.totalReturn.toFixed(2)}%
                </span>
                ，年化回报率为 {performanceData.annualizedReturn.toFixed(2)}%。
              </p>
            </div>
          </div>

          <div className="flex items-start">
            <div className="flex-shrink-0">
              <div className="flex items-center justify-center h-10 w-10 rounded-full bg-primary-100">
                <ExclamationTriangleIcon className="h-6 w-6 text-primary-600" />
              </div>
            </div>
            <div className="ml-4">
              <h4 className="text-sm font-medium text-neutral-900">建议</h4>
              <p className="mt-1 text-sm text-neutral-600">
                {performanceData.sharpeRatio < 1 && '建议优化策略以提高风险调整后收益。'}
                {performanceData.maxDrawdown > 20 && '建议加强风险管理以降低最大回撤。'}
                {performanceData.winRate < 40 && '建议调整入场条件以提高胜率。'}
                {performanceData.sharpeRatio >= 1 && performanceData.maxDrawdown <= 20 && performanceData.winRate >= 40 &&
                  '策略表现良好，建议继续观察并考虑适当扩大规模。'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PerformanceAnalysis