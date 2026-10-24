import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Tag,
  Button,
  Space,
  Tabs,
  Table,
  Timeline,
  Alert,
  Spin,
  Empty,
  Tooltip,
  Badge,
  Descriptions,
  Divider,
  List,
  Avatar,
  message,
  Switch,
  Typography,
} from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
  SyncOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  LineChartOutlined,
  FireOutlined,
  BugOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import { useNavigate, useParams } from 'react-router-dom'
import dayjs from 'dayjs'
import { Line, Column } from '@ant-design/plots'

import { useStrategyDetail, useStrategyExecution } from '../../hooks/strategies'
import { Strategy, StrategyStatus, RiskLevel } from '../../types'
import ExecutionMonitor from './ExecutionMonitor'
import BacktestPanel from './BacktestPanel'

// Styles
import './StrategyDetails.css'

const { TabPane } = Tabs
const { Text } = Typography

interface StrategyDetailsProps {
  strategyId: string
  onEdit?: () => void
  onDelete?: () => void
  embedded?: boolean
}

const StrategyDetails: React.FC<StrategyDetailsProps> = ({
  strategyId,
  onEdit,
  onDelete,
  embedded = false,
}) => {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('overview')
  const [realTimeEnabled, setRealTimeEnabled] = useState(true)

  const {
    strategy,
    performance,
    metrics,
    executionStatus,
    riskMetrics,
    logs,
    orders,
    positions,
    isLoading,
    isRealTimeActive,
    refreshAll,
    refreshPerformance,
    refreshExecutionStatus,
    refreshLogs,
    refreshOrders,
    refreshPositions,
    setRealTimeEnabled,
  } = useStrategyDetail({ strategyId, autoFetch: true })

  const {
    isExecuting,
    executionState,
    startStrategy,
    stopStrategy,
    pauseStrategy,
    resumeStrategy,
    executeOnce,
    emergencyStop,
  } = useStrategyExecution({ strategyId })

  // Format performance data for charts
  const performanceData = performance?.historical?.map((item: any) => ({
    date: dayjs(item.date).format('YYYY-MM-DD'),
    value: item.value,
    benchmark: item.benchmark,
  })) || []

  // Drawdown chart data
  const drawdownData = performance?.drawdown?.map((item: any) => ({
    date: dayjs(item.date).format('YYYY-MM-DD'),
    value: item.value,
  })) || []

  // Recent trades table columns
  const tradesColumns = [
    {
      title: '時間',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (time: string) => dayjs(time).format('MM-DD HH:mm:ss'),
      sorter: (a: any, b: any) => dayjs(a.timestamp).valueOf() - dayjs(b.timestamp).valueOf(),
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
      title: '盈虧',
      dataIndex: 'pnl',
      key: 'pnl',
      align: 'right' as const,
      render: (pnl: number) => (
        <Text style={{ color: pnl >= 0 ? '#52c41a' : '#f5222d' }}>
          {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}
        </Text>
      ),
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          filled: { color: 'success', text: '已成交' },
          partially_filled: { color: 'processing', text: '部分成交' },
          cancelled: { color: 'default', text: '已取消' },
          rejected: { color: 'error', text: '已拒絕' },
        }
        const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.filled
        return <Badge status={config.color} text={config.text} />
      },
    },
  ]

  // Execution logs columns
  const logsColumns = [
    {
      title: '時間',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (time: string) => dayjs(time).format('MM-DD HH:mm:ss'),
      width: 150,
    },
    {
      title: '級別',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level: string) => {
        const levelConfig = {
          ERROR: { color: 'red', icon: <ExclamationCircleOutlined /> },
          WARN: { color: 'orange', icon: <WarningOutlined /> },
          INFO: { color: 'blue', icon: <InfoCircleOutlined /> },
          DEBUG: { color: 'default', icon: <BugOutlined /> },
        }
        const config = levelConfig[level as keyof typeof levelConfig] || levelConfig.INFO
        return (
          <Tag color={config.color} icon={config.icon}>
            {level}
          </Tag>
        )
      },
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
    },
  ]

  // Handle action buttons
  const handleStart = async () => {
    try {
      await startStrategy()
    } catch (error) {
      // Error is handled in the hook
    }
  }

  const handleStop = async () => {
    try {
      await stopStrategy()
    } catch (error) {
      // Error is handled in the hook
    }
  }

  const handlePause = async () => {
    try {
      await pauseStrategy()
    } catch (error) {
      // Error is handled in the hook
    }
  }

  const handleResume = async () => {
    try {
      await resumeStrategy()
    } catch (error) {
      // Error is handled in the hook
    }
  }

  const handleExecuteOnce = async () => {
    try {
      await executeOnce()
    } catch (error) {
      // Error is handled in the hook
    }
  }

  const handleEmergencyStop = async () => {
    try {
      await emergencyStop()
    } catch (error) {
      // Error is handled in the hook
    }
  }

  const handleEdit = () => {
    if (onEdit) {
      onEdit()
    } else {
      navigate(`/strategies/${strategyId}/edit`)
    }
  }

  // Get status color and icon
  const getStatusInfo = (status: StrategyStatus) => {
    const statusMap = {
      [StrategyStatus.ACTIVE]: { color: 'success', icon: <FireOutlined />, text: '運行中' },
      [StrategyStatus.INACTIVE]: { color: 'default', icon: <StopOutlined />, text: '已停止' },
      [StrategyStatus.TESTING]: { color: 'processing', icon: <SyncOutlined spin />, text: '測試中' },
      [StrategyStatus.ARCHIVED]: { color: 'warning', icon: <StopOutlined />, text: '已歸檔' },
    }
    return statusMap[status] || statusMap[StrategyStatus.INACTIVE]
  }

  if (isLoading && !strategy) {
    return (
      <div className="strategy-details-loading">
        <Spin size="large" />
        <p>加載策略詳情中...</p>
      </div>
    )
  }

  if (!strategy) {
    return (
      <Empty
        description="策略不存在或已被刪除"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      >
        <Button type="primary" onClick={() => navigate('/strategies')}>
          返回策略列表
        </Button>
      </Empty>
    )
  }

  const statusInfo = getStatusInfo(strategy.status)

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className={`strategy-details ${embedded ? 'embedded' : ''}`}
    >
      {/* Header */}
      <Card className="strategy-header">
        <Row justify="space-between" align="middle">
          <Col>
            <Space direction="vertical" size="small">
              <Space>
                <h2 className="strategy-name">{strategy.name}</h2>
                <Tag color={statusInfo.color} icon={statusInfo.icon}>
                  {statusInfo.text}
                </Tag>
                <Tag color={strategy.riskLevel === 'low' ? 'green' : strategy.riskLevel === 'medium' ? 'orange' : 'red'}>
                  {strategy.riskLevel.toUpperCase()}
                </Tag>
              </Space>
              <Text type="secondary">{strategy.description}</Text>
            </Space>
          </Col>
          <Col>
            <Space>
              <Tooltip title="實時數據更新">
                <Switch
                  checkedChildren="實時"
                  unCheckedChildren="手動"
                  checked={realTimeEnabled}
                  onChange={setRealTimeEnabled}
                />
              </Tooltip>
              <Button icon={<SyncOutlined />} onClick={refreshAll}>
                刷新
              </Button>
              <Button icon={<EditOutlined />} onClick={handleEdit}>
                編輯
              </Button>
              {strategy.status === StrategyStatus.ACTIVE ? (
                <Space>
                  <Button icon={<PauseCircleOutlined />} onClick={handlePause}>
                    暫停
                  </Button>
                  <Button danger icon={<StopOutlined />} onClick={handleStop}>
                    停止
                  </Button>
                  <Button danger icon={<ExclamationCircleOutlined />} onClick={handleEmergencyStop}>
                    緊急停止
                  </Button>
                </Space>
              ) : (
                <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleStart}>
                  啟動
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Key Metrics */}
      <Row gutter={[16, 16]} className="metrics-row">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="總回報率"
              value={strategy.performance.totalReturn * 100}
              precision={2}
              valueStyle={{ color: strategy.performance.totalReturn >= 0 ? '#52c41a' : '#f5222d' }}
              prefix={strategy.performance.totalReturn >= 0 ? '+' : ''}
              suffix="%"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="夏普比率"
              value={strategy.performance.sharpeRatio}
              precision={2}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="最大回撤"
              value={strategy.performance.maxDrawdown * 100}
              precision={2}
              valueStyle={{ color: '#ff4d4f' }}
              suffix="%"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="勝率"
              value={strategy.performance.winRate * 100}
              precision={1}
              valueStyle={{ color: '#52c41a' }}
              suffix="%"
            />
          </Card>
        </Col>
      </Row>

      {/* Details Tabs */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane
            tab={
              <span>
                <LineChartOutlined />
                概覽
              </span>
            }
            key="overview"
          >
            <Row gutter={[16, 16]}>
              {/* Performance Chart */}
              <Col xs={24} lg={16}>
                <Card title="績效走勢" size="small">
                  {performanceData.length > 0 ? (
                    <Line
                      data={performanceData}
                      xField="date"
                      yField="value"
                      smooth
                      color={['#1890ff', '#52c41a']}
                      seriesField="type"
                      legend={{
                        position: 'top',
                      }}
                      tooltip={{
                        formatter: (datum: any) => ({
                          name: datum.type === 'value' ? '策略績效' : '基準',
                          value: `${(datum.value * 100).toFixed(2)}%`,
                        }),
                      }}
                    />
                  ) : (
                    <Empty description="暫無績效數據" />
                  )}
                </Card>
              </Col>

              {/* Strategy Info */}
              <Col xs={24} lg={8}>
                <Card title="策略信息" size="small">
                  <Descriptions column={1}>
                    <Descriptions.Item label="策略ID">{strategy.id}</Descriptions.Item>
                    <Descriptions.Item label="策略類型">{strategy.type}</Descriptions.Item>
                    <Descriptions.Item label="風險級別">
                      <Tag color={strategy.riskLevel === 'low' ? 'green' : strategy.riskLevel === 'medium' ? 'orange' : 'red'}>
                        {strategy.riskLevel}
                      </Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="創建時間">
                      {dayjs(strategy.createdAt).format('YYYY-MM-DD HH:mm:ss')}
                    </Descriptions.Item>
                    <Descriptions.Item label="最後更新">
                      {dayjs(strategy.updatedAt).format('YYYY-MM-DD HH:mm:ss')}
                    </Descriptions.Item>
                    <Descriptions.Item label="最後活躍">
                      {strategy.lastActive ? dayjs(strategy.lastActive).format('YYYY-MM-DD HH:mm:ss') : '未運行'}
                    </Descriptions.Item>
                  </Descriptions>
                </Card>

                {/* Execution Status */}
                {executionStatus && (
                  <Card title="執行狀態" size="small" style={{ marginTop: 16 }}>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div>
                        <Text>運行狀態: </Text>
                        <Badge status={executionState === 'running' ? 'success' : executionState === 'error' ? 'error' : 'default'} />
                        <Text strong> {executionState}</Text>
                      </div>
                      <div>
                        <Text>運行時長: </Text>
                        <Text>{executionStatus.uptime || 'N/A'}</Text>
                      </div>
                      <div>
                        <Text>執行次數: </Text>
                        <Text>{executionStatus.executionCount || 0}</Text>
                      </div>
                      <div>
                        <Text>當前持倉: </Text>
                        <Text>{executionStatus.positionCount || 0}</Text>
                      </div>
                      <div>
                        <Text>CPU使用率: </Text>
                        <Progress percent={executionStatus.cpuUsage || 0} size="small" />
                      </div>
                      <div>
                        <Text>內存使用: </Text>
                        <Progress percent={executionStatus.memoryUsage || 0} size="small" />
                      </div>
                    </Space>
                  </Card>
                )}
              </Col>
            </Row>
          </TabPane>

          <TabPane
            tab={
              <span>
                <TrophyOutlined />
                績效分析
              </span>
            }
            key="performance"
          >
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <Card title="詳細績效指標" size="small">
                  <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12} md={8}>
                      <Statistic
                        title="年化收益率"
                        value={performance?.annualReturn || 0}
                        precision={2}
                        suffix="%"
                      />
                    </Col>
                    <Col xs={24} sm={12} md={8}>
                      <Statistic
                        title="波動率"
                        value={performance?.volatility || 0}
                        precision={2}
                        suffix="%"
                      />
                    </Col>
                    <Col xs={24} sm={12} md={8}>
                      <Statistic
                        title="最大連續盈利"
                        value={performance?.maxConsecutiveWins || 0}
                      />
                    </Col>
                    <Col xs={24} sm={12} md={8}>
                      <Statistic
                        title="最大連續虧損"
                        value={performance?.maxConsecutiveLosses || 0}
                      />
                    </Col>
                    <Col xs={24} sm={12} md={8}>
                      <Statistic
                        title="盈虧比"
                        value={performance?.profitLossRatio || 0}
                        precision={2}
                      />
                    </Col>
                    <Col xs={24} sm={12} md={8}>
                      <Statistic
                        title="卡爾瑪比率"
                        value={performance?.calmarRatio || 0}
                        precision={2}
                      />
                    </Col>
                  </Row>
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane
            tab={
              <span>
                <SyncOutlined />
                執行監控
              </span>
            }
            key="execution"
          >
            <ExecutionMonitor
              strategyId={strategyId}
              realTime={realTimeEnabled}
            />
          </TabPane>

          <TabPane
            tab={
              <span>
                <FireOutlined />
                交易記錄
              </span>
            }
            key="trades"
          >
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <Card title="最近交易" size="small">
                  <Table
                    columns={tradesColumns}
                    dataSource={orders}
                    rowKey="id"
                    pagination={{
                      pageSize: 10,
                      showSizeChanger: true,
                      showQuickJumper: true,
                    }}
                    loading={!orders}
                    scroll={{ x: 800 }}
                  />
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane
            tab={
              <span>
                <LineChartOutlined />
                回測分析
              </span>
            }
            key="backtest"
          >
            <BacktestPanel
              strategyId={strategyId}
            />
          </TabPane>

          <TabPane
            tab={
              <span>
                <ClockCircleOutlined />
                執行日誌
              </span>
            }
            key="logs"
          >
            <Card title="執行日誌" size="small">
              <Table
                columns={logsColumns}
                dataSource={logs}
                rowKey="id"
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                }}
                loading={!logs}
                scroll={{ y: 400 }}
              />
            </Card>
          </TabPane>
        </Tabs>
      </Card>
    </motion.div>
  )
}

export default StrategyDetails