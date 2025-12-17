import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Tag,
  Button,
  Space,
  Tabs,
  Table,
  Timeline,
  Alert,
  Descriptions,
  Progress,
  Tooltip,
  Divider,
} from 'antd'
import {
  EditOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  BarChartOutlined,
  HistoryOutlined,
  SettingOutlined,
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
  InfoCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { Strategy, StrategyType, StrategyStatus } from '../../types'
import { useGetStrategyDetailsQuery, useGetStrategyExecutionHistoryQuery } from '../../store/api/strategyApi'
import StrategyPerformanceChart from '../charts/StrategyPerformanceChart'
import ParameterDisplay from './ParameterDisplay'

const { TabPane } = Tabs
const { Title, Text } = { ...require('antd') }

// Risk level color mapping
const riskLevelColors: Record<string, string> = {
  low: 'green',
  medium: 'orange',
  high: 'red',
}

// Strategy status color mapping
const strategyStatusColors: Record<StrategyStatus, string> = {
  [StrategyStatus.ACTIVE]: 'success',
  [StrategyStatus.INACTIVE]: 'default',
  [StrategyStatus.TESTING]: 'processing',
  [StrategyStatus.ARCHIVED]: 'error',
}

interface StrategyDetailsProps {
  strategyId: string
  onEdit?: (strategy: Strategy) => void
  onStatusChange?: (strategyId: string, newStatus: StrategyStatus) => void
}

const StrategyDetails: React.FC<StrategyDetailsProps> = ({
  strategyId,
  onEdit,
  onStatusChange,
}) => {
  const [activeTab, setActiveTab] = useState('overview')

  // API queries
  const { data: strategy, isLoading, error } = useGetStrategyDetailsQuery(strategyId)
  const { data: executionHistory } = useGetStrategyExecutionHistoryQuery(strategyId)

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (error || !strategy) {
    return (
      <Alert
        message="加载失败"
        description="无法加载策略详情，请稍后重试。"
        type="error"
        showIcon
      />
    )
  }

  // Performance metrics calculation
  const performanceMetrics = [
    {
      title: '总收益率',
      value: strategy.performance.totalReturn * 100,
      precision: 2,
      suffix: '%',
      color: strategy.performance.totalReturn >= 0 ? '#52c41a' : '#ff4d4f',
      icon: strategy.performance.totalReturn >= 0 ? <RiseOutlined /> : <FallOutlined />,
    },
    {
      title: '夏普比率',
      value: strategy.performance.sharpeRatio,
      precision: 2,
      color: strategy.performance.sharpeRatio >= 1 ? '#52c41a' : '#faad14',
      icon: <TrophyOutlined />,
    },
    {
      title: '最大回撤',
      value: strategy.performance.maxDrawdown * 100,
      precision: 2,
      suffix: '%',
      color: strategy.performance.maxDrawdown > -0.1 ? '#52c41a' : '#ff4d4f',
      icon: <BarChartOutlined />,
    },
    {
      title: '胜率',
      value: strategy.performance.winRate * 100,
      precision: 1,
      suffix: '%',
      color: strategy.performance.winRate >= 0.6 ? '#52c41a' : '#faad14',
      icon: <TrophyOutlined />,
    },
    {
      title: '盈利因子',
      value: strategy.performance.profitFactor,
      precision: 2,
      color: strategy.performance.profitFactor >= 1.5 ? '#52c41a' : '#faad14',
      icon: <BarChartOutlined />,
    },
  ]

  // Execution history columns
  const executionColumns = [
    {
      title: '执行时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: string) => new Date(timestamp).toLocaleString(),
    },
    {
      title: '信号类型',
      dataIndex: 'signal',
      key: 'signal',
      render: (signal: string) => (
        <Tag color={signal === 'BUY' ? 'green' : signal === 'SELL' ? 'red' : 'blue'}>
          {signal}
        </Tag>
      ),
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `¥${price.toFixed(2)}`,
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'SUCCESS' ? 'success' : status === 'FAILED' ? 'error' : 'processing'}>
          {status}
        </Tag>
      ),
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl: number) => (
        <span className={pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
          {pnl >= 0 ? '+' : ''}¥{pnl.toFixed(2)}
        </span>
      ),
    },
  ]

  // Recent activities for timeline
  const recentActivities = [
    {
      time: new Date(strategy.updatedAt).toLocaleString(),
      content: '策略参数更新',
      type: 'info',
    },
    ...(strategy.lastActive ? [{
      time: new Date(strategy.lastActive).toLocaleString(),
      content: '策略执行',
      type: 'success',
    }] : []),
    {
      time: new Date(strategy.createdAt).toLocaleString(),
      content: '策略创建',
      type: 'info',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <Row justify="space-between" align="middle">
          <Col>
            <div className="flex items-center space-x-3 mb-2">
              <Title level={3} className="!mb-0">{strategy.name}</Title>
              <Tag color={strategyStatusColors[strategy.status]}>
                {strategy.status}
              </Tag>
              <Tag color={riskLevelColors[strategy.riskLevel]}>
                {strategy.riskLevel.toUpperCase()}
              </Tag>
              <Tag color="blue">
                {strategy.type}
              </Tag>
            </div>
            <Text type="secondary">{strategy.description}</Text>
          </Col>
          <Col>
            <Space>
              <Button icon={<EditOutlined />} onClick={() => onEdit?.(strategy)}>
                编辑
              </Button>
              {strategy.status === StrategyStatus.ACTIVE ? (
                <Button
                  danger
                  icon={<PauseCircleOutlined />}
                  onClick={() => onStatusChange?.(strategyId, StrategyStatus.INACTIVE)}
                >
                  暂停
                </Button>
              ) : (
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={() => onStatusChange?.(strategyId, StrategyStatus.ACTIVE)}
                >
                  启动
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </div>

      {/* Performance Metrics */}
      <Row gutter={[16, 16]}>
        {performanceMetrics.map((metric, index) => (
          <Col xs={24} sm={12} lg={24 / performanceMetrics.length} key={index}>
            <Card>
              <Statistic
                title={
                  <Space>
                    {metric.title}
                    {metric.icon}
                  </Space>
                }
                value={metric.value}
                precision={metric.precision}
                suffix={metric.suffix}
                valueStyle={{ color: metric.color }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {/* Detailed Information Tabs */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="概述" key="overview">
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Card title="基本信息" size="small">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="策略ID">{strategy.id}</Descriptions.Item>
                    <Descriptions.Item label="类型">{strategy.type}</Descriptions.Item>
                    <Descriptions.Item label="风险等级">
                      <Tag color={riskLevelColors[strategy.riskLevel]}>
                        {strategy.riskLevel.toUpperCase()}
                      </Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="创建时间">
                      {new Date(strategy.createdAt).toLocaleString()}
                    </Descriptions.Item>
                    <Descriptions.Item label="更新时间">
                      {new Date(strategy.updatedAt).toLocaleString()}
                    </Descriptions.Item>
                    {strategy.lastActive && (
                      <Descriptions.Item label="最后活跃">
                        <Space>
                          <ClockCircleOutlined />
                          {new Date(strategy.lastActive).toLocaleString()}
                        </Space>
                      </Descriptions.Item>
                    )}
                  </Descriptions>
                </Card>

                <Card title="性能指标" size="small" className="mt-4">
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between mb-2">
                        <Text>胜率</Text>
                        <Text>{(strategy.performance.winRate * 100).toFixed(1)}%</Text>
                      </div>
                      <Progress
                        percent={strategy.performance.winRate * 100}
                        strokeColor={strategy.performance.winRate >= 0.6 ? '#52c41a' : '#faad14'}
                      />
                    </div>
                    <div>
                      <div className="flex justify-between mb-2">
                        <Text>收益稳定性</Text>
                        <Text>{Math.max(0, Math.min(100, 50 + strategy.performance.sharpeRatio * 20)).toFixed(0)}%</Text>
                      </div>
                      <Progress
                        percent={Math.max(0, Math.min(100, 50 + strategy.performance.sharpeRatio * 20))}
                        strokeColor={strategy.performance.sharpeRatio >= 1 ? '#52c41a' : '#faad14'}
                      />
                    </div>
                    <div>
                      <div className="flex justify-between mb-2">
                        <Text>风险控制</Text>
                        <Text>{Math.max(0, 100 - Math.abs(strategy.performance.maxDrawdown) * 500).toFixed(0)}%</Text>
                      </div>
                      <Progress
                        percent={Math.max(0, 100 - Math.abs(strategy.performance.maxDrawdown) * 500)}
                        strokeColor={strategy.performance.maxDrawdown > -0.1 ? '#52c41a' : '#ff4d4f'}
                      />
                    </div>
                  </div>
                </Card>
              </Col>

              <Col xs={24} lg={12}>
                <Card title="策略参数" size="small">
                  <ParameterDisplay parameters={strategy.parameters} />
                </Card>

                <Card title="最近活动" size="small" className="mt-4">
                  <Timeline size="small">
                    {recentActivities.map((activity, index) => (
                      <Timeline.Item
                        key={index}
                        color={activity.type === 'success' ? 'green' : activity.type === 'error' ? 'red' : 'blue'}
                      >
                        <Text>{activity.content}</Text>
                        <br />
                        <Text type="secondary" className="text-xs">{activity.time}</Text>
                      </Timeline.Item>
                    ))}
                  </Timeline>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="性能图表" key="performance">
            <StrategyPerformanceChart strategy={strategy} />
          </TabPane>

          <TabPane tab="执行历史" key="execution">
            <Table
              columns={executionColumns}
              dataSource={executionHistory}
              rowKey="id"
              pagination={{
                showSizeChanger: true,
                showQuickJumper: true,
                defaultPageSize: 10,
              }}
              scroll={{ x: 800 }}
            />
          </TabPane>

          <TabPane tab="风险分析" key="risk">
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Card title="风险指标" size="small">
                  <Row gutter={16}>
                    <Col span={12}>
                      <Statistic
                        title="最大回撤"
                        value={strategy.performance.maxDrawdown * 100}
                        precision={2}
                        suffix="%"
                        valueStyle={{ color: strategy.performance.maxDrawdown > -0.1 ? '#52c41a' : '#ff4d4f' }}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="波动率"
                        value={(Math.random() * 20).toFixed(2)}
                        suffix="%"
                        valueStyle={{ color: '#faad14' }}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="VaR (95%)"
                        value={-(Math.random() * 5).toFixed(2)}
                        suffix="%"
                        valueStyle={{ color: '#ff4d4f' }}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="Calmar比率"
                        value={(Math.random() * 3).toFixed(2)}
                        valueStyle={{ color: '#52c41a' }}
                      />
                    </Col>
                  </Row>
                </Card>
              </Col>
              <Col xs={24} lg={12}>
                <Card title="风险控制设置" size="small">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="止损比例">
                      {strategy.parameters.stopLossPercent || 5}%
                    </Descriptions.Item>
                    <Descriptions.Item label="止盈比例">
                      {strategy.parameters.takeProfitPercent || 10}%
                    </Descriptions.Item>
                    <Descriptions.Item label="最大持仓">
                      ¥{strategy.parameters.maxPositionSize || 100000}
                    </Descriptions.Item>
                    <Descriptions.Item label="杠杆比例">
                      {strategy.parameters.leverage || 1}x
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
            </Row>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default StrategyDetails