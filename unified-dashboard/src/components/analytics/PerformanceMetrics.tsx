import React from 'react'
import { Card, Row, Col, Statistic, Progress, Typography, Space, Tooltip } from 'antd'
import {
  TrendingUpOutlined,
  TrophyOutlined,
  PercentageOutlined,
  LineChartOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'

const { Text, Title } = Typography

interface PerformanceMetricsProps {
  metrics: {
    totalReturn: number
    annualizedReturn: number
    sharpeRatio: number
    sortinoRatio: number
    maxDrawdown: number
    calmarRatio: number
    winRate: number
    profitFactor: number
    avgWin: number
    avgLoss: number
  }
}

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ metrics }) => {
  const getPerformanceColor = (value: number, type: string) => {
    if (type === 'drawdown') {
      return value > -10 ? '#52c41a' : value > -20 ? '#faad14' : '#ff4d4f'
    }
    if (type === 'ratio') {
      return value > 1.5 ? '#52c41a' : value > 1 ? '#faad14' : '#ff4d4f'
    }
    return value > 0 ? '#52c41a' : '#ff4d4f'
  }

  const MetricCard = ({ title, value, suffix, icon, type = 'default', tooltip }: any) => (
    <Card size="small" className="hover:shadow-md transition-shadow">
      <div className="space-y-2">
        <Space>
          {icon}
          <Text strong>{title}</Text>
          {tooltip && (
            <Tooltip title={tooltip}>
              <InfoCircleOutlined className="text-gray-400" />
            </Tooltip>
          )}
        </Space>
        <Statistic
          value={value}
          precision={type === 'ratio' ? 2 : 2}
          suffix={suffix}
          valueStyle={{
            color: getPerformanceColor(value, type),
            fontSize: '20px',
            fontWeight: 'bold',
          }}
        />
      </div>
    </Card>
  )

  return (
    <Card title="績效指標" size="small">
      <Row gutter={[16, 16]}>
        {/* Return Metrics */}
        <Col xs={24} sm={12} md={8}>
          <MetricCard
            title="總收益率"
            value={metrics.totalReturn}
            suffix="%"
            icon={<TrendingUpOutlined />}
            tooltip="投資期內的總收益率"
          />
        </Col>
        <Col xs={24} sm={12} md={8}>
          <MetricCard
            title="年化收益率"
            value={metrics.annualizedReturn}
            suffix="%"
            icon={<LineChartOutlined />}
            tooltip="將總收益率換算為年化收益率"
          />
        </Col>
        <Col xs={24} sm={12} md={8}>
          <MetricCard
            title="最大回撤"
            value={metrics.maxDrawdown}
            suffix="%"
            icon={<TrendingUpOutlined />}
            type="drawdown"
            tooltip="歷史上最大的資產價值下跌幅度"
          />
        </Col>

        {/* Risk-Adjusted Ratios */}
        <Col xs={24} sm={12} md={8}>
          <MetricCard
            title="夏普比率"
            value={metrics.sharpeRatio}
            icon={<TrophyOutlined />}
            type="ratio"
            tooltip="風險調整後的收益指標，越高越好"
          />
        </Col>
        <Col xs={24} sm={12} md={8}>
          <MetricCard
            title="索提諾比率"
            value={metrics.sortinoRatio}
            icon={<TrophyOutlined />}
            type="ratio"
            tooltip="只考慮下行風險的風險調整收益指標"
          />
        </Col>
        <Col xs={24} sm={12} md={8}>
          <MetricCard
            title="卡瑪比率"
            value={metrics.calmarRatio}
            icon={<TrophyOutlined />}
            type="ratio"
            tooltip="年化收益率與最大回撤的比率"
          />
        </Col>

        {/* Trading Metrics */}
        <Col xs={24} sm={12} md={8}>
          <div className="space-y-2">
            <Space>
              <PercentageOutlined />
              <Text strong>勝率</Text>
              <Tooltip title="盈利交易佔總交易次數的比例">
                <InfoCircleOutlined className="text-gray-400" />
              </Tooltip>
            </Space>
            <Progress
              percent={metrics.winRate}
              status={metrics.winRate > 60 ? 'success' : 'normal'}
              format={() => `${metrics.winRate.toFixed(1)}%`}
            />
          </div>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <MetricCard
            title="盈利因子"
            value={metrics.profitFactor}
            icon={<PercentageOutlined />}
            type="ratio"
            tooltip="總盈利與總虧損的比率"
          />
        </Col>

        {/* Average Win/Loss */}
        <Col xs={24} md={8}>
          <Card size="small" title="平均盈虧">
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Text type="secondary">平均盈利:</Text>
                <Text className="text-green-600 font-bold">
                  +{metrics.avgWin.toFixed(2)}%
                </Text>
              </div>
              <div className="flex justify-between items-center">
                <Text type="secondary">平均虧損:</Text>
                <Text className="text-red-600 font-bold">
                  {metrics.avgLoss.toFixed(2)}%
                </Text>
              </div>
              <div className="flex justify-between items-center">
                <Text type="secondary">盈虧比:</Text>
                <Text strong>
                  {(Math.abs(metrics.avgWin / metrics.avgLoss)).toFixed(2)}:1
                </Text>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </Card>
  )
}

export default PerformanceMetrics