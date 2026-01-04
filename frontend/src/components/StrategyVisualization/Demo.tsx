import React, { useState } from 'react'
import {
  MixedStrategyViewer,
  WeightAnalysis,
  ParameterPreview,
  SensitivityAnalysis,
  MixedStrategyData,
  StrategyWeights,
  ParameterConfig
} from './index'

// Demo data for mixed strategies
const demoData: MixedStrategyData[] = [
  {
    date: '2024-01',
    timestamp: 1704067200000,
    price: 100,
    open: 99,
    high: 102,
    low: 98,
    close: 100,
    volume: 1000000,
    signal: 1,
    signal_strength: 0.8,
    gdp: 2.5,
    inflation: 3.2,
    unemployment: 4.1,
    interest_rate: 5.25,
    ma_short: 98,
    ma_long: 95,
    rsi: 65,
    price_weight: 0.4,
    economic_weight: 0.3,
    volume_weight: 0.2,
    technical_weight: 0.1
  },
  {
    date: '2024-02',
    timestamp: 1706745600000,
    price: 102,
    open: 100,
    high: 105,
    low: 100,
    close: 102,
    volume: 1200000,
    signal: 1,
    signal_strength: 0.6,
    gdp: 2.6,
    inflation: 3.1,
    unemployment: 4.0,
    interest_rate: 5.25,
    ma_short: 100,
    ma_long: 96,
    rsi: 70,
    price_weight: 0.4,
    economic_weight: 0.3,
    volume_weight: 0.2,
    technical_weight: 0.1
  },
  {
    date: '2024-03',
    timestamp: 1709337600000,
    price: 98,
    open: 102,
    high: 103,
    low: 97,
    close: 98,
    volume: 1500000,
    signal: -1,
    signal_strength: 0.7,
    gdp: 2.7,
    inflation: 3.0,
    unemployment: 3.9,
    interest_rate: 5.00,
    ma_short: 101,
    ma_long: 97,
    rsi: 45,
    price_weight: 0.4,
    economic_weight: 0.3,
    volume_weight: 0.2,
    technical_weight: 0.1
  }
]

// Demo weights
const demoWeights: StrategyWeights = {
  price: 0.4,
  economic: 0.3,
  volume: 0.2,
  technical: 0.1
}

// Demo parameter configuration
const demoParameterConfig: { [key: string]: ParameterConfig } = {
  shortWindow: {
    type: 'number',
    label: '短期窗口',
    min: 5,
    max: 20,
    step: 1,
    description: '短期移动平均窗口期',
    impact: 'high'
  },
  longWindow: {
    type: 'number',
    label: '长期窗口',
    min: 20,
    max: 60,
    step: 1,
    description: '长期移动平均窗口期',
    impact: 'high'
  },
  rsiPeriod: {
    type: 'number',
    label: 'RSI周期',
    min: 7,
    max: 21,
    step: 1,
    description: 'RSI指标计算周期',
    impact: 'medium'
  },
  rsiThreshold: {
    type: 'number',
    label: 'RSI阈值',
    min: 30,
    max: 90,
    step: 5,
    description: 'RSI超买超卖判断阈值',
    impact: 'medium'
  },
  stopLoss: {
    type: 'range',
    label: '止损比例',
    min: 0.01,
    max: 0.1,
    step: 0.01,
    description: '自动止损触发比例',
    impact: 'high'
  }
}

// Demo sensitivity data
const demoSensitivityData = {
  shortWindow: [
    { value: 5, return: 0.08, sharpe: 1.2, drawdown: -0.15 },
    { value: 10, return: 0.12, sharpe: 1.5, drawdown: -0.10 },
    { value: 15, return: 0.15, sharpe: 1.8, drawdown: -0.08 },
    { value: 20, return: 0.13, sharpe: 1.6, drawdown: -0.09 }
  ],
  rsiThreshold: [
    { value: 50, return: 0.10, sharpe: 1.3, drawdown: -0.12 },
    { value: 60, return: 0.13, sharpe: 1.5, drawdown: -0.10 },
    { value: 70, return: 0.15, sharpe: 1.8, drawdown: -0.08 },
    { value: 80, return: 0.11, sharpe: 1.4, drawdown: -0.11 }
  ]
}

