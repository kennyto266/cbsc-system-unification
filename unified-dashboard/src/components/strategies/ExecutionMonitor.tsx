import React, { useState, useEffect, useRef } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Tag,
  Button,
  Space,
  Table,
  Timeline,
  Alert,
  Spin,
  Empty,
  Tooltip,
  Badge,
  Descriptions,
  List,
  Avatar,
  message,
  Switch,
  Modal,
  Form,
  InputNumber,
  Input,
  Select,
  Typography,
} from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  LineChartOutlined,
  FireOutlined,
  SyncOutlined,
  DashboardOutlined,
  ApiOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import dayjs from 'dayjs'
import { Line, Gauge } from '@ant-design/plots'

import { useStrategyExecution } from '../../hooks/strategies'

// Styles
import './ExecutionMonitor.css'

const { Text } = Typography

interface ExecutionMonitorProps {
  strategyId: string
  realTime?: boolean
  embedded?: boolean
}

interface ExecutionEvent {
  id: string
  timestamp: string
  type: 'order' | 'position' | 'signal' | 'error' | 'info'
  message: string
  details?: any
}

interface Position {
  id: string
  symbol: string
  side: 'LONG' | 'SHORT'
  quantity: number
  entryPrice: number
  currentPrice: number
  pnl: number
  pnlPercent: number
  entryTime: string
}

interface Order {
  id: string
  symbol: string
  side: 'BUY' | 'SELL'
  type: 'MARKET' | 'LIMIT' | 'STOP'
  quantity: number
  price: number
  status: 'pending' | 'filled' | 'partial' | 'cancelled'
  createTime: string
  updateTime: string
}

