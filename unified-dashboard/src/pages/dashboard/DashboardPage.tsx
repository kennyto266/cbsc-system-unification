import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Progress, Tag, Button, Space, Typography, Alert } from 'antd'
import {
  RiseOutlined,
  FallOutlined,
  DollarOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  AlertOutlined,
  RocketOutlined,
  ReloadOutlined,
} from '@ant-design/icons'

// Hooks
import { useGetAnalyticsDataQuery } from '../../store/api/analyticsApi'
import { useGetActiveStrategiesQuery } from '../../store/api/monitoringApi'
import { useWebSocket } from '../../hooks/useWebSocket'

// Components
import MetricCard from '../../components/dashboard/MetricCard'
import MarketOverview from '../../components/dashboard/MarketOverview'
import RecentSignals from '../../components/dashboard/RecentSignals'
import SystemHealth from '../../components/dashboard/SystemHealth'
import QuickActions from '../../components/dashboard/QuickActions'

// 新的Chart.js圖表組件
import {
  StrategyPerformanceChart,
  AssetAllocationChart,
  StrategyComparisonChart,
  RiskReturnScatterChart,
  RealTimePriceChart
} from '../../components/Charts'
import { Strategy, StrategyType } from '../../types'

const { Title, Text } = Typography

const DashboardPage: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'1d' | '1w' | '1m' | '3m'>('1m')
  const [chartTimeRange, setChartTimeRange] = useState<'1D' | '1W' | '1M' | '3M' | '6M' | '1Y'>('1M')
  const [comparisonMetric, setComparisonMetric] = useState<'totalReturn' | 'sharpeRatio' | 'maxDrawdown' | 'winRate' | 'profitFactor'>('totalReturn')
  const [filterType, setFilterType] = useState<StrategyType | 'all'>('all')
  const { isConnected } = useWebSocket()

  // 模擬策略數據
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

  // Fetch dashboard data
  const { data: analyticsData, isLoading: analyticsLoading, error: analyticsError } = useGetAnalyticsDataQuery({
    timeRange,
    includeBenchmark: true,
  })

  const { data: activeStrategies, isLoading: strategiesLoading } = useGetActiveStrategiesQuery()

  // Mock data for demonstration
  const performanceData = [
    { date: '2024-01-01', portfolio: 100000, benchmark: 100000 },
    { date: '2024-01-02', portfolio: 101500, benchmark: 100500 },
    { date: '2024-01-03', portfolio: 102200, benchmark: 100800 },
    { date: '2024-01-04', portfolio: 103800, benchmark: 101200 },
    { date: '2024-01-05', portfolio: 104500, benchmark: 101000 },
    { date: '2024-01-06', portfolio: 105800, benchmark: 101800 },
    { date: '2024-01-07', portfolio: 106200, benchmark: 102200 },
  ]

  const allocationData = [
    { name: 'RSI策略', value: 35, color: '#1890ff' },
    { name: 'MACD策略', value: 25, color: '#52c41a' },
    { name: '布林带策略', value: 20, color: '#faad14' },
    { name: '动量策略', value: 20, color: '#722ed1' },
  ]

  const recentActivity = [
    { id: 1, type: 'signal', strategy: 'RSI策略', action: '买入', time: '2分钟前', status: 'success' },
    { id: 2, type: 'execution', strategy: 'MACD策略', action: '执行完成', time: '5分钟前', status: 'success' },
    { id: 3, type: 'alert', strategy: '布林带策略', action: '风险警告', time: '10分钟前', status: 'warning' },
    { id: 4, type: 'signal', strategy: '动量策略', action: '卖出', time: '15分钟前', status: 'success' },
  ]

  const systemMetrics = {
    cpu: 45,
    memory: 62,
    disk: 38,
    network: 23,
  }

  if (analyticsError) {
    return (
      <Alert
        message="数据加载失败"
        description="无法加载Dashboard数据，请检查网络连接或稍后重试。"
        type="error"
        showIcon
        action={
          <Button size="small" onClick={() => window.location.reload()}>
            刷新页面
          </Button>
        }
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} className="!mb-2">
            CBSC策略管理Dashboard
          </Title>
          <Text type="secondary">
            实时监控您的量化交易策略表现和市场动态
          </Text>
        </div>
        <Space>
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={() => window.location.reload()}
          >
            刷新数据
          </Button>
          <Tag color={isConnected ? 'success' : 'error'}>
            WebSocket: {isConnected ? '已连接' : '未连接'}
          </Tag>
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

      {/* 新的Chart.js圖表區域 - 策略性能和資產配置 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <StrategyPerformanceChart
            strategies={mockStrategies}
            timeRange={chartTimeRange}
            onTimeRangeChange={setChartTimeRange}
          />
        </Col>
        <Col xs={24} lg={8}>
          <AssetAllocationChart
            strategies={mockStrategies}
            totalValue={100000}
            showDetails={true}
          />
        </Col>
      </Row>

      {/* 第二行 - 策略對比和風險收益分析 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <StrategyComparisonChart
            strategies={mockStrategies}
            metric={comparisonMetric}
            onMetricChange={setComparisonMetric}
            sortBy="value"
            showTopN={10}
          />
        </Col>
        <Col xs={24} lg={12}>
          <RiskReturnScatterChart
            strategies={mockStrategies}
            showQuadrants={true}
            showEfficientFrontier={true}
            filterType={filterType}
            onFilterChange={setFilterType}
          />
        </Col>
      </Row>

      {/* 第三行 - 實時價格圖表和系統監控 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <RealTimePriceChart
            strategy={mockStrategies[0]} // 使用第一個策略作為示例
            symbol="BTC/USDT"
            timeFrame="1h"
            showVolume={true}
            showIndicators={true}
            autoUpdate={true}
          />
        </Col>
        <Col xs={24} lg={8}>
          <div className="space-y-4">
            {/* 系統資源監控 */}
            <Card title="系统资源使用情况" size="small">
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12}>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between mb-2">
                        <Text>CPU使用率</Text>
                        <Text>{systemMetrics.cpu}%</Text>
                      </div>
                      <Progress percent={systemMetrics.cpu} status="active" strokeColor="#1890ff" />
                    </div>
                    <div>
                      <div className="flex justify-between mb-2">
                        <Text>内存使用率</Text>
                        <Text>{systemMetrics.memory}%</Text>
                      </div>
                      <Progress percent={systemMetrics.memory} status="active" strokeColor="#52c41a" />
                    </div>
                  </div>
                </Col>
                <Col xs={24} sm={12}>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between mb-2">
                        <Text>磁盘使用率</Text>
                        <Text>{systemMetrics.disk}%</Text>
                      </div>
                      <Progress percent={systemMetrics.disk} status="active" strokeColor="#faad14" />
                    </div>
                    <div>
                      <div className="flex justify-between mb-2">
                        <Text>网络使用率</Text>
                        <Text>{systemMetrics.network}%</Text>
                      </div>
                      <Progress percent={systemMetrics.network} status="active" strokeColor="#722ed1" />
                    </div>
                  </div>
                </Col>
              </Row>
            </Card>
            {/* 最近信號 */}
            <RecentSignals />
          </div>
        </Col>
      </Row>

      {/* Bottom Row */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <SystemHealth />
        </Col>
        <Col xs={24} lg={16}>
          <QuickActions />
        </Col>
      </Row>
    </div>
  )
}

export default DashboardPage