import React, { useState, useEffect } from 'react'
import { Card, List, Progress, Tag, Button, Space, Statistic, Row, Col, Typography, Tooltip } from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  SettingOutlined,
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
  SyncOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'
import { useWebSocket } from '../../../hooks/useWebSocket'

const { Title, Text } = Typography

interface Strategy {
  id: string
  name: string
  status: 'active' | 'paused' | 'stopped'
  type: string
  performance: {
    totalReturn: number
    winRate: number
    sharpeRatio: number
    maxDrawdown: number
  }
  execution: {
    totalTrades: number
    successRate: number
    avgProfit: number
  }
  lastSignal?: string
  riskLevel: 'low' | 'medium' | 'high'
}

interface StrategyMonitorProps {
  config?: {
    refreshInterval?: number
    showPerformance?: boolean
    showExecution?: boolean
    maxStrategies?: number
  }
  isMinimized?: boolean
  isMaximized?: boolean
  onConfigChange?: (config: any) => void
}

const StrategyMonitor: React.FC<StrategyMonitorProps> = ({
  config = {},
  isMinimized = false,
  isMaximized = false,
  onConfigChange
}) => {
  const [strategies, setStrategies] = useState<Strategy[]>([
    {
      id: '1',
      name: 'RSI Mean Reversion',
      status: 'active',
      type: 'Technical',
      performance: {
        totalReturn: 15.8,
        winRate: 65.2,
        sharpeRatio: 1.45,
        maxDrawdown: -8.3,
      },
      execution: {
        totalTrades: 142,
        successRate: 65.2,
        avgProfit: 1.12,
      },
      lastSignal: 'BUY - 2 min ago',
      riskLevel: 'medium',
    },
    {
      id: '2',
      name: 'MACD Momentum',
      status: 'active',
      type: 'Momentum',
      performance: {
        totalReturn: 24.2,
        winRate: 58.7,
        sharpeRatio: 1.78,
        maxDrawdown: -12.5,
      },
      execution: {
        totalTrades: 89,
        successRate: 58.7,
        avgProfit: 2.87,
      },
      lastSignal: 'HOLD - 15 min ago',
      riskLevel: 'high',
    },
    {
      id: '3',
      name: 'Sentiment Analysis',
      status: 'paused',
      type: 'Sentiment',
      performance: {
        totalReturn: 8.9,
        winRate: 72.1,
        sharpeRatio: 0.95,
        maxDrawdown: -4.2,
      },
      execution: {
        totalTrades: 67,
        successRate: 72.1,
        avgProfit: 0.89,
      },
      lastSignal: 'SELL - 1 hour ago',
      riskLevel: 'low',
    },
  ])

  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null)
  const { isConnected } = useWebSocket()

  const {
    refreshInterval = 5000,
    showPerformance = true,
    showExecution = true,
    maxStrategies = 10
  } = config

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setStrategies(prev => prev.map(strategy => {
        if (strategy.status === 'active') {
          // Randomly update performance metrics slightly
          const performanceChange = (Math.random() - 0.5) * 0.5
          return {
            ...strategy,
            performance: {
              ...strategy.performance,
              totalReturn: Math.max(-100, strategy.performance.totalReturn + performanceChange),
            },
          }
        }
        return strategy
      }))
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [refreshInterval])

  const getStatusIcon = (status: Strategy['status']) => {
    switch (status) {
      case 'active':
        return <PlayCircleOutlined className="text-green-500" />
      case 'paused':
        return <PauseCircleOutlined className="text-yellow-500" />
      case 'stopped':
        return <PauseCircleOutlined className="text-red-500" />
    }
  }

  const getStatusColor = (status: Strategy['status']) => {
    switch (status) {
      case 'active':
        return 'success'
      case 'paused':
        return 'warning'
      case 'stopped':
        return 'error'
    }
  }

  const getRiskColor = (level: Strategy['riskLevel']) => {
    switch (level) {
      case 'low':
        return 'green'
      case 'medium':
        return 'orange'
      case 'high':
        return 'red'
    }
  }

  if (isMinimized) {
    return null
  }

  return (
    <div className="h-full w-full flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <Title level={5} className="!mb-1 flex items-center gap-2">
            Strategy Monitor
            <Tooltip title="Monitor your trading strategies in real-time">
              <InfoCircleOutlined className="text-gray-400 text-sm" />
            </Tooltip>
          </Title>
          <Text type="secondary" className="text-xs">
            {strategies.filter(s => s.status === 'active').length} active strategies
          </Text>
        </div>
        <Space>
          <Tag color={isConnected ? 'success' : 'error'} className="text-xs">
            {isConnected ? 'Live' : 'Offline'}
          </Tag>
          <Button
            type="text"
            size="small"
            icon={<SettingOutlined />}
            onClick={() => console.log('Strategy settings')}
          />
        </Space>
      </div>

      {/* Summary Stats */}
      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={24} sm={8}>
          <Statistic
            title="Active Strategies"
            value={strategies.filter(s => s.status === 'active').length}
            prefix={<PlayCircleOutlined />}
            valueStyle={{ fontSize: isMaximized ? '20px' : '16px' }}
          />
        </Col>
        <Col xs={24} sm={8}>
          <Statistic
            title="Avg Return"
            value={strategies.reduce((sum, s) => sum + s.performance.totalReturn, 0) / strategies.length}
            precision={2}
            suffix="%"
            prefix={strategies.reduce((sum, s) => sum + s.performance.totalReturn, 0) / strategies.length > 0 ?
              <RiseOutlined /> : <FallOutlined />}
            valueStyle={{
              fontSize: isMaximized ? '20px' : '16px',
              color: strategies.reduce((sum, s) => sum + s.performance.totalReturn, 0) / strategies.length > 0 ?
                '#3f8600' : '#cf1322'
            }}
          />
        </Col>
        <Col xs={24} sm={8}>
          <Statistic
            title="Total Trades"
            value={strategies.reduce((sum, s) => sum + s.execution.totalTrades, 0)}
            prefix={<TrophyOutlined />}
            valueStyle={{ fontSize: isMaximized ? '20px' : '16px' }}
          />
        </Col>
      </Row>

      {/* Strategy List */}
      <div className="flex-1 overflow-auto">
        <List
          size="small"
          dataSource={strategies.slice(0, maxStrategies)}
          renderItem={(strategy) => (
            <List.Item
              className={`cursor-pointer transition-colors hover:bg-gray-50 ${
                selectedStrategy === strategy.id ? 'bg-blue-50' : ''
              }`}
              onClick={() => setSelectedStrategy(strategy.id === selectedStrategy ? null : strategy.id)}
            >
              <List.Item.Meta
                avatar={getStatusIcon(strategy.status)}
                title={
                  <div className="flex justify-between items-center">
                    <Space>
                      <Text strong>{strategy.name}</Text>
                      <Tag size="small">{strategy.type}</Tag>
                      <Tag size="small" color={getRiskColor(strategy.riskLevel)}>
                        {strategy.riskLevel}
                      </Tag>
                    </Space>
                    <Tag size="small" color={getStatusColor(strategy.status)}>
                      {strategy.status}
                    </Tag>
                  </div>
                }
                description={
                  <div className="space-y-2">
                    {/* Performance Metrics */}
                    {showPerformance && (
                      <Row gutter={[8, 8]}>
                        <Col span={6}>
                          <div>
                            <Text type="secondary" className="text-xs">Return</Text>
                            <div className={`font-semibold text-xs ${
                              strategy.performance.totalReturn > 0 ? 'text-green-500' : 'text-red-500'
                            }`}>
                              {strategy.performance.totalReturn > 0 ? '+' : ''}{strategy.performance.totalReturn.toFixed(2)}%
                            </div>
                          </div>
                        </Col>
                        <Col span={6}>
                          <div>
                            <Text type="secondary" className="text-xs">Win Rate</Text>
                            <div className="font-semibold text-xs">
                              {strategy.performance.winRate.toFixed(1)}%
                            </div>
                          </div>
                        </Col>
                        <Col span={6}>
                          <div>
                            <Text type="secondary" className="text-xs">Sharpe</Text>
                            <div className="font-semibold text-xs">
                              {strategy.performance.sharpeRatio.toFixed(2)}
                            </div>
                          </div>
                        </Col>
                        <Col span={6}>
                          <div>
                            <Text type="secondary" className="text-xs">Max DD</Text>
                            <div className="font-semibold text-xs text-red-500">
                              {strategy.performance.maxDrawdown.toFixed(2)}%
                            </div>
                          </div>
                        </Col>
                      </Row>
                    )}

                    {/* Execution Metrics */}
                    {showExecution && (
                      <Row gutter={[8, 8]}>
                        <Col span={8}>
                          <div>
                            <Text type="secondary" className="text-xs">Trades</Text>
                            <div className="font-semibold text-xs">
                              {strategy.execution.totalTrades}
                            </div>
                          </div>
                        </Col>
                        <Col span={8}>
                          <div>
                            <Text type="secondary" className="text-xs">Success Rate</Text>
                            <Progress
                              percent={strategy.execution.successRate}
                              size="small"
                              showInfo={false}
                              strokeColor={strategy.execution.successRate > 60 ? '#52c41a' : '#faad14'}
                            />
                          </div>
                        </Col>
                        <Col span={8}>
                          <div>
                            <Text type="secondary" className="text-xs">Avg Profit</Text>
                            <div className={`font-semibold text-xs ${
                              strategy.execution.avgProfit > 0 ? 'text-green-500' : 'text-red-500'
                            }`}>
                              {strategy.execution.avgProfit > 0 ? '+' : ''}{strategy.execution.avgProfit.toFixed(2)}%
                            </div>
                          </div>
                        </Col>
                      </Row>
                    )}

                    {/* Last Signal */}
                    {strategy.lastSignal && (
                      <div className="flex items-center gap-2">
                        <SyncOutlined className="text-blue-500 text-xs" />
                        <Text type="secondary" className="text-xs">
                          {strategy.lastSignal}
                        </Text>
                      </div>
                    )}
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </div>
    </div>
  )
}

export default StrategyMonitor