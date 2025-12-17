import React, { useMemo, useState } from 'react'
import { Card, Statistic, Progress, Row, Col, Typography, Space, Tooltip } from 'antd'
import {
  TrendingUpOutlined,
  TrendingDownOutlined,
  InfoCircleOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  MinusOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import { chartUtils } from '../../utils/charts'
import { useRealTimeData } from '../../hooks'

const { Text } = Typography

export interface MetricData {
  label: string
  value: number
  previousValue?: number
  unit?: string
  format?: 'decimal' | 'percentage' | 'currency'
  target?: number
  min?: number
  max?: number
  status?: 'success' | 'warning' | 'error' | 'normal'
  description?: string
  icon?: React.ReactNode
  color?: string
  showProgress?: boolean
  showTrend?: boolean
}

export interface MetricsWidgetProps {
  title?: string
  metrics: MetricData[]
  columns?: number
  compact?: boolean
  size?: 'small' | 'default' | 'large'
  theme?: 'light' | 'dark'
  showSparkline?: boolean
  realTime?: boolean
  updateInterval?: number
  onMetricClick?: (metric: MetricData, index: number) => void
  className?: string
  cardProps?: any
}

const MetricsWidget: React.FC<MetricsWidgetProps> = ({
  title,
  metrics,
  columns = 2,
  compact = false,
  size = 'default',
  theme = 'light',
  showSparkline = false,
  realTime = false,
  updateInterval = 5000,
  onMetricClick,
  className,
  cardProps,
}) => {
  const [hoveredMetric, setHoveredMetric] = useState<number | null>(null)

  // Format value based on format type
  const formatValue = useCallback((value: number, format?: string, unit?: string): string => {
    switch (format) {
      case 'percentage':
        return `${value.toFixed(2)}%`
      case 'currency':
        return chartUtils.formatCurrency(value)
      default:
        const formatted = chartUtils.formatNumber(value)
        return unit ? `${formatted} ${unit}` : formatted
    }
  }, [])

  // Calculate trend
  const getTrend = useCallback((metric: MetricData) => {
    if (!metric.previousValue || metric.previousValue === metric.value) {
      return {
        icon: <MinusOutlined />,
        color: '#8c8c8c',
        text: 'No change',
      }
    }

    const change = metric.value - metric.previousValue
    const changePercent = (change / metric.previousValue) * 100

    if (change > 0) {
      return {
        icon: <ArrowUpOutlined />,
        color: '#52c41a',
        text: `+${changePercent.toFixed(1)}%`,
      }
    } else {
      return {
        icon: <ArrowDownOutlined />,
        color: '#f5222d',
        text: `${changePercent.toFixed(1)}%`,
      }
    }
  }, [])

  // Get progress color based on status
  const getProgressColor = useCallback((metric: MetricData) => {
    if (metric.status === 'success') return '#52c41a'
    if (metric.status === 'warning') return '#faad14'
    if (metric.status === 'error') return '#f5222d'
    if (metric.color) return metric.color

    // Auto-determine based on target
    if (metric.target) {
      const ratio = metric.value / metric.target
      if (ratio >= 1) return '#52c41a'
      if (ratio >= 0.8) return '#faad14'
      return '#f5222d'
    }

    return '#1890ff'
  }, [])

  // Render individual metric
  const renderMetric = (metric: MetricData, index: number) => {
    const trend = metric.showTrend ? getTrend(metric) : null
    const progressColor = getProgressColor(metric)
    const isHovered = hoveredMetric === index

    return (
      <Col key={index} span={24 / columns}>
        <motion.div
          className={`metric-item ${isHovered ? 'hovered' : ''}`}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onHoverStart={() => setHoveredMetric(index)}
          onHoverEnd={() => setHoveredMetric(null)}
          onClick={() => onMetricClick?.(metric, index)}
          style={{
            padding: compact ? '8px' : '16px',
            borderRadius: '8px',
            cursor: onMetricClick ? 'pointer' : 'default',
            background: isHovered
              ? theme === 'dark' ? 'rgba(255, 255, 255, 0.05)'
              : 'rgba(0, 0, 0, 0.02)'
              : 'transparent',
            transition: 'all 0.2s ease',
          }}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-2">
                {metric.icon && (
                  <span style={{ color: metric.color || progressColor }}>
                    {metric.icon}
                  </span>
                )}
                <Text
                  type="secondary"
                  style={{
                    fontSize: size === 'small' ? 12 : size === 'large' ? 16 : 14,
                  }}
                >
                  {metric.label}
                </Text>
                {metric.description && (
                  <Tooltip title={metric.description}>
                    <InfoCircleOutlined style={{ fontSize: 12, opacity: 0.5 }} />
                  </Tooltip>
                )}
              </div>

              <div className="flex items-baseline space-x-2">
                <Statistic
                  value={metric.value}
                  precision={metric.format === 'currency' ? 2 : 2}
                  suffix={metric.unit}
                  valueStyle={{
                    fontSize: size === 'small' ? 18 : size === 'large' ? 28 : 24,
                    fontWeight: 'bold',
                    color: metric.color || progressColor,
                  }}
                />
                {trend && (
                  <div className="flex items-center space-x-1">
                    <span style={{ color: trend.color, fontSize: 12 }}>
                      {trend.icon}
                    </span>
                    <Text
                      style={{
                        color: trend.color,
                        fontSize: 12,
                        fontWeight: 500,
                      }}
                    >
                      {trend.text}
                    </Text>
                  </div>
                )}
              </div>

              {metric.showProgress && metric.target && (
                <div className="mt-3">
                  <Progress
                    percent={Math.min((metric.value / metric.target) * 100, 100)}
                    strokeColor={progressColor}
                    size="small"
                    showInfo={false}
                  />
                  <div className="flex justify-between mt-1">
                    <Text type="secondary" style={{ fontSize: 10 }}>
                      {formatValue(metric.value, metric.format, metric.unit)}
                    </Text>
                    <Text type="secondary" style={{ fontSize: 10 }}>
                      Target: {formatValue(metric.target, metric.format, metric.unit)}
                    </Text>
                  </div>
                </div>
              )}

              {metric.min !== undefined && metric.max !== undefined && (
                <div className="mt-2">
                  <Text type="secondary" style={{ fontSize: 10 }}>
                    Range: {formatValue(metric.min, metric.format, metric.unit)} -{' '}
                    {formatValue(metric.max, metric.format, metric.unit)}
                  </Text>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </Col>
    )
  }

  return (
    <Card
      title={title}
      className={`metrics-widget ${compact ? 'compact' : ''} ${className || ''}`}
      size={size}
      {...cardProps}
      bodyStyle={{ padding: compact ? '12px' : '24px' }}
    >
      <Row gutter={[16, 16]}>
        {metrics.map((metric, index) => renderMetric(metric, index))}
      </Row>
    </Card>
  )
}

export default MetricsWidget