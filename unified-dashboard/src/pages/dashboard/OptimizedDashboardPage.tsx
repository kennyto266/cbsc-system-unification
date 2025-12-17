import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { Row, Col, Card, Statistic, Progress, Tag, Button, Space, Typography, Alert, Tabs } from 'antd'
import {
  RiseOutlined,
  FallOutlined,
  DollarOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  AlertOutlined,
  RocketOutlined,
  ReloadOutlined,
  BarChartOutlined,
  ThunderboltOutlined
} from '@ant-design/icons'

// 优化的 Hooks
import { useGetAnalyticsDataQuery } from '../../store/api/analyticsApi'
import { useGetActiveStrategiesQuery } from '../../store/api/monitoringApi'
import { useWebSocket } from '../../hooks/useWebSocket'
import { useIntersectionObserver } from '../../hooks/useIntersectionObserver'
import { usePerformanceMonitor } from '../../hooks/usePerformanceMonitor'
import { useIndicatorDataProcessor } from '../../hooks/useIndicatorDataProcessor'

// 优化的组件
import MetricCard from '../../components/dashboard/MetricCard'
import MarketOverview from '../../components/dashboard/MarketOverview'
import RecentSignals from '../../components/dashboard/RecentSignals'
import SystemHealth from '../../components/dashboard/SystemHealth'
import QuickActions from '../../components/dashboard/QuickActions'
import CBSCTabPage from './CBSCTabPage'
import PerformanceMonitor from '../../components/performance/PerformanceMonitor'

// 优化的图表组件
import OptimizedStrategyPerformanceChart from '../../components/charts/OptimizedStrategyPerformanceChart'
import OptimizedAssetAllocationChart from '../../components/charts/OptimizedAssetAllocationChart'
import OptimizedStrategyComparisonChart from '../../components/charts/OptimizedStrategyComparisonChart'
import OptimizedRiskReturnScatterChart from '../../components/charts/OptimizedRiskReturnScatterChart'
import OptimizedRealTimePriceChart from '../../components/charts/OptimizedRealTimePriceChart'

// 虚拟化组件
import VirtualizedIndicatorList from '../../components/technical-indicators/VirtualizedIndicatorList'

import { Strategy, StrategyType } from '../../types'

const { Title, Text } = Typography
const { TabPane } = Tabs

