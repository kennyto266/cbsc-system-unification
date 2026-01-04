import React, { useState } from 'react';
import EconomicBacktestReports from '../components/BacktestReports/EconomicBacktestReports';
import ExportQueueManager from '../components/ExportTools/ExportQueueManager';

// Mock data for demonstration
const mockReport = {
  id: 'demo-report-1',
  strategyName: 'Interest Rate Strategy',
  strategy: {
    name: 'Interest Rate Differential',
    category: 'economic',
    parameters: {
      interestRateThreshold: 0.02,
      lookbackPeriod: 30,
      minTradeSize: 10000
    }
  },
  period: {
    start: '2023-01-01',
    end: '2024-01-01',
    duration: 365
  },
  metrics: {
    totalReturn: 0.156,
    annualizedReturn: 0.156,
    maxDrawdown: -0.082,
    sharpeRatio: 1.45,
    sortinoRatio: 2.03,
    calmarRatio: 1.90,
    volatility: 0.145,
    winRate: 0.62,
    profitFactor: 1.85,
    averageWin: 1250.50,
    averageLoss: -675.30,
    totalTrades: 48,
    winningTrades: 30,
    losingTrades: 18
  },
  economicData: {
    indicators: [
      {
        name: 'Fed Funds Rate',
        values: [4.5, 4.75, 5.0, 5.25, 5.5, 5.25, 5.0, 4.75, 4.5, 4.25]
      },
      {
        name: 'CPI YoY',
        values: [3.2, 3.5, 3.8, 4.0, 3.9, 3.7, 3.5, 3.3, 3.1, 2.9]
      },
      {
        name: 'Unemployment Rate',
        values: [3.6, 3.7, 3.8, 3.9, 4.0, 4.1, 4.0, 3.9, 3.8, 3.7]
      },
      {
        name: 'GDP Growth QoQ',
        values: [0.6, 0.8, 0.5, 0.7, 0.4, 0.6, 0.5, 0.7, 0.6, 0.8]
      },
      {
        name: 'PMI',
        values: [52.3, 51.8, 50.5, 49.8, 50.2, 51.5, 52.1, 51.9, 52.5, 51.7]
      },
      {
        name: 'Consumer Confidence',
        values: [108.5, 107.2, 105.8, 103.9, 104.5, 106.2, 107.8, 108.3, 109.1, 107.9]
      }
    ],
    correlation: {
      'Fed Funds Rate': 0.65,
      'CPI YoY': -0.32,
      'Unemployment Rate': -0.48,
      'GDP Growth QoQ': 0.42,
      'PMI': 0.58,
      'Consumer Confidence': 0.35
    }
  },
  strategyComparison: [
    {
      name: 'Interest Rate Strategy',
      totalReturn: 0.156,
      sharpeRatio: 1.45,
      maxDrawdown: -0.082,
      correlation: 1.0,
      volatility: 0.145,
      winRate: 0.62
    },
    {
      name: 'Momentum Strategy',
      totalReturn: 0.098,
      sharpeRatio: 0.87,
      maxDrawdown: -0.156,
      correlation: 0.34,
      volatility: 0.198,
      winRate: 0.48
    },
    {
      name: 'Value Strategy',
      totalReturn: 0.112,
      sharpeRatio: 0.95,
      maxDrawdown: -0.124,
      correlation: 0.42,
      volatility: 0.168,
      winRate: 0.53
    },
    {
      name: 'Mean Reversion',
      totalReturn: 0.087,
      sharpeRatio: 0.92,
      maxDrawdown: -0.098,
      correlation: 0.28,
      volatility: 0.132,
      winRate: 0.55
    },
    {
      name: 'Technical Analysis',
      totalReturn: 0.076,
      sharpeRatio: 0.68,
      maxDrawdown: -0.187,
      correlation: 0.45,
      volatility: 0.225,
      winRate: 0.42
    }
  ],
  contributionBreakdown: [
    { factor: 'Interest Rate Exposure', contribution: 0.085, weight: 0.45 },
    { factor: 'Inflation Hedge', contribution: 0.032, weight: 0.20 },
    { factor: 'Currency Impact', contribution: 0.023, weight: 0.15 },
    { factor: 'Market Timing', contribution: 0.016, weight: 0.20 }
  ],
  equityCurve: Array.from({ length: 12 }, (_, i) => ({
    date: `2023-${String(i + 1).padStart(2, '0')}-01`,
    portfolioValue: 100000 * (1 + 0.156 * (i + 1) / 12),
    benchmarkValue: 100000 * (1 + 0.089 * (i + 1) / 12)
  })),
  trades: Array.from({ length: 20 }, (_, i) => ({
    date: `2023-${String(Math.floor(i / 2) + 1).padStart(2, '0')}-${String((i % 2) * 15 + 1).padStart(2, '0')}`,
    type: i % 2 === 0 ? 'buy' : 'sell',
    price: 100 + i * 5 + (Math.random() - 0.5) * 10,
    quantity: 100 + Math.floor(Math.random() * 200),
    profit: i % 2 === 1 ? 250 * (i / 2) * (0.5 + Math.random() * 0.5) : undefined,
    profitPercent: i % 2 === 1 ? 0.025 * (i / 2) * (0.5 + Math.random() * 0.5) : undefined
  })),
  generatedAt: '2024-01-02T10:00:00Z'
};

const EconomicBacktestReportDemo: React.FC = () => {
  const [showQueueManager, setShowQueueManager] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-semibold text-gray-900">
              Economic Strategy Backtest Demo
            </h1>
            <button
              onClick={() => setShowQueueManager(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
            >
              <span>Export Queue</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-8">
          <h2 className="text-lg font-semibold text-blue-900 mb-2">
            Economic Strategy Backtest Report Component
          </h2>
          <p className="text-blue-700">
            This demo showcases the EconomicBacktestReports component with performance metrics,
            correlation analysis, contribution breakdown, and strategy comparison features.
            Click the "Export Report" button to test the export functionality.
          </p>
        </div>

        {/* Report Component */}
        <EconomicBacktestReports report={mockReport} />
      </div>

      {/* Export Queue Manager Modal */}
      <ExportQueueManager
        isOpen={showQueueManager}
        onClose={() => setShowQueueManager(false)}
      />
    </div>
  );
};

export default EconomicBacktestReportDemo;