/**
 * Enhanced Dashboard Page with Real-time WebSocket Integration
 * 集成實時WebSocket功能的增強Dashboard頁面
 */

import React, { useState } from 'react'
import { Row, Col, Card, Button, Space, Typography, Alert } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'

// Hooks
import { useGetAnalyticsDataQuery } from '@store/api/analyticsApi'
import { useGetActiveStrategiesQuery } from '@store/api/monitoringApi'
import { useWebSocket } from '@hooks/useWebSocket'

// Components
import MetricCard from '@components/dashboard/MetricCard'
import MarketOverview from '@components/dashboard/MarketOverview'
import RecentSignals from '@components/dashboard/RecentSignals'
import SystemHealth from '@components/dashboard/SystemHealth'
import QuickActions from '@components/dashboard/QuickActions'
import WebSocketStatusIndicator from '../../components/Dashboard/WebSocketStatusIndicator'
import RealTimeSignals from '../../components/Dashboard/RealTimeSignals'
import RealTimeStrategyPerformance from '../../components/Dashboard/RealTimeStrategyPerformance'

// Chart Components
import {
  StrategyPerformanceChart,
  AssetAllocationChart,
  StrategyComparisonChart,
  RiskReturnScatterChart,
  RealTimePriceChart
} from '@components/Charts'
import { Strategy, StrategyType } from '../../types'

const { Title, Text } = Typography

