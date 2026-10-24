import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, DollarSign, Target, Activity, BarChart3, RefreshCw, Wifi, WifiOff } from 'lucide-react'

// Square-UI Components
import { MetricCard, Tabs, Grid, MetricsGrid, ChartGrid } from '@/components/square-ui'
import { Button } from '@/components/ui/button'

// Hooks
import { useGetAnalyticsDataQuery } from '../../store/api/analyticsApi'
import { useGetActiveStrategiesQuery } from '../../store/api/monitoringApi'
import { useWebSocket } from '../../hooks/useWebSocket'

// Components
import MarketOverview from '../../components/dashboard/MarketOverview'
import RecentSignals from '../../components/dashboard/RecentSignals'
import SystemHealth from '../../components/dashboard/SystemHealth'
import QuickActions from '../../components/dashboard/QuickActions'
import CBSCTabPage from './CBSCTabPage'

// Charts
import {
  StrategyPerformanceChart,
  AssetAllocationChart,
  StrategyComparisonChart,
  RiskReturnScatterChart,
  RealTimePriceChart
} from '../../components/Charts'

import { Strategy, StrategyType } from '../../types'

const DashboardPageModern: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'1d' | '1w' | '1m' | '3m'>('1m')
  const [chartTimeRange, setChartTimeRange] = useState<'1D' | '1W' | '1M' | '3M' | '6M' | '1Y'>('1M')
  const [comparisonMetric, setComparisonMetric] = useState<'totalReturn' | 'sharpeRatio' | 'maxDrawdown' | 'winRate' | 'profitFactor'>('totalReturn')
  const [filterType, setFilterType] = useState<StrategyType | 'all'>('all')
  const { isConnected } = useWebSocket()

  // Fetch dashboard data
  const { data: analyticsData, isLoading: analyticsLoading, error: analyticsError } = useGetAnalyticsDataQuery({
    timeRange,
    includeBenchmark: true,
  })

  const { data: activeStrategies, isLoading: strategiesLoading } = useGetActiveStrategiesQuery()

  // Mock strategies data
  const mockStrategies: Strategy[] = [
    {
      id: '1',
      name: 'RSI均值回歸策略',
      type: StrategyType.MEAN_REVERSION,
      status: 'active' as any,
      riskLevel: 'medium' as any,
      description: '基於相對強弱指數的均值回歸交易策略',
      parameters: { rsiPeriod: 14, oversoldLevel: 30, overboughtLevel: 70 },
      performance: {
        totalReturn: 0.185,
        sharpeRatio: 1.45,
        maxDrawdown: -0.08,
        winRate: 0.65,
        profitFactor: 1.8
      },
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    },
    {
      id: '2',
      name: 'MACD動量策略',
      type: StrategyType.MOMENTUM,
      status: 'active' as any,
      riskLevel: 'high' as any,
      description: '基於MACD指標的動量追蹤策略',
      parameters: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
      performance: {
        totalReturn: 0.242,
        sharpeRatio: 1.78,
        maxDrawdown: -0.15,
        winRate: 0.58,
        profitFactor: 2.1
      },
      createdAt: '2024-02-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    },
    {
      id: '3',
      name: '情感分析策略',
      type: StrategyType.SENTIMENT,
      status: 'active' as any,
      riskLevel: 'low' as any,
      description: '基於市場情感分析的交易策略',
      parameters: { sentimentSource: 'twitter', threshold: 0.6 },
      performance: {
        totalReturn: 0.123,
        sharpeRatio: 1.12,
        maxDrawdown: -0.05,
        winRate: 0.72,
        profitFactor: 1.5
      },
      createdAt: '2024-03-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    },
    {
      id: '4',
      name: '布林帶突破策略',
      type: StrategyType.TECHNICAL,
      status: 'active' as any,
      riskLevel: 'medium' as any,
      description: '基於布林帶的突破交易策略',
      parameters: { period: 20, stdDev: 2 },
      performance: {
        totalReturn: 0.156,
        sharpeRatio: 1.34,
        maxDrawdown: -0.10,
        winRate: 0.61,
        profitFactor: 1.7
      },
      createdAt: '2024-04-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    },
    {
      id: '5',
      name: '統計套利策略',
      type: StrategyType.ARBITRAGE,
      status: 'active' as any,
      riskLevel: 'low' as any,
      description: '基於統計分析的套利策略',
      parameters: { lookbackPeriod: 30, zScoreThreshold: 2 },
      performance: {
        totalReturn: 0.089,
        sharpeRatio: 2.15,
        maxDrawdown: -0.03,
        winRate: 0.78,
        profitFactor: 1.9
      },
      createdAt: '2024-05-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    }
  ]

  // Tab items configuration
  const tabItems = [
    {
      key: 'strategies',
      label: '策略管理',
      icon: <BarChart3 className="w-4 h-4" />,
      content: (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="space-y-6"
        >
          {/* Header */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gradient bg-gradient-to-r from-primary-600 to-cbsc-cyan bg-clip-text text-transparent">
                CBSC策略管理Dashboard
              </h1>
              <p className="text-gray-600 mt-2">
                實時監控您的量化交易策略表現和市場動態
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                icon={<RefreshCw className="w-4 h-4" />}
                onClick={() => window.location.reload()}
              >
                刷新數據
              </Button>
              <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
                isConnected
                  ? 'bg-success-50 text-success-700'
                  : 'bg-error-50 text-error-700'
              }`}>
                {isConnected ? (
                  <>
                    <Wifi className="w-4 h-4" />
                    WebSocket已連接
                  </>
                ) : (
                  <>
                    <WifiOff className="w-4 h-4" />
                    WebSocket未連接
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <MetricsGrid>
            <MetricCard
              title="總資產價值"
              value={analyticsData?.portfolio?.totalValue || 106200}
              format="currency"
              currency="CNY"
              trend={5.8}
              icon={<DollarSign className="w-5 h-5" />}
              loading={analyticsLoading}
              description="相比上月增長"
            />
            <MetricCard
              title="總收益率"
              value={analyticsData?.portfolio?.totalReturn || 0.062}
              format="percentage"
              trend={2.1}
              icon={<TrendingUp className="w-5 h-5" />}
              loading={analyticsLoading}
              description="年化收益率"
            />
            <MetricCard
              title="夏普比率"
              value={analyticsData?.portfolio?.sharpeRatio || 1.85}
              precision={2}
              trend={0.15}
              icon={<Target className="w-5 h-5" />}
              loading={analyticsLoading}
              description="風險調整後收益"
            />
            <MetricCard
              title="活躍策略"
              value={activeStrategies?.length || 8}
              trend={1}
              icon={<Activity className="w-5 h-5" />}
              loading={strategiesLoading}
              description="正在運行的策略數"
            />
          </MetricsGrid>

          {/* Charts Section */}
          <ChartGrid>
            <StrategyPerformanceChart
              strategies={mockStrategies}
              timeRange={chartTimeRange}
              onTimeRangeChange={setChartTimeRange}
            />
            <AssetAllocationChart
              strategies={mockStrategies}
              totalValue={100000}
              showDetails={true}
            />
          </ChartGrid>

          {/* Second Row - Strategy Comparison and Risk Analysis */}
          <ChartGrid>
            <StrategyComparisonChart
              strategies={mockStrategies}
              metric={comparisonMetric}
              onMetricChange={setComparisonMetric}
              sortBy="value"
              showTopN={10}
            />
            <RiskReturnScatterChart
              strategies={mockStrategies}
              showQuadrants={true}
              showEfficientFrontier={true}
              filterType={filterType}
              onFilterChange={setFilterType}
            />
          </ChartGrid>

          {/* Real-time Price Chart */}
          <div className="mb-6">
            <RealTimePriceChart
              strategy={mockStrategies[0]}
              symbol="BTC/USDT"
              timeFrame="1h"
              showVolume={true}
              showIndicators={true}
              autoUpdate={true}
            />
          </div>

          {/* Bottom Section */}
          <Grid cols={{ lg: 3, md: 2, sm: 1 }} gap={6}>
            <div className="lg:col-span-1">
              <SystemHealth />
            </div>
            <div className="lg:col-span-1">
              <RecentSignals />
            </div>
            <div className="lg:col-span-1">
              <QuickActions />
            </div>
          </Grid>
        </motion.div>
      ),
    },
    {
      key: 'cbsc',
      label: 'CBSC牛熊證',
      icon: <BarChart3 className="w-4 h-4" />,
      badge: "New",
      content: <CBSCTabPage />,
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
      <div className="container mx-auto px-4 py-8">
        <Tabs
          items={tabItems}
          defaultActiveKey="strategies"
          type="pills"
          size="large"
          animated={true}
          className="w-full"
        />
      </div>
    </div>
  )
}

export default DashboardPageModern