export const StrategyVisualizationDemo: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'viewer' | 'weights' | 'parameters' | 'sensitivity'>('viewer')
  const [parameters, setParameters] = useState({
    shortWindow: 10,
    longWindow: 30,
    rsiPeriod: 14,
    rsiThreshold: 70,
    stopLoss: 0.05,
    takeProfit: 0.1
  })

  const tabs = [
    { id: 'viewer', label: '混合策略视图' },
    { id: 'weights', label: '权重分析' },
    { id: 'parameters', label: '参数预览' },
    { id: 'sensitivity', label: '敏感性分析' }
  ]

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        策略可视化组件演示
      </h1>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        {activeTab === 'viewer' && (
          <MixedStrategyViewer
            data={demoData}
            title="价格与经济指标混合策略"
            onTimeframeChange={(timeframe) => console.log('Timeframe changed:', timeframe)}
            onExport={(data) => console.log('Exporting data:', data)}
          />
        )}

        {activeTab === 'weights' && (
          <WeightAnalysis
            weights={demoWeights}
            contributions={[
              { name: '价格策略', weight: 0.4, contribution: 0.35, performance: 0.12, sharpe: 1.8, maxDrawdown: -0.08 },
              { name: '经济指标', weight: 0.3, contribution: 0.25, performance: 0.08, sharpe: 1.5, maxDrawdown: -0.10 },
              { name: '成交量', weight: 0.2, contribution: 0.25, performance: 0.05, sharpe: 1.2, maxDrawdown: -0.12 },
              { name: '技术指标', weight: 0.1, contribution: 0.15, performance: 0.02, sharpe: 0.8, maxDrawdown: -0.05 }
            ]}
            adjustable={true}
            showContributions={true}
            showMetrics={true}
            showRadar={true}
            onWeightChange={(weights) => console.log('Weights changed:', weights)}
            onExport={(weights) => console.log('Exporting weights:', weights)}
          />
        )}

        {activeTab === 'parameters' && (
          <ParameterPreview
            parameters={parameters}
            parameterConfig={demoParameterConfig}
            previewResults={{
              totalReturn: 0.15,
              sharpeRatio: 1.8,
              maxDrawdown: -0.08,
              winRate: 0.65,
              profitFactor: 1.5
            }}
            adjustable={true}
            onParameterChange={(param, value) => {
              setParameters(prev => ({ ...prev, [param]: value }))
              console.log('Parameter changed:', param, value)
            }}
            onApply={(params) => console.log('Apply parameters:', params)}
            showImpact={true}
            parameterImpact={{
              shortWindow: { impact: 0.03, sensitivity: 'high', description: '影响交易信号频率' },
              rsiThreshold: { impact: 0.02, sensitivity: 'medium', description: '影响超买超卖判断' }
            }}
          />
        )}

        {activeTab === 'sensitivity' && (
          <SensitivityAnalysis
            parameters={parameters}
            sensitivityData={demoSensitivityData}
            optimalParameters={{
              shortWindow: 15,
              rsiThreshold: 70
            }}
            recommendations={[
              {
                parameter: 'shortWindow',
                reason: '当前值偏低，可能错过趋势机会',
                suggestion: '增加到15',
                impact: 'high',
                expectedImprovement: 0.03
              },
              {
                parameter: 'rsiThreshold',
                reason: '当前值合适，保持稳定',
                suggestion: '保持70',
                impact: 'low'
              }
            ]}
            onParameterChange={(param, config) => console.log('Sensitivity param change:', param, config)}
            onOptimize={(params) => console.log('Optimize parameters:', params)}
            onExport={(data) => console.log('Export sensitivity:', data)}
            showRecommendations={true}
          />
        )}
      </div>

      {/* Component Info */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
        <h2 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
          组件说明
        </h2>
        <ul className="space-y-1 text-sm text-blue-800 dark:text-blue-200">
          <li>• <strong>MixedStrategyViewer:</strong> 支持价格、成交量、经济指标和技术指标的混合展示</li>
          <li>• <strong>WeightAnalysis:</strong> 权重分布分析、贡献度可视化和性能指标展示</li>
          <li>• <strong>ParameterPreview:</strong> 实时参数调整、性能预览和影响分析</li>
          <li>• <strong>SensitivityAnalysis:</strong> 参数敏感性分析、最优化建议和双参数热力图</li>
        </ul>
      </div>
    </div>
  )
}

export default StrategyVisualizationDemo