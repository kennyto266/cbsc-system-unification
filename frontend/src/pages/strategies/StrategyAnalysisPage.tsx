import React, { useState } from 'react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Link } from 'react-router-dom'
import {
  ArrowLeftIcon,
  ChartBarIcon,
  SparklesIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  BeakerIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'

const StrategyAnalysisPage: React.FC = () => {
  const [selectedStrategy, setSelectedStrategy] = useState('1')

  // Mock performance data
  const PERFORMANCE_DATA = {
    totalReturn: 15.4,
    annualReturn: 12.8,
    sharpeRatio: 1.85,
    maxDrawdown: -8.2,
    volatility: 12.3,
    winRate: 68.5,
    profitFactor: 2.1,
    calmarRatio: 1.56,
    var95: -2.34,
    cvar95: -3.45,
  }

  const METRICS = [
    {
      label: '總收益率',
      value: PERFORMANCE_DATA.totalReturn,
      unit: '%',
      icon: <ArrowUpIcon className="h-5 w-5" />,
      color: 'green',
      format: (v: number) => v.toFixed(1),
    },
    {
      label: '年化收益',
      value: PERFORMANCE_DATA.annualReturn,
      unit: '%',
      icon: <ArrowUpIcon className="h-5 w-5" />,
      color: 'green',
      format: (v: number) => v.toFixed(1),
    },
    {
      label: '夏普比率',
      value: PERFORMANCE_DATA.sharpeRatio,
      unit: '',
      icon: <ChartBarIcon className="h-5 w-5" />,
      color: 'blue',
      format: (v: number) => v.toFixed(2),
    },
    {
      label: '最大回撤',
      value: PERFORMANCE_DATA.maxDrawdown,
      unit: '%',
      icon: <ArrowDownIcon className="h-5 w-5" />,
      color: 'red',
      format: (v: number) => v.toFixed(1),
    },
    {
      label: '波動率',
      value: PERFORMANCE_DATA.volatility,
      unit: '%',
      icon: <BeakerIcon className="h-5 w-5" />,
      color: 'purple',
      format: (v: number) => v.toFixed(1),
    },
    {
      label: '勝率',
      value: PERFORMANCE_DATA.winRate,
      unit: '%',
      icon: <SparklesIcon className="h-5 w-5" />,
      color: 'green',
      format: (v: number) => v.toFixed(1),
    },
    {
      label: '盈利因子',
      value: PERFORMANCE_DATA.profitFactor,
      unit: '',
      icon: <BeakerIcon className="h-5 w-5" />,
      color: 'blue',
      format: (v: number) => v.toFixed(2),
    },
    {
      label: '卡馬比率',
      value: PERFORMANCE_DATA.calmarRatio,
      unit: '',
      icon: <ChartBarIcon className="h-5 w-5" />,
      color: 'purple',
      format: (v: number) => v.toFixed(2),
    },
    {
      label: 'VaR (95%)',
      value: PERFORMANCE_DATA.var95,
      unit: '%',
      icon: <ArrowDownIcon className="h-5 w-5" />,
      color: 'red',
      format: (v: number) => v.toFixed(2),
    },
    {
      label: 'CVaR (95%)',
      value: PERFORMANCE_DATA.cvar95,
      unit: '%',
      icon: <ArrowDownIcon className="h-5 w-5" />,
      color: 'red',
      format: (v: number) => v.toFixed(2),
    },
  ]

  const getMetricBadge = (value: number, color: string) => {
    const colorClasses = {
      green: `text-green-600 ${value >= 0 ? 'bg-green-50' : 'bg-red-50'}`,
      red: 'text-red-600 bg-red-50',
      blue: 'text-blue-600 bg-blue-50',
      purple: 'text-purple-600 bg-purple-50',
    }
    const actualColor = color === 'green' && value < 0 ? 'red' : color
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded ${colorClasses[actualColor as keyof typeof colorClasses]}`}>
        {value >= 0 ? '+' : ''}{value}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/strategies/list">
          <Button variant="outline" size="sm">
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            返回列表
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            策略分析
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            深入分析策略表現和風險指標
          </p>
        </div>
      </div>

      {/* Strategy Selector */}
      <Card className="p-4">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          選擇策略
        </label>
        <select
          value={selectedStrategy}
          onChange={(e) => setSelectedStrategy(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
        >
          <option value="1">CBSC RSI策略</option>
          <option value="2">情緒動量策略</option>
          <option value="3">月度再平衡策略</option>
        </select>
      </Card>

      {/* Performance Metrics */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          績效指標
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {METRICS.map((metric) => (
            <Card key={metric.label} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                  {metric.icon}
                </div>
                {getMetricBadge(metric.value, metric.color)}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                {metric.label}
              </div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {metric.format(metric.value)}{metric.unit}
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Performance Chart */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          收益曲線
        </h2>
        <Card className="p-6">
          <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="text-center">
              <ChartBarIcon className="h-16 w-16 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-500 dark:text-gray-400">
                圖表展示區域
              </p>
              <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
                當前為模擬數據展示，實際部署時將顯示真實圖表
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Risk Analysis */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          風險分析
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              回撤分析
            </h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600 dark:text-gray-400">最大回撤</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {PERFORMANCE_DATA.maxDrawdown.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-red-500 h-2 rounded-full"
                    style={{ width: `${Math.abs(PERFORMANCE_DATA.maxDrawdown)}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600 dark:text-gray-400">平均回撤</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    -3.2%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div className="bg-orange-500 h-2 rounded-full" style={{ width: '32%' }} />
                </div>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              風險指標
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">VaR (95%)</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {PERFORMANCE_DATA.var95.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">CVaR (95%)</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {PERFORMANCE_DATA.cvar95.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">波動率</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {PERFORMANCE_DATA.volatility.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Beta</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  0.85
                </span>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Trade Analysis */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          交易分析
        </h2>
        <Card className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">總交易次數</div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">156</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">盈利交易</div>
              <div className="text-2xl font-bold text-green-600">107</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">虧損交易</div>
              <div className="text-2xl font-bold text-red-600">49</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">勝率</div>
              <div className="text-2xl font-bold text-blue-600">
                {PERFORMANCE_DATA.winRate.toFixed(1)}%
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Button className="flex-1">
          <DocumentTextIcon className="h-5 w-5 mr-2" />
          導出報告
        </Button>
        <Button variant="outline" className="flex-1">
          <BeakerIcon className="h-5 w-5 mr-2" />
          運行回測
        </Button>
      </div>

      {/* API Note */}
      <Card className="p-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-3">
          <DocumentTextIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>分析數據來源：</strong> 這些指標來自 GET /api/strategies/{'{'}id{'}'}/backtest/results API。
              當前顯示模擬數據。實際部署時將根據真實回測結果計算所有指標。
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default StrategyAnalysisPage
