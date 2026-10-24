import React, { useState, useEffect, useMemo } from 'react'
import { Row, Col, Card, Statistic, Progress, Tag, Space, Button, Alert, Typography, List, Avatar } from 'antd'
import {
  RiseOutlined,
  FallOutlined,
  DollarOutlined,
  TrophyOutlined,
  RocketOutlined,
  AlertOutlined,
  RiseOutlined,
  EyeOutlined,
  ReloadOutlined,
  ClockCircleOutlined,
  FireOutlined,
} from '@ant-design/icons'

// Enhanced Chart Components
import {
  StrategyPerformanceChart,
  AssetAllocationChart,
  RiskReturnScatterChart,
  MarketOverviewChart,
} from '../Charts'

// Hooks and Services
import { useAppSelector } from '../../hooks/redux'
import { useWebSocket } from '../../hooks/useWebSocket'
import { selectStrategies } from '../../store/slices/strategiesSlice'
import { selectMonitoring } from '../../store/slices/monitoringSlice'
import { selectAnalytics } from '../../store/slices/analyticsSlice'

// Components
import MetricCard from '../common/MetricCard'
import StrategyQuickActions from '../common/StrategyQuickActions'
import RecentActivity from '../common/RecentActivity'
import MarketMovers from '../common/MarketMovers'

const { Title, Text } = Typography

interface DashboardOverviewProps {
  timeRange?: '1d' | '1w' | '1m' | '3m' | '6m' | '1y'
  refreshInterval?: number
  enableRealTimeUpdates?: boolean
}

const DashboardOverview: React.FC<DashboardOverviewProps> = ({
  timeRange = '1m',
  refreshInterval = 30000,
  enableRealTimeUpdates = true
}) => {
  // Redux state
  const { strategies, loading: strategiesLoading } = useAppSelector(selectStrategies)
  const { systemHealth, alerts } = useAppSelector(selectMonitoring)
  const { performanceData, marketData } = useAppSelector(selectAnalytics)

  // Local state
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange)
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const [isRefreshing, setIsRefreshing] = useState(false)

  // WebSocket for real-time updates
  const { isConnected, lastMessage } = useWebSocket({
    enabled: enableRealTimeUpdates,
    onMessage: handleRealTimeUpdate,
  })

  // Handle real-time WebSocket updates
  function handleRealTimeUpdate(data: any) {
    if (data.type === 'performance_update' || data.type === 'market_data') {
      setLastUpdated(new Date())
    }
  }

  // Calculate key metrics
  const metrics = useMemo(() => {
    const activeStrategies = strategies.filter(s => s.status === 'active')
    const totalReturn = activeStrategies.reduce((sum, s) => sum + (s.performance?.totalReturn || 0), 0)
    const avgSharpeRatio = activeStrategies.length > 0
      ? activeStrategies.reduce((sum, s) => sum + (s.performance?.sharpeRatio || 0), 0) / activeStrategies.length
      : 0
    const totalValue = performanceData?.portfolioValue || 100000
    const todayReturn = performanceData?.dailyReturn || 0

    return {
      totalValue,
      totalReturn,
      avgSharpeRatio,
      activeStrategiesCount: activeStrategies.length,
      todayReturn,
      dailyChange: marketData?.dailyChange || 0,
    }
  }, [strategies, performanceData, marketData])

  // Handle refresh
  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      // Trigger data refresh
      await new Promise(resolve => setTimeout(resolve, 1000))
      setLastUpdated(new Date())
    } finally {
      setIsRefreshing(false)
    }
  }

  // Performance trend data
  const performanceTrendData = useMemo(() => {
    // Generate sample trend data based on selected time range
    const points = selectedTimeRange === '1d' ? 24 : selectedTimeRange === '1w' ? 7 : 30
    return Array.from({ length: points }, (_, i) => ({
      date: new Date(Date.now() - (points - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      portfolio: 100000 + (Math.random() - 0.3) * 10000,
      benchmark: 100000 + (Math.random() - 0.4) * 8000,
    }))
  }, [selectedTimeRange])

  // Top performing strategies
  const topStrategies = useMemo(() => {
    return strategies
      .filter(s => s.performance && s.status === 'active')
      .sort((a, b) => (b.performance?.totalReturn || 0) - (a.performance?.totalReturn || 0))
      .slice(0, 5)
  }, [strategies])

  // Recent alerts
  const criticalAlerts = useMemo(() => {
    return alerts
      .filter(alert => alert.severity === 'critical' && !alert.read)
      .slice(0, 3)
  }, [alerts])

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} className="!mb-2">
            CBSC策略管理总览
          </Title>
          <Text type="secondary">
            实时监控您的量化交易策略表现和市场动态
          </Text>
        </div>

        <Space>
          <Button
            icon={<ReloadOutlined />}
            loading={isRefreshing}
            onClick={handleRefresh}
          >
            刷新数据
          </Button>

          <Tag color={isConnected ? 'success' : 'error'}>
            <Space>
              <ClockCircleOutlined />
              {lastUpdated.toLocaleTimeString()}
            </Space>
          </Tag>
        </Space>
      </div>

      {/* Critical Alerts */}
      {criticalAlerts.length > 0 && (
        <Alert
          message={`您有 ${criticalAlerts.length} 个重要警告需要关注`}
          description={
            <List
              size="small"
              dataSource={criticalAlerts}
              renderItem={alert => (
                <List.Item>
                  <Space>
                    <AlertOutlined style={{ color: '#ff4d4f' }} />
                    <Text>{alert.message}</Text>
                  </Space>
                </List.Item>
              )}
            />
          }
          type="error"
          showIcon
          closable
        />
      )}

      {/* Key Metrics Row */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="总资产价值"
            value={metrics.totalValue}
            precision={2}
            prefix="¥"
            trend={metrics.dailyChange}
            icon={<DollarOutlined />}
            loading={strategiesLoading}
            trendDirection={metrics.dailyChange >= 0 ? 'up' : 'down'}
          />
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="总收益率"
            value={metrics.totalReturn * 100}
            precision={2}
            suffix="%"
            trend={metrics.todayReturn * 100}
            icon={<RiseOutlined />}
            loading={strategiesLoading}
            trendDirection={metrics.todayReturn >= 0 ? 'up' : 'down'}
          />
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="平均夏普比率"
            value={metrics.avgSharpeRatio}
            precision={2}
            icon={<TrophyOutlined />}
            loading={strategiesLoading}
          />
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="活跃策略"
            value={metrics.activeStrategiesCount}
            icon={<RocketOutlined />}
            loading={strategiesLoading}
            extra={
              <Text type="secondary" className="text-xs">
                共 {strategies.length} 个策略
              </Text>
            }
          />
        </Col>
      </Row>

      {/* Charts Row 1 - Performance and Allocation */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card
            title={
              <Space>
                <BarChartOutlined />
                策略组合表现
                <Tag color="blue">{selectedTimeRange}</Tag>
              </Space>
            }
            extra={
              <Space>
                {['1d', '1w', '1m', '3m', '6m', '1y'].map(range => (
                  <Button
                    key={range}
                    size="small"
                    type={selectedTimeRange === range ? 'primary' : 'default'}
                    onClick={() => setSelectedTimeRange(range as any)}
                  >
                    {range}
                  </Button>
                ))}
              </Space>
            }
          >
            <StrategyPerformanceChart
              data={performanceTrendData}
              height={300}
              showLegend={true}
              showTooltip={true}
              timeRange={selectedTimeRange}
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card
            title={<Space><EyeOutlined />策略资产配置</Space>}
            extra={<Button size="small" type="link">查看详情</Button>}
          >
            <AssetAllocationChart
              strategies={strategies}
              totalValue={metrics.totalValue}
              height={300}
              showLabels={true}
              interactive={true}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts Row 2 - Risk Analysis and Market Overview */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card
            title={<Space><FireOutlined />风险收益分析</Space>}
            extra={<Button size="small" type="link">高级分析</Button>}
          >
            <RiskReturnScatterChart
              strategies={strategies.filter(s => s.performance)}
              height={300}
              showQuadrants={true}
              showEfficientFrontier={true}
              interactive={true}
            />
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card
            title={<Space><RiseOutlined />市场概览</Space>}
            extra={<Button size="small" type="link">实时行情</Button>}
          >
            <MarketOverviewChart
              height={300}
              showVolume={true}
              showIndicators={true}
              timeFrame="1D"
            />
          </Card>
        </Col>
      </Row>

      {/* Bottom Row - Top Strategies and Recent Activity */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <TrophyOutlined />
                顶级策略表现
                <Tag color="gold">TOP 5</Tag>
              </Space>
            }
            extra={<Button size="small" type="link">查看全部</Button>}
          >
            <List
              dataSource={topStrategies}
              renderItem={(strategy, index) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <Avatar style={{
                        backgroundColor: index === 0 ? '#fadb14' : index === 1 ? '#c0c0c0' : '#cd7f32',
                        color: '#000'
                      }}>
                        {index + 1}
                      </Avatar>
                    }
                    title={
                      <Space>
                        <Text strong>{strategy.name}</Text>
                        <Tag color={strategy.status === 'active' ? 'success' : 'default'}>
                          {strategy.status}
                        </Tag>
                      </Space>
                    }
                    description={
                      <Row gutter={16}>
                        <Col span={8}>
                          <Text type="secondary">收益率:</Text>
                          <Text strong className="ml-1">
                            {((strategy.performance?.totalReturn || 0) * 100).toFixed(2)}%
                          </Text>
                        </Col>
                        <Col span={8}>
                          <Text type="secondary">夏普比率:</Text>
                          <Text strong className="ml-1">
                            {(strategy.performance?.sharpeRatio || 0).toFixed(2)}
                          </Text>
                        </Col>
                        <Col span={8}>
                          <Text type="secondary">胜率:</Text>
                          <Text strong className="ml-1">
                            {((strategy.performance?.winRate || 0) * 100).toFixed(1)}%
                          </Text>
                        </Col>
                      </Row>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card
            title={<Space><ClockCircleOutlined />最近活动</Space>}
            extra={<Button size="small" type="link">查看历史</Button>}
          >
            <RecentActivity
              limit={10}
              showTime={true}
              showType={true}
            />
          </Card>
        </Col>
      </Row>

      {/* Quick Actions Section */}
      <Card
        title={
          <Space>
            <RocketOutlined />
            快速操作
          </Space>
        }
      >
        <StrategyQuickActions
          strategies={strategies}
          onActionComplete={() => handleRefresh()}
        />
      </Card>
    </div>
  )
}

export default DashboardOverview