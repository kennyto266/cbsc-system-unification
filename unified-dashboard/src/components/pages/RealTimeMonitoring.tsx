import React, { useState, useEffect, useMemo } from 'react'
import {
  Row,
  Col,
  Card,
  Statistic,
  Progress,
  Tag,
  Alert,
  List,
  Space,
  Button,
  Typography,
  Badge,
  Table,
  Timeline,
  Tooltip,
  Switch,
} from 'antd'
import {
  ThunderboltOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  RocketOutlined,
  DatabaseOutlined,
  ApiOutlined,
  MonitorOutlined,
  ReloadOutlined,
  SettingOutlined,
  BellOutlined,
} from '@ant-design/icons'

// Enhanced Chart Components
import {
  SystemMetricsChart,
  RealTimePriceChart,
  PerformanceHeatmap,
  NetworkActivityChart,
} from '../Charts'

// Hooks and Services
import { useAppSelector } from '../../hooks/redux'
import { useWebSocket } from '../../hooks/useWebSocket'
import { selectMonitoring, selectStrategies } from '../../store/slices'

// Components
import MetricCard from '../common/MetricCard'
import AlertPanel from '../common/AlertPanel'
import SystemResourceMonitor from '../common/SystemResourceMonitor'
import ConnectionStatus from '../common/ConnectionStatus'

const { Title, Text } = Typography

interface RealTimeMonitoringProps {
  refreshInterval?: number
  enableAlerts?: boolean
  enableSystemMetrics?: boolean
  enableNetworkMonitoring?: boolean
}

