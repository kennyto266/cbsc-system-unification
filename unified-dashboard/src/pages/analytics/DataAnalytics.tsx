import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Select, DatePicker, Button, Space, Typography, Statistic, Table, Tag, Progress } from 'antd'
import {
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  TrendingUpOutlined,
  DownloadOutlined,
  FilterOutlined,
  CalendarOutlined,
} from '@ant-design/icons'

// Charts
import {
  PerformanceAnalyticsChart,
  RiskAnalysisChart,
  SectorAllocationChart,
  CorrelationMatrixChart,
  DrawdownChart,
} from '../../components/charts/AnalyticsCharts'

// Components
import AnalyticsFilter from '../../components/analytics/AnalyticsFilter'
import PerformanceMetrics from '../../components/analytics/PerformanceMetrics'
import RiskMetrics from '../../components/analytics/RiskMetrics'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { Option } = Select

const DataAnalytics: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'1M' | '3M' | '6M' | '1Y' | 'ALL'>('6M')
  const [selectedStrategy, setSelectedStrategy] = useState<string>('all')
  const [benchmark, setBenchmark] = useState<string>('HS300')
  const [analysisType, setAnalysisType] = useState<'performance' | 'risk' | 'allocation' | 'correlation'>('performance')

  // Mock data for demonstration
  const strategies = [
    { id: 'all', name: '所有策略' },
    { id: '1', name: 'RSI策略' },
    { id: '2', name: 'MACD策略' },
    { id: '3', name: '布林帶策略' },
    { id: '4', name: '情感分析策略' },
    { id: '5', name: '多因子策略' },
  ]

  const benchmarks = [
    { id: 'HS300', name: '滬深300' },
    { id: 'CSI500', name: '中證500' },
    { id: 'SZSE', name: '深證成指' },
    { id: 'BTC', name: '比特幣' },
  ]

  const performanceMetrics = {
    totalReturn: 28.5,
    annualizedReturn: 18.2,
    sharpeRatio: 1.65,
    sortinoRatio: 2.31,
    maxDrawdown: -12.3,
    calmarRatio: 1.48,
    winRate: 64.5,
    profitFactor: 1.85,
    avgWin: 2.34,
    avgLoss: -1.27,
  }

  const riskMetrics = {
    volatility: 14.2,
    beta: 0.85,
    alpha: 5.3,
    var95: -2.15,
    cvar95: -3.42,
    skewness: 0.23,
    kurtosis: 2.87,
    informationRatio: 0.92,
  }

  const sectorAllocation = [
    { sector: '科技', allocation: 35, performance: 18.5 },
    { sector: '金融', allocation: 25, performance: 8.2 },
    { sector: '消費', allocation: 20, performance: 12.7 },
    { sector: '醫療', allocation: 15, performance: 15.3 },
    { sector: '能源', allocation: 5, performance: -3.2 },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} className="!mb-2">
            數據分析中心
          </Title>
          <Text type="secondary">
            策略績效、風險分析和資產配置的深度洞察
          </Text>
        </div>
        <Space>
          <Button icon={<DownloadOutlined />} type="primary">
            導出報告
          </Button>
          <Button icon={<FilterOutlined />}>
            高級過濾
          </Button>
        </Space>
      </div>

      {/* Analysis Controls */}
      <Card size="small">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={6} md={4}>
            <Text className="block mb-2">分析類型</Text>
            <Select
              value={analysisType}
              onChange={setAnalysisType}
              style={{ width: '100%' }}
            >
              <Option value="performance">績效分析</Option>
              <Option value="risk">風險分析</Option>
              <Option value="allocation">配置分析</Option>
              <Option value="correlation">相關性分析</Option>
            </Select>
          </Col>
          <Col xs={24} sm={6} md={4}>
            <Text className="block mb-2">時間範圍</Text>
            <Select
              value={timeRange}
              onChange={setTimeRange}
              style={{ width: '100%' }}
            >
              <Option value="1M">1個月</Option>
              <Option value="3M">3個月</Option>
              <Option value="6M">6個月</Option>
              <Option value="1Y">1年</Option>
              <Option value="ALL">全部</Option>
            </Select>
          </Col>
          <Col xs={24} sm={6} md={4}>
            <Text className="block mb-2">策略選擇</Text>
            <Select
              value={selectedStrategy}
              onChange={setSelectedStrategy}
              style={{ width: '100%' }}
            >
              {strategies.map(strategy => (
                <Option key={strategy.id} value={strategy.id}>
                  {strategy.name}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={6} md={4}>
            <Text className="block mb-2">基準指數</Text>
            <Select
              value={benchmark}
              onChange={setBenchmark}
              style={{ width: '100%' }}
            >
              {benchmarks.map(b => (
                <Option key={b.id} value={b.id}>
                  {b.name}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={24} md={8}>
            <Text className="block mb-2">自定義時間</Text>
            <RangePicker
              style={{ width: '100%' }}
              placeholder={['開始日期', '結束日期']}
            />
          </Col>
        </Row>
      </Card>

      {/* Performance Metrics Overview */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="總收益率"
              value={performanceMetrics.totalReturn}
              precision={2}
              suffix="%"
              valueStyle={{ color: '#3f8600' }}
              prefix={<TrendingUpOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="年化收益率"
              value={performanceMetrics.annualizedReturn}
              precision={2}
              suffix="%"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="夏普比率"
              value={performanceMetrics.sharpeRatio}
              precision={2}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="最大回撤"
              value={performanceMetrics.maxDrawdown}
              precision={2}
              suffix="%"
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Performance Chart */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="績效表現" extra={
            <Space>
              <Button
                type={analysisType === 'performance' ? 'primary' : 'link'}
                icon={<LineChartOutlined />}
                size="small"
                onClick={() => setAnalysisType('performance')}
              >
                曲線圖
              </Button>
              <Button
                type={analysisType === 'risk' ? 'primary' : 'link'}
                icon={<BarChartOutlined />}
                size="small"
                onClick={() => setAnalysisType('risk')}
              >
                風險圖
              </Button>
            </Space>
          }>
            {analysisType === 'performance' ? (
              <PerformanceAnalyticsChart
                timeRange={timeRange}
                strategy={selectedStrategy}
                benchmark={benchmark}
              />
            ) : (
              <RiskAnalysisChart
                timeRange={timeRange}
                strategy={selectedStrategy}
              />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="資產配置" extra={
            <Button
              type={analysisType === 'allocation' ? 'primary' : 'link'}
              icon={<PieChartOutlined />}
              size="small"
              onClick={() => setAnalysisType('allocation')}
            >
              餅圖
            </Button>
          }>
            <SectorAllocationChart
              data={sectorAllocation}
              showDetails={true}
            />
          </Card>
        </Col>
      </Row>

      {/* Detailed Metrics */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <PerformanceMetrics metrics={performanceMetrics} />
        </Col>
        <Col xs={24} lg={12}>
          <RiskMetrics metrics={riskMetrics} />
        </Col>
      </Row>

      {/* Drawdown Analysis */}
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card title="回撤分析" extra={
            <Space>
              <Text type="secondary">最大回撤: {performanceMetrics.maxDrawdown}%</Text>
              <Text type="secondary">卡瑪比率: {performanceMetrics.calmarRatio}</Text>
            </Space>
          }>
            <DrawdownChart
              timeRange={timeRange}
              strategy={selectedStrategy}
              showRecoveryTime={true}
            />
          </Card>
        </Col>
      </Row>

      {/* Correlation Matrix */}
      {analysisType === 'correlation' && (
        <Row gutter={[16, 16]}>
          <Col xs={24}>
            <Card title="策略相關性矩陣" extra={
              <Text type="secondary">
                顯示各策略之間的相關性係數
              </Text>
            }>
              <CorrelationMatrixChart
                strategies={strategies.slice(1)} // Exclude 'all'
                timeRange={timeRange}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Trade Analysis Table */}
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card title="交易分析" extra={<Button type="text">導出數據</Button>}>
            <Table
              dataSource={[
                {
                  key: '1',
                  strategy: 'RSI策略',
                  totalTrades: 245,
                  winningTrades: 158,
                  winRate: 64.5,
                  avgProfit: 2.34,
                  avgLoss: -1.27,
                  profitFactor: 1.85,
                  expectancy: 0.82,
                },
                {
                  key: '2',
                  strategy: 'MACD策略',
                  totalTrades: 189,
                  winningTrades: 112,
                  winRate: 59.3,
                  avgProfit: 3.12,
                  avgLoss: -1.89,
                  profitFactor: 1.72,
                  expectancy: 0.65,
                },
                {
                  key: '3',
                  strategy: '布林帶策略',
                  totalTrades: 167,
                  winningTrades: 98,
                  winRate: 58.7,
                  avgProfit: 2.87,
                  avgLoss: -1.54,
                  profitFactor: 1.68,
                  expectancy: 0.59,
                },
              ]}
              columns={[
                {
                  title: '策略',
                  dataIndex: 'strategy',
                  key: 'strategy',
                },
                {
                  title: '總交易次數',
                  dataIndex: 'totalTrades',
                  key: 'totalTrades',
                },
                {
                  title: '盈利交易',
                  dataIndex: 'winningTrades',
                  key: 'winningTrades',
                },
                {
                  title: '勝率',
                  dataIndex: 'winRate',
                  key: 'winRate',
                  render: (value: number) => (
                    <Progress
                      percent={value}
                      size="small"
                      status={value > 60 ? 'success' : 'normal'}
                      format={() => `${value.toFixed(1)}%`}
                    />
                  ),
                },
                {
                  title: '平均盈利',
                  dataIndex: 'avgProfit',
                  key: 'avgProfit',
                  render: (value: number) => (
                    <Text className="text-green-600">+{value.toFixed(2)}%</Text>
                  ),
                },
                {
                  title: '平均虧損',
                  dataIndex: 'avgLoss',
                  key: 'avgLoss',
                  render: (value: number) => (
                    <Text className="text-red-600">{value.toFixed(2)}%</Text>
                  ),
                },
                {
                  title: '盈利因子',
                  dataIndex: 'profitFactor',
                  key: 'profitFactor',
                  render: (value: number) => (
                    <Tag color={value > 1.5 ? 'green' : 'orange'}>
                      {value.toFixed(2)}
                    </Tag>
                  ),
                },
                {
                  title: '期望收益',
                  dataIndex: 'expectancy',
                  key: 'expectancy',
                  render: (value: number) => (
                    <Text className={value > 0 ? 'text-green-600' : 'text-red-600'}>
                      {value > 0 ? '+' : ''}{value.toFixed(2)}%
                    </Text>
                  ),
                },
              ]}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default DataAnalytics