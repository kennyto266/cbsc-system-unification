import React from 'react'
import { Card, Row, Col, Statistic, Progress, Typography, Space, Tooltip } from 'antd'
import {
  AlertOutlined,
  SafetyOutlined,
  LineChartOutlined,
  BarChartOutlined,
  InfoCircleOutlined,
  DashboardOutlined,
  TrophyOutlined,
} from '@ant-design/icons'

const { Text } = Typography

interface RiskMetricsProps {
  metrics: {
    volatility: number
    beta: number
    alpha: number
    var95: number
    cvar95: number
    skewness: number
    kurtosis: number
    informationRatio: number
  }
}

const RiskMetrics: React.FC<RiskMetricsProps> = ({ metrics: m }) => {
  // 防禦 undefined/null（GridItem 可能不傳 metrics prop）
  const metrics = m || {
    volatility: 0, beta: 0, alpha: 0, var95: 0, cvar95: 0,
    skewness: 0, kurtosis: 0, informationRatio: 0,
  }
  const getRiskColor = (value: number, type: string) => {
    switch (type) {
      case 'volatility':
        return value < 15 ? '#52c41a' : value < 25 ? '#faad14' : '#ff4d4f'
      case 'beta':
        return Math.abs(value - 1) < 0.2 ? '#52c41a' : Math.abs(value - 1) < 0.5 ? '#faad14' : '#ff4d4f'
      case 'alpha':
        return value > 5 ? '#52c41a' : value > 0 ? '#faad14' : '#ff4d4f'
      case 'var':
        return value > -2 ? '#52c41a' : value > -5 ? '#faad14' : '#ff4d4f'
      case 'skewness':
        return value > 0.5 ? '#52c41a' : value < -0.5 ? '#ff4d4f' : '#faad14'
      case 'kurtosis':
        return Math.abs(value - 3) < 1 ? '#52c41a' : Math.abs(value - 3) < 2 ? '#faad14' : '#ff4d4f'
      case 'infoRatio':
        return value > 0.5 ? '#52c41a' : value > 0 ? '#faad14' : '#ff4d4f'
      default:
        return '#1890ff'
    }
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
          precision={2}
          suffix={suffix}
          valueStyle={{
            color: getRiskColor(value, type),
            fontSize: '20px',
            fontWeight: 'bold',
          }}
        />
      </div>
    </Card>
  )

  return (
    <Card title="風險指標" size="small">
      <Row gutter={[16, 16]}>
        {/* Volatility Risk */}
        <Col xs={24} sm={12} md={8}>
          <div className="space-y-2">
            <Space>
              <LineChartOutlined />
              <Text strong>波動率</Text>
              <Tooltip title="收益率的標準差，衡量價格波動程度">
                <InfoCircleOutlined className="text-gray-400" />
              </Tooltip>
            </Space>
            <Progress
              percent={metrics.volatility}
              status={metrics.volatility < 15 ? 'success' : metrics.volatility < 25 ? 'normal' : 'exception'}
              format={() => `${metrics.volatility.toFixed(1)}%`}
              strokeColor={getRiskColor(metrics.volatility, 'volatility')}
            />
            <Text type="secondary" className="text-xs">
              {metrics.volatility < 15 ? '低波動' : metrics.volatility < 25 ? '中等波動' : '高波動'}
            </Text>
          </div>
        </Col>

        {/* Market Risk */}
        <Col xs={24} sm={12} md={8}>
          <MetricCard
            title="Beta係數"
            value={metrics.beta}
            icon={<BarChartOutlined />}
            type="beta"
            tooltip="相對於市場的系統性風險，1表示與市場同步"
          />
        </Col>
        <Col xs={24} sm={12} md={8}>
          <MetricCard
            title="Alpha收益"
            value={metrics.alpha}
            suffix="%"
            icon={<TrophyOutlined />}
            type="alpha"
            tooltip="相對於基準的超額收益"
          />
        </Col>

        {/* Value at Risk */}
        <Col xs={24} sm={12} md={8}>
          <MetricCard
            title="VaR (95%)"
            value={metrics.var95}
            suffix="%"
            icon={<AlertOutlined />}
            type="var"
            tooltip="95%置信度下的最大可能虧損"
          />
        </Col>
        <Col xs={24} sm={12} md={8}>
          <MetricCard
            title="CVaR (95%)"
            value={metrics.cvar95}
            suffix="%"
            icon={<SafetyOutlined />}
            type="var"
            tooltip="95%置信度下的條件期望虧損"
          />
        </Col>
        <Col xs={24} sm={12} md={8}>
          <MetricCard
            title="信息比率"
            value={metrics.informationRatio}
            icon={<DashboardOutlined />}
            type="infoRatio"
            tooltip="相對於基準的超額收益與追蹤誤差的比率"
          />
        </Col>

        {/* Distribution Metrics */}
        <Col xs={24} md={12}>
          <Card size="small" title="收益分佈特徵">
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <Space>
                  <Text>偏度</Text>
                  <Tooltip title="衡量收益分佈的不對稱性">
                    <InfoCircleOutlined className="text-gray-400 text-xs" />
                  </Tooltip>
                </Space>
                <div className="flex items-center space-x-2">
                  <Text
                    strong
                    style={{ color: getRiskColor(metrics.skewness, 'skewness') }}
                  >
                    {metrics.skewness.toFixed(3)}
                  </Text>
                  <Text type="secondary" className="text-xs">
                    {metrics.skewness > 0.5 ? '右偏' : metrics.skewness < -0.5 ? '左偏' : '對稱'}
                  </Text>
                </div>
              </div>

              <div className="flex justify-between items-center">
                <Space>
                  <Text>峰度</Text>
                  <Tooltip title="衡量收益分佈的尾部厚度">
                    <InfoCircleOutlined className="text-gray-400 text-xs" />
                  </Tooltip>
                </Space>
                <div className="flex items-center space-x-2">
                  <Text
                    strong
                    style={{ color: getRiskColor(metrics.kurtosis, 'kurtosis') }}
                  >
                    {metrics.kurtosis.toFixed(3)}
                  </Text>
                  <Text type="secondary" className="text-xs">
                    {Math.abs(metrics.kurtosis - 3) < 1 ? '正常' :
                     Math.abs(metrics.kurtosis - 3) < 2 ? '輕微異常' : '顯著異常'}
                  </Text>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-gray-200">
                <Text type="secondary" className="text-xs">
                  峰度為3表示正態分佈，大於3表示厚尾（尖峰），小於3表示薄尾（平峰）
                </Text>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </Card>
  )
}

export default RiskMetrics