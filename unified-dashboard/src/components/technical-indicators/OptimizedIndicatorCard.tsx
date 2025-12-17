import React, { memo, useCallback, useMemo } from 'react'
import {
  Card,
  Tag,
  Button,
  Tooltip,
  Space,
  Typography,
  Row,
  Col,
  Avatar,
  Skeleton
} from 'antd'
import {
  StarOutlined,
  StarFilled,
  PlusOutlined,
  EyeOutlined,
  SettingOutlined,
  BookOutlined
} from '@ant-design/icons'
import { motion } from 'framer-motion'

import { TechnicalIndicator, IndicatorCategory } from '../../types/technical-indicators'
import { INDICATOR_CATEGORIES } from '../../data/technical-indicators-library'

const { Title, Text, Paragraph } = Typography

interface OptimizedIndicatorCardProps {
  indicator: TechnicalIndicator
  onSelect: () => void
  onToggleFavorite: (e: React.MouseEvent) => void
  onAddToConfiguration: () => void
  size?: 'small' | 'default' | 'large'
  showActions?: boolean
  loading?: boolean
  lazy?: boolean
}

// 缓存分类信息以避免重复计算
const categoryCache = new Map<IndicatorCategory, any>()

// 使用 memo 和自定义比较函数优化重渲染
const OptimizedIndicatorCard = memo<OptimizedIndicatorCardProps>(({
  indicator,
  onSelect,
  onToggleFavorite,
  onAddToConfiguration,
  size = 'default',
  showActions = true,
  loading = false,
  lazy = true
}) => {
  // 缓存分类信息
  const categoryInfo = useMemo(() => {
    if (categoryCache.has(indicator.category)) {
      return categoryCache.get(indicator.category)
    }

    const info = INDICATOR_CATEGORIES[indicator.category]
    categoryCache.set(indicator.category, info)
    return info
  }, [indicator.category])

  // 缓存参数摘要
  const parameterSummary = useMemo(() => {
    if (indicator.parameters.length === 0) return '无需参数'
    const mainParams = indicator.parameters.slice(0, 2)
    const paramsText = mainParams.map(p => `${p.name}: ${p.value}`).join(', ')
    return indicator.parameters.length > 2 ? `${paramsText}...` : paramsText
  }, [indicator.parameters])

  // 缓存信号数量
  const signalCount = useMemo(() => {
    const buySignals = indicator.signals?.buy?.length || 0
    const sellSignals = indicator.signals?.sell?.length || 0
    return buySignals + sellSignals
  }, [indicator.signals])

  // 使用 useCallback 避免函数重创建
  const handleSelect = useCallback(() => {
    onSelect()
  }, [onSelect])

  const handleToggleFavorite = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    onToggleFavorite(e)
  }, [onToggleFavorite])

  const handleAddToConfiguration = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    onAddToConfiguration()
  }, [onAddToConfiguration])

  // 动画变体 - 使用更简单的动画以提高性能
  const cardVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
    hover: { y: -2 }
  }

  // 如果正在加载，显示骨架屏
  if (loading) {
    return (
      <Card className="h-full">
        <Skeleton avatar paragraph={{ rows: 4 }} active />
      </Card>
    )
  }

  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      whileHover="hover"
      transition={{ duration: 0.2 }}
      layout
    >
      <Card
        hoverable
        className={`h-full indicator-card ${indicator.favorite ? 'favorite-card' : ''}`}
        onClick={handleSelect}
        bodyStyle={{ padding: size === 'small' ? '12px' : '16px' }}
        style={{
          border: indicator.favorite ? `2px solid ${categoryInfo.color}` : undefined,
          background: `linear-gradient(135deg, ${categoryInfo.color}08 0%, transparent 100%)`
        }}
        actions={showActions ? [
          <Tooltip title="查看详情" key="view">
            <EyeOutlined onClick={handleSelect} />
          </Tooltip>,
          <Tooltip title={indicator.favorite ? '取消收藏' : '添加收藏'} key="favorite">
            {indicator.favorite ? (
              <StarFilled
                style={{ color: '#faad14' }}
                onClick={handleToggleFavorite}
              />
            ) : (
              <StarOutlined onClick={handleToggleFavorite} />
            )}
          </Tooltip>,
          <Tooltip title="添加到配置" key="add">
            <PlusOutlined onClick={handleAddToConfiguration} />
          </Tooltip>
        ] : undefined}
      >
        {/* Card Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center">
            <Avatar
              size={size === 'small' ? 32 : 40}
              style={{
                backgroundColor: categoryInfo.color,
                marginRight: '8px'
              }}
              icon={categoryInfo.icon}
            />
            <div className="flex-1">
              <Title
                level={size === 'small' ? 5 : 4}
                className="!mb-0 !leading-tight"
                ellipsis={{ rows: 1 }}
              >
                {indicator.name}
              </Title>
              <Space size={4} className="mt-1">
                <Tag
                  color={categoryInfo.color}
                  size="small"
                  style={{ margin: 0 }}
                >
                  {categoryInfo.name}
                </Tag>
                {indicator.custom && (
                  <Tag color="purple" size="small" style={{ margin: 0 }}>
                    自定义
                  </Tag>
                )}
              </Space>
            </div>
          </div>
          {indicator.favorite && (
            <StarFilled
              className="text-yellow-500"
              style={{ fontSize: '16px' }}
            />
          )}
        </div>

        {/* Description */}
        <Paragraph
          ellipsis={{ rows: size === 'small' ? 2 : 3 }}
          className="text-gray-600 mb-3"
          style={{ fontSize: '12px', lineHeight: '1.4' }}
        >
          {indicator.description}
        </Paragraph>

        {/* Parameters Summary */}
        {indicator.parameters.length > 0 && (
          <div className="mb-3">
            <Text type="secondary" style={{ fontSize: '11px' }}>
              参数: {parameterSummary}
            </Text>
          </div>
        )}

        {/* Visual Settings Preview */}
        <div className="mb-3">
          <div className="flex items-center justify-between">
            <Text type="secondary" style={{ fontSize: '11px' }}>
              样式预览
            </Text>
            <div className="flex items-center space-x-2">
              <div
                className="w-8 h-1 rounded"
                style={{
                  backgroundColor: indicator.visualSettings.color,
                  opacity: indicator.visualSettings.opacity
                }}
              />
              {indicator.visualSettings.style === 'histogram' && (
                <div
                  className="w-1 h-3 rounded"
                  style={{
                    backgroundColor: indicator.visualSettings.color,
                    opacity: indicator.visualSettings.opacity
                  }}
                />
              )}
            </div>
          </div>
        </div>

        {/* Tags - 只显示前3个 */}
        {indicator.tags.length > 0 && (
          <div className="mb-3">
            <Space wrap size={[4, 4]}>
              {indicator.tags.slice(0, 3).map((tag) => (
                <Tag
                  key={tag}
                  size="small"
                  style={{ margin: 0, fontSize: '10px' }}
                >
                  {tag}
                </Tag>
              ))}
              {indicator.tags.length > 3 && (
                <Tag size="small" style={{ margin: 0, fontSize: '10px' }}>
                  +{indicator.tags.length - 3}
                </Tag>
              )}
            </Space>
          </div>
        )}

        {/* Footer Stats */}
        <Row gutter={8} className="pt-2 border-t border-gray-100">
          <Col span={8}>
            <div className="text-center">
              <Text style={{ fontSize: '16px', fontWeight: 600 }}>
                {indicator.parameters.length}
              </Text>
              <div>
                <Text type="secondary" style={{ fontSize: '10px' }}>
                  参数
                </Text>
              </div>
            </div>
          </Col>
          <Col span={8}>
            <div className="text-center">
              <Text style={{ fontSize: '16px', fontWeight: 600 }}>
                {signalCount}
              </Text>
              <div>
                <Text type="secondary" style={{ fontSize: '10px' }}>
                  信号
                </Text>
              </div>
            </div>
          </Col>
          <Col span={8}>
            <div className="text-center">
              <Text style={{ fontSize: '16px', fontWeight: 600 }}>
                {indicator.tags.length}
              </Text>
              <div>
                <Text type="secondary" style={{ fontSize: '10px' }}>
                  标签
                </Text>
              </div>
            </div>
          </Col>
        </Row>

        {/* Quick Actions (仅在大尺寸卡片显示) */}
        {size === 'large' && showActions && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <Space size="small">
              <Button
                size="small"
                type="primary"
                ghost
                icon={<PlusOutlined />}
                onClick={handleAddToConfiguration}
              >
                添加
              </Button>
              <Button
                size="small"
                icon={<SettingOutlined />}
                onClick={(e) => {
                  e.stopPropagation()
                  // Open configuration
                }}
              >
                配置
              </Button>
              <Button
                size="small"
                icon={<BookOutlined />}
                onClick={(e) => {
                  e.stopPropagation()
                  // Open documentation
                }}
              >
                文档
              </Button>
            </Space>
          </div>
        )}
      </Card>

      <style jsx>{`
        .indicator-card {
          transition: all 0.3s ease;
          border-radius: 8px;
        }

        .indicator-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        }

        .favorite-card {
          position: relative;
          overflow: hidden;
        }

        .favorite-card::before {
          content: '';
          position: absolute;
          top: 0;
          right: 0;
          width: 60px;
          height: 60px;
          background: linear-gradient(
            135deg,
            transparent 0%,
            transparent 50%,
            rgba(250, 173, 20, 0.1) 50%,
            rgba(250, 173, 20, 0.1) 100%
          );
          z-index: 0;
        }
      `}</style>
    </motion.div>
  )
}, (prevProps, nextProps) => {
  // 自定义比较函数，仅比较真正影响渲染的属性
  const propsToCompare = [
    'indicator.id',
    'indicator.favorite',
    'indicator.name',
    'indicator.description',
    'size',
    'showActions',
    'loading'
  ]

  for (const prop of propsToCompare) {
    const keys = prop.split('.')
    let prevValue = prevProps as any
    let nextValue = nextProps as any

    for (const key of keys) {
      prevValue = prevValue?.[key]
      nextValue = nextValue?.[key]
    }

    if (prevValue !== nextValue) {
      return false // 需要重新渲染
    }
  }

  return true // 不需要重新渲染
})

OptimizedIndicatorCard.displayName = 'OptimizedIndicatorCard'

export default OptimizedIndicatorCard