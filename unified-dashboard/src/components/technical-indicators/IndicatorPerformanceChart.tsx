import React, { useState, useEffect } from 'react'
import {
  Card,
  Select,
  DatePicker,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Space,
  Spin,
  Empty,
  Alert,
  Button,
  Tooltip
} from 'antd'
import {
  LineChartOutlined,
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
  InfoCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title as ChartTitle,
  Tooltip as ChartTooltip,
  Legend,
  TimeScale,
  CandlestickController,
  OhlcController
} from 'chart.js'
import { Line, Bar, Scatter } from 'react-chartjs-2'
import 'chartjs-adapter-date-fns'
import dayjs from 'dayjs'

import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import {
  fetchIndicatorPerformance,
  selectPerformanceByIndicator,
  selectIsLoading
} from '../../store/slices/technicalIndicatorsSlice'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ChartTitle,
  ChartTooltip,
  Legend,
  TimeScale
)

const { Option } = Select
const { RangePicker } = DatePicker

interface IndicatorPerformanceChartProps {
  indicatorId: string
  symbol?: string
  timeframe?: string
  height?: number
  showControls?: boolean
  showStats?: boolean
}

const IndicatorPerformanceChart: React.FC<IndicatorPerformanceChartProps> = ({
  indicatorId,
  symbol = 'BTC/USDT',
  timeframe = '1h',
  height = 300,
  showControls = true,
  showStats = true
}) => {
  const dispatch = useAppDispatch()
  const performance = useAppSelector(selectPerformanceByIndicator(indicatorId))
  const isLoading = useAppSelector(selectIsLoading)

  const [selectedTimeframe, setSelectedTimeframe] = useState(timeframe)
  const [selectedSymbol, setSelectedSymbol] = useState(symbol)
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(30, 'day'),
    dayjs()
  ])
  const [chartType, setChartType] = useState<'line' | 'bar' | 'scatter'>('line')

  useEffect(() => {
    if (indicatorId) {
      dispatch(fetchIndicatorPerformance({
        indicatorId,
        symbol: selectedSymbol,
        timeframe: selectedTimeframe
      }))
    }
  }, [dispatch, indicatorId, selectedSymbol, selectedTimeframe])

  // Generate mock performance data for demonstration
  const generateMockData = () => {
    const dates = []
    const values = []
    const signals = []

    for (let i = 0; i < 100; i++) {
      const date = dayjs().subtract(100 - i, 'day').toDate()
      dates.push(date)

      // Generate random indicator values
      const baseValue = 50
      const variation = Math.sin(i * 0.1) * 20 + Math.random() * 10
      values.push(baseValue + variation)

      // Generate random signals
      if (Math.random() > 0.9) {
        signals.push({
          x: date,
          y: baseValue + variation,
          type: Math.random() > 0.5 ? 'BUY' : 'SELL'
        })
      }
    }

    return { dates, values, signals }
  }

  const mockData = generateMockData()

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: '指标性能图表',
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            return `值: ${context.parsed.y.toFixed(2)}`
          }
        }
      }
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: 'day' as const
        }
      },
      y: {
        beginAtZero: true
      }
    }
  }

  const chartData = {
    labels: mockData.dates,
    datasets: [
      {
        label: '指标值',
        data: mockData.values,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.1
      },
      {
        label: '买入信号',
        data: mockData.signals.filter(s => s.type === 'BUY').map(s => ({ x: s.x, y: s.y })),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.8)',
        pointRadius: 8,
        pointHoverRadius: 10,
        showLine: false
      },
      {
        label: '卖出信号',
        data: mockData.signals.filter(s => s.type === 'SELL').map(s => ({ x: s.x, y: s.y })),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.8)',
        pointRadius: 8,
        pointHoverRadius: 10,
        showLine: false
      }
    ]
  }

  const statsColumns = [
    {
      title: '指标',
      dataIndex: 'indicator',
      key: 'indicator',
      render: (text: string) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '时间周期',
      dataIndex: 'period',
      key: 'period'
    },
    {
      title: '成功率',
      dataIndex: 'successRate',
      key: 'successRate',
      render: (value: number) => (
        <span style={{ color: value > 60 ? '#52c41a' : value > 40 ? '#faad14' : '#ff4d4f' }}>
          {(value * 100).toFixed(2)}%
        </span>
      )
    },
    {
      title: '盈亏比',
      dataIndex: 'profitFactor',
      key: 'profitFactor',
      render: (value: number) => (
        <span style={{ color: value > 1.5 ? '#52c41a' : value > 1 ? '#faad14' : '#ff4d4f' }}>
          {value.toFixed(2)}
        </span>
      )
    },
    {
      title: '最大回撤',
      dataIndex: 'maxDrawdown',
      key: 'maxDrawdown',
      render: (value: number) => (
        <span style={{ color: value > -20 ? '#52c41a' : value > -10 ? '#faad14' : '#ff4d4f' }}>
          {(value * 100).toFixed(2)}%
        </span>
      )
    },
    {
      title: '夏普比率',
      dataIndex: 'sharpeRatio',
      key: 'sharpeRatio',
      render: (value: number) => (
        <span style={{ color: value > 1 ? '#52c41a' : value > 0.5 ? '#faad14' : '#ff4d4f' }}>
          {value.toFixed(2)}
        </span>
      )
    }
  ]

  const statsData = performance ? [{
    key: '1',
    indicator: indicatorId,
    period: '30天',
    successRate: performance.statistics.successRate,
    profitFactor: performance.statistics.profitFactor,
    maxDrawdown: performance.statistics.maxDrawdown,
    sharpeRatio: performance.statistics.sharpeRatio
  }] : []

  const renderChart = () => {
    if (chartType === 'line') {
      return <Line data={chartData} options={chartOptions} />
    } else if (chartType === 'bar') {
      return <Bar data={chartData} options={chartOptions} />
    } else {
      return <Scatter data={chartData} options={chartOptions} />
    }
  }

  return (
    <div className="indicator-performance-chart">
      {/* Controls */}
      {showControls && (
        <Card size="small" className="mb-4">
          <Row gutter={16}>
            <Col>
              <Space>
                <span>交易品种:</span>
                <Select
                  value={selectedSymbol}
                  onChange={setSelectedSymbol}
                  style={{ width: 120 }}
                >
                  <Option value="BTC/USDT">BTC/USDT</Option>
                  <Option value="ETH/USDT">ETH/USDT</Option>
                  <Option value="BNB/USDT">BNB/USDT</Option>
                </Select>
              </Space>
            </Col>
            <Col>
              <Space>
                <span>时间框架:</span>
                <Select
                  value={selectedTimeframe}
                  onChange={setSelectedTimeframe}
                  style={{ width: 100 }}
                >
                  <Option value="1m">1分钟</Option>
                  <Option value="5m">5分钟</Option>
                  <Option value="15m">15分钟</Option>
                  <Option value="1h">1小时</Option>
                  <Option value="4h">4小时</Option>
                  <Option value="1d">日线</Option>
                </Select>
              </Space>
            </Col>
            <Col>
              <Space>
                <span>图表类型:</span>
                <Select
                  value={chartType}
                  onChange={setChartType}
                  style={{ width: 100 }}
                >
                  <Option value="line">折线图</Option>
                  <Option value="bar">柱状图</Option>
                  <Option value="scatter">散点图</Option>
                </Select>
              </Space>
            </Col>
            <Col>
              <Space>
                <span>日期范围:</span>
                <RangePicker
                  value={dateRange}
                  onChange={(dates) => dates && setDateRange(dates)}
                />
              </Space>
            </Col>
            <Col>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => dispatch(fetchIndicatorPerformance({
                  indicatorId,
                  symbol: selectedSymbol,
                  timeframe: selectedTimeframe
                }))}
              >
                刷新数据
              </Button>
            </Col>
          </Row>
        </Card>
      )}

      {/* Statistics */}
      {showStats && statsData.length > 0 && (
        <Row gutter={16} className="mb-4">
          <Col span={6}>
            <Card>
              <Statistic
                title="总信号数"
                value={performance?.statistics.totalSignals || 0}
                prefix={<LineChartOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="成功率"
                value={(performance?.statistics.successRate || 0) * 100}
                precision={2}
                suffix="%"
                valueStyle={{
                  color: (performance?.statistics.successRate || 0) > 0.6 ? '#3f8600' : '#cf1322'
                }}
                prefix={<TrophyOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="盈亏比"
                value={performance?.statistics.profitFactor || 0}
                precision={2}
                valueStyle={{
                  color: (performance?.statistics.profitFactor || 0) > 1.5 ? '#3f8600' : '#cf1322'
                }}
                prefix={<RiseOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="最大回撤"
                value={(performance?.statistics.maxDrawdown || 0) * 100}
                precision={2}
                suffix="%"
                valueStyle={{
                  color: (performance?.statistics.maxDrawdown || 0) > -10 ? '#3f8600' : '#cf1322'
                }}
                prefix={<FallOutlined />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Chart */}
      <Card title="性能图表" className="mb-4">
        {isLoading ? (
          <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Spin size="large" />
          </div>
        ) : (
          <div style={{ height }}>
            {renderChart()}
          </div>
        )}
      </Card>

      {/* Detailed Stats Table */}
      <Card
        title="详细统计数据"
        extra={
          <Tooltip title="基于历史回测数据">
            <InfoCircleOutlined />
          </Tooltip>
        }
      >
        {statsData.length > 0 ? (
          <Table
            columns={statsColumns}
            dataSource={statsData}
            pagination={false}
            size="small"
          />
        ) : (
          <Empty description="暂无统计数据" />
        )}
      </Card>

      {/* Info Alert */}
      <Alert
        message="性能说明"
        description="以上数据基于历史回测结果，不代表未来表现。实际交易中可能存在滑点、延迟等因素影响。"
        type="info"
        showIcon
        className="mt-4"
      />
    </div>
  )
}

export default IndicatorPerformanceChart