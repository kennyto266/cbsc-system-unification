import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Progress, Alert, Button, Space, Typography, Tag, Divider } from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  DollarOutlined,
  TrophyOutlined,
  RocketOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
  EyeOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useTheme } from '../../contexts/ThemeContext'
import { useWindowSize, useBreakpoints } from '../../hooks/useWindowSize'
import { useWebSocket } from '../../hooks/useWebSocket'
import cbscAdapter from '../../adapters/CBSCAdapter'

const { Title, Text } = Typography

const NewDashboardPage: React.FC = () => {
  const { themeConfig, isDark } = useTheme()
  const { width } = useWindowSize()
  const { isMobile, isTablet } = useBreakpoints()
  const { isConnected } = useWebSocket()

  // State management
  const [loading, setLoading] = useState(false)
  const [systemStatus, setSystemStatus] = useState<any>(null)
  const [portfolioData, setPortfolioData] = useState<any>(null)
  const [strategies, setStrategies] = useState<any[]>([])

  // Load initial data
  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      // Load system status
      const status = await cbscAdapter.healthCheck()
      setSystemStatus(status)

      // Load portfolio data
      const portfolio = await cbscAdapter.getPortfolio()
      setPortfolioData(portfolio)

      // Load strategies
      const strategiesData = await cbscAdapter.getStrategies()
      setStrategies(strategiesData.slice(0, 5)) // Show first 5 strategies
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  // Mock data for demonstration
  const mockMetrics = {
    totalValue: 1250000,
    totalReturn: 12.5,
    sharpeRatio: 1.85,
    maxDrawdown: -8.2,
    winRate: 68.5,
    activeStrategies: 8,
    todayProfit: 15000,
  }

  const recentActivities = [
    { id: 1, type: 'strategy', name: 'RSI策略', action: '執行買入信號', time: '2分鐘前', status: 'success' },
    { id: 2, type: 'alert', name: '市場風險', action: '波動率超過閾值', time: '5分鐘前', status: 'warning' },
    { id: 3, type: 'strategy', name: 'MACD策略', action: '執行賣出信號', time: '10分鐘前', status: 'success' },
    { id: 4, type: 'system', name: '系統更新', action: '技術指標庫已更新', time: '30分鐘前', status: 'info' },
  ]

  // Calculate grid span based on screen size
  const getColSpan = () => {
    if (isMobile) return 24
    if (isTablet) return 12
    return 6
  }

  return (
    <div style={{ padding: isMobile ? '16px' : '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2} style={{ margin: 0, color: themeConfig.colors.text }}>
              CBSC 量化交易儀表板
            </Title>
            <Text type="secondary">
              實時監控您的交易策略和市場動態
            </Text>
          </Col>
          <Col>
            <Space>
              <Tag color={isConnected ? 'success' : 'error'}>
                {isConnected ? '已連接' : '未連接'}
              </Tag>
              <Button
                type="primary"
                icon={<ReloadOutlined />}
                onClick={loadDashboardData}
                loading={loading}
              >
                刷新數據
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* Connection Status Alert */}
      {!isConnected && (
        <Alert
          message="WebSocket連接斷開"
          description="實時數據更新暫停，請檢查網絡連接或刷新頁面。"
          type="warning"
          showIcon
          closable
          style={{ marginBottom: '24px' }}
        />
      )}

      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <Statistic
              title="總資產價值"
              value={mockMetrics.totalValue}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="HKD"
              valueStyle={{ color: themeConfig.colors.success }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <Statistic
              title="總收益率"
              value={mockMetrics.totalReturn}
              precision={2}
              suffix="%"
              prefix={mockMetrics.totalReturn >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              valueStyle={{
                color: mockMetrics.totalReturn >= 0 ? themeConfig.colors.success : themeConfig.colors.error
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <Statistic
              title="夏普比率"
              value={mockMetrics.sharpeRatio}
              precision={2}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: themeConfig.colors.primary }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <Statistic
              title="活躍策略"
              value={mockMetrics.activeStrategies}
              prefix={<RocketOutlined />}
              valueStyle={{ color: themeConfig.colors.info }}
            />
          </Card>
        </Col>
      </Row>

      {/* Second Row - Performance Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={8}>
          <Card title="策略表現" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text>勝率</Text>
                <Progress percent={mockMetrics.winRate} status="active" />
              </div>
              <div>
                <Text>最大回撤</Text>
                <Progress
                  percent={Math.abs(mockMetrics.maxDrawdown)}
                  status="active"
                  strokeColor={themeConfig.colors.error}
                  format={() => `${mockMetrics.maxDrawdown}%`}
                />
              </div>
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={16}>
          <Card title="今日盈虧" size="small">
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="今日盈虧"
                  value={mockMetrics.todayProfit}
                  precision={2}
                  prefix={mockMetrics.todayProfit >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                  suffix="HKD"
                  valueStyle={{
                    color: mockMetrics.todayProfit >= 0 ? themeConfig.colors.success : themeConfig.colors.error
                  }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="收益率"
                  value={(mockMetrics.todayProfit / mockMetrics.totalValue * 100)}
                  precision={2}
                  suffix="%"
                  valueStyle={{
                    color: mockMetrics.todayProfit >= 0 ? themeConfig.colors.success : themeConfig.colors.error
                  }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Third Row - Strategies and Activities */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card
            title="活躍策略"
            size="small"
            extra={
              <Button type="text" icon={<EyeOutlined />} size="small">
                查看全部
              </Button>
            }
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              {strategies.map((strategy, index) => (
                <div key={index} style={{
                  padding: '8px 0',
                  borderBottom: index < strategies.length - 1 ? `1px solid ${themeConfig.colors.border}` : 'none'
                }}>
                  <Row justify="space-between" align="middle">
                    <Col>
                      <Text strong>{strategy.name || `策略 ${index + 1}`}</Text>
                      <div>
                        <Tag color={strategy.status === 'active' ? 'success' : 'default'}>
                          {strategy.status === 'active' ? '運行中' : '已停止'}
                        </Tag>
                      </div>
                    </Col>
                    <Col>
                      <Text type={strategy.return >= 0 ? 'success' : 'danger'}>
                        {strategy.return >= 0 ? '+' : ''}{strategy.return || '0.00'}%
                      </Text>
                    </Col>
                  </Row>
                </div>
              ))}
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card
            title="最近活動"
            size="small"
            extra={
              <Button type="text" icon={<SettingOutlined />} size="small">
                設置
              </Button>
            }
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              {recentActivities.map((activity) => (
                <div key={activity.id} style={{
                  padding: '8px 0',
                  borderBottom: activity.id < recentActivities.length ? `1px solid ${themeConfig.colors.border}` : 'none'
                }}>
                  <Row justify="space-between" align="middle">
                    <Col flex="auto">
                      <div>
                        <Text strong>{activity.name}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {activity.action}
                        </Text>
                      </div>
                    </Col>
                    <Col>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {activity.time}
                      </Text>
                      <br />
                      <Tag
                        color={
                          activity.status === 'success' ? 'success' :
                          activity.status === 'warning' ? 'warning' :
                          activity.status === 'error' ? 'error' : 'default'
                        }
                        size="small"
                      >
                        {activity.status === 'success' ? '成功' :
                         activity.status === 'warning' ? '警告' :
                         activity.status === 'error' ? '錯誤' : '信息'}
                      </Tag>
                    </Col>
                  </Row>
                </div>
              ))}
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default NewDashboardPage