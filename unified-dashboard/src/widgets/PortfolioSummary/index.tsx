import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Progress, Pie, Tooltip, Typography, Space } from 'antd'
import {
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  TrophyOutlined,
  PieChartOutlined
} from '@ant-design/icons'
import { PieConfig } from '@ant-design/plots'

const { Title, Text } = Typography

interface Asset {
  name: string
  value: number
  percentage: number
  change: number
}

interface PortfolioData {
  totalValue: number
  totalReturn: number
  dailyChange: number
  dailyChangePercent: number
  assets: Asset[]
  allocation: {
    stocks: number
    crypto: number
    bonds: number
    cash: number
  }
}

interface PortfolioSummaryProps {
  config?: {
    refreshInterval?: number
    showAllocation?: boolean
    showAssets?: boolean
    currency?: string
  }
  isMinimized?: boolean
  isMaximized?: boolean
  onConfigChange?: (config: any) => void
}

const PortfolioSummary: React.FC<PortfolioSummaryProps> = ({
  config = {},
  isMinimized = false,
  isMaximized = false,
  onConfigChange
}) => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData>({
    totalValue: 1250000,
    totalReturn: 18.5,
    dailyChange: 15420,
    dailyChangePercent: 1.24,
    assets: [
      { name: 'Bitcoin', value: 450000, percentage: 36, change: 2.5 },
      { name: 'Ethereum', value: 280000, percentage: 22.4, change: 3.2 },
      { name: 'Stocks', value: 320000, percentage: 25.6, change: -0.8 },
      { name: 'Bonds', value: 150000, percentage: 12, change: 0.3 },
      { name: 'Cash', value: 50000, percentage: 4, change: 0 },
    ],
    allocation: {
      stocks: 45,
      crypto: 40,
      bonds: 10,
      cash: 5,
    }
  })

  const {
    refreshInterval = 10000,
    showAllocation = true,
    showAssets = true,
    currency = 'USD'
  } = config

  // Simulate real-time portfolio updates
  useEffect(() => {
    const interval = setInterval(() => {
      setPortfolioData(prev => {
        const changeAmount = (Math.random() - 0.5) * 5000
        const newTotalValue = prev.totalValue + changeAmount
        const dailyChangePercent = (changeAmount / prev.totalValue) * 100

        return {
          ...prev,
          totalValue: newTotalValue,
          dailyChange: prev.dailyChange + changeAmount,
          dailyChangePercent: dailyChangePercent,
          assets: prev.assets.map(asset => ({
            ...asset,
            value: asset.value * (1 + (Math.random() - 0.5) * 0.01),
            change: asset.change + (Math.random() - 0.5) * 0.5,
          })),
        }
      })
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [refreshInterval])

  const formatCurrency = (value: number) => {
    const currencySymbol = currency === 'USD' ? '$' : currency === 'EUR' ? '€' : '¥'
    if (value >= 1e9) return `${currencySymbol}${(value / 1e9).toFixed(2)}B`
    if (value >= 1e6) return `${currencySymbol}${(value / 1e6).toFixed(2)}M`
    if (value >= 1e3) return `${currencySymbol}${(value / 1e3).toFixed(2)}K`
    return `${currencySymbol}${value.toFixed(2)}`
  }

  // Pie chart configuration
  const pieConfig: PieConfig = {
    data: portfolioData.assets.map(asset => ({
      type: asset.name,
      value: asset.value,
    })),
    angleField: 'value',
    colorField: 'type',
    radius: isMaximized ? 0.8 : 0.6,
    label: {
      type: 'outer',
      content: '{name} {percentage}',
    },
    interactions: [
      {
        type: 'pie-legend-active',
      },
      {
        type: 'element-active',
      },
    ],
    animation: true,
  }

  return (
    <div className="h-full w-full flex flex-col">
      {/* Header */}
      <div className="mb-4">
        <Title level={5} className="!mb-1">
          Portfolio Summary
        </Title>
        <Text type="secondary" className="text-xs">
          Total portfolio value and performance
        </Text>
      </div>

      {/* Portfolio Value & Returns */}
      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={24} sm={12}>
          <Card size="small" className="h-full">
            <Statistic
              title="Total Value"
              value={portfolioData.totalValue}
              formatter={(value) => formatCurrency(value as number)}
              precision={0}
              valueStyle={{
                fontSize: isMaximized ? '28px' : '20px',
                color: '#3f8600',
              }}
              prefix={<DollarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12}>
          <Card size="small" className="h-full">
            <div className="space-y-2">
              <Statistic
                title="Daily Change"
                value={portfolioData.dailyChange}
                formatter={(value) => formatCurrency(value as number)}
                precision={2}
                valueStyle={{
                  fontSize: '16px',
                  color: portfolioData.dailyChangePercent > 0 ? '#3f8600' : '#cf1322',
                }}
                prefix={
                  portfolioData.dailyChangePercent > 0 ? <RiseOutlined /> : <FallOutlined />
                }
              />
              <Statistic
                title="Total Return"
                value={portfolioData.totalReturn}
                precision={2}
                suffix="%"
                valueStyle={{
                  fontSize: '16px',
                  color: portfolioData.totalReturn > 0 ? '#3f8600' : '#cf1322',
                }}
                prefix={
                  portfolioData.totalReturn > 0 ? <TrophyOutlined /> : <FallOutlined />
                }
              />
            </div>
          </Card>
        </Col>
      </Row>

      {/* Asset Allocation */}
      {showAllocation && (
        <Card size="small" title="Asset Allocation" className="mb-4 flex-1">
          <Row gutter={[16, 16]}>
            <Col xs={24} md={isMaximized ? 12 : 24}>
              <div className="h-48">
                <Pie {...pieConfig} />
              </div>
            </Col>
            <Col xs={24} md={isMaximized ? 12 : 24}>
              <Space direction="vertical" className="w-full">
                {Object.entries(portfolioData.allocation).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between">
                    <Text className="capitalize">{key}</Text>
                    <div className="flex items-center gap-2 flex-1 max-w-[200px]">
                      <Progress
                        percent={value}
                        size="small"
                        showInfo={false}
                        strokeColor={
                          key === 'crypto' ? '#f7931a' :
                          key === 'stocks' ? '#1890ff' :
                          key === 'bonds' ? '#52c41a' : '#faad14'
                        }
                      />
                      <Text className="text-xs w-12 text-right">{value}%</Text>
                    </div>
                  </div>
                ))}
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      {/* Top Assets */}
      {showAssets && (
        <Card size="small" title="Top Assets" className="flex-1">
          <div className="space-y-3">
            {portfolioData.assets.slice(0, isMaximized ? 10 : 5).map((asset, index) => (
              <div key={asset.name} className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white text-xs font-bold">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-center">
                      <Text strong className="text-sm">{asset.name}</Text>
                      <Space>
                        <Text className="text-sm">{formatCurrency(asset.value)}</Text>
                        <Text className={`text-xs ${
                          asset.change > 0 ? 'text-green-500' : 'text-red-500'
                        }`}>
                          {asset.change > 0 ? '+' : ''}{asset.change.toFixed(2)}%
                        </Text>
                      </Space>
                    </div>
                    <Progress
                      percent={asset.percentage}
                      size="small"
                      showInfo={false}
                      strokeColor="#1890ff"
                      className="mt-1"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Performance Summary */}
      {!isMinimized && (
        <Row gutter={[16, 16]} className="mt-4">
          <Col xs={24} sm={8}>
            <Card size="small">
              <Statistic
                title="Best Performer"
                value={portfolioData.assets.reduce((best, asset) =>
                  asset.change > best.change ? asset : best
                ).name}
                valueStyle={{ fontSize: '14px' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card size="small">
              <Statistic
                title="Worst Performer"
                value={portfolioData.assets.reduce((worst, asset) =>
                  asset.change < worst.change ? asset : worst
                ).name}
                valueStyle={{ fontSize: '14px' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card size="small">
              <Statistic
                title="Total Assets"
                value={portfolioData.assets.length}
                prefix={<PieChartOutlined />}
                valueStyle={{ fontSize: '14px' }}
              />
            </Card>
          </Col>
        </Row>
      )}
    </div>
  )
}

export default PortfolioSummary