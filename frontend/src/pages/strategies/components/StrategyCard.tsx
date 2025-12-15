import React from 'react'
import { Card, Tag, Button, Space, Tooltip, Progress } from 'antd'
import {
  EditOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  EyeOutlined,
  MoreOutlined,
  TrendingUpOutlined,
  TrendingDownOutlined,
  FireOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import type { Strategy } from '../types'
import { StrategyStatus, StrategyType } from '../types'

// Strategy Card Component - 策略卡片组件
interface StrategyCardProps {
  strategy: Strategy
  onRun?: (id: string) => void
  onStop?: (id: string) => void
  onPause?: (id: string) => void
  onEdit?: (id: string) => void
  onDelete?: (id: string) => void
  onDuplicate?: (id: string) => void
}

const StrategyCard: React.FC<StrategyCardProps> = ({
  strategy,
  onRun,
  onStop,
  onPause,
  onEdit,
  onDelete,
  onDuplicate,
}) => {
  const navigate = useNavigate()

  // Get status color
  const getStatusColor = (status: StrategyStatus) => {
    const colorMap = {
      [StrategyStatus.DRAFT]: 'default',
      [StrategyStatus.ACTIVE]: 'processing',
      [StrategyStatus.PAUSED]: 'warning',
      [StrategyStatus.STOPPED]: 'default',
      [StrategyStatus.ARCHIVED]: 'default',
      [StrategyStatus.ERROR]: 'error',
    }
    return colorMap[status] || 'default'
  }

  // Get status text
  const getStatusText = (status: StrategyStatus) => {
    const textMap = {
      [StrategyStatus.DRAFT]: '草稿',
      [StrategyStatus.ACTIVE]: '运行中',
      [StrategyStatus.PAUSED]: '已暂停',
      [StrategyStatus.STOPPED]: '已停止',
      [StrategyStatus.ARCHIVED]: '已归档',
      [StrategyStatus.ERROR]: '错误',
    }
    return textMap[status] || '未知'
  }

  // Get type text
  const getTypeText = (type: StrategyType) => {
    const typeMap = {
      [StrategyType.MOMENTUM]: '动量',
      [StrategyType.MEAN_REVERSION]: '均值回归',
      [StrategyType.ARBITRAGE]: '套利',
      [StrategyType.TREND_FOLLOWING]: '趋势跟踪',
      [StrategyType.CUSTOM]: '自定义',
    }
    return typeMap[type] || '未知'
  }

  // Get type icon
  const getTypeIcon = (type: StrategyType) => {
    const iconMap = {
      [StrategyType.MOMENTUM]: <TrendingUpOutlined />,
      [StrategyType.MEAN_REVERSION]: <TrendingDownOutlined />,
      [StrategyType.ARBITRAGE]: <FireOutlined />,
      [StrategyType.TREND_FOLLOWING]: <TrendingUpOutlined />,
      [StrategyType.CUSTOM]: <MoreOutlined />,
    }
    return iconMap[type] || <MoreOutlined />
  }

  // Performance color
  const getPerformanceColor = (value: number) => {
    if (value > 0.1) return '#52c41a'
    if (value > 0) return '#73d13d'
    if (value < -0.1) return '#ff4d4f'
    if (value < 0) return '#ff7875'
    return '#8c8c8c'
  }

  // Performance icon
  const getPerformanceIcon = (value: number) => {
    if (value > 0) return <TrendingUpOutlined />
    if (value < 0) return <TrendingDownOutlined />
    return null
  }

  // Action buttons
  const actions = [
    <Tooltip title="查看详情" key="view">
      <Button
        type="text"
        icon={<EyeOutlined />}
        onClick={() => navigate(`/strategies/${strategy.id}`)}
      />
    </Tooltip>,
    <Tooltip title="编辑" key="edit">
      <Button
        type="text"
        icon={<EditOutlined />}
        onClick={() => onEdit?.(strategy.id)}
      />
    </Tooltip>,
  ]

  // Add control buttons based on status
  if (strategy.status === StrategyStatus.ACTIVE) {
    actions.push(
      <Tooltip title="暂停" key="pause">
        <Button
          type="text"
          icon={<PauseCircleOutlined />}
          onClick={() => onPause?.(strategy.id)}
        />
      </Tooltip>
    )
  } else if (strategy.status === StrategyStatus.PAUSED || strategy.status === StrategyStatus.STOPPED) {
    actions.push(
      <Tooltip title="启动" key="start">
        <Button
          type="text"
          icon={<PlayCircleOutlined />}
          onClick={() => onRun?.(strategy.id)}
        />
      </Tooltip>
    )
  }

  return (
    <Card
      hoverable
      className="h-full"
      actions={actions}
      cover={
        <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-lg font-semibold mb-1 truncate">{strategy.name}</h3>
              <Space>
                <Tag color={getStatusColor(strategy.status)}>
                  {getStatusText(strategy.status)}
                </Tag>
                <Tag icon={getTypeIcon(strategy.type)} color="blue">
                  {getTypeText(strategy.type)}
                </Tag>
              </Space>
            </div>
          </div>
        </div>
      }
    >
      <Card.Meta
        description={
          <div className="space-y-3">
            {/* Description */}
            {strategy.description && (
              <p className="text-gray-600 text-sm line-clamp-2">
                {strategy.description}
              </p>
            )}

            {/* Performance Summary */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-gray-500 mb-1">总收益率</p>
                <div className="flex items-center">
                  {strategy.performance?.totalReturn !== undefined && (
                    <>
                      {getPerformanceIcon(strategy.performance.totalReturn)}
                      <span
                        className="font-semibold text-sm ml-1"
                        style={{ color: getPerformanceColor(strategy.performance.totalReturn) }}
                      >
                        {(strategy.performance.totalReturn * 100).toFixed(2)}%
                      </span>
                    </>
                  )}
                  {strategy.performance?.totalReturn === undefined && (
                    <span className="text-gray-400 text-sm">-</span>
                  )}
                </div>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">夏普比率</p>
                <span className="font-semibold text-sm">
                  {strategy.performance?.sharpeRatio?.toFixed(2) || '-'}
                </span>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">胜率</p>
                <span className="font-semibold text-sm">
                  {strategy.performance?.winRate
                    ? `${(strategy.performance.winRate * 100).toFixed(1)}%`
                    : '-'}
                </span>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">最大回撤</p>
                <span className="font-semibold text-sm text-red-500">
                  {strategy.performance?.maxDrawdown
                    ? `-${(strategy.performance.maxDrawdown * 100).toFixed(2)}%`
                    : '-'}
                </span>
              </div>
            </div>

            {/* Risk Level Indicator */}
            <div>
              <p className="text-xs text-gray-500 mb-1">风险等级</p>
              <Progress
                percent={strategy.performance?.maxDrawdown ? strategy.performance.maxDrawdown * 100 : 0}
                strokeColor={
                  strategy.performance?.maxDrawdown
                    ? strategy.performance.maxDrawdown > 0.2
                      ? '#ff4d4f'
                      : strategy.performance.maxDrawdown > 0.1
                      ? '#faad14'
                      : '#52c41a'
                    : '#d9d9d9'
                }
                showInfo={false}
                size="small"
              />
            </div>

            {/* Tags */}
            {strategy.tags && strategy.tags.length > 0 && (
              <div className="pt-2">
                <Space wrap size={[0, 4]}>
                  {strategy.tags.slice(0, 3).map(tag => (
                    <Tag key={tag} size="small">
                      {tag}
                    </Tag>
                  ))}
                  {strategy.tags.length > 3 && (
                    <Tag size="small">+{strategy.tags.length - 3}</Tag>
                  )}
                </Space>
              </div>
            )}

            {/* Last Run Time */}
            {strategy.lastRunAt && (
              <p className="text-xs text-gray-500">
                最后运行: {new Date(strategy.lastRunAt).toLocaleString()}
              </p>
            )}
          </div>
        }
      />
    </Card>
  )
}

export default StrategyCard