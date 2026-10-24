/**
 * News Announcement Widget - Displays news and announcements
 */

import React from 'react'
import { List, Card, Tag, Avatar, Typography, Space, Button } from 'antd'
import {
  NotificationOutlined,
  BulbOutlined,
  AlertOutlined,
  TagOutlined,
  CalendarOutlined,
  RocketOutlined,
} from '@ant-design/icons'
import { WidgetContainer } from '../Widget/WidgetContainer'

const { Text, Paragraph } = Typography

interface NewsAnnouncementProps {
  news?: Array<{
    id: string
    title: string
    content: string
    type: 'market' | 'strategy' | 'system' | 'announcement'
    priority: 'high' | 'medium' | 'low'
    time: string
    source?: string
  }>
}

export const NewsAnnouncement: React.FC<NewsAnnouncementProps> = ({
  news = [],
}) => {
  // Default mock news if none provided
  const mockNews = news.length > 0 ? news : [
    {
      id: '1',
      title: '美联储利率决议影响市场波动',
      content: '美联储宣布维持利率不变，但暗示年内可能降息。科技股普遍上涨，纳斯达克指数创新高。',
      type: 'market' as const,
      priority: 'high' as const,
      time: '2小时前',
      source: '财经头条',
    },
    {
      id: '2',
      title: '新策略"量化动量"上线',
      content: '基于机器学习的量化动量策略已正式上线，历史回测年化收益率35%，夏普比率2.1。',
      type: 'strategy' as const,
      priority: 'medium' as const,
      time: '4小时前',
      source: '策略团队',
    },
    {
      id: '3',
      title: '系统维护通知',
      content: '将于本周六凌晨2:00-4:00进行系统维护，期间可能影响策略执行，请提前做好准备。',
      type: 'system' as const,
      priority: 'medium' as const,
      time: '6小时前',
      source: '技术团队',
    },
    {
      id: '4',
      title: 'BTC突破新高',
      content: '比特币价格突破45000美元，创近三个月新高。相关加密货币策略表现优异。',
      type: 'market' as const,
      priority: 'high' as const,
      time: '8小时前',
      source: '币世界',
    },
    {
      id: '5',
      title: '年度报告发布',
      content: '2023年度投资报告已发布，整体收益率28.5%，超越基准指数15个百分点。',
      type: 'announcement' as const,
      priority: 'low' as const,
      time: '1天前',
      source: '投资部',
    },
  ]

  const getTypeConfig = (type: string) => {
    const configs = {
      market: { icon: <BulbOutlined />, color: 'blue', label: '市场' },
      strategy: { icon: <RocketOutlined />, color: 'green', label: '策略' },
      system: { icon: <AlertOutlined />, color: 'orange', label: '系统' },
      announcement: { icon: <NotificationOutlined />, color: 'purple', label: '公告' },
    }
    return configs[type as keyof typeof configs] || configs.market
  }

  const getPriorityConfig = (priority: string) => {
    const configs = {
      high: { color: 'red', label: '重要' },
      medium: { color: 'orange', label: '普通' },
      low: { color: 'default', label: '一般' },
    }
    return configs[priority as keyof typeof configs] || configs.low
  }

  const newsItemRender = (item: any) => {
    const typeConfig = getTypeConfig(item.type)
    const priorityConfig = getPriorityConfig(item.priority)

    return (
      <List.Item
        actions={[
          <Button
            type="link"
            size="small"
            onClick={() => window.open('#', '_blank')}
          >
            查看详情
          </Button>,
        ]}
      >
        <List.Item.Meta
          avatar={
            <Avatar
              icon={typeConfig.icon}
              style={{
                backgroundColor: typeConfig.color === 'blue' ? '#1890ff' :
                                 typeConfig.color === 'green' ? '#52c41a' :
                                 typeConfig.color === 'orange' ? '#faad14' : '#722ed1',
              }}
            />
          }
          title={
            <Space>
              <Text strong>{item.title}</Text>
              {item.priority === 'high' && <Tag color="red" size="small">重要</Tag>}
            </Space>
          }
          description={
            <div className="space-y-2">
              <Paragraph
                ellipsis={{ rows: 2, expandable: false }}
                className="text-gray-600 mb-2"
              >
                {item.content}
              </Paragraph>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Tag color={typeConfig.color} size="small" icon={typeConfig.icon}>
                  {typeConfig.label}
                </Tag>
                <Tag color={priorityConfig.color} size="small">
                  {priorityConfig.label}
                </Tag>
                <span>{item.time}</span>
                {item.source && (
                  <>
                    <span>•</span>
                    <span>{item.source}</span>
                  </>
                )}
              </div>
            </div>
          }
        />
      </List.Item>
    )
  }

  const stats = {
    total: mockNews.length,
    unread: mockNews.filter(n => n.priority === 'high').length,
    market: mockNews.filter(n => n.type === 'market').length,
    strategy: mockNews.filter(n => n.type === 'strategy').length,
  }

  return (
    <WidgetContainer
      id="news-announcement"
      type="news-announcement"
      title="新闻公告"
      extra={
        <Space>
          <Tag icon={<NotificationOutlined />}>
            共 {stats.total} 条
          </Tag>
          {stats.unread > 0 && (
            <Tag color="red" icon={<AlertOutlined />}>
              {stats.unread} 条重要
            </Tag>
          )}
        </Space>
      }
    >
      <div className="space-y-4">
        {/* Quick Stats */}
        <div className="grid grid-cols-4 gap-2 text-center">
          <div className="bg-blue-50 rounded p-2">
            <div className="text-lg font-semibold text-blue-600">{stats.market}</div>
            <div className="text-xs text-gray-600">市场</div>
          </div>
          <div className="bg-green-50 rounded p-2">
            <div className="text-lg font-semibold text-green-600">{stats.strategy}</div>
            <div className="text-xs text-gray-600">策略</div>
          </div>
          <div className="bg-orange-50 rounded p-2">
            <div className="text-lg font-semibold text-orange-600">
              {mockNews.filter(n => n.type === 'system').length}
            </div>
            <div className="text-xs text-gray-600">系统</div>
          </div>
          <div className="bg-purple-50 rounded p-2">
            <div className="text-lg font-semibold text-purple-600">
              {mockNews.filter(n => n.type === 'announcement').length}
            </div>
            <div className="text-xs text-gray-600">公告</div>
          </div>
        </div>

        {/* News List */}
        <Card size="small" className="!border-none !shadow-none">
          <List
            dataSource={mockNews}
            renderItem={newsItemRender}
            size="small"
          />
        </Card>

        {/* View More Button */}
        <div className="text-center pt-2">
          <Button type="link" size="small">
            查看更多消息
          </Button>
        </div>
      </div>
    </WidgetContainer>
  )
}