import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Progress, Statistic, Typography, Space, Tag } from 'antd'
import {
  ServerOutlined,
  DatabaseOutlined,
  CloudOutlined,
  WifiOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'

const { Text } = Typography

interface MetricData {
  name: string
  value: number
  unit: string
  status: 'normal' | 'warning' | 'critical'
  threshold?: {
    warning: number
    critical: number
  }
  trend?: number
  details?: {
    used?: number
    total?: number
    available?: number
  }
}

interface SystemMetricsProps {
  refreshInterval?: number
  showDetails?: boolean
}

const SystemMetrics: React.FC<SystemMetricsProps> = ({
  refreshInterval = 5000,
  showDetails = false,
}) => {
  const [metrics, setMetrics] = useState<MetricData[]>([
    {
      name: 'CPU使用率',
      value: 45,
      unit: '%',
      status: 'normal',
      threshold: { warning: 70, critical: 90 },
      trend: 2.1,
      details: {
        used: 3.6,
        total: 8,
        available: 4.4,
      },
    },
    {
      name: '内存使用',
      value: 68,
      unit: '%',
      status: 'warning',
      threshold: { warning: 70, critical: 90 },
      trend: -1.5,
      details: {
        used: 10.88,
        total: 16,
        available: 5.12,
      },
    },
    {
      name: '磁盘使用',
      value: 38,
      unit: '%',
      status: 'normal',
      threshold: { warning: 80, critical: 95 },
      trend: 0.8,
      details: {
        used: 152,
        total: 400,
        available: 248,
      },
    },
    {
      name: '网络带宽',
      value: 23,
      unit: '%',
      status: 'normal',
      threshold: { warning: 70, critical: 90 },
      trend: -2.3,
    },
    {
      name: 'API响应时间',
      value: 85,
      unit: 'ms',
      status: 'warning',
      threshold: { warning: 100, critical: 500 },
      trend: 5.2,
    },
    {
      name: '数据库连接',
      value: 12,
      unit: '/20',
      status: 'normal',
      threshold: { warning: 15, critical: 19 },
      details: {
        used: 12,
        total: 20,
        available: 8,
      },
    },
  ])

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prevMetrics =>
        prevMetrics.map(metric => ({
          ...metric,
          value: Math.max(0, Math.min(100, metric.value + (Math.random() - 0.5) * 5)),
          trend: (Math.random() - 0.5) * 10,
        }))
      )
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [refreshInterval])

  const getMetricIcon = (name: string) => {
    if (name.includes('CPU')) return <ServerOutlined />
    if (name.includes('内存')) return <ThunderboltOutlined />
    if (name.includes('磁盘')) return <DatabaseOutlined />
    if (name.includes('网络')) return <WifiOutlined />
    if (name.includes('API')) return <CloudOutlined />
    return <ClockCircleOutlined />
  }

  const getProgressColor = (status: string, value: number) => {
    switch (status) {
      case 'critical':
        return '#ff4d4f'
      case 'warning':
        return '#faad14'
      case 'normal':
      default:
        if (value > 70) return '#faad14'
        if (value > 90) return '#ff4d4f'
        return '#52c41a'
    }
  }

  const getStatusTag = (status: string) => {
    const config = {
      normal: { color: 'success', text: '正常' },
      warning: { color: 'warning', text: '警告' },
      critical: { color: 'error', text: '嚴重' },
    }

    const { color, text } = config[status] || config.normal
    return <Tag color={color}>{text}</Tag>
  }

  const formatDetails = (metric: MetricData) => {
    if (!metric.details || !showDetails) return null

    const { used, total, available } = metric.details
    if (used && total) {
      return (
        <div className="text-xs text-gray-500 space-y-1">
          <div>已用: {used}GB / 总计: {total}GB</div>
          {available && <div>可用: {available}GB</div>}
        </div>
      )
    }

    if (metric.unit.includes('/')) {
      return (
        <div className="text-xs text-gray-500 space-y-1">
          <div>当前: {metric.value} {metric.unit}</div>
          {available && <div>可用: {available}个连接</div>}
        </div>
      )
    }

    return null
  }

  return (
    <Card title="系统指標監控" size="small">
      <Row gutter={[16, 16]}>
        {metrics.map((metric, index) => (
          <Col xs={24} sm={12} lg={8} key={index}>
            <Card size="small" className="hover:shadow-md transition-shadow">
              <div className="space-y-3">
                {/* Metric Header */}
                <div className="flex items-center justify-between">
                  <Space>
                    {getMetricIcon(metric.name)}
                    <Text strong>{metric.name}</Text>
                  </Space>
                  {getStatusTag(metric.status)}
                </div>

                {/* Metric Value */}
                <div className="flex items-baseline justify-between">
                  <Statistic
                    value={metric.value}
                    suffix={metric.unit}
                    valueStyle={{
                      fontSize: '20px',
                      fontWeight: 'bold',
                    }}
                  />
                  {metric.trend !== undefined && (
                    <Text
                      type={metric.trend > 0 ? 'danger' : 'success'}
                      className="text-sm"
                    >
                      {metric.trend > 0 ? '↑' : '↓'} {Math.abs(metric.trend).toFixed(1)}%
                    </Text>
                  )}
                </div>

                {/* Progress Bar */}
                <Progress
                  percent={metric.unit === '%' ? metric.value : (metric.value / parseFloat(metric.unit)) * 100}
                  status={metric.status === 'critical' ? 'exception' : 'normal'}
                  strokeColor={getProgressColor(metric.status, metric.value)}
                  showInfo={false}
                  size="small"
                />

                {/* Details */}
                {formatDetails(metric)}

                {/* Threshold Indicator */}
                {metric.threshold && (
                  <div className="text-xs text-gray-400">
                    閾值: 警告 {metric.threshold.warning}%, 嚴重 {metric.threshold.critical}%
                  </div>
                )}
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </Card>
  )
}

export default SystemMetrics