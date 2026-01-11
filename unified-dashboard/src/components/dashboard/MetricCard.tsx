import React from 'react'
import { Card, Statistic } from 'antd'

interface MetricCardProps {
  title: string
  value: number
  suffix?: string
  prefix?: string
  precision?: number
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, suffix, prefix, precision = 2 }) => {
  return (
    <Card>
      <Statistic
        title={title}
        value={value}
        suffix={suffix}
        prefix={prefix}
        precision={precision}
      />
    </Card>
  )
}

export default MetricCard
