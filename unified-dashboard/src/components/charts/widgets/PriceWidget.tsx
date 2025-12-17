import React, { useMemo, useCallback } from 'react'
import { Card, Statistic, Typography, Space, Tag } from 'antd'
import {
  RiseOutlined,
  FallOutlined,
  MinusOutlined,
  ClockCircleOutlined,
  DollarOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import { chartUtils } from '../../utils/charts'
import { useRealTimeData } from '../../hooks'

const { Text } = Typography

export interface PriceData {
  price: number
  change: number
  changePercent: number
  high: number
  low: number
  volume: number
  timestamp: string | Date
  symbol: string
}

export interface PriceWidgetProps {
  symbol: string
  price: number
  change: number
  changePercent: number
  high?: number
  low?: number
  volume?: number
  open?: number
  previousClose?: number
  marketCap?: number
  currency?: string
  showSparkline?: boolean
  sparklineData?: Array<{ timestamp: string | Date; value: number }>
  showDetails?: boolean
  compact?: boolean
  size?: 'small' | 'default' | 'large'
  theme?: 'light' | 'dark'
  realTime?: boolean
  updateInterval?: number
  onClick?: () => void
  className?: string
}

const PriceWidget: React.FC<PriceWidgetProps> = ({
  symbol,
  price,
  change,
  changePercent,
  high,
  low,
  volume,
  open,
  previousClose,
  marketCap,
  currency = 'USD',
  showSparkline = true,
  sparklineData = [],
  showDetails = true,
  compact = false,
  size = 'default',
  theme = 'light',
  realTime = false,
  updateInterval = 5000,
  onClick,
  className,
}) => {
  const [hovered, setHovered] = useState(false)

  // Real-time data subscription
  const { data: realTimeData, isConnected } = useRealTimeData(
    realTime ? `price-${symbol}` : null,
    updateInterval
  )

  // Use real-time data if available
  const currentPrice = realTimeData?.price || price
  const currentChange = realTimeData?.change || change
  const currentChangePercent = realTimeData?.changePercent || changePercent

  // Determine change color and icon
  const changeInfo = useMemo(() => {
    if (currentChange > 0) {
      return {
        color: '#52c41a',
        icon: <RiseOutlined />,
        text: 'Up',
      }
    } else if (currentChange < 0) {
      return {
        color: '#f5222d',
        icon: <FallOutlined />,
        text: 'Down',
      }
    } else {
      return {
        color: '#8c8c8c',
        icon: <MinusOutlined />,
        text: 'Unchanged',
      }
    }
  }, [currentChange])

  // Format price
  const formattedPrice = useMemo(() => {
    return chartUtils.formatCurrency(currentPrice, currency)
  }, [currentPrice, currency])

  // Calculate price range for sparkline
  const priceRange = useMemo(() => {
    if (!showSparkline || sparklineData.length === 0) return null

    const prices = sparklineData.map(d => d.value)
    const min = Math.min(...prices)
    const max = Math.max(...prices)
    const range = max - min

    return { min, max, range }
  }, [showSparkline, sparklineData])

  // Generate sparkline path
  const sparklinePath = useMemo(() => {
    if (!priceRange || sparklineData.length === 0) return ''

    const width = 100
    const height = 30
    const padding = 2

    const xScale = (width - 2 * padding) / (sparklineData.length - 1)
    const yScale = (height - 2 * padding) / priceRange.range

    const points = sparklineData.map((point, index) => {
      const x = padding + index * xScale
      const y = height - padding - (point.value - priceRange.min) * yScale
      return `${x},${y}`
    })

    return `M${points.join(' L')}`
  }, [priceRange, sparklineData])

  // Component size configurations
  const sizeConfig = useMemo(() => {
    switch (size) {
      case 'small':
        return {
          title: 16,
          price: 20,
          change: 12,
          details: 10,
          sparklineHeight: 20,
        }
      case 'large':
        return {
          title: 20,
          price: 32,
          change: 16,
          details: 12,
          sparklineHeight: 40,
        }
      default:
        return {
          title: 18,
          price: 24,
          change: 14,
          details: 11,
          sparklineHeight: 30,
        }
    }
  }, [size])

  return (
    <Card
      className={`price-widget ${compact ? 'compact' : ''} ${className || ''}`}
      size={size}
      hoverable={!!onClick}
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      bodyStyle={{ padding: compact ? '12px' : '16px' }}
    >
      <div className="price-widget-content">
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <Typography.Title
              level={5}
              style={{ margin: 0, fontSize: sizeConfig.title }}
            >
              {symbol}
            </Typography.Title>
            {realTime && (
              <Tag
                color={isConnected ? 'green' : 'red'}
                size="small"
                icon={<ClockCircleOutlined />}
              >
                {isConnected ? 'Live' : 'Offline'}
              </Tag>
            )}
          </div>
          <DollarOutlined style={{ color: '#1890ff' }} />
        </div>

        {/* Price */}
        <div className="flex items-baseline space-x-3 mb-3">
          <Statistic
            value={currentPrice}
            precision={2}
            prefix={currency}
            valueStyle={{
              fontSize: sizeConfig.price,
              fontWeight: 'bold',
              color: theme === 'dark' ? '#fff' : '#000',
            }}
          />
          <div className="flex items-center space-x-1">
            {changeInfo.icon}
            <Text
              style={{
                color: changeInfo.color,
                fontSize: sizeConfig.change,
                fontWeight: 500,
              }}
            >
              {currentChange > 0 ? '+' : ''}
              {currentChange.toFixed(2)} ({currentChangePercent.toFixed(2)}%)
            </Text>
          </div>
        </div>

        {/* Sparkline */}
        {showSparkline && sparklinePath && (
          <div className="mb-3">
            <svg
              width="100%"
              height={sizeConfig.sparklineHeight}
              viewBox={`0 0 100 ${sizeConfig.sparklineHeight}`}
            >
              <path
                d={sparklinePath}
                fill="none"
                stroke={changeInfo.color}
                strokeWidth="2"
              />
              <path
                d={`${sparklinePath} L 100,${sizeConfig.sparklineHeight} L 0,${sizeConfig.sparklineHeight} Z`}
                fill={changeInfo.color}
                fillOpacity="0.1"
              />
            </svg>
          </div>
        )}

        {/* Details */}
        {showDetails && !compact && (
          <motion.div
            className="price-details"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: hovered ? 1 : 0.7, height: 'auto' }}
            transition={{ duration: 0.2 }}
          >
            <Space size="large" wrap>
              {(high !== undefined || low !== undefined) && (
                <div>
                  <Text type="secondary" style={{ fontSize: sizeConfig.details }}>
                    Day Range
                  </Text>
                  <div>
                    <Text style={{ fontSize: sizeConfig.details }}>
                      {low && chartUtils.formatCurrency(low, currency)} - {high && chartUtils.formatCurrency(high, currency)}
                    </Text>
                  </div>
                </div>
              )}

              {open !== undefined && (
                <div>
                  <Text type="secondary" style={{ fontSize: sizeConfig.details }}>
                    Open
                  </Text>
                  <div>
                    <Text style={{ fontSize: sizeConfig.details }}>
                      {chartUtils.formatCurrency(open, currency)}
                    </Text>
                  </div>
                </div>
              )}

              {volume !== undefined && (
                <div>
                  <Text type="secondary" style={{ fontSize: sizeConfig.details }}>
                    Volume
                  </Text>
                  <div>
                    <Text style={{ fontSize: sizeConfig.details }}>
                      {chartUtils.formatNumber(volume)}
                    </Text>
                  </div>
                </div>
              )}

              {marketCap !== undefined && (
                <div>
                  <Text type="secondary" style={{ fontSize: sizeConfig.details }}>
                    Market Cap
                  </Text>
                  <div>
                    <Text style={{ fontSize: sizeConfig.details }}>
                      {chartUtils.formatCurrency(marketCap, currency, 0)}
                    </Text>
                  </div>
                </div>
              )}
            </Space>
          </motion.div>
        )}

        {/* Last Update */}
        <div className="mt-2">
          <Text type="secondary" style={{ fontSize: 10 }}>
            Last updated: {new Date().toLocaleTimeString()}
          </Text>
        </div>
      </div>
    </Card>
  )
}

export default PriceWidget