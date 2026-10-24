/**
 * Strategy Overview Widget - Displays summary of trading strategies
 */

import React from 'react'
import { Row, Col, Statistic, Progress, Tag, Card, List, Avatar } from 'antd'
import {
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
  DollarOutlined,
  RocketOutlined,
} from '@ant-design/icons'
import { WidgetContainer } from '../Widget/WidgetContainer'

interface StrategyOverviewProps {
  strategies?: Array<{
    id: string
    name: string
    status: 'active' | 'inactive' | 'paused'
    performance: {
      totalReturn: number
      dailyReturn: number
      winRate: number
      sharpeRatio: number
    }
    risk: 'low' | 'medium' | 'high'
  }>
}

export const StrategyOverview: React.FC<StrategyOverviewProps> = ({
  strategies = [],
}) => {
  // Calculate summary metrics
  const totalStrategies = strategies.length
  const activeStrategies = strategies.filter(s => s.status === 'active').length
  const avgReturn = strategies.length > 0
    ? strategies.reduce((sum, s) => sum + s.performance.totalReturn, 0) / strategies.length
    : 0
  const avgWinRate = strategies.length > 0
    ? strategies.reduce((sum, s) => sum + s.performance.winRate, 0) / strategies.length
    : 0

  const riskColors = {
    low: 'green',
    medium: 'orange',
    high: 'red',
  }

  const riskLabels = {
    low: '低风险',
    medium: '中风险',
    high: '高风险',
  }

  return (
    <WidgetContainer
      id="strategy-overview"
      type="strategy-overview"
      title="策略概览"
    >
      <div className="space-y-4">
        {/* Summary Metrics */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12}>
            <Statistic
              title="总策略数"
              value={totalStrategies}
              prefix={<RocketOutlined />}
              suffix="个"
            />
          </Col>
          <Col xs={24} sm={12}>
            <Statistic
              title="活跃策略"
              value={activeStrategies}
              prefix={<TrophyOutlined />}
              suffix="个"
              valueStyle={{ color: activeStrategies > 0 ? '#3f8600' : '#cf1322' }}
            />
          </Col>
          <Col xs={24} sm={12}>
            <Statistic
              title="平均收益率"
              value={avgReturn * 100}
              precision={2}
              prefix={avgReturn >= 0 ? <RiseOutlined /> : <FallOutlined />}
              suffix="%"
              valueStyle={{ color: avgReturn >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Col>
          <Col xs={24} sm={12}>
            <Statistic
              title="平均胜率"
              value={avgWinRate * 100}
              precision={1}
              prefix={<DollarOutlined />}
              suffix="%"
            />
          </Col>
        </Row>

        {/* Strategy List */}
        <Card title="策略详情" size="small" className="mt-4">
          <List
            dataSource={strategies.slice(0, 5)} // Show top 5 strategies
            renderItem={(strategy) => (
              <List.Item>
                <List.Item.Meta
                  avatar={
                    <Avatar
                      icon={<RocketOutlined />}
                      style={{
                        backgroundColor: strategy.status === 'active' ? '#52c41a' : '#8c8c8c',
                      }}
                    />
                  }
                  title={strategy.name}
                  description={
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Tag color={strategy.status === 'active' ? 'success' : 'default'}>
                          {strategy.status === 'active' ? '运行中' : '已停止'}
                        </Tag>
                        <Tag color={riskColors[strategy.risk]}>
                          {riskLabels[strategy.risk]}
                        </Tag>
                      </div>
                      <Row gutter={16}>
                        <Col span={8}>
                          <div className="text-xs text-gray-500">日收益</div>
                          <div className={`font-semibold ${
                            strategy.performance.dailyReturn >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {(strategy.performance.dailyReturn * 100).toFixed(2)}%
                          </div>
                        </Col>
                        <Col span={8}>
                          <div className="text-xs text-gray-500">胜率</div>
                          <Progress
                            percent={strategy.performance.winRate * 100}
                            size="small"
                            format={(percent) => `${percent?.toFixed(0)}%`}
                          />
                        </Col>
                        <Col span={8}>
                          <div className="text-xs text-gray-500">夏普比率</div>
                          <div className="font-semibold">
                            {strategy.performance.sharpeRatio.toFixed(2)}
                          </div>
                        </Col>
                      </Row>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        </Card>
      </div>
    </WidgetContainer>
  )
}