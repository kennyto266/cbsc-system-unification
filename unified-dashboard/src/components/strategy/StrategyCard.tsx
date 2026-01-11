import React from 'react'
import { Card, Tag, Button, Space, Tooltip, Progress, Row, Col, Statistic } from 'antd'
import {
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  EyeOutlined,
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons'
import { Strategy, StrategyType, StrategyStatus } from '../../types'

// Strategy type color mapping
const strategyTypeColors: Record<StrategyType, string> = {
  [StrategyType.SENTIMENT]: 'blue',
  [StrategyType.TECHNICAL]: 'green',
  [StrategyType.MOMENTUM]: 'purple',
  [StrategyType.MEAN_REVERSION]: 'orange',
  [StrategyType.ARBITRAGE]: 'cyan',
}

// Strategy status color mapping
const strategyStatusColors: Record<StrategyStatus, string> = {
  [StrategyStatus.ACTIVE]: 'success',
  [StrategyStatus.INACTIVE]: 'default',
  [StrategyStatus.TESTING]: 'processing',
  [StrategyStatus.ARCHIVED]: 'error',
}

// Risk level color mapping
const riskLevelColors: Record<string, string> = {
  low: 'green',
  medium: 'orange',
  high: 'red',
}

interface StrategyCardProps {
  strategy: Strategy
  onEdit?: (strategy: Strategy) => void
  onDelete?: (strategyId: string) => void
  onView?: (strategy: Strategy) => void
  onStatusChange?: (strategyId: string, newStatus: StrategyStatus) => void
  loading?: boolean
}

const StrategyCard: React.FC<StrategyCardProps> = ({
  strategy,
  onEdit,
  onDelete,
  onView,
  onStatusChange,
  loading = false,
}) => {
  const performanceColor = strategy.performance.totalReturn >= 0 ? '#52c41a' : '#ff4d4f'
  const performanceIcon = strategy.performance.totalReturn >= 0 ? <RiseOutlined /> : <FallOutlined />

  return (
    <Card
      className="h-full hover:shadow-lg transition-shadow duration-300"
      size="small"
      actions={[
        <Tooltip title="查看详情">
          <EyeOutlined key="view" onClick={() => onView?.(strategy)} />
        </Tooltip>,
        <Tooltip title="编辑">
          <EditOutlined key="edit" onClick={() => onEdit?.(strategy)} />
        </Tooltip>,
        strategy.status === StrategyStatus.ACTIVE ? (
          <Tooltip title="暂停">
            <PauseCircleOutlined
              key="pause"
              onClick={() => onStatusChange?.(strategy.id, StrategyStatus.INACTIVE)}
            />
          </Tooltip>
        ) : (
          <Tooltip title="启动">
            <PlayCircleOutlined
              key="play"
              onClick={() => onStatusChange?.(strategy.id, StrategyStatus.ACTIVE)}
            />
          </Tooltip>
        ),
        <Tooltip title="删除">
          <DeleteOutlined key="delete" onClick={() => onDelete?.(strategy.id)} />
        </Tooltip>,
      ]}
      loading={loading}
    >
      {/* Header */}
      <div className="mb-3">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-lg font-semibold truncate flex-1">{strategy.name}</h3>
          <Tag color={strategyStatusColors[strategy.status]}>
            {strategy.status}
          </Tag>
        </div>
        <p className="text-gray-600 text-sm line-clamp-2 mb-3">
          {strategy.description}
        </p>

        {/* Tags */}
        <Space wrap className="mb-3">
          <Tag color={strategyTypeColors[strategy.type]}>
            {strategy.type}
          </Tag>
          <Tag color={riskLevelColors[strategy.riskLevel]}>
            {strategy.riskLevel.toUpperCase()} RISK
          </Tag>
        </Space>
      </div>

      {/* Performance Metrics */}
      <div className="space-y-3">
        <Row gutter={16}>
          <Col span={12}>
            <Statistic
              title="总收益率"
              value={strategy.performance.totalReturn * 100}
              precision={2}
              suffix="%"
              valueStyle={{ color: performanceColor, fontSize: '16px' }}
              prefix={performanceIcon}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="夏普比率"
              value={strategy.performance.sharpeRatio}
              precision={2}
              valueStyle={{
                color: strategy.performance.sharpeRatio >= 1 ? '#52c41a' : '#faad14',
                fontSize: '16px'
              }}
              prefix={<TrophyOutlined />}
            />
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Statistic
              title="胜率"
              value={strategy.performance.winRate * 100}
              precision={1}
              suffix="%"
              valueStyle={{
                color: strategy.performance.winRate >= 0.6 ? '#52c41a' : '#faad14',
                fontSize: '14px'
              }}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="最大回撤"
              value={strategy.performance.maxDrawdown * 100}
              precision={2}
              suffix="%"
              valueStyle={{
                color: strategy.performance.maxDrawdown > -0.1 ? '#52c41a' : '#ff4d4f',
                fontSize: '14px'
              }}
            />
          </Col>
        </Row>

        {/* Progress bars for visual indicators */}
        <div className="space-y-2">
          <div>
            <div className="flex justify-between text-xs text-gray-600 mb-1">
              <span>胜率</span>
              <span>{(strategy.performance.winRate * 100).toFixed(1)}%</span>
            </div>
            <Progress
              percent={strategy.performance.winRate * 100}
              size="small"
              strokeColor={strategy.performance.winRate >= 0.6 ? '#52c41a' : '#faad14'}
            />
          </div>

          <div>
            <div className="flex justify-between text-xs text-gray-600 mb-1">
              <span>收益表现</span>
              <span>{Math.max(0, Math.min(100, 50 + strategy.performance.totalReturn * 500)).toFixed(0)}%</span>
            </div>
            <Progress
              percent={Math.max(0, Math.min(100, 50 + strategy.performance.totalReturn * 500))}
              size="small"
              strokeColor={performanceColor}
            />
          </div>
        </div>
      </div>

      {/* Footer with timestamps */}
      <div className="mt-4 pt-3 border-t border-gray-200">
        <div className="flex justify-between text-xs text-gray-500">
          <span>创建: {new Date(strategy.createdAt).toLocaleDateString()}</span>
          {strategy.lastActive && (
            <span>活跃: {new Date(strategy.lastActive).toLocaleDateString()}</span>
          )}
        </div>
      </div>
    </Card>
  )
}

export default StrategyCard