const DashboardPageWithRealTime: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'1d' | '1w' | '1m' | '3m'>('1m')
  const [chartTimeRange, setChartTimeRange] = useState<'1D' | '1W' | '1M' | '3M' | '6M' | '1Y'>('1M')
  const [comparisonMetric, setComparisonMetric] = useState<'totalReturn' | 'sharpeRatio' | 'maxDrawdown' | 'winRate' | 'profitFactor'>('totalReturn')
  const [filterType, setFilterType] = useState<StrategyType | 'all'>('all')

  // WebSocket連接
  const { isConnected, isReconnecting, lastError, disconnect, connect } = useWebSocket({
    autoConnect: true,
    reconnectInterval: 3000
  })

  // 模擬策略數據
  const mockStrategies: Strategy[] = [
    {
      id: '1',
      name: 'RSI均值回歸策略',
      type: StrategyType.MEAN_REVERSION,
      status: 'active' as any,
      riskLevel: 'medium' as any,
      description: '基於相對強弱指數的均值回歸交易策略',
      parameters: { rsiPeriod: 14, oversoldLevel: 30, overboughtLevel: 70 },
      performance: {
        totalReturn: 0.185,
        sharpeRatio: 1.45,
        maxDrawdown: -0.08,
        winRate: 0.65,
        profitFactor: 1.8
      },
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    },
    {
      id: '2',
      name: 'MACD動量策略',
      type: StrategyType.MOMENTUM,
      status: 'active' as any,
      riskLevel: 'high' as any,
      description: '基於MACD指標的動量追蹤策略',
      parameters: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
      performance: {
        totalReturn: 0.242,
        sharpeRatio: 1.78,
        maxDrawdown: -0.15,
        winRate: 0.58,
        profitFactor: 2.1
      },
      createdAt: '2024-02-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    },
    {
      id: '3',
      name: '情感分析策略',
      type: StrategyType.SENTIMENT,
      status: 'active' as any,
      riskLevel: 'low' as any,
      description: '基於市場情感分析的交易策略',
      parameters: { sentimentSource: 'twitter', threshold: 0.6 },
      performance: {
        totalReturn: 0.123,
        sharpeRatio: 1.12,
        maxDrawdown: -0.05,
        winRate: 0.72,
        profitFactor: 1.5
      },
      createdAt: '2024-03-01T00:00:00Z',
      updatedAt: '2024-12-10T00:00:00Z'
    }
  ]

  // API數據查詢
  const { data: analyticsData, isLoading: analyticsLoading, error: analyticsError } = useGetAnalyticsDataQuery({
    timeRange,
    includeBenchmark: true,
  })

  const { data: activeStrategies, isLoading: strategiesLoading } = useGetActiveStrategiesQuery()

  // 系統資源指標
  const systemMetrics = {
    cpu: 45,
    memory: 62,
    disk: 38,
    network: 23,
  }

  // 錯誤處理
  if (analyticsError) {
    return (
      <Alert
        message="數據加載失敗"
        description="無法加載Dashboard數據，請檢查網絡連接或稍後重試。"
        type="error"
        showIcon
        action={
          <Button size="small" onClick={() => window.location.reload()}>
            刷新頁面
          </Button>
        }
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with WebSocket Status */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} className="!mb-2">
            CBSC策略管理Dashboard (實時版)
          </Title>
          <Text type="secondary">
            實時監控您的量化交易策略表現和市場動態
          </Text>
        </div>
        <Space>
          <WebSocketStatusIndicator />
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={() => window.location.reload()}
          >
            刷新數據
          </Button>
        </Space>
      </div>

      {/* WebSocket Connection Alert */}
      {!isConnected && lastError && (
        <Alert
          message="WebSocket連接異常"
          description={`無法連接到實時數據服務: ${lastError}`}
          type="warning"
          showIcon
          action={
            <Button size="small" onClick={() => connect()}>
              重新連接
            </Button>
          }
          closable
        />
      )}

      {/* Key Metrics */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="總資產價值"
            value={analyticsData?.portfolio?.totalValue || 106200}
            precision={2}
            prefix="¥"
            trend={5.8}
            loading={analyticsLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="總收益率"
            value={analyticsData?.portfolio?.totalReturn || 6.2}
            precision={2}
            suffix="%"
            trend={2.1}
            loading={analyticsLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="夏普比率"
            value={analyticsData?.portfolio?.sharpeRatio || 1.85}
            precision={2}
            trend={0.15}
            loading={analyticsLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="活躍策略"
            value={activeStrategies?.length || 8}
            trend={1}
            loading={strategiesLoading}
          />
        </Col>
      </Row>

      {/* Real-time Data Section */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <RealTimeStrategyPerformance />
        </Col>
        <Col xs={24} lg={10}>
          <RealTimeSignals />
        </Col>
      </Row>

      {/* Chart.js Charts Section */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <StrategyPerformanceChart
            strategies={mockStrategies}
            timeRange={chartTimeRange}
            onTimeRangeChange={setChartTimeRange}
          />
        </Col>
        <Col xs={24} lg={8}>
          <AssetAllocationChart
            strategies={mockStrategies}
            totalValue={100000}
            showDetails={true}
          />
        </Col>
      </Row>

      {/* Market Overview and Comparison */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <MarketOverview />
        </Col>
        <Col xs={24} lg={12}>
          <StrategyComparisonChart
            strategies={mockStrategies}
            metric={comparisonMetric}
            onMetricChange={setComparisonMetric}
          />
        </Col>
      </Row>

      {/* System Health and Activity */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <SystemHealth />
        </Col>
        <Col xs={24} lg={16}>
          <Card title="系統資源使用情況">
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12}>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-2">
                      <Text>CPU使用率</Text>
                      <Text>{systemMetrics.cpu}%</Text>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${systemMetrics.cpu}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-2">
                      <Text>內存使用率</Text>
                      <Text>{systemMetrics.memory}%</Text>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-600 h-2 rounded-full"
                        style={{ width: `${systemMetrics.memory}%` }}
                      />
                    </div>
                  </div>
                </div>
              </Col>
              <Col xs={24} sm={12}>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-2">
                      <Text>磁盤使用率</Text>
                      <Text>{systemMetrics.disk}%</Text>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-yellow-600 h-2 rounded-full"
                        style={{ width: `${systemMetrics.disk}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-2">
                      <Text>網絡使用率</Text>
                      <Text>{systemMetrics.network}%</Text>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-purple-600 h-2 rounded-full"
                        style={{ width: `${systemMetrics.network}%` }}
                      />
                    </div>
                  </div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Bottom Section */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <RecentSignals />
        </Col>
        <Col xs={24} lg={16}>
          <QuickActions />
        </Col>
      </Row>
    </div>
  )
}

export default DashboardPageWithRealTime