import React, { useState, useEffect, useMemo } from 'react'
import {
  Row,
  Col,
  Card,
  Select,
  DatePicker,
  Space,
  Typography,
  Button,
  Table,
  Statistic,
  Progress,
  Tag,
  Tooltip,
  Switch,
  InputNumber,
} from 'antd'
import {
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  DownloadOutlined,
  SettingOutlined,
  TrophyOutlined,
  RocketOutlined,
  DollarOutlined,
  RiseOutlined,
  CalendarOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'

// Enhanced Chart Components
import {
  AdvancedPerformanceChart,
  CorrelationMatrix,
  RiskDecompositionChart,
  MonteCarloSimulation,
  BacktestResultsChart,
  StrategyAttributionChart,
} from '../Charts'

// Hooks and Services
import { useAppSelector } from '../../hooks/redux'
import { selectStrategies, selectAnalytics } from '../../store/slices'

// Components
import MetricCard from '../common/MetricCard'
import ExportDataModal from '../common/ExportDataModal'
import AnalyticsFilter from '../common/AnalyticsFilter'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { Option } = Select

interface DataAnalyticsProps {
  enableAdvancedAnalytics?: boolean
  enableMonteCarlo?: boolean
  enableAttribution?: boolean
}

const DataAnalytics: React.FC<DataAnalyticsProps> = ({
  enableAdvancedAnalytics = true,
  enableMonteCarlo = true,
  enableAttribution = true
}) => {
  // Redux state
  const { strategies } = useAppSelector(selectStrategies)
  const { analyticsData, backtestResults, riskMetrics } = useAppSelector(selectAnalytics)

  // Local state
  const [timeRange, setTimeRange] = useState('1y')
  const [customDateRange, setCustomDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(1, 'year'),
    dayjs()
  ])
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([])
  const [benchmark, setBenchmark] = useState('SPY')
  const [analysisType, setAnalysisType] = useState('performance')
  const [exportModalVisible, setExportModalVisible] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)

  // Calculate analytics metrics
  const analyticsMetrics = useMemo(() => {
    const activeStrategies = strategies.filter(s => s.status === 'active')
    const totalReturn = analyticsData?.totalReturn || 0
    const volatility = analyticsData?.volatility || 0
    const sharpeRatio = analyticsData?.sharpeRatio || 0
    const maxDrawdown = analyticsData?.maxDrawdown || 0
    const winRate = analyticsData?.winRate || 0

    return {
      totalReturn,
      volatility,
      sharpeRatio,
      maxDrawdown,
      winRate,
      activeStrategies: activeStrategies.length,
      beta: analyticsData?.beta || 0,
      alpha: analyticsData?.alpha || 0,
      informationRatio: analyticsData?.informationRatio || 0,
    }
  }, [analyticsData, strategies])

  // Performance data for charts
  const performanceData = useMemo(() => {
    // Generate sample performance data based on time range
    const days = timeRange === '1m' ? 30 : timeRange === '3m' ? 90 : timeRange === '6m' ? 180 : 365
    return Array.from({ length: days }, (_, i) => {
      const date = dayjs().subtract(days - i, 'day')
      const portfolioValue = 100000 * (1 + (Math.random() - 0.3) * 0.01 * i)
      const benchmarkValue = 100000 * (1 + (Math.random() - 0.4) * 0.008 * i)

      return {
        date: date.format('YYYY-MM-DD'),
        portfolio: portfolioValue,
        benchmark: benchmarkValue,
        return: (portfolioValue - 100000) / 100000,
        benchmarkReturn: (benchmarkValue - 100000) / 100000,
      }
    })
  }, [timeRange])

  // Risk decomposition data
  const riskDecomposition = useMemo(() => [
    { category: '市场风险', value: 45, color: '#ff4d4f' },
    { category: '信用风险', value: 20, color: '#faad14' },
    { category: '流动性风险', value: 15, color: '#1890ff' },
    { category: '操作风险', value: 10, color: '#52c41a' },
    { category: '模型风险', value: 10, color: '#722ed1' },
  ], [])

  // Strategy correlation matrix
  const correlationData = useMemo(() => {
    const activeStrategies = strategies.filter(s => s.status === 'active').slice(0, 10)
    const correlations = []

    for (let i = 0; i < activeStrategies.length; i++) {
      for (let j = 0; j < activeStrategies.length; j++) {
        correlations.push({
          strategy1: activeStrategies[i].name,
          strategy2: activeStrategies[j].name,
          correlation: i === j ? 1 : Math.random() * 2 - 1,
        })
      }
    }

    return correlations
  }, [strategies])

  // Attribution analysis data
  const attributionData = useMemo(() => {
    const strategies = selectedStrategies.length > 0
      ? selectedStrategies.map(id => strategies.find(s => s.id === id))
      : strategies.filter(s => s.status === 'active')

    return strategies.map(strategy => ({
      name: strategy?.name || 'Unknown',
      contribution: (Math.random() - 0.3) * 100,
      allocation: Math.random() * 100,
      selection: (Math.random() - 0.5) * 50,
      interaction: (Math.random() - 0.5) * 20,
    }))
  }, [strategies, selectedStrategies])

  // Export report data
  const exportReportData = () => {
    return {
      timeRange,
      strategies: selectedStrategies,
      benchmark,
      metrics: analyticsMetrics,
      performanceData,
      riskDecomposition,
      generatedAt: new Date().toISOString(),
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} className="!mb-2">
            数据分析
          </Title>
          <Text type="secondary">
            深度分析策略表现、风险归因和投资组合优化
          </Text>
        </div>

        <Space>
          <Tooltip title="高级分析功能">
            <Switch
              checked={showAdvanced}
              onChange={setShowAdvanced}
              checkedChildren="高级"
              unCheckedChildren="基础"
            />
          </Tooltip>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => setExportModalVisible(true)}
          >
            导出报告
          </Button>
        </Space>
      </div>

      {/* Analysis Controls */}
      <Card>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Text strong className="block mb-2">时间范围</Text>
            <Select
              value={timeRange}
              onChange={setTimeRange}
              style={{ width: '100%' }}
            >
              <Option value="1m">最近1个月</Option>
              <Option value="3m">最近3个月</Option>
              <Option value="6m">最近6个月</Option>
              <Option value="1y">最近1年</Option>
              <Option value="custom">自定义</Option>
            </Select>
          </Col>

          {timeRange === 'custom' && (
            <Col xs={24} sm={12} md={6}>
              <Text strong className="block mb-2">自定义日期</Text>
              <RangePicker
                value={customDateRange}
                onChange={setCustomDateRange}
                style={{ width: '100%' }}
              />
            </Col>
          )}

          <Col xs={24} sm={12} md={6}>
            <Text strong className="block mb-2">基准指数</Text>
            <Select
              value={benchmark}
              onChange={setBenchmark}
              style={{ width: '100%' }}
            >
              <Option value="SPY">标普500</Option>
              <Option value="QQQ">纳斯达克100</Option>
              <Option value="VTI">美国整体市场</Option>
              <Option value="HSI">恒生指数</Option>
              <Option value="000300">沪深300</Option>
            </Select>
          </Col>

          <Col xs={24} sm={12} md={6}>
            <Text strong className="block mb-2">分析类型</Text>
            <Select
              value={analysisType}
              onChange={setAnalysisType}
              style={{ width: '100%' }}
            >
              <Option value="performance">性能分析</Option>
              <Option value="risk">风险分析</Option>
              <Option value="attribution">归因分析</Option>
              <Option value="correlation">相关性分析</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      {/* Key Metrics */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="总收益率"
            value={analyticsMetrics.totalReturn * 100}
            precision={2}
            suffix="%"
            trend={analyticsMetrics.totalReturn * 100}
            icon={<RiseOutlined />}
            trendDirection={analyticsMetrics.totalReturn >= 0 ? 'up' : 'down'}
          />
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="夏普比率"
            value={analyticsMetrics.sharpeRatio}
            precision={2}
            icon={<TrophyOutlined />}
          />
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="最大回撤"
            value={analyticsMetrics.maxDrawdown * 100}
            precision={2}
            suffix="%"
            icon={<RocketOutlined />}
            trendDirection="down"
          />
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="胜率"
            value={analyticsMetrics.winRate * 100}
            precision={1}
            suffix="%"
            icon={<BarChartOutlined />}
          />
        </Col>
      </Row>

      {/* Advanced Metrics */}
      {showAdvanced && (
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <MetricCard
              title="Alpha"
              value={analyticsMetrics.alpha * 100}
              precision={2}
              suffix="%"
              icon={<LineChartOutlined />}
            />
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <MetricCard
              title="Beta"
              value={analyticsMetrics.beta}
              precision={2}
              icon={<DollarOutlined />}
            />
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <MetricCard
              title="信息比率"
              value={analyticsMetrics.informationRatio}
              precision={2}
              icon={<PieChartOutlined />}
            />
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <MetricCard
              title="波动率"
              value={analyticsMetrics.volatility * 100}
              precision={2}
              suffix="%"
              icon={<CalendarOutlined />}
            />
          </Col>
        </Row>
      )}

      {/* Performance Analysis */}
      {analysisType === 'performance' && (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={16}>
            <Card
              title={
                <Space>
                  <LineChartOutlined />
                  投资组合表现
                  <Tag color="blue">{timeRange}</Tag>
                </Space>
              }
            >
              <AdvancedPerformanceChart
                data={performanceData}
                benchmark={benchmark}
                height={400}
                showDrawdown={true}
                showRollingReturns={showAdvanced}
              />
            </Card>
          </Col>

          <Col xs={24} lg={8}>
            <Card title="收益率分布" size="small">
              <div className="space-y-4">
                <div>
                  <Text>月度收益率分布</Text>
                  <Progress
                    percent={65}
                    status="active"
                    strokeColor="#52c41a"
                  />
                </div>
                <div>
                  <Text>正收益月份占比</Text>
                  <Progress
                    percent={68}
                    status="active"
                    strokeColor="#1890ff"
                  />
                </div>
                <div>
                  <Text>最佳月度收益率</Text>
                  <Text strong>+15.2%</Text>
                </div>
                <div>
                  <Text>最差月度收益率</Text>
                  <Text strong style={{ color: '#ff4d4f' }}>-8.7%</Text>
                </div>
              </div>
            </Card>
          </Col>
        </Row>
      )}

      {/* Risk Analysis */}
      {analysisType === 'risk' && (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card title="风险分解">
              <RiskDecompositionChart
                data={riskDecomposition}
                height={350}
                interactive={true}
              />
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="策略相关性矩阵">
              <CorrelationMatrix
                data={correlationData}
                height={350}
                colorScale={['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffcc', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Attribution Analysis */}
      {(analysisType === 'attribution' || enableAttribution) && (
        <Card title="收益归因分析">
          <StrategyAttributionChart
            data={attributionData}
            height={400}
            showDetails={showAdvanced}
          />
        </Card>
      )}

      {/* Monte Carlo Simulation */}
      {showAdvanced && enableMonteCarlo && (
        <Card title="蒙特卡洛模拟">
          <MonteCarloSimulation
            simulations={1000}
            timeHorizon={252} // 1 year trading days
            initialCapital={100000}
            height={350}
            showPercentiles={true}
          />
        </Card>
      )}

      {/* Backtest Results */}
      {showAdvanced && (
        <Card title="回测结果详情">
          <BacktestResultsChart
            data={backtestResults || []}
            height={400}
            showMetrics={true}
            showBenchmark={true}
          />
        </Card>
      )}

      {/* Strategy Performance Comparison */}
      <Card title="策略表现对比">
        <Table
          columns={[
            {
              title: '策略名称',
              dataIndex: 'name',
              key: 'name',
            },
            {
              title: '收益率',
              dataIndex: 'return',
              key: 'return',
              render: (value: number) => (
                <Text style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
                  {(value * 100).toFixed(2)}%
                </Text>
              ),
              sorter: (a, b) => a.return - b.return,
            },
            {
              title: '夏普比率',
              dataIndex: 'sharpe',
              key: 'sharpe',
              render: (value: number) => value?.toFixed(2) || '-',
              sorter: (a, b) => a.sharpe - b.sharpe,
            },
            {
              title: '最大回撤',
              dataIndex: 'maxDrawdown',
              key: 'maxDrawdown',
              render: (value: number) => (
                <Text style={{ color: '#ff4d4f' }}>
                  {(value * 100).toFixed(2)}%
                </Text>
              ),
              sorter: (a, b) => a.maxDrawdown - b.maxDrawdown,
            },
            {
              title: '胜率',
              dataIndex: 'winRate',
              key: 'winRate',
              render: (value: number) => `${(value * 100).toFixed(1)}%`,
              sorter: (a, b) => a.winRate - b.winRate,
            },
          ]}
          dataSource={strategies.map(strategy => ({
            key: strategy.id,
            name: strategy.name,
            return: strategy.performance?.totalReturn || 0,
            sharpe: strategy.performance?.sharpeRatio || 0,
            maxDrawdown: Math.abs(strategy.performance?.maxDrawdown || 0),
            winRate: strategy.performance?.winRate || 0,
          }))}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
          }}
        />
      </Card>

      {/* Export Modal */}
      <ExportDataModal
        visible={exportModalVisible}
        onCancel={() => setExportModalVisible(false)}
        data={exportReportData()}
        format="pdf"
      />
    </div>
  )
}

export default DataAnalytics