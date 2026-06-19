import React from 'react'
import { Card, Statistic, Typography, Space } from 'antd'
import {
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons'

const { Text } = Typography

interface MetricCardProps {
  title: string
  value: number
  precision?: number
  prefix?: string
  suffix?: string
  icon?: React.ReactNode
  loading?: boolean
  trend?: number
  trendDirection?: 'up' | 'down'
  extra?: React.ReactNode
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  precision = 2,
  prefix,
  suffix,
  icon,
  loading = false,
  trend,
  trendDirection,
  extra,
}) => {
  const getTrendIcon = () => {
    if (trend === undefined) return null

    if (trendDirection === 'up' || trend > 0) {
      return <RiseOutlined style={{ color: '#3f8600' }} />
    }
    return <FallOutlined style={{ color: '#cf1322' }} />
  }

  const getTrendText = () => {
    if (trend === undefined) return null

    const trendValue = Math.abs(trend) * (suffix === '%' ? 1 : 100)
    return (
      <Text
        type={trendDirection === 'up' || trend > 0 ? 'success' : 'danger'}
        className="text-sm"
      >
        {trendDirection === 'up' || trend > 0 ? '+' : ''}{trendValue.toFixed(2)}%
      </Text>
    )
  }

  return (
    <Card loading={loading} className="hover:shadow-md transition-shadow">
      <Statistic
        title={
          <Space>
            {icon}
            <Text>{title}</Text>
          </Space>
        }
        value={value}
        precision={precision}
        prefix={prefix}
        suffix={suffix}
      />

      {(trend !== undefined || trendDirection) && (
        <div className="mt-2">
          <Space>
            {getTrendIcon()}
            {getTrendText()}
            <Text type="secondary" className="text-sm">
              vs 昨日
            </Text>
          </Space>
        </div>
      )}

      {extra && (
        <div className="mt-2">
          {extra}
        </div>
      )}
    </Card>
  )
}

export default MetricCard