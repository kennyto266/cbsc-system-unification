import React, { useState, useEffect } from 'react'
import { Card, Statistic, Row, Col, Progress, Tag, Space, Typography, Button, Tooltip } from 'antd'
import {
  RiseOutlined,
  FallOutlined,
  DollarOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'
import { useWebSocket } from '../../../hooks/useWebSocket'

const { Title, Text } = Typography

interface MarketOverviewProps {
  config?: {
    refreshInterval?: number
    showDetails?: boolean
    markets?: string[]
  }
  isMinimized?: boolean
  isMaximized?: boolean
  onConfigChange?: (config: any) => void
}

const MarketOverview: React.FC<MarketOverviewProps> = ({
  config = {},
  isMinimized = false,
  isMaximized = false,
  onConfigChange
}) => {
  const [marketData, setMarketData] = useState({
    totalMarketCap: 2850000000000,
    marketCapChange: 2.34,
    totalVolume: 125000000000,
    volumeChange: -1.56,
    btcDominance: 48.5,
    ethDominance: 18.2,
    fearGreedIndex: 72,
    fearGreedChange: 5,
  })

  const [lastUpdate, setLastUpdate] = useState(new Date())
  const { isConnected } = useWebSocket()

  const {
    refreshInterval = 30000,
    showDetails = true,
    markets = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA']
  } = config

  // Simulate real-time data updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMarketData(prev => ({
        ...prev,
        totalMarketCap: prev.totalMarketCap * (1 + (Math.random() - 0.5) * 0.002),
        marketCapChange: prev.marketCapChange + (Math.random() - 0.5) * 0.5,
        totalVolume: prev.totalVolume * (1 + (Math.random() - 0.5) * 0.01),
        volumeChange: prev.volumeChange + (Math.random() - 0.5) * 0.8,
        btcDominance: Math.max(0, Math.min(100, prev.btcDominance + (Math.random() - 0.5) * 0.5)),
        fearGreedIndex: Math.max(0, Math.min(100, prev.fearGreedIndex + (Math.random() - 0.5) * 3)),
      }))
      setLastUpdate(new Date())
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [refreshInterval])

  const formatNumber = (num: number, currency = '') => {
    if (num >= 1e12) return `${currency}${(num / 1e12).toFixed(2)}T`
    if (num >= 1e9) return `${currency}${(num / 1e9).toFixed(2)}B`
    if (num >= 1e6) return `${currency}${(num / 1e6).toFixed(2)}M`
    if (num >= 1e3) return `${currency}${(num / 1e3).toFixed(2)}K`
    return `${currency}${num.toFixed(2)}`
  }

  const getFearGreedColor = (index: number) => {
    if (index < 25) return '#ff4d4f'
    if (index < 45) return '#faad14'
    if (index < 55) return '#faad14'
    if (index < 75) return '#52c41a'
    return '#52c41a'
  }

  const getFearGreedText = (index: number) => {
    if (index < 25) return 'Extreme Fear'
    if (index < 45) return 'Fear'
    if (index < 55) return 'Neutral'
    if (index < 75) return 'Greed'
    return 'Extreme Greed'
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
            Market Overview
            <Tooltip title="Real-time market data">
              <InfoCircleOutlined className="text-gray-400 text-sm" />
            </Tooltip>
          </Title>
          <Text type="secondary" className="text-xs">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </Text>
        </div>
        <Space>
          <Tag color={isConnected ? 'success' : 'error'} className="text-xs">
            {isConnected ? 'Live' : 'Offline'}
          </Tag>
          <Button
            type="text"
            size="small"
            icon={<ReloadOutlined />}
            onClick={() => setLastUpdate(new Date())}
          />
        </Space>
      </div>

      {/* Market Cap & Volume */}
      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={24} sm={12}>
          <Card size="small" className="h-full">
            <Statistic
              title="Market Cap"
              value={marketData.totalMarketCap}
              formatter={(value) => formatNumber(value as number, '$')}
              precision={2}
              valueStyle={{
                fontSize: isMaximized ? '24px' : '18px',
                color: marketData.marketCapChange > 0 ? '#3f8600' : '#cf1322',
              }}
              prefix={
                marketData.marketCapChange > 0 ? <RiseOutlined /> : <FallOutlined />
              }
              suffix={
                <Text type={marketData.marketCapChange > 0 ? 'success' : 'danger'} className="text-xs ml-2">
                  {marketData.marketCapChange > 0 ? '+' : ''}{marketData.marketCapChange.toFixed(2)}%
                </Text>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12}>
          <Card size="small" className="h-full">
            <Statistic
              title="24h Volume"
              value={marketData.totalVolume}
              formatter={(value) => formatNumber(value as number, '$')}
              precision={2}
              valueStyle={{
                fontSize: isMaximized ? '24px' : '18px',
                color: marketData.volumeChange > 0 ? '#3f8600' : '#cf1322',
              }}
              prefix={
                marketData.volumeChange > 0 ? <RiseOutlined /> : <FallOutlined />
              }
              suffix={
                <Text type={marketData.volumeChange > 0 ? 'success' : 'danger'} className="text-xs ml-2">
                  {marketData.volumeChange > 0 ? '+' : ''}{marketData.volumeChange.toFixed(2)}%
                </Text>
              }
            />
          </Card>
        </Col>
      </Row>

      {/* Dominance & Fear & Greed */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12}>
          <Card size="small" title="Dominance">
            <Space direction="vertical" className="w-full">
              <div className="flex justify-between items-center">
                <Text>BTC Dominance</Text>
                <Text strong>{marketData.btcDominance.toFixed(1)}%</Text>
              </div>
              <Progress
                percent={marketData.btcDominance}
                strokeColor="#f7931a"
                size="small"
                showInfo={false}
              />
              <div className="flex justify-between items-center">
                <Text>ETH Dominance</Text>
                <Text strong>{marketData.ethDominance.toFixed(1)}%</Text>
              </div>
              <Progress
                percent={marketData.ethDominance}
                strokeColor="#627eea"
                size="small"
                showInfo={false}
              />
            </Space>
          </Card>
        </Col>
        <Col xs={24} sm={12}>
          <Card size="small" title="Fear & Greed Index">
            <div className="text-center">
              <div
                className="text-2xl font-bold mb-2"
                style={{ color: getFearGreedColor(marketData.fearGreedIndex) }}
              >
                {marketData.fearGreedIndex}
              </div>
              <Progress
                percent={marketData.fearGreedIndex}
                strokeColor={getFearGreedColor(marketData.fearGreedIndex)}
                size="small"
                showInfo={false}
              />
              <Text className="text-sm text-gray-500 mt-1 block">
                {getFearGreedText(marketData.fearGreedIndex)}
              </Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Additional Details */}
      {showDetails && markets.length > 0 && (
        <Card size="small" title="Top Markets" className="mt-4">
          <Row gutter={[8, 8]}>
            {markets.map((market) => (
              <Col key={market} xs={8} sm={6} md={4}>
                <div className="text-center">
                  <Text strong>{market}</Text>
                  <div className="text-xs text-gray-500">
                    ${(Math.random() * 100000).toFixed(2)}
                  </div>
                  <div className={`text-xs ${(Math.random() > 0.5) ? 'text-green-500' : 'text-red-500'}`}>
                    {(Math.random() > 0.5 ? '+' : '-')}{(Math.random() * 10).toFixed(2)}%
                  </div>
                </div>
              </Col>
            ))}
          </Row>
        </Card>
      )}
    </div>
  )
}

export default MarketOverview