const ExecutionMonitor: React.FC<ExecutionMonitorProps> = ({
  strategyId,
  realTime = true,
  embedded = false,
}) => {
  const [events, setEvents] = useState<ExecutionEvent[]>([])
  const [manualOrderModalVisible, setManualOrderModalVisible] = useState(false)
  const [form] = Form.useForm()

  const {
    isExecuting,
    executionState,
    executionStatus,
    orders,
    positions,
    realTimeData,
    isRealTimeActive,
    startStrategy,
    stopStrategy,
    pauseStrategy,
    resumeStrategy,
    executeOnce,
    placeManualOrder,
    emergencyStop,
    refreshAll,
  } = useStrategyExecution({ strategyId, autoRefresh: realTime })

  // Real-time chart data
  const [chartData, setChartData] = useState<any[]>([])

  // Update chart data
  useEffect(() => {
    if (executionStatus && executionStatus.pnlHistory) {
      const data = executionStatus.pnlHistory.map((item: any, index: number) => ({
        time: dayjs(item.timestamp).format('HH:mm:ss'),
        value: item.pnl,
        index: index,
      }))
      setChartData(data)
    }
  }, [executionStatus])

  // Add execution event
  const addEvent = (event: Omit<ExecutionEvent, 'id' | 'timestamp'>) => {
    const newEvent: ExecutionEvent = {
      ...event,
      id: `event_${Date.now()}_${Math.random()}`,
      timestamp: dayjs().toISOString(),
    }
    setEvents(prev => [newEvent, ...prev.slice(0, 99)]) // Keep last 100 events
  }

  // Handle manual order
  const handleManualOrder = async (values: any) => {
    try {
      await placeManualOrder(values)
      setManualOrderModalVisible(false)
      form.resetFields()
      message.success('手動訂單已提交')
    } catch (error) {
      // Error is handled in the hook
    }
  }

  // Get execution state color
  const getExecutionStateColor = (state: string) => {
    const stateColors = {
      running: '#52c41a',
      paused: '#faad14',
      stopped: '#f5222d',
      error: '#ff4d4f',
      starting: '#1890ff',
      stopping: '#ff7a45',
    }
    return stateColors[state as keyof typeof stateColors] || '#d9d9d9'
  }

  // Position table columns
  const positionColumns = [
    {
      title: '品種',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => <strong>{symbol}</strong>,
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'LONG' ? 'green' : 'red'}>
          {side === 'LONG' ? '做多' : '做空'}
        </Tag>
      ),
    },
    {
      title: '數量',
      dataIndex: 'quantity',
      key: 'quantity',
      align: 'right' as const,
    },
    {
      title: '開倉價',
      dataIndex: 'entryPrice',
      key: 'entryPrice',
      align: 'right' as const,
      render: (price: number) => price.toFixed(4),
    },
    {
      title: '當前價',
      dataIndex: 'currentPrice',
      key: 'currentPrice',
      align: 'right' as const,
      render: (price: number) => price.toFixed(4),
    },
    {
      title: '盈虧',
      dataIndex: 'pnl',
      key: 'pnl',
      align: 'right' as const,
      render: (pnl: number, record: Position) => (
        <span style={{ color: pnl >= 0 ? '#52c41a' : '#f5222d' }}>
          {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)} ({pnl >= 0 ? '+' : ''}{record.pnlPercent.toFixed(2)}%)
        </span>
      ),
      sorter: (a: Position, b: Position) => a.pnl - b.pnl,
    },
    {
      title: '持倉時間',
      dataIndex: 'entryTime',
      key: 'entryTime',
      render: (time: string) => dayjs(time).fromNow(),
    },
  ]

  // Order table columns
  const orderColumns = [
    {
      title: '時間',
      dataIndex: 'createTime',
      key: 'createTime',
      render: (time: string) => dayjs(time).format('HH:mm:ss'),
      width: 100,
    },
    {
      title: '品種',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'BUY' ? 'green' : 'red'}>
          {side === 'BUY' ? '買入' : '賣出'}
        </Tag>
      ),
    },
    {
      title: '類型',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: '數量',
      dataIndex: 'quantity',
      key: 'quantity',
      align: 'right' as const,
    },
    {
      title: '價格',
      dataIndex: 'price',
      key: 'price',
      align: 'right' as const,
      render: (price: number) => price.toFixed(4),
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          pending: { color: 'processing', text: '待成交' },
          filled: { color: 'success', text: '已成交' },
          partial: { color: 'warning', text: '部分成交' },
          cancelled: { color: 'default', text: '已取消' },
        }
        const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending
        return <Badge status={config.color} text={config.text} />
      },
    },
  ]

  // Real-time metrics chart config
  const realTimeChartConfig = {
    data: chartData,
    xField: 'time',
    yField: 'value',
    smooth: true,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    color: '#1890ff',
    point: {
      size: 3,
      shape: 'circle',
    },
    tooltip: {
      formatter: (datum: any) => ({
        name: '盈虧',
        value: `${datum.value >= 0 ? '+' : ''}${datum.value.toFixed(2)}`,
      }),
    },
  }

  return (
    <div className={`execution-monitor ${embedded ? 'embedded' : ''}`}>
      {/* Execution Status */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <Statistic
              title="執行狀態"
              value={executionState}
              valueStyle={{ color: getExecutionStateColor(executionState) }}
              prefix={
                <Badge
                  status={executionState === 'running' ? 'processing' : executionState === 'error' ? 'error' : 'default'}
                />
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <Statistic
              title="當前盈虧"
              value={executionStatus?.totalPnl || 0}
              precision={2}
              valueStyle={{ color: (executionStatus?.totalPnl || 0) >= 0 ? '#52c41a' : '#f5222d' }}
              prefix={(executionStatus?.totalPnl || 0) >= 0 ? '+' : ''}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <Statistic
              title="執行次數"
              value={executionStatus?.executionCount || 0}
              prefix={<ThunderboltOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card size="small">
            <Statistic
              title="運行時長"
              value={executionStatus?.uptime || '00:00:00'}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Control Panel */}
      <Card title="執行控制" size="small" style={{ marginTop: 16 }}>
        <Space wrap>
          {isExecuting ? (
            <>
              <Button icon={<PauseCircleOutlined />} onClick={pauseStrategy}>
                暫停
              </Button>
              <Button icon={<PlayCircleOutlined />} onClick={resumeStrategy}>
                恢復
              </Button>
              <Button onClick={executeOnce}>
                執行一次
              </Button>
              <Button danger icon={<StopOutlined />} onClick={stopStrategy}>
                停止
              </Button>
              <Button danger icon={<ExclamationCircleOutlined />} onClick={emergencyStop}>
                緊急停止
              </Button>
            </>
          ) : (
            <Button type="primary" icon={<PlayCircleOutlined />} onClick={startStrategy}>
              啟動策略
            </Button>
          )}
          <Button icon={<ApiOutlined />} onClick={() => setManualOrderModalVisible(true)}>
            手動下單
          </Button>
          <Button icon={<SyncOutlined />} onClick={refreshAll}>
            刷新數據
          </Button>
          <Tooltip title={isRealTimeActive ? "實時數據已連接" : "實時數據未連接"}>
            <Badge
              status={isRealTimeActive ? "processing" : "default"}
              text={`實時: ${isRealTimeActive ? '開啟' : '關閉'}`}
            />
          </Tooltip>
        </Space>
      </Card>

      {/* Real-time Chart */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={16}>
          <Card title="實時盈虧" size="small">
            {chartData.length > 0 ? (
              <Line {...realTimeChartConfig} />
            ) : (
              <Empty description="暫無數據" />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="系統資源" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text>CPU使用率</Text>
                <Progress
                  percent={executionStatus?.cpuUsage || 0}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
              </div>
              <div>
                <Text>內存使用率</Text>
                <Progress
                  percent={executionStatus?.memoryUsage || 0}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#ff7875',
                  }}
                />
              </div>
              <div>
                <Text>延遲</Text>
                <Progress
                  percent={executionStatus?.latency || 0}
                  strokeColor={{
                    '0%': '#52c41a',
                    '100%': '#f5222d',
                  }}
                />
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Positions and Orders */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="當前持倉" size="small">
            <Table
              columns={positionColumns}
              dataSource={positions}
              rowKey="id"
              pagination={false}
              scroll={{ y: 300 }}
              size="small"
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="最近訂單" size="small">
            <Table
              columns={orderColumns}
              dataSource={orders?.slice(0, 10)}
              rowKey="id"
              pagination={false}
              scroll={{ y: 300 }}
              size="small"
            />
          </Card>
        </Col>
      </Row>

      {/* Execution Events */}
      <Card title="執行事件" size="small" style={{ marginTop: 16 }}>
        <Timeline
          mode="left"
          items={events.slice(0, 10).map(event => ({
            color: event.type === 'error' ? 'red' : event.type === 'warning' ? 'orange' : 'blue',
            dot: event.type === 'error' ? <ExclamationCircleOutlined /> :
                 event.type === 'order' ? <ApiOutlined /> :
                 event.type === 'position' ? <TrophyOutlined /> :
                 event.type === 'signal' ? <ThunderboltOutlined /> :
                 <InfoCircleOutlined />,
            children: (
              <div>
                <Text type="secondary">{dayjs(event.timestamp).format('HH:mm:ss')}</Text>
                <br />
                <Text>{event.message}</Text>
                {event.details && (
                  <div style={{ marginTop: 4 }}>
                    <Text type="secondary" code>
                      {JSON.stringify(event.details, null, 2)}
                    </Text>
                  </div>
                )}
              </div>
            ),
          }))}
        />
      </Card>

      {/* Manual Order Modal */}
      <Modal
        title="手動下單"
        open={manualOrderModalVisible}
        onCancel={() => setManualOrderModalVisible(false)}
        onOk={() => form.submit()}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleManualOrder}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="交易品種"
                name="symbol"
                rules={[{ required: true, message: '請輸入交易品種' }]}
              >
                <Input placeholder="如: BTCUSDT" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="交易方向"
                name="side"
                rules={[{ required: true, message: '請選擇交易方向' }]}
              >
                <Select placeholder="選擇交易方向">
                  <Select.Option value="BUY">買入</Select.Option>
                  <Select.Option value="SELL">賣出</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="訂單類型"
                name="type"
                rules={[{ required: true, message: '請選擇訂單類型' }]}
              >
                <Select placeholder="選擇訂單類型">
                  <Select.Option value="MARKET">市價單</Select.Option>
                  <Select.Option value="LIMIT">限價單</Select.Option>
                  <Select.Option value="STOP">止損單</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="數量"
                name="quantity"
                rules={[{ required: true, message: '請輸入數量' }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  step={0.01}
                  placeholder="0.00"
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="價格"
                name="price"
                dependencies={['type']}
                rules={[
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (getFieldValue('type') === 'MARKET') {
                        return Promise.resolve()
                      }
                      if (!value || value <= 0) {
                        return Promise.reject(new Error('請輸入有效價格'))
                      }
                      return Promise.resolve()
                    },
                  }),
                ]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  step={0.01}
                  placeholder="0.00"
                  disabled={form.getFieldValue('type') === 'MARKET'}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="有效期"
                name="timeInForce"
              >
                <Select defaultValue="GTC">
                  <Select.Option value="GTC">撤銷前有效</Select.Option>
                  <Select.Option value="IOC">立即成交或撤銷</Select.Option>
                  <Select.Option value="FOK">全部成交或撤銷</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  )
}

export default ExecutionMonitor