const RealTimeMonitoring: React.FC<RealTimeMonitoringProps> = ({
  refreshInterval = 5000,
  enableAlerts = true,
  enableSystemMetrics = true,
  enableNetworkMonitoring = true
}) => {
  // Redux state
  const { systemHealth, alerts, networkActivity } = useAppSelector(selectMonitoring)
  const { strategies } = useAppSelector(selectStrategies)

  // Local state
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [selectedAlert, setSelectedAlert] = useState<any>(null)

  // WebSocket connection for real-time data
  const { isConnected, lastMessage, reconnectCount } = useWebSocket({
    enabled: true,
    reconnectInterval: 3000,
    maxReconnectAttempts: 10,
    onMessage: handleRealTimeMessage,
    onConnectionChange: handleConnectionChange,
  })

  // Handle real-time WebSocket messages
  function handleRealTimeMessage(data: any) {
    setLastUpdate(new Date())

    switch (data.type) {
      case 'system_health':
        // Update system health metrics
        break
      case 'strategy_alert':
        // Handle strategy alerts
        break
      case 'market_data':
        // Handle market data updates
        break
      case 'network_activity':
        // Handle network activity
        break
      default:
        console.log('Unknown message type:', data.type)
    }
  }

  // Handle connection status changes
  function handleConnectionChange(connected: boolean) {
    if (!connected) {
      console.warn('WebSocket connection lost, attempting to reconnect...')
    }
  }

  // Calculate system metrics
  const systemMetrics = useMemo(() => {
    const activeStrategies = strategies.filter(s => s.status === 'active').length
    const criticalAlerts = alerts.filter(a => a.severity === 'critical' && !a.read).length
    const totalAlerts = alerts.filter(a => !a.read).length

    return {
      cpuUsage: systemHealth?.cpuUsage || 0,
      memoryUsage: systemHealth?.memoryUsage || 0,
      diskUsage: systemHealth?.diskUsage || 0,
      networkLatency: systemHealth?.networkLatency || 0,
      activeConnections: systemHealth?.activeConnections || 0,
      uptime: systemHealth?.uptime || 0,
      activeStrategies,
      criticalAlerts,
      totalAlerts,
    }
  }, [systemHealth, alerts, strategies])

  // Recent activities
  const recentActivities = useMemo(() => {
    const activities = []

    // Add strategy status changes
    strategies.forEach(strategy => {
      if (strategy.lastActive) {
        activities.push({
          type: 'strategy',
          message: `策略 ${strategy.name} ${strategy.status === 'active' ? '启动' : '停止'}`,
          timestamp: new Date(strategy.lastActive),
          severity: strategy.status === 'active' ? 'success' : 'info',
          icon: strategy.status === 'active' ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />,
        })
      }
    })

    // Add system alerts
    alerts.slice(0, 5).forEach(alert => {
      activities.push({
        type: 'alert',
        message: alert.message,
        timestamp: new Date(alert.timestamp),
        severity: alert.severity,
        icon: <AlertOutlined />,
      })
    })

    return activities.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime()).slice(0, 10)
  }, [strategies, alerts])

  // Network activity columns
  const networkColumns = [
    {
      title: '服务',
      dataIndex: 'service',
      key: 'service',
    },
    {
      title: '请求/秒',
      dataIndex: 'requestsPerSecond',
      key: 'requestsPerSecond',
      render: (value: number) => value.toFixed(2),
    },
    {
      title: '响应时间',
      dataIndex: 'responseTime',
      key: 'responseTime',
      render: (value: number) => `${value}ms`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'healthy' ? 'success' : status === 'warning' ? 'warning' : 'error'}>
          {status === 'healthy' ? '正常' : status === 'warning' ? '警告' : '错误'}
        </Tag>
      ),
    },
  ]

  // Simulated network activity data
  const networkData = useMemo(() => [
    {
      key: '1',
      service: '策略执行引擎',
      requestsPerSecond: Math.random() * 100,
      responseTime: Math.floor(Math.random() * 500) + 50,
      status: 'healthy',
    },
    {
      key: '2',
      service: '数据获取服务',
      requestsPerSecond: Math.random() * 200,
      responseTime: Math.floor(Math.random() * 300) + 30,
      status: Math.random() > 0.8 ? 'warning' : 'healthy',
    },
    {
      key: '3',
      service: 'WebSocket服务',
      requestsPerSecond: Math.random() * 50,
      responseTime: Math.floor(Math.random() * 100) + 20,
      status: 'healthy',
    },
    {
      key: '4',
      service: 'API网关',
      requestsPerSecond: Math.random() * 150,
      responseTime: Math.floor(Math.random() * 200) + 40,
      status: 'healthy',
    },
  ], [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} className="!mb-2">
            实时监控
          </Title>
          <Text type="secondary">
            系统状态、策略执行和网络活动的实时监控
          </Text>
        </div>

        <Space>
          <Tooltip title="自动刷新">
            <Switch
              checked={autoRefresh}
              onChange={setAutoRefresh}
              checkedChildren="开"
              unCheckedChildren="关"
            />
          </Tooltip>
          <Button icon={<ReloadOutlined />} onClick={() => window.location.reload()}>
            刷新
          </Button>
          <Badge dot={systemMetrics.totalAlerts > 0}>
            <Button icon={<BellOutlined />}>
              通知 {systemMetrics.totalAlerts > 0 && `(${systemMetrics.totalAlerts})`}
            </Button>
          </Badge>
        </Space>
      </div>

      {/* Critical Alerts */}
      {systemMetrics.criticalAlerts > 0 && (
        <Alert
          message={`您有 ${systemMetrics.criticalAlerts} 个紧急告警需要立即处理`}
          type="error"
          showIcon
          closable
          action={
            <Button size="small" danger>
              查看详情
            </Button>
          }
        />
      )}

      {/* Connection Status */}
      <Card>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <ConnectionStatus
              isConnected={isConnected}
              reconnectCount={reconnectCount}
              lastUpdate={lastUpdate}
            />
          </Col>
          <Col xs={24} sm={8}>
            <Statistic
              title="活跃策略"
              value={systemMetrics.activeStrategies}
              prefix={<RocketOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Col>
          <Col xs={24} sm={8}>
            <Statistic
              title="系统运行时间"
              value={systemMetrics.uptime}
              suffix="小时"
              prefix={<ClockCircleOutlined />}
            />
          </Col>
        </Row>
      </Card>

      {/* System Metrics Row */}
      {enableSystemMetrics && (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={16}>
            <Card
              title={
                <Space>
                  <MonitorOutlined />
                  系统资源使用情况
                </Space>
              }
              extra={
                <Text type="secondary" className="text-xs">
                  最后更新: {lastUpdate.toLocaleTimeString()}
                </Text>
              }
            >
              <SystemMetricsChart
                data={{
                  cpu: systemMetrics.cpuUsage,
                  memory: systemMetrics.memoryUsage,
                  disk: systemMetrics.diskUsage,
                  network: systemMetrics.networkLatency,
                }}
                height={300}
                realTime={autoRefresh}
              />
            </Card>
          </Col>

          <Col xs={24} lg={8}>
            <Card title="资源详情" size="small">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <div className="flex justify-between mb-2">
                    <Text>CPU 使用率</Text>
                    <Text>{systemMetrics.cpuUsage.toFixed(1)}%</Text>
                  </div>
                  <Progress
                    percent={systemMetrics.cpuUsage}
                    status={systemMetrics.cpuUsage > 80 ? 'exception' : systemMetrics.cpuUsage > 60 ? 'active' : 'normal'}
                    strokeColor={systemMetrics.cpuUsage > 80 ? '#ff4d4f' : systemMetrics.cpuUsage > 60 ? '#faad14' : '#52c41a'}
                  />
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <Text>内存使用率</Text>
                    <Text>{systemMetrics.memoryUsage.toFixed(1)}%</Text>
                  </div>
                  <Progress
                    percent={systemMetrics.memoryUsage}
                    status={systemMetrics.memoryUsage > 80 ? 'exception' : systemMetrics.memoryUsage > 60 ? 'active' : 'normal'}
                    strokeColor={systemMetrics.memoryUsage > 80 ? '#ff4d4f' : systemMetrics.memoryUsage > 60 ? '#faad14' : '#52c41a'}
                  />
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <Text>磁盘使用率</Text>
                    <Text>{systemMetrics.diskUsage.toFixed(1)}%</Text>
                  </div>
                  <Progress
                    percent={systemMetrics.diskUsage}
                    status={systemMetrics.diskUsage > 90 ? 'exception' : 'normal'}
                    strokeColor={systemMetrics.diskUsage > 90 ? '#ff4d4f' : '#52c41a'}
                  />
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <Text>网络延迟</Text>
                    <Text>{systemMetrics.networkLatency.toFixed(0)}ms</Text>
                  </div>
                  <Progress
                    percent={Math.min(systemMetrics.networkLatency / 5, 100)}
                    status={systemMetrics.networkLatency > 500 ? 'exception' : systemMetrics.networkLatency > 200 ? 'active' : 'normal'}
                    strokeColor={systemMetrics.networkLatency > 500 ? '#ff4d4f' : systemMetrics.networkLatency > 200 ? '#faad14' : '#52c41a'}
                  />
                </div>
              </Space>
            </Card>
          </Col>
        </Row>
      )}

      {/* Network Monitoring and Recent Activities */}
      <Row gutter={[16, 16]}>
        {enableNetworkMonitoring && (
          <Col xs={24} lg={12}>
            <Card
              title={
                <Space>
                  <ApiOutlined />
                  网络活动监控
                </Space>
              }
            >
              <Table
                columns={networkColumns}
                dataSource={networkData}
                pagination={false}
                size="small"
              />
            </Card>
          </Col>
        )}

        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <ClockCircleOutlined />
                最近活动
              </Space>
            }
            extra={
              <Button type="text" size="small">
                查看全部
              </Button>
            }
          >
            <Timeline
              mode="left"
              items={recentActivities.map((activity, index) => ({
                key: index,
                dot: activity.icon,
                color: activity.severity === 'critical' ? 'red' :
                      activity.severity === 'warning' ? 'orange' :
                      activity.severity === 'success' ? 'green' : 'blue',
                children: (
                  <div>
                    <Text>{activity.message}</Text>
                    <br />
                    <Text type="secondary" className="text-xs">
                      {activity.timestamp.toLocaleString()}
                    </Text>
                  </div>
                ),
              }))}
            />
          </Card>
        </Col>
      </Row>

      {/* Performance Heatmap */}
      <Card
        title={
          <Space>
            <ThunderboltOutlined />
            策略性能热力图
          </Space>
        }
      >
        <PerformanceHeatmap
          strategies={strategies}
          metrics={['return', 'sharpe', 'drawdown', 'winrate']}
          height={400}
          interactive={true}
        />
      </Card>

      {/* Real-time Market Data */}
      <Card
        title={
          <Space>
            <DatabaseOutlined />
            实时市场数据
          </Space>
        }
      >
        <RealTimePriceChart
          symbols={['BTC/USDT', 'ETH/USDT', 'BNB/USDT']}
          timeFrame="1m"
          height={300}
          autoUpdate={autoRefresh}
        />
      </Card>

      {/* Alert Panel */}
      {enableAlerts && (
        <AlertPanel
          alerts={alerts}
          onAlertClick={setSelectedAlert}
          onAlertDismiss={(alertId) => {
            // Implement alert dismissal logic
            console.log('Dismiss alert:', alertId)
          }}
        />
      )}
    </div>
  )
}

export default RealTimeMonitoring