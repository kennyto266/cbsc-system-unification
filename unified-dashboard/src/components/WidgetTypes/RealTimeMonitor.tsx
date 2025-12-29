/**
 * Real Time Monitor Widget - Displays real-time market and strategy monitoring
 */

import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Table, Tag, Statistic, Alert, Progress, List, Avatar } from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  FireOutlined,
  StockOutlined,
} from '@ant-design/icons'
import { Line } from '@ant-design/plots'
import { WidgetContainer } from '../Widget/WidgetContainer'
import { useWebSocket } from '../../hooks/useWebSocket'

interface RealTimeMonitorProps {
  symbols?: string[]
  strategies?: Array<{
    id: string
    name: string
    status: 'running' | 'paused' | 'stopped'
    lastSignal: {
      time: string
      type: 'buy' | 'sell' | 'hold'
      symbol: string
      price: number
    }
  }>
}

export const RealTimeMonitor: React.FC<RealTimeMonitorProps> = ({
  symbols = ['BTC/USDT', 'ETH/USDT', 'AAPL', 'TSLA'],
  strategies = [],
}) => {
  const { isConnected, lastMessage } = useWebSocket()
  const [marketData, setMarketData] = useState<any[]>([])
  const [alerts, setAlerts] = useState<any[]>([])

  // Simulate real-time data updates
  useEffect(() => {
    const generateRandomPrice = (base: number) => {
      return base + (Math.random() - 0.5) * base * 0.001
    }

    const initialData = symbols.map(symbol => ({
      symbol,
      price: Math.random() * 1000 + 100,
      change: (Math.random() - 0.5) * 0.02,
      volume: Math.random() * 1000000,
    }))
    setMarketData(initialData)

    const interval = setInterval(() => {
      setMarketData(prev =>
        prev.map(item => ({
          ...item,
          price: generateRandomPrice(item.price),
          change: (Math.random() - 0.5) * 0.02,
          volume: Math.random() * 1000000,
        }))
      )

      // Simulate random alerts
      if (Math.random() > 0.8) {
        const randomSymbol = symbols[Math.floor(Math.random() * symbols.length)]
        const alertTypes = ['价格突破', '成交量异常', '波动率预警', '趋势反转']
        const randomAlert = alertTypes[Math.floor(Math.random() * alertTypes.length)]

        setAlerts(prev => [
          {
            id: Date.now(),
            time: new Date().toLocaleTimeString(),
            symbol: randomSymbol,
            type: randomAlert,
            level: Math.random() > 0.5 ? 'warning' : 'info',
          },
          ...prev.slice(0, 4), // Keep only 5 recent alerts
        ])
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [symbols])

  // Generate price history for chart
  const priceHistory = marketData[0] ? Array.from({ length: 50 }, (_, i) => ({
    time: new Date(Date.now() - (49 - i) * 1000).toLocaleTimeString(),
    value: generateRandomPrice(marketData[0].price),
  })) : []

  const priceChartConfig = {
    data: priceHistory,
    xField: 'time',
    yField: 'value',
    smooth: true,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    color: '#1890ff',
    tooltip: {
      formatter: (datum: any) => ({
        name: '价格',
        value: `$${datum.value.toFixed(2)}`,
      }),
    },
  }

  const marketColumns = [
    {
      title: '标的',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      render: (value: number) => `$${value.toFixed(2)}`,
    },
    {
      title: '涨跌幅',
      dataIndex: 'change',
      key: 'change',
      width: 100,
      render: (value: number) => (
        <span className={value > 0 ? 'text-green-600' : 'text-red-600'}>
          {value > 0 ? '+' : ''}{(value * 100).toFixed(2)}%
        </span>
      ),
    },
    {
      title: '成交量',
      dataIndex: 'volume',
      key: 'volume',
      width: 120,
      render: (value: number) => (value / 1000000).toFixed(2) + 'M',
    },
  ]

  const strategyColumns = [
    {
      title: '策略',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          running: { color: 'success', text: '运行中', icon: <PlayCircleOutlined /> },
          paused: { color: 'warning', text: '已暂停', icon: <PauseCircleOutlined /> },
          stopped: { color: 'default', text: '已停止', icon: <PauseCircleOutlined /> },
        }
        const config = statusConfig[status as keyof typeof statusConfig]
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        )
      },
    },
    {
      title: '最新信号',
      dataIndex: 'lastSignal',
      key: 'lastSignal',
      render: (signal: any) => (
        <div className="text-xs">
          <div className="font-semibold">{signal.symbol}</div>
          <div className="text-gray-500">{signal.time}</div>
          <Tag
            color={signal.type === 'buy' ? 'green' : signal.type === 'sell' ? 'red' : 'default'}
            size="small"
          >
            {signal.type.toUpperCase()} @ ${signal.price.toFixed(2)}
          </Tag>
        </div>
      ),
    },
  ]

  const alertItemRender = (item: any) => (
    <List.Item>
      <List.Item.Meta
        avatar={
          <Avatar
            icon={
              item.level === 'warning' ? (
                <WarningOutlined style={{ color: '#faad14' }} />
              ) : (
                <CheckCircleOutlined style={{ color: '#52c41a' }} />
              )
            }
          />
        }
        title={
          <div className="flex items-center justify-between">
            <span>{item.type}</span>
            <span className="text-xs text-gray-500">{item.time}</span>
          </div>
        }
        description={item.symbol}
      />
    </List.Item>
  )

  return (
    <WidgetContainer
      id="real-time-monitor"
      type="real-time-monitor"
      title="实时监控"
      extra={
        <Tag color={isConnected ? 'success' : 'error'} icon={isConnected ? <CheckCircleOutlined /> : <WarningOutlined />}>
          {isConnected ? '已连接' : '未连接'}
        </Tag>
      }
    >
      <div className="space-y-4">
        {/* Connection Status */}
        {!isConnected && (
          <Alert
            message="WebSocket连接已断开"
            description="实时数据可能无法更新，请检查网络连接"
            type="warning"
            showIcon
            closable
          />
        )}

        {/* Quick Stats */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="监控标的"
              value={marketData.length}
              prefix={<StockOutlined />}
              suffix="个"
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="活跃策略"
              value={strategies.filter(s => s.status === 'running').length}
              prefix={<PlayCircleOutlined />}
              suffix="个"
              valueStyle={{ color: '#3f8600' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="今日预警"
              value={alerts.length}
              prefix={<WarningOutlined />}
              suffix="条"
              valueStyle={{ color: '#faad14' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="更新时间"
              value={new Date().toLocaleTimeString()}
              prefix={<ClockCircleOutlined />}
            />
          </Col>
        </Row>

        {/* Price Chart */}
        <Card title="实时价格" size="small">
          <Line {...priceChartConfig} height={200} />
        </Card>

        {/* Market Data Table */}
        <Card title="市场数据" size="small">
          <Table
            dataSource={marketData}
            columns={marketColumns}
            pagination={false}
            size="small"
            scroll={{ x: true }}
          />
        </Card>

        {/* Strategy Status */}
        <Card title="策略状态" size="small">
          <Table
            dataSource={strategies}
            columns={strategyColumns}
            pagination={false}
            size="small"
          />
        </Card>

        {/* Alerts */}
        <Card title="最新预警" size="small">
          <List
            dataSource={alerts}
            renderItem={alertItemRender}
            size="small"
          />
        </Card>
      </div>
    </WidgetContainer>
  )
}