/**
 * Backtest Results Widget - Displays backtesting results and analysis
 */

import React from 'react'
import { Row, Col, Card, Statistic, Table, Tag, Progress, DatePicker, Space } from 'antd'
import {
  HistoryOutlined,
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
  CalendarOutlined,
} from '@ant-design/icons'
import { Column } from '@ant-design/plots'
import { WidgetContainer } from '../Widget/WidgetContainer'

interface BacktestResultsProps {
  results?: {
    period: {
      start: string
      end: string
    }
    summary: {
      totalReturn: number
      annualizedReturn: number
      sharpeRatio: number
      maxDrawdown: number
      winRate: number
      totalTrades: number
      profitFactor: number
      avgWin: number
      avgLoss: number
    }
    monthlyReturns: Array<{
      month: string
      return: number
    }>
    topTrades: Array<{
      date: string
      symbol: string
      type: 'long' | 'short'
      entry: number
      exit: number
      profit: number
      profitPercent: number
    }>
  }
}

export const BacktestResults: React.FC<BacktestResultsProps> = ({
  results,
}) => {
  // Default mock data if none provided
  const backtestData = results || {
    period: {
      start: '2023-01-01',
      end: '2024-01-01',
    },
    summary: {
      totalReturn: 0.285,
      annualizedReturn: 0.285,
      sharpeRatio: 1.92,
      maxDrawdown: -0.125,
      winRate: 0.62,
      totalTrades: 156,
      profitFactor: 1.85,
      avgWin: 0.025,
      avgLoss: -0.015,
    },
    monthlyReturns: [
      { month: '2023-01', return: 0.025 },
      { month: '2023-02', return: -0.015 },
      { month: '2023-03', return: 0.035 },
      { month: '2023-04', return: 0.018 },
      { month: '2023-05', return: -0.008 },
      { month: '2023-06', return: 0.042 },
      { month: '2023-07', return: 0.028 },
      { month: '2023-08', return: -0.012 },
      { month: '2023-09', return: 0.038 },
      { month: '2023-10', return: 0.015 },
      { month: '2023-11', return: 0.022 },
      { month: '2023-12', return: 0.045 },
    ],
    topTrades: [
      {
        date: '2023-06-15',
        symbol: 'AAPL',
        type: 'long',
        entry: 175.25,
        exit: 195.80,
        profit: 20.55,
        profitPercent: 0.117,
      },
      {
        date: '2023-09-08',
        symbol: 'TSLA',
        type: 'short',
        entry: 275.40,
        exit: 245.20,
        profit: 30.20,
        profitPercent: 0.110,
      },
      {
        date: '2023-12-01',
        symbol: 'MSFT',
        type: 'long',
        entry: 378.50,
        exit: 405.25,
        profit: 26.75,
        profitPercent: 0.071,
      },
    ],
  }

  const monthlyReturnConfig = {
    data: backtestData.monthlyReturns.map(item => ({
      ...item,
      type: item.return >= 0 ? '盈利' : '亏损',
      value: Math.abs(item.return * 100),
    })),
    xField: 'month',
    yField: 'value',
    seriesField: 'type',
    columnWidthRatio: 0.8,
    meta: {
      value: {
        alias: '收益率 (%)',
      },
      month: {
        alias: '月份',
      },
    },
    color: ['#52c41a', '#ff4d4f'],
    legend: {
      custom: true,
      items: [
        { name: '盈利', value: '盈利', marker: { style: { fill: '#52c41a' } } },
        { name: '亏损', value: '亏损', marker: { style: { fill: '#ff4d4f' } } },
      ],
    },
  }

  const tradeColumns = [
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
      width: 100,
    },
    {
      title: '标的',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 80,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type: string) => (
        <Tag color={type === 'long' ? 'green' : 'red'}>
          {type === 'long' ? '做多' : '做空'}
        </Tag>
      ),
    },
    {
      title: '入场价',
      dataIndex: 'entry',
      key: 'entry',
      width: 80,
      render: (value: number) => `$${value.toFixed(2)}`,
    },
    {
      title: '出场价',
      dataIndex: 'exit',
      key: 'exit',
      width: 80,
      render: (value: number) => `$${value.toFixed(2)}`,
    },
    {
      title: '盈亏',
      dataIndex: 'profit',
      key: 'profit',
      width: 80,
      render: (value: number) => (
        <span className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
          ${value.toFixed(2)}
        </span>
      ),
    },
    {
      title: '收益率',
      dataIndex: 'profitPercent',
      key: 'profitPercent',
      width: 80,
      render: (value: number) => (
        <span className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
          {(value * 100).toFixed(2)}%
        </span>
      ),
    },
  ]

  return (
    <WidgetContainer
      id="backtest-results"
      type="backtest-results"
      title="回测结果"
      extra={
        <Space>
          <DatePicker.RangePicker size="small" />
          <Tag icon={<CalendarOutlined />}>
            {backtestData.period.start} 至 {backtestData.period.end}
          </Tag>
        </Space>
      }
    >
      <div className="space-y-4">
        {/* Summary Statistics */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card size="small">
              <Statistic
                title="总收益率"
                value={backtestData.summary.totalReturn * 100}
                precision={2}
                suffix="%"
                valueStyle={{ color: backtestData.summary.totalReturn > 0 ? '#3f8600' : '#cf1322' }}
                prefix={backtestData.summary.totalReturn > 0 ? <RiseOutlined /> : <FallOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card size="small">
              <Statistic
                title="夏普比率"
                value={backtestData.summary.sharpeRatio}
                precision={2}
                valueStyle={{ color: backtestData.summary.sharpeRatio > 1.5 ? '#3f8600' : '#8c8c8c' }}
                prefix={<TrophyOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card size="small">
              <Statistic
                title="胜率"
                value={backtestData.summary.winRate * 100}
                precision={1}
                suffix="%"
                valueStyle={{ color: backtestData.summary.winRate > 0.5 ? '#3f8600' : '#8c8c8c' }}
                prefix={<HistoryOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card size="small">
              <Statistic
                title="总交易次数"
                value={backtestData.summary.totalTrades}
                valueStyle={{ color: '#1890ff' }}
                prefix={<HistoryOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* Additional Metrics */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            <Card size="small" title="最大回撤">
              <Statistic
                value={backtestData.summary.maxDrawdown * 100}
                precision={2}
                suffix="%"
                valueStyle={{ color: '#ff4d4f' }}
                prefix={<FallOutlined />}
              />
              <Progress
                percent={Math.abs(backtestData.summary.maxDrawdown) * 100}
                showInfo={false}
                strokeColor="#ff4d4f"
                className="mt-2"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Card size="small" title="盈利因子">
              <Statistic
                value={backtestData.summary.profitFactor}
                precision={2}
                valueStyle={{ color: backtestData.summary.profitFactor > 1.5 ? '#3f8600' : '#8c8c8c' }}
              />
              <div className="text-xs text-gray-500 mt-2">
                平均盈利: {(backtestData.summary.avgWin * 100).toFixed(2)}%<br />
                平均亏损: {(backtestData.summary.avgLoss * 100).toFixed(2)}%
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Card size="small" title="年化收益率">
              <Statistic
                value={backtestData.summary.annualizedReturn * 100}
                precision={2}
                suffix="%"
                valueStyle={{ color: backtestData.summary.annualizedReturn > 0 ? '#3f8600' : '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Monthly Returns Chart */}
        <Card title="月度收益分布" size="small">
          <Column {...monthlyReturnConfig} height={200} />
        </Card>

        {/* Top Trades Table */}
        <Card title="最佳交易" size="small">
          <Table
            dataSource={backtestData.topTrades}
            columns={tradeColumns}
            pagination={false}
            size="small"
            scroll={{ x: true }}
          />
        </Card>
      </div>
    </WidgetContainer>
  )
}