const OptimizedDashboardPage: React.FC = () => {
  // 状态管理 - 使用 useState 的函数式更新避免重渲染
  const [timeRange, setTimeRange] = useState<'1d' | '1w' | '1m' | '3m'>('1m')
  const [chartTimeRange, setChartTimeRange] = useState<'1D' | '1W' | '1M' | '3M' | '6M' | '1Y'>('1M')
  const [comparisonMetric, setComparisonMetric] = useState<'totalReturn' | 'sharpeRatio' | 'maxDrawdown' | 'winRate' | 'profitFactor'>('totalReturn')
  const [filterType, setFilterType] = useState<StrategyType | 'all'>('all')
  const [showPerformanceMonitor, setShowPerformanceMonitor] = useState(process.env.NODE_ENV === 'development')

  const { isConnected } = useWebSocket()
  const { startMeasure, endMeasure, getMetrics } = usePerformanceMonitor()
  const { processIndicatorData, isProcessing } = useIndicatorDataProcessor({
    onSuccess: (result) => {
      console.log('Data processing completed:', result)
    }
  })

  // 数据获取
  const { data: analyticsData, isLoading: analyticsLoading, error: analyticsError } = useGetAnalyticsDataQuery({
    timeRange,
    includeBenchmark: true,
  })

  const { data: activeStrategies, isLoading: strategiesLoading } = useGetActiveStrategiesQuery()

  // 模拟策略数据 - 使用 useMemo 缓存
  const mockStrategies = useMemo(() => [
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
  ], [])

  // 优化数据处理 - 使用 Web Workers 处理大量数据
  const optimizedStrategies = useMemo(() => {
    if (!mockStrategies.length) return []

    // 模拟大数据集处理
    const largeDataSet = Array.from({ length: 1000 }, (_, i) => ({
      ...mockStrategies[i % mockStrategies.length],
      id: `${mockStrategies[i % mockStrategies.length].id}-${i}`,
      performance: {
        ...mockStrategies[i % mockStrategies.length].performance,
        totalReturn: mockStrategies[i % mockStrategies.length].performance.totalReturn * (1 + Math.random() * 0.2 - 0.1)
      }
    }))

    return largeDataSet
  }, [mockStrategies])

  // 懒加载处理
  const chartContainerRef = React.useRef<HTMLDivElement>(null)
  const { isIntersecting: isChartVisible } = useIntersectionObserver(chartContainerRef, {
    threshold: 0.1,
    rootMargin: '100px'
  })

  // 事件处理函数 - 使用 useCallback 避免重创建
  const handleRefresh = useCallback(() => {
    window.location.reload()
  }, [])

  const handleTimeRangeChange = useCallback((range: typeof timeRange) => {
    setTimeRange(range)
  }, [])

  const handleChartTimeRangeChange = useCallback((range: typeof chartTimeRange) => {
    setChartTimeRange(range)
  }, [])

  const handleMetricChange = useCallback((metric: typeof comparisonMetric) => {
    setComparisonMetric(metric)
  }, [])

  const handleFilterChange = useCallback((type: typeof filterType) => {
    setFilterType(type)
  }, [])

  // 性能监控
  useEffect(() => {
    if (showPerformanceMonitor) {
      const metrics = getMetrics()
      console.log('Dashboard Performance Metrics:', metrics)
    }
  }, [showPerformanceMonitor, getMetrics])

  if (analyticsError) {
    return (
      <Alert
        message="数据加载失败"
        description="无法加载Dashboard数据，请检查网络连接或稍后重试。"
        type="error"
        showIcon
        action={
          <Button size="small" onClick={handleRefresh}>
            刷新页面
          </Button>
        }
      />
    )
  }

  return (
    <div>
      <Tabs
        defaultActiveKey="strategies"
        size="large"
        className="w-full"
        items={[
          {
            key: 'strategies',
            label: (
              <span>
                <RocketOutlined />
                策略管理
              </span>
            ),
            children: (
              <div className="space-y-6">
                {/* Header */}
                <div className="flex justify-between items-center">
                  <div>
                    <Title level={2} className="!mb-2">
                      CBSC策略管理Dashboard (优化版)
                    </Title>
                    <Text type="secondary">
                      实时监控您的量化交易策略表现和市场动态
                    </Text>
                  </div>
                  <Space>
                    <Button
                      type="primary"
                      icon={<ReloadOutlined />}
                      onClick={handleRefresh}
                      loading={isProcessing}
                    >
                      刷新数据
                    </Button>
                    <Tag color={isConnected ? 'success' : 'error'}>
                      WebSocket: {isConnected ? '已连接' : '未连接'}
                    </Tag>
                    {process.env.NODE_ENV === 'development' && (
                      <Button
                        type="text"
                        icon={<ThunderboltOutlined />}
                        onClick={() => setShowPerformanceMonitor(!showPerformanceMonitor)}
                      >
                        性能监控
                      </Button>
                    )}
                  </Space>
                </div>

                {/* Key Metrics */}
                <Row gutter={[16, 16]}>
                  <Col xs={24} sm={12} lg={6}>
                    <MetricCard
                      title="总资产价值"
                      value={analyticsData?.portfolio?.totalValue || 106200}
                      precision={2}
                      prefix="¥"
                      trend={5.8}
                      icon={<DollarOutlined />}
                      loading={analyticsLoading}
                    />
                  </Col>
                  <Col xs={24} sm={12} lg={6}>
                    <MetricCard
                      title="总收益率"
                      value={analyticsData?.portfolio?.totalReturn || 6.2}
                      precision={2}
                      suffix="%"
                      trend={2.1}
                      icon={<RiseOutlined />}
                      loading={analyticsLoading}
                    />
                  </Col>
                  <Col xs={24} sm={12} lg={6}>
                    <MetricCard
                      title="夏普比率"
                      value={analyticsData?.portfolio?.sharpeRatio || 1.85}
                      precision={2}
                      trend={0.15}
                      icon={<TrophyOutlined />}
                      loading={analyticsLoading}
                    />
                  </Col>
                  <Col xs={24} sm={12} lg={6}>
                    <MetricCard
                      title="活跃策略"
                      value={activeStrategies?.length || 8}
                      trend={1}
                      icon={<RocketOutlined />}
                      loading={strategiesLoading}
                    />
                  </Col>
                </Row>

                {/* 优化的图表区域 - 使用懒加载 */}
                <div ref={chartContainerRef}>
                  <Row gutter={[16, 16]}>
                    <Col xs={24} lg={16}>
                      <OptimizedStrategyPerformanceChart
                        strategies={optimizedStrategies}
                        timeRange={chartTimeRange}
                        onTimeRangeChange={handleChartTimeRangeChange}
                        lazy={true}
                        visible={isChartVisible}
                      />
                    </Col>
                    <Col xs={24} lg={8}>
                      <OptimizedAssetAllocationChart
                        strategies={optimizedStrategies}
                        totalValue={100000}
                        showDetails={true}
                        lazy={true}
                        visible={isChartVisible}
                      />
                    </Col>
                  </Row>

                  {/* 第二行 - 策略對比和風險收益分析 */}
                  <Row gutter={[16, 16]}>
                    <Col xs={24} lg={12}>
                      <OptimizedStrategyComparisonChart
                        strategies={optimizedStrategies}
                        metric={comparisonMetric}
                        onMetricChange={handleMetricChange}
                        sortBy="value"
                        showTopN={10}
                        lazy={true}
                        visible={isChartVisible}
                      />
                    </Col>
                    <Col xs={24} lg={12}>
                      <OptimizedRiskReturnScatterChart
                        strategies={optimizedStrategies}
                        showQuadrants={true}
                        showEfficientFrontier={true}
                        filterType={filterType}
                        onFilterChange={handleFilterChange}
                        lazy={true}
                        visible={isChartVisible}
                      />
                    </Col>
                  </Row>

                  {/* 第三行 - 實時價格圖表和系統監控 */}
                  <Row gutter={[16, 16]}>
                    <Col xs={24} lg={16}>
                      <OptimizedRealTimePriceChart
                        strategy={mockStrategies[0]}
                        symbol="BTC/USDT"
                        timeFrame="1h"
                        showVolume={true}
                        showIndicators={true}
                        autoUpdate={true}
                        lazy={true}
                        visible={isChartVisible}
                      />
                    </Col>
                    <Col xs={24} lg={8}>
                      <div className="space-y-4">
                        {/* 系統資源監控 */}
                        <SystemHealth />
                        {/* 最近信號 */}
                        <RecentSignals />
                      </div>
                    </Col>
                  </Row>
                </div>

                {/* Bottom Row */}
                <Row gutter={[16, 16]}>
                  <Col xs={24} lg={8}>
                    <QuickActions />
                  </Col>
                  <Col xs={24} lg={16}>
                    {/* 虚拟化指标列表 */}
                    <Card title="技术指标" className="h-full">
                      <VirtualizedIndicatorList
                        indicators={optimizedStrategies}
                        onSelect={(strategy) => console.log('Selected:', strategy)}
                        onToggleFavorite={(id) => console.log('Toggle favorite:', id)}
                        onAddToConfiguration={(strategy) => console.log('Add to config:', strategy)}
                      />
                    </Card>
                  </Col>
                </Row>
              </div>
            ),
          },
          {
            key: 'cbsc',
            label: (
              <span>
                <BarChartOutlined />
                CBSC牛熊证
              </span>
            ),
            children: <CBSCTabPage />,
          },
        ]}
      />

      {/* 性能监控面板 */}
      {showPerformanceMonitor && (
        <div className="fixed bottom-4 right-4 w-96 z-50">
          <PerformanceMonitor
            visible={showPerformanceMonitor}
            onMetricsUpdate={(metrics) => {
              console.log('Updated metrics:', metrics)
            }}
          />
        </div>
      )}
    </div>
  )
}

export default OptimizedDashboardPage