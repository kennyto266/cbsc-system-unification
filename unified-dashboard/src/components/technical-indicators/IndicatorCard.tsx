import React from 'react'
import {
  Card,
  Tag,
  Button,
  Tooltip,
  Space,
  Typography,
  Row,
  Col,
  Avatar
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

interface IndicatorCardProps {
  indicator: TechnicalIndicator
  onSelect: () => void
  onToggleFavorite: (e: React.MouseEvent) => void
  onAddToConfiguration: () => void
  size?: 'small' | 'default' | 'large'
  showActions?: boolean
}

const IndicatorCard: React.FC<IndicatorCardProps> = ({
  indicator,
  onSelect,
  onToggleFavorite,
  onAddToConfiguration,
  size = 'default',
  showActions = true
}) => {
  const categoryInfo = INDICATOR_CATEGORIES[indicator.category]

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.3,
        ease: 'easeOut'
      }
    },
    hover: {
      y: -5,
      transition: {
        duration: 0.2
      }
    }
  }

  const getParameterSummary = () => {
    if (indicator.parameters.length === 0) return '无需参数'
    const mainParams = indicator.parameters.slice(0, 2)
    const paramsText = mainParams.map(p => `${p.name}: ${p.value}`).join(', ')
    return indicator.parameters.length > 2 ? `${paramsText}...` : paramsText
  }

  const getSignalCount = () => {
    const buySignals = indicator.signals?.buy?.length || 0
    const sellSignals = indicator.signals?.sell?.length || 0
    return buySignals + sellSignals
  }

  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      whileHover="hover"
      layout
    >
      <Card
        hoverable
        className={`h-full indicator-card ${indicator.favorite ? 'favorite-card' : ''}`}
        onClick={onSelect}
        bodyStyle={{ padding: size === 'small' ? '12px' : '16px' }}
        style={{
          border: indicator.favorite ? `2px solid ${categoryInfo.color}` : undefined,
          background: `linear-gradient(135deg, ${categoryInfo.color}08 0%, transparent 100%)`
        }}
        actions={showActions ? [
          <Tooltip title="查看详情">
            <EyeOutlined key="view" onClick={onSelect} />
          </Tooltip>,
          <Tooltip title={indicator.favorite ? '取消收藏' : '添加收藏'}>
            {indicator.favorite ? (
              <StarFilled
                key="favorite"
                style={{ color: '#faad14' }}
                onClick={onToggleFavorite}
              />
            ) : (
              <StarOutlined key="favorite" onClick={onToggleFavorite} />
            )}
          </Tooltip>,
          <Tooltip title="添加到配置">
            <PlusOutlined key="add" onClick={(e) => {
              e.stopPropagation()
              onAddToConfiguration()
            }} />
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
              参数: {getParameterSummary()}
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

        {/* Tags */}
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
                {getSignalCount()}
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

        {/* Quick Actions (for larger cards) */}
        {size === 'large' && showActions && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <Space size="small">
              <Button
                size="small"
                type="primary"
                ghost
                icon={<PlusOutlined />}
                onClick={(e) => {
                  e.stopPropagation()
                  onAddToConfiguration()
                }}
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
}

export default IndicatorCard