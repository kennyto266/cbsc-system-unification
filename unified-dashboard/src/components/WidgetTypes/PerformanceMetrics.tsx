/**
 * Performance Metrics Widget - Displays detailed performance metrics
 */

import React from 'react'
import { Row, Col, Card, Statistic, Progress, Table, Tag } from 'antd'
import {
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
  LineChartOutlined,
  FireOutlined,
} from '@ant-design/icons'
import { Line } from '@ant-design/plots'
import { WidgetContainer } from '../Widget/WidgetContainer'

interface PerformanceMetricsProps {
  data?: {
    totalReturn: number
    annualizedReturn: number
    sharpeRatio: number
    sortinoRatio: number
    maxDrawdown: number
    volatility: number
    winRate: number
    profitFactor: number
    calmarRatio: number
    dailyReturns: Array<{
      date: string
      portfolio: number
      benchmark: number
    }>
  }
}

export const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({
  data,
}) => {
  // Default mock data if none provided
  const metrics = data || {
    totalReturn: 0.186,
    annualizedReturn: 0.224,
    sharpeRatio: 1.85,
    sortinoRatio: 2.56,
    maxDrawdown: -0.085,
    volatility: 0.122,
    winRate: 0.65,
    profitFactor: 1.8,
    calmarRatio: 2.64,
    dailyReturns: [
      { date: '2024-01-01', portfolio: 100000, benchmark: 100000 },
      { date: '2024-01-02', portfolio: 101500, benchmark: 100500 },
      { date: '2024-01-03', portfolio: 102200, benchmark: 100800 },
      { date: '2024-01-04', portfolio: 103800, benchmark: 101200 },
      { date: '2024-01-05', portfolio: 104500, benchmark: 101000 },
      { date: '2024-01-06', portfolio: 105800, benchmark: 101800 },
      { date: '2024-01-07', portfolio: 106200, benchmark: 102200 },
    ],
  }

  const getMetricColor = (value: number, isHigherBetter = true) => {
    if (isHigherBetter) {
      return value > 0 ? '#3f8600' : '#cf1322'
    } else {
      return value < 0 ? '#3f8600' : '#cf1322'
    }
  }

  const getPerformanceLevel = (value: number, levels: { good: number; average: number; isHigherBetter?: boolean }) => {
    const isHigherBetter = levels.isHigherBetter !== false
    if (isHigherBetter) {
      if (value >= levels.good) return { color: 'success', text: '优秀' }
      if (value >= levels.average) return { color: 'processing', text: '良好' }
      return { color: 'warning', text: '一般' }
    } else {
      if (value <= levels.good) return { color: 'success', text: '优秀' }
      if (value <= levels.average) return { color: 'processing', text: '良好' }
      return { color: 'warning', text: '一般' }
    }
  }

  const performanceTableData = [
    {
      metric: '总收益率',
      value: `${(metrics.totalReturn * 100).toFixed(2)}%`,
      level: getPerformanceLevel(metrics.totalReturn, { good: 0.15, average: 0.05 }),
      icon: <RiseOutlined />,
    },
    {
      metric: '年化收益率',
      value: `${(metrics.annualizedReturn * 100).toFixed(2)}%`,
      level: getPerformanceLevel(metrics.annualizedReturn, { good: 0.20, average: 0.10 }),
      icon: <LineChartOutlined />,
    },
    {
      metric: '夏普比率',
      value: metrics.sharpeRatio.toFixed(2),
      level: getPerformanceLevel(metrics.sharpeRatio, { good: 2.0, average: 1.0 }),
      icon: <TrophyOutlined />,
    },
    {
      metric: '索提诺比率',
      value: metrics.sortinoRatio.toFixed(2),
      level: getPerformanceLevel(metrics.sortinoRatio, { good: 2.5, average: 1.5 }),
      icon: <FireOutlined />,
    },
    {
      metric: '最大回撤',
      value: `${(metrics.maxDrawdown * 100).toFixed(2)}%`,
      level: getPerformanceLevel(Math.abs(metrics.maxDrawdown), { good: 0.05, average: 0.10, isHigherBetter: false }),
      icon: <FallOutlined />,
    },
    {
      metric: '波动率',
      value: `${(metrics.volatility * 100).toFixed(2)}%`,
      level: getPerformanceLevel(metrics.volatility, { good: 0.10, average: 0.15, isHigherBetter: false }),
      icon: <LineChartOutlined />,
    },
    {
      metric: '胜率',
      value: `${(metrics.winRate * 100).toFixed(1)}%`,
      level: getPerformanceLevel(metrics.winRate, { good: 0.60, average: 0.50 }),
      icon: <TrophyOutlined />,
    },
    {
      metric: '盈利因子',
      value: metrics.profitFactor.toFixed(2),
      level: getPerformanceLevel(metrics.profitFactor, { good: 1.5, average: 1.2 }),
      icon: <RiseOutlined />,
    },
  ]

  const chartConfig = {
    data: metrics.dailyReturns,
    xField: 'date',
    yField: 'portfolio',
    seriesField: 'type',
    smooth: true,
    tooltip: {
      formatter: (datum: any) => ({
        name: datum.type === 'portfolio' ? '投资组合' : '基准',
        value: `¥${datum.portfolio?.toLocaleString() || datum.benchmark?.toLocaleString()}`,
      }),
    },
    color: ['#1890ff', '#52c41a'],
    legend: {
      custom: true,
      items: [
        { name: '投资组合', value: 'portfolio', marker: { style: { fill: '#1890ff' } } },
        { name: '基准', value: 'benchmark', marker: { style: { fill: '#52c41a' } } },
      ],
    },
  }

  // Transform data for the chart
  const chartData = [
    ...metrics.dailyReturns.map(item => ({
      ...item,
      type: '投资组合',
      value: item.portfolio,
    })),
    ...metrics.dailyReturns.map(item => ({
      ...item,
      type: '基准',
      value: item.benchmark,
    })),
  ]

  return (
    <WidgetContainer
      id="performance-metrics"
      type="performance-metrics"
      title="性能指标"
    >
      <div className="space-y-4">
        {/* Key Metrics Row */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card size="small">
              <Statistic
                title="总收益率"
                value={metrics.totalReturn * 100}
                precision={2}
                suffix="%"
                valueStyle={{ color: getMetricColor(metrics.totalReturn) }}
                prefix={metrics.totalReturn >= 0 ? <RiseOutlined /> : <FallOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card size="small">
              <Statistic
                title="夏普比率"
                value={metrics.sharpeRatio}
                precision={2}
                valueStyle={{ color: metrics.sharpeRatio > 1 ? '#3f8600' : '#8c8c8c' }}
                prefix={<TrophyOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card size="small">
              <Statistic
                title="最大回撤"
                value={metrics.maxDrawdown * 100}
                precision={2}
                suffix="%"
                valueStyle={{ color: getMetricColor(metrics.maxDrawdown, false) }}
                prefix={<FallOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card size="small">
              <Statistic
                title="胜率"
                value={metrics.winRate * 100}
                precision={1}
                suffix="%"
                valueStyle={{ color: metrics.winRate > 0.5 ? '#3f8600' : '#8c8c8c' }}
                prefix={<TrophyOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* Performance Chart */}
        <Card title="收益曲线" size="small">
          <Line
            {...{
              ...chartConfig,
              data: chartData,
            }}
            height={200}
          />
        </Card>

        {/* Detailed Metrics Table */}
        <Card title="详细指标" size="small">
          <Table
            dataSource={performanceTableData}
            pagination={false}
            size="small"
            columns={[
              {
                title: '指标',
                dataIndex: 'metric',
                key: 'metric',
                render: (text, record) => (
                  <div className="flex items-center gap-2">
                    {record.icon}
                    <span>{text}</span>
                  </div>
                ),
              },
              {
                title: '数值',
                dataIndex: 'value',
                key: 'value',
                align: 'right',
              },
              {
                title: '评级',
                dataIndex: 'level',
                key: 'level',
                render: (level) => (
                  <Tag color={level.color}>{level.text}</Tag>
                ),
              },
            ]}
          />
        </Card>
      </div>
    </WidgetContainer>
  )
}