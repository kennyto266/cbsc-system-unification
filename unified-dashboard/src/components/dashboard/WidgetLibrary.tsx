/**
 * Widget Library Component - Displays available widgets for adding to dashboard
 */

import React from 'react'
import { Card, Row, Col, Button, Typography, Tag, Space } from 'antd'
import {
  RocketOutlined,
  TrophyOutlined,
  HistoryOutlined,
  StockOutlined,
  NotificationOutlined,
} from '@ant-design/icons'
import { WidgetType } from '../../types/widget'

const { Title, Text } = Typography

interface WidgetLibraryProps {
  availableTypes: WidgetType[]
  onAddWidget: (type: WidgetType, config?: any) => void
}

const widgetDefinitions = {
  'strategy-overview': {
    icon: <RocketOutlined />,
    title: '策略概览',
    description: '显示所有策略的基本信息和状态',
    tags: ['策略', '概览'],
    defaultSize: { w: 4, h: 4 },
  },
  'performance-metrics': {
    icon: <TrophyOutlined />,
    title: '性能指标',
    description: '展示详细的策略性能指标和分析',
    tags: ['性能', '指标', '分析'],
    defaultSize: { w: 6, h: 5 },
  },
  'backtest-results': {
    icon: <HistoryOutlined />,
    title: '回测结果',
    description: '显示策略历史回测结果和统计',
    tags: ['回测', '历史', '统计'],
    defaultSize: { w: 8, h: 6 },
  },
  'real-time-monitor': {
    icon: <StockOutlined />,
    title: '实时监控',
    description: '实时监控市场和策略执行状态',
    tags: ['实时', '监控', '市场'],
    defaultSize: { w: 6, h: 4 },
  },
  'news-announcement': {
    icon: <NotificationOutlined />,
    title: '新闻公告',
    description: '显示最新市场新闻和系统公告',
    tags: ['新闻', '公告', '资讯'],
    defaultSize: { w: 3, h: 5 },
  },
}

export const WidgetLibrary: React.FC<WidgetLibraryProps> = ({
  availableTypes,
  onAddWidget,
}) => {
  const handleAddWidget = (type: WidgetType) => {
    const definition = widgetDefinitions[type]
    onAddWidget(type, {
      w: definition.defaultSize.w,
      h: definition.defaultSize.h,
    })
  }

  return (
    <div className="widget-library">
      <Space direction="vertical" size="large" className="w-full">
        <div>
          <Title level={4}>选择组件</Title>
          <Text type="secondary">
            点击添加组件到仪表板，支持拖拽调整大小和位置
          </Text>
        </div>

        <Row gutter={[16, 16]}>
          {availableTypes.map(type => {
            const definition = widgetDefinitions[type]
            return (
              <Col span={24} key={type}>
                <Card
                  hoverable
                  size="small"
                  className="widget-card"
                  actions={[
                    <Button
                      type="primary"
                      size="small"
                      onClick={() => handleAddWidget(type)}
                    >
                      添加到仪表板
                    </Button>,
                  ]}
                >
                  <Card.Meta
                    avatar={
                      <div className="text-2xl text-blue-500">
                        {definition.icon}
                      </div>
                    }
                    title={
                      <Space>
                        {definition.title}
                        <Tag size="small">
                          {definition.defaultSize.w}x{definition.defaultSize.h}
                        </Tag>
                      </Space>
                    }
                    description={
                      <div className="space-y-2">
                        <Text type="secondary">{definition.description}</Text>
                        <div>
                          {definition.tags.map(tag => (
                            <Tag key={tag} size="small">{tag}</Tag>
                          ))}
                        </div>
                      </div>
                    }
                  />
                </Card>
              </Col>
            )
          })}
        </Row>

        <div className="text-center">
          <Text type="secondary" className="text-xs">
            提示：组件默认大小为 {widgetDefinitions[availableTypes[0]]?.defaultSize.w}x{widgetDefinitions[availableTypes[0]]?.defaultSize.h} 网格单位
          </Text>
        </div>
      </Space>
    </div>
  )
}