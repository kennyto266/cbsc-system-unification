import React, { useState } from 'react'
import { Card, Tag, Button, Space, Progress, Tooltip, Dropdown, Menu, Checkbox, Badge } from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  EditOutlined,
  CopyOutlined,
  DeleteOutlined,
  MoreOutlined,
  TrophyOutlined,
  LineChartOutlined,
  ExclamationCircleOutlined,
  FireOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'

import { Strategy, StrategyStatus, RiskLevel } from '../../types'

// Styles
import './StrategyCard.css'

interface StrategyCardProps {
  strategy: Strategy
  onStart: () => void
  onStop: () => void
  onPause: () => void
  onResume: () => void
  onEdit: () => void
  onDuplicate: () => void
  onDelete: () => void
  onSelect?: (selected: boolean) => void
  selected?: boolean
  compact?: boolean
}

const StrategyCard: React.FC<StrategyCardProps> = ({
  strategy,
  onStart,
  onStop,
  onPause,
  onResume,
  onEdit,
  onDuplicate,
  onDelete,
  onSelect,
  selected = false,
  compact = false,
}) => {
  const navigate = useNavigate()
  const [isActionsMenuOpen, setIsActionsMenuOpen] = useState(false)

  // Get status configuration
  const getStatusConfig = (status: StrategyStatus) => {
    const configs = {
      active: { color: 'success', text: '運行中', icon: <FireOutlined /> },
      inactive: { color: 'default', text: '已停止', icon: <StopOutlined /> },
      testing: { color: 'processing', text: '測試中', icon: <ExclamationCircleOutlined /> },
      archived: { color: 'warning', text: '已歸檔', icon: <StopOutlined /> },
    }
    return configs[status] || configs.inactive
  }

  // Get risk level configuration
  const getRiskConfig = (level: RiskLevel) => {
    const configs = {
      low: { color: 'green', text: '低風險', icon: '🟢' },
      medium: { color: 'orange', text: '中風險', icon: '🟡' },
      high: { color: 'red', text: '高風險', icon: '🔴' },
    }
    return configs[level] || configs.medium
  }

  // Get performance color
  const getPerformanceColor = (value: number) => {
    if (value > 0.1) return '#52c41a'
    if (value > 0) return '#73d13d'
    if (value < -0.1) return '#ff4d4f'
    return '#ffa940'
  }

  // Format performance value
  const formatPerformance = (value: number, isPercentage = true) => {
    const formatted = value.toFixed(2)
    return isPercentage ? `${value > 0 ? '+' : ''}${formatted}%` : formatted
  }

  // Status config
  const statusConfig = getStatusConfig(strategy.status)
  const riskConfig = getRiskConfig(strategy.riskLevel)

  // Action menu items
  const actionMenuItems = [
    {
      key: 'edit',
      icon: <EditOutlined />,
      label: '編輯策略',
      onClick: onEdit,
    },
    {
      key: 'duplicate',
      icon: <CopyOutlined />,
      label: '複製策略',
      onClick: onDuplicate,
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: '刪除策略',
      onClick: onDelete,
      danger: true,
    },
  ]

  // Main action button based on status
  const getMainActionButton = () => {
    switch (strategy.status) {
      case StrategyStatus.ACTIVE:
        return (
          <Button
            icon={<PauseCircleOutlined />}
            onClick={onPause}
            size="small"
          >
            暫停
          </Button>
        )
      case StrategyStatus.INACTIVE:
        return (
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={onStart}
            size="small"
          >
            啟動
          </Button>
        )
      case StrategyStatus.PAUSED:
        return (
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={onResume}
            size="small"
          >
            恢復
          </Button>
        )
      default:
        return (
          <Button
            icon={<PlayCircleOutlined />}
            onClick={onStart}
            size="small"
            disabled
          >
            啟動
          </Button>
        )
    }
  }

  // Card click handler
  const handleCardClick = (e: React.MouseEvent) => {
    // Prevent navigation when clicking on buttons
    if ((e.target as HTMLElement).closest('button, .ant-dropdown')) {
      return
    }
    navigate(`/strategies/${strategy.id}`)
  }

  return (
    <motion.div
      whileHover={{ y: -4, boxShadow: '0 8px 24px rgba(0,0,0,0.12)' }}
      whileTap={{ scale: 0.98 }}
      className={`strategy-card ${compact ? 'compact' : ''} ${selected ? 'selected' : ''}`}
      onClick={handleCardClick}
    >
      <Card
        hoverable
        className="strategy-card-content"
        bodyStyle={{ padding: compact ? '12px' : '16px' }}
        extra={
          onSelect && (
            <Checkbox
              checked={selected}
              onChange={(e) => {
                e.stopPropagation()
                onSelect(e.target.checked)
              }}
            />
          )
        }
      >
        {/* Header */}
        <div className="strategy-header">
          <div className="strategy-title">
            <h4 className="strategy-name">{strategy.name}</h4>
            <Tag color={statusConfig.color} className="strategy-status">
              {statusConfig.icon} {statusConfig.text}
            </Tag>
          </div>

          <div className="strategy-actions">
            <Space size="small">
              {getMainActionButton()}
              <Dropdown
                menu={{ items: actionMenuItems }}
                trigger={['click']}
                onOpenChange={setIsActionsMenuOpen}
                placement="bottomRight"
              >
                <Button
                  icon={<MoreOutlined />}
                  size="small"
                  onClick={(e) => e.stopPropagation()}
                />
              </Dropdown>
            </Space>
          </div>
        </div>

        {/* Basic Info */}
        <div className="strategy-info">
          <div className="info-row">
            <span className="label">類型:</span>
            <Tag>{strategy.type}</Tag>
            <span className="label" style={{ marginLeft: 16 }}>風險:</span>
            <Tag color={riskConfig.color}>
              {riskConfig.icon} {riskConfig.text}
            </Tag>
          </div>
          <div className="info-row">
            <span className="label">最後更新:</span>
            <span className="value">{dayjs(strategy.updatedAt).format('MM-DD HH:mm')}</span>
          </div>
        </div>

        {/* Performance Metrics */}
        {!compact && (
          <div className="strategy-performance">
            <div className="performance-grid">
              <div className="metric">
                <div className="metric-label">總回報</div>
                <div
                  className="metric-value"
                  style={{ color: getPerformanceColor(strategy.performance.totalReturn) }}
                >
                  {formatPerformance(strategy.performance.totalReturn * 100)}
                </div>
              </div>
              <div className="metric">
                <div className="metric-label">夏普比率</div>
                <div className="metric-value">
                  {strategy.performance.sharpeRatio.toFixed(2)}
                </div>
              </div>
              <div className="metric">
                <div className="metric-label">最大回撤</div>
                <div className="metric-value negative">
                  {formatPerformance(strategy.performance.maxDrawdown * 100)}
                </div>
              </div>
              <div className="metric">
                <div className="metric-label">勝率</div>
                <div className="metric-value">
                  {formatPerformance(strategy.performance.winRate * 100)}
                </div>
              </div>
            </div>

            {/* Progress Bar for Active Strategies */}
            {strategy.status === StrategyStatus.ACTIVE && (
              <div className="execution-progress">
                <div className="progress-info">
                  <span className="label">執行進度</span>
                  <span className="progress-value">
                    {Math.floor(Math.random() * 40 + 60)}% {/* Simulated progress */}
                  </span>
                </div>
                <Progress
                  percent={Math.floor(Math.random() * 40 + 60)}
                  showInfo={false}
                  size="small"
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
              </div>
            )}
          </div>
        )}

        {/* Compact Performance Summary */}
        {compact && (
          <div className="compact-performance">
            <Space size="small">
              <Badge
                count={`${formatPerformance(strategy.performance.totalReturn * 100)}`}
                style={{
                  backgroundColor: getPerformanceColor(strategy.performance.totalReturn),
                }}
              />
              <span className="compact-metric">夏普: {strategy.performance.sharpeRatio.toFixed(2)}</span>
              <span className="compact-metric">勝率: {formatPerformance(strategy.performance.winRate * 100)}</span>
            </Space>
          </div>
        )}

        {/* Strategy Description (if not compact) */}
        {!compact && strategy.description && (
          <div className="strategy-description">
            <p>{strategy.description}</p>
          </div>
        )}
      </Card>
    </motion.div>
  )
}

export default StrategyCard