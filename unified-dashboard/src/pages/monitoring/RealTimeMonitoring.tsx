import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Progress, Tag, Alert, Timeline, Button, Space, Tooltip, Typography, List, Badge } from 'antd'
import {
  CheckCircleOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
  EyeOutlined,
  SettingOutlined,
  FireOutlined,
  ThunderboltOutlined,
  DashboardOutlined,
  AlertOutlined,
} from '@ant-design/icons'

// Charts
import {
  SystemResourceChart,
  AlertTrendChart,
  StrategyExecutionChart,
  NetworkLatencyChart,
} from '../../components/charts/MonitoringCharts'

// Hooks
import { useWebSocket } from '../../hooks/useWebSocket'
import { useAppSelector } from '../../hooks/redux'
import { selectMonitoring } from '../../store/slices/monitoringSlice'
import { selectStrategies } from '../../store/slices/strategiesSlice'

// Components
import MetricCard from '../../components/monitoring/MetricCard'
import AlertPanel from '../../components/monitoring/AlertPanel'
import SystemMetrics from '../../components/monitoring/SystemMetrics'
import StrategyStatusMonitor from '../../components/monitoring/StrategyStatusMonitor'

const { Title, Text } = Typography

interface Alert {
  id: string
  type: 'error' | 'warning' | 'info'
  title: string
  message: string
  timestamp: string
  strategy?: string
  severity: 'low' | 'medium' | 'high' | 'critical'
}

interface SystemMetric {
  name: string
  value: number
  unit: string
  status: 'normal' | 'warning' | 'critical'
  trend: number
}

