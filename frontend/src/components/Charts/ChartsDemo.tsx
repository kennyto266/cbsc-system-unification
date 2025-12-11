import React from 'react';
import { ChartsDashboard } from './ChartsDashboard';
import { Strategy } from '../../types/index';

// Mock strategy data for demonstration
const mockStrategies: Strategy[] = [
  {
    id: 'direct_rsi',
    name: '直接RSI情绪策略',
    type: 'direct_rsi',
    category: 'core_cbsc',
    status: 'active',
    performance: {
      totalReturn: 0.254,
      sharpeRatio: 1.45,
      maxDrawdown: 8.3,
      volatility: 12.5,
      winRate: 0.62,
      profitFactor: 1.8,
      calmarRatio: 0.95,
      var95: -0.03,
      cvar95: -0.045,
      lastUpdated: new Date('2025-12-11T10:30:00Z'),
      dataQualityScore: 98
    },
    parameters: {
      rsi_period: 14,
      rsi_overbought: 70,
      rsi_oversold: 30
    },
    latestSignal: null,
    description: '基于牛熊比例的RSI计算，识别极端情绪信号'
  },
  {
    id: 'sentiment_momentum',
    name: '情绪动量策略',
    type: 'sentiment_momentum',
    category: 'core_cbsc',
    status: 'active',
    performance: {
      totalReturn: 0.186,
      sharpeRatio: 1.12,
      maxDrawdown: 11.7,
      volatility: 14.8,
      winRate: 0.58,
      profitFactor: 1.6,
      calmarRatio: 0.72,
      var95: -0.042,
      cvar95: -0.058,
      lastUpdated: new Date('2025-12-11T10:25:00Z'),
      dataQualityScore: 96
    },
    parameters: {
      momentum_period: 20,
      sentiment_threshold: 0.5
    },
    latestSignal: null,
    description: 'MACD风格的情绪变化率分析，捕捉情绪转折点'
  },
  {
    id: 'composite_index',
    name: '复合指标策略',
    type: 'composite_index',
    category: 'multi_factor',
    status: 'active',
    performance: {
      totalReturn: 0.321,
      sharpeRatio: 1.87,
      maxDrawdown: 6.2,
      volatility: 11.2,
      winRate: 0.67,
      profitFactor: 2.1,
      calmarRatio: 1.35,
      var95: -0.025,
      cvar95: -0.035,
      lastUpdated: new Date('2025-12-11T10:35:00Z'),
      dataQualityScore: 99
    },
    parameters: {
      index_weights: [0.4, 0.3, 0.3],
      rebalance_period: 30
    },
    latestSignal: null,
    description: '多维度情绪综合，布林带风格的情绪区间分析'
  },
  {
    id: 'volatility_adjusted',
    name: '波动率调整策略',
    type: 'volatility_adjusted',
    category: 'multi_factor',
    status: 'inactive',
    performance: {
      totalReturn: 0.143,
      sharpeRatio: 0.78,
      maxDrawdown: 15.6,
      volatility: 18.3,
      winRate: 0.52,
      profitFactor: 1.4,
      calmarRatio: 0.45,
      var95: -0.058,
      cvar95: -0.072,
      lastUpdated: new Date('2025-12-11T10:15:00Z'),
      dataQualityScore: 94
    },
    parameters: {
      volatility_target: 0.15,
      leverage_cap: 1.5
    },
    latestSignal: null,
    description: '成交量加权的情绪分析，考虑市场信心度'
  }
];

// Demo component for testing charts
export const ChartsDemo: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            圖表組件演示
          </h1>
          <p className="text-gray-600">
            展示Chart.js集成的各種策略可視化圖表
          </p>
        </div>

        <ChartsDashboard
          strategies={mockStrategies}
          height={400}
          showControls={true}
          defaultLayout="grid"
        />

        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              功能特性
            </h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Sharpe比率條形圖 - 策略績效排名</li>
              <li>• 最大回撤折線圖 - 風險趨勢分析</li>
              <li>• 策略雷達圖 - 多維度性能對比</li>
              <li>• 實時數據更新 - WebSocket集成</li>
              <li>• 響應式設計 - 適配各種屏幕</li>
              <li>• 交互式控制 - 自定義顯示選項</li>
            </ul>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              技術規格
            </h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Chart.js 4.x - 現代化圖表庫</li>
              <li>• React-Chartjs-2 - React組件封裝</li>
              <li>• TypeScript - 類型安全</li>
              <li>• Ant Design - UI組件庫</li>
              <li>• Tailwind CSS - 樣式框架</li>
              <li>• 自定義主題 - 一致的視覺風格</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChartsDemo;