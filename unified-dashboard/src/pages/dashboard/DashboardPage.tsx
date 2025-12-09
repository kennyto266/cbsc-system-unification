import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Progress, Tag, Button, Space, Typography, Alert } from 'antd'
import {
  LineChart,
  Line,
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
  ResponsiveContainer
} from 'recharts'
import {
  TrendingUpOutlined,
  TrendingDownOutlined,
  DollarOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  AlertOutlined,
  RocketOutlined,
  ReloadOutlined,
} from '@ant-design/icons'

// Hooks
import { useGetAnalyticsDataQuery } from '@store/api/analyticsApi'
import { useGetActiveStrategiesQuery } from '@store/api/monitoringApi'
import { useWebSocket } from '@hooks/useWebSocket'

// Components
import MetricCard from '@components/dashboard/MetricCard'
import StrategyPerformanceChart from '@components/charts/StrategyPerformanceChart'
import MarketOverview from '@components/dashboard/MarketOverview'
import RecentSignals from '@components/dashboard/RecentSignals'
import SystemHealth from '@components/dashboard/SystemHealth'
import QuickActions from '@components/dashboard/QuickActions'

const { Title, Text } = Typography

const DashboardPage: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'1d' | '1w' | '1m' | '3m'>('1m')
  const { isConnected } = useWebSocket()

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
            icon={<TrendingUpOutlined />}
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

      {/* Charts Row */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card
            title="投资组合表现"
            extra={
              <Space>
                <Button
                  size="small"
                  type={timeRange === '1d' ? 'primary' : 'default'}
                  onClick={() => setTimeRange('1d')}
                >
                  1天
                </Button>
                <Button
                  size="small"
                  type={timeRange === '1w' ? 'primary' : 'default'}
                  onClick={() => setTimeRange('1w')}
                >
                  1周
                </Button>
                <Button
                  size="small"
                  type={timeRange === '1m' ? 'primary' : 'default'}
                  onClick={() => setTimeRange('1m')}
                >
                  1月
                </Button>
                <Button
                  size="small"
                  type={timeRange === '3m' ? 'primary' : 'default'}
                  onClick={() => setTimeRange('3m')}
                >
                  3月
                </Button>
              </Space>
            }
          >
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="portfolio"
                  stroke="#1890ff"
                  fill="#1890ff"
                  fillOpacity={0.3}
                  name="投资组合"
                />
                <Area
                  type="monotone"
                  dataKey="benchmark"
                  stroke="#8c8c8c"
                  fill="#8c8c8c"
                  fillOpacity={0.3}
                  name="基准"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="策略分配">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={allocationData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {allocationData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Second Row */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <StrategyPerformanceChart />
        </Col>
        <Col xs={24} lg={12}>
          <MarketOverview />
        </Col>
      </Row>

      {/* Third Row */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="系统资源使用情况">
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
        </Col>
        <Col xs={24} lg={8}>
          <RecentSignals />
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