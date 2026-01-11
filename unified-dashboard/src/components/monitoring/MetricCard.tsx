import React from 'react'
import { Card, Statistic, Typography, Space } from 'antd'
import { TrendingUpOutlined, TrendingDownOutlined } from '@ant-design/icons'

const { Text } = Typography

interface MetricCardProps {
  title: string
  value: number
  suffix?: string
  prefix?: React.ReactNode
  status?: 'normal' | 'warning' | 'error' | 'success'
  icon?: React.ReactNode
  trend?: number
  description?: string
  loading?: boolean
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  suffix,
  prefix,
  status = 'normal',
  icon,
  trend,
  description,
  loading = false,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
      case 'normal':
        return '#52c41a'
      case 'warning':
        return '#faad14'
      case 'error':
        return '#ff4d4f'
      default:
        return '#1890ff'
    }
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
        suffix={suffix}
        prefix={prefix}
        valueStyle={{
          color: getStatusColor(status),
          fontWeight: 'bold',
        }}
      />
      {trend !== undefined && (
        <div className="mt-2">
          <Space>
            {trend > 0 ? (
              <TrendingUpOutlined style={{ color: '#ff4d4f' }} />
            ) : (
              <TrendingDownOutlined style={{ color: '#52c41a' }} />
            )}
            <Text
              type={trend > 0 ? 'danger' : 'success'}
              className="text-sm"
            >
              {trend > 0 ? '+' : ''}{trend}%
            </Text>
            <Text type="secondary" className="text-sm">
              vs 昨日
            </Text>
          </Space>
        </div>
      )}
      {description && (
        <Text type="secondary" className="text-xs block mt-1">
          {description}
        </Text>
      )}
    </Card>
  )
}

export default MetricCard