const RealTimeMonitoring: React.FC = () => {
  const [selectedTimeRange, setSelectedTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('1h')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(5000) // 5 seconds

  // Redux state
  const { systemHealth, alerts, metrics } = useAppSelector(selectMonitoring)
  const { strategies } = useAppSelector(selectStrategies)

  // WebSocket for real-time updates
  const { isConnected, lastMessage } = useWebSocket({
    endpoint: '/ws/monitoring',
    reconnect: true,
  })

  // Mock data for demonstration
  const mockSystemMetrics: SystemMetric[] = [
    { name: 'CPU使用率', value: 45, unit: '%', status: 'normal', trend: 2.1 },
    { name: '内存使用', value: 68, unit: '%', status: 'warning', trend: -1.5 },
    { name: '磁盘IO', value: 23, unit: '%', status: 'normal', trend: 0.8 },
    { name: '网络延迟', value: 12, unit: 'ms', status: 'normal', trend: -2.3 },
    { name: 'API响应时间', value: 85, unit: 'ms', status: 'warning', trend: 5.2 },
  ]

  const mockAlerts: Alert[] = [
    {
      id: '1',
      type: 'warning',
      title: '内存使用率过高',
      message: '系统内存使用率达到68%，建议检查并优化内存占用',
      timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
      severity: 'medium',
    },
    {
      id: '2',
      type: 'error',
      title: 'RSI策略执行失败',
      message: 'RSI超卖买入策略在14:30执行时发生网络超时',
      timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
      strategy: 'RSI超卖买入策略',
      severity: 'high',
    },
    {
      id: '3',
      type: 'info',
      title: '系统自动备份完成',
      message: '每日系统备份已于凌晨2:00成功完成',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      severity: 'low',
    },
  ]

  const mockStrategyStatuses = [
    { id: '1', name: 'RSI策略', status: 'running', lastRun: '2分钟前', nextRun: '13分钟后', executions: 145, successRate: 98.6 },
    { id: '2', name: 'MACD策略', status: 'running', lastRun: '5分钟前', nextRun: '25分钟后', executions: 132, successRate: 96.2 },
    { id: '3', name: '布林带策略', status: 'error', lastRun: '1小时前', nextRun: '-', executions: 89, successRate: 94.4 },
    { id: '4', name: '多因子策略', status: 'idle', lastRun: '30分钟前', nextRun: '30分钟后', executions: 76, successRate: 99.1 },
  ]

  const systemMetrics = metrics || mockSystemMetrics
  const systemAlerts = alerts || mockAlerts

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      // Trigger data refresh
      console.log('Auto-refreshing monitoring data...')
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'success'
      case 'idle': return 'default'
      case 'error': return 'error'
      case 'warning': return 'warning'
      default: return 'default'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'red'
      case 'high': return 'orange'
      case 'medium': return 'gold'
      case 'low': return 'blue'
      default: return 'default'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} className="!mb-2">
            實時監控中心
          </Title>
          <Text type="secondary">
            系統狀態和策略執行的即時監控
          </Text>
        </div>
        <Space>
          <Badge
            count={systemAlerts.filter(a => a.severity === 'critical' || a.severity === 'high').length}
            overflowCount={99}
          >
            <Button
              type="primary"
              icon={<AlertOutlined />}
              onClick={() => console.log('View all alerts')}
            >
              告警中心
            </Button>
          </Badge>
          <Tooltip title={autoRefresh ? '关闭自动刷新' : '开启自动刷新'}>
            <Button
              type={autoRefresh ? 'primary' : 'default'}
              icon={<ReloadOutlined />}
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              {autoRefresh ? '自动刷新' : '手动刷新'}
            </Button>
          </Tooltip>
          <Button
            icon={<SettingOutlined />}
            onClick={() => console.log('Open monitoring settings')}
          >
            設置
          </Button>
        </Space>
      </div>

      {/* Connection Status */}
      {!isConnected && (
        <Alert
          message="WebSocket連接斷開"
          description="實時數據更新已暫停，請檢查網絡連接"
          type="warning"
          showIcon
          action={
            <Button size="small" type="primary" onClick={() => window.location.reload()}>
              重新連接
            </Button>
          }
        />
      )}

      {/* System Overview Metrics */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="系統健康度"
            value={92}
            suffix="%"
            status="normal"
            icon={<DashboardOutlined />}
            trend={1.2}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="活躍策略"
            value={strategies?.filter(s => s.status === 'active').length || 8}
            status="normal"
            icon={<ThunderboltOutlined />}
            description="正在執行中"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="待處理告警"
            value={systemAlerts.filter(a => a.severity === 'critical' || a.severity === 'high').length}
            status="warning"
            icon={<WarningOutlined />}
            description="需要關注"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="今日執行次數"
            value={1248}
            status="success"
            icon={<FireOutlined />}
            trend={8.5}
          />
        </Col>
      </Row>

      {/* System Resource Monitoring */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="系統資源監控" extra={
            <Space>
              <Button size="small" onClick={() => setSelectedTimeRange('1h')} type={selectedTimeRange === '1h' ? 'primary' : 'link'}>1小時</Button>
              <Button size="small" onClick={() => setSelectedTimeRange('6h')} type={selectedTimeRange === '6h' ? 'primary' : 'link'}>6小時</Button>
              <Button size="small" onClick={() => setSelectedTimeRange('24h')} type={selectedTimeRange === '24h' ? 'primary' : 'link'}>24小時</Button>
              <Button size="small" onClick={() => setSelectedTimeRange('7d')} type={selectedTimeRange === '7d' ? 'primary' : 'link'}>7天</Button>
            </Space>
          }>
            <SystemResourceChart
              timeRange={selectedTimeRange}
              metrics={systemMetrics}
              showLegend={true}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="當前系統指標" size="small">
            <div className="space-y-4">
              {systemMetrics.map((metric, index) => (
                <div key={index}>
                  <div className="flex justify-between items-center mb-2">
                    <Text strong>{metric.name}</Text>
                    <Space>
                      <Text type={metric.status === 'critical' ? 'danger' : metric.status === 'warning' ? 'warning' : 'secondary'}>
                        {metric.value}{metric.unit}
                      </Text>
                      <Tag color={getStatusColor(metric.status)}>
                        {metric.status === 'normal' ? '正常' : metric.status === 'warning' ? '警告' : '嚴重'}
                      </Tag>
                    </Space>
                  </div>
                  <Progress
                    percent={metric.value}
                    status={metric.status === 'critical' ? 'exception' : metric.status === 'warning' ? 'active' : 'normal'}
                    strokeColor={metric.status === 'critical' ? '#ff4d4f' : metric.status === 'warning' ? '#faad14' : '#52c41a'}
                    showInfo={false}
                  />
                  {metric.trend !== 0 && (
                    <Text className="text-xs" type={metric.trend > 0 ? 'danger' : 'success'}>
                      {metric.trend > 0 ? '↑' : '↓'} {Math.abs(metric.trend)}%
                    </Text>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      {/* Strategy Execution Monitoring */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="策略執行監控" extra={<Button type="text" icon={<EyeOutlined />} size="small">詳情</Button>}>
            <StrategyExecutionChart
              strategies={mockStrategyStatuses}
              timeRange={selectedTimeRange}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="網絡延遲監控" extra={<Button type="text" icon={<EyeOutlined />} size="small">詳情</Button>}>
            <NetworkLatencyChart
              timeRange={selectedTimeRange}
              services={['API Gateway', 'Database', 'Redis', 'WebSocket']}
            />
          </Card>
        </Col>
      </Row>

      {/* Strategy Status List */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card title="策略狀態監控" extra={
            <Space>
              <Button size="small" icon={<ReloadOutlined />}>刷新</Button>
              <Button size="small" icon={<EyeOutlined />}>詳情</Button>
            </Space>
          }>
            <List
              dataSource={mockStrategyStatuses}
              renderItem={(strategy) => (
                <List.Item
                  actions={[
                    <Button key="view" type="text" size="small" icon={<EyeOutlined />} />,
                    <Button key="settings" type="text" size="small" icon={<SettingOutlined />} />,
                  ]}
                >
                  <List.Item.Meta
                    avatar={
                      <Badge
                        status={getStatusColor(strategy.status) as any}
                        text={strategy.name}
                      />
                    }
                    description={
                      <Space direction="vertical" size="small" className="w-full">
                        <div className="flex justify-between">
                          <Text type="secondary">上次執行: {strategy.lastRun}</Text>
                          <Text type="secondary">下次執行: {strategy.nextRun}</Text>
                        </div>
                        <div className="flex justify-between">
                          <Text type="secondary">執行次數: {strategy.executions}</Text>
                          <Text type="secondary">成功率: {strategy.successRate}%</Text>
                        </div>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <AlertPanel
            title="系統告警"
            alerts={systemAlerts}
            maxItems={10}
            showSeverity={true}
            onAlertClick={(alert) => console.log('Alert clicked:', alert)}
            onClearAll={() => console.log('Clear all alerts')}
          />
        </Col>
      </Row>

      {/* Alert Trend Chart */}
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card title="告警趨勢分析" extra={
            <Space>
              <Button size="small" onClick={() => setSelectedTimeRange('1h')} type={selectedTimeRange === '1h' ? 'primary' : 'link'}>1小時</Button>
              <Button size="small" onClick={() => setSelectedTimeRange('6h')} type={selectedTimeRange === '6h' ? 'primary' : 'link'}>6小時</Button>
              <Button size="small" onClick={() => setSelectedTimeRange('24h')} type={selectedTimeRange === '24h' ? 'primary' : 'link'}>24小時</Button>
              <Button size="small" onClick={() => setSelectedTimeRange('7d')} type={selectedTimeRange === '7d' ? 'primary' : 'link'}>7天</Button>
            </Space>
          }>
            <AlertTrendChart
              timeRange={selectedTimeRange}
              showSeverityBreakdown={true}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default RealTimeMonitoring