import React, { useState, useEffect } from 'react'
import { Table, Tag, Button, Space, Tooltip, Typography, Progress, Badge } from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  EyeOutlined,
  SettingOutlined,
  ReloadOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

const { Text } = Typography

interface StrategyStatus {
  id: string
  name: string
  status: 'running' | 'paused' | 'stopped' | 'error'
  lastRun: string
  nextRun: string
  executions: {
    total: number
    success: number
    failed: number
  }
  performance: {
    avgExecutionTime: number
    successRate: number
    last24hProfit: number
  }
  resources: {
    cpu: number
    memory: number
  }
}

interface StrategyStatusMonitorProps {
  strategies?: StrategyStatus[]
  onStrategyAction?: (strategyId: string, action: string) => void
  refreshInterval?: number
}

const StrategyStatusMonitor: React.FC<StrategyStatusMonitorProps> = ({
  strategies = [],
  onStrategyAction,
  refreshInterval = 5000,
}) => {
  const [strategyList, setStrategyList] = useState<StrategyStatus[]>([
    {
      id: '1',
      name: 'RSI均值回歸策略',
      status: 'running',
      lastRun: '2分鐘前',
      nextRun: '13分鐘後',
      executions: {
        total: 1456,
        success: 1435,
        failed: 21,
      },
      performance: {
        avgExecutionTime: 125,
        successRate: 98.6,
        last24hProfit: 2.35,
      },
      resources: {
        cpu: 15,
        memory: 8,
      },
    },
    {
      id: '2',
      name: 'MACD動量策略',
      status: 'running',
      lastRun: '5分鐘前',
      nextRun: '25分鐘後',
      executions: {
        total: 1234,
        success: 1187,
        failed: 47,
      },
      performance: {
        avgExecutionTime: 98,
        successRate: 96.2,
        last24hProfit: 1.82,
      },
      resources: {
        cpu: 12,
        memory: 6,
      },
    },
    {
      id: '3',
      name: '布林帶突破策略',
      status: 'error',
      lastRun: '1小時前',
      nextRun: '-',
      executions: {
        total: 892,
        success: 842,
        failed: 50,
      },
      performance: {
        avgExecutionTime: 0,
        successRate: 94.4,
        last24hProfit: -0.45,
      },
      resources: {
        cpu: 0,
        memory: 0,
      },
    },
    {
      id: '4',
      name: '情感分析策略',
      status: 'paused',
      lastRun: '30分鐘前',
      nextRun: '30分鐘後',
      executions: {
        total: 756,
        success: 749,
        failed: 7,
      },
      performance: {
        avgExecutionTime: 210,
        successRate: 99.1,
        last24hProfit: 0,
      },
      resources: {
        cpu: 2,
        memory: 1,
      },
    },
  ])

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setStrategyList(prevStrategies =>
        prevStrategies.map(strategy => {
          if (strategy.status === 'running') {
            return {
              ...strategy,
              performance: {
                ...strategy.performance,
                last24hProfit: strategy.performance.last24hProfit + (Math.random() - 0.5) * 0.1,
              },
            }
          }
          return strategy
        })
      )
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [refreshInterval])

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'running':
        return { color: 'success', icon: <PlayCircleOutlined />, text: '運行中' }
      case 'paused':
        return { color: 'default', icon: <PauseCircleOutlined />, text: '已暫停' }
      case 'stopped':
        return { color: 'warning', icon: <StopOutlined />, text: '已停止' }
      case 'error':
        return { color: 'error', icon: <WarningOutlined />, text: '錯誤' }
      default:
        return { color: 'default', icon: <ClockCircleOutlined />, text: '未知' }
    }
  }

  const columns: ColumnsType<StrategyStatus> = [
    {
      title: '策略名稱',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: StrategyStatus) => (
        <Space>
          <Badge status={getStatusConfig(record.status).color as any} />
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const config = getStatusConfig(status)
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        )
      },
      filters: [
        { text: '運行中', value: 'running' },
        { text: '已暫停', value: 'paused' },
        { text: '已停止', value: 'stopped' },
        { text: '錯誤', value: 'error' },
      ],
      onFilter: (value, record) => record.status === value,
    },
    {
      title: '執行狀況',
      key: 'execution',
      render: (_, record: StrategyStatus) => (
        <Space direction="vertical" size="small">
          <div className="flex justify-between">
            <Text type="secondary">上次執行:</Text>
            <Text>{record.lastRun}</Text>
          </div>
          <div className="flex justify-between">
            <Text type="secondary">下次執行:</Text>
            <Text>{record.nextRun}</Text>
          </div>
          <div className="flex justify-between">
            <Text type="secondary">總執行次數:</Text>
            <Text>{record.executions.total}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: '成功率',
      key: 'successRate',
      render: (_, record: StrategyStatus) => (
        <div className="space-y-1">
          <Progress
            percent={record.performance.successRate}
            size="small"
            status={record.performance.successRate >= 95 ? 'success' : 'normal'}
            format={() => `${record.performance.successRate.toFixed(1)}%`}
          />
          <div className="text-xs text-gray-500">
            成功: {record.executions.success} / 失敗: {record.executions.failed}
          </div>
        </div>
      ),
      sorter: (a, b) => a.performance.successRate - b.performance.successRate,
    },
    {
      title: '24h收益',
      dataIndex: ['performance', 'last24hProfit'],
      key: 'profit',
      render: (profit: number) => (
        <Text className={profit >= 0 ? 'text-green-600' : 'text-red-600'}>
          {profit >= 0 ? '+' : ''}{profit.toFixed(2)}%
        </Text>
      ),
      sorter: (a, b) => a.performance.last24hProfit - b.performance.last24hProfit,
    },
    {
      title: '資源使用',
      key: 'resources',
      render: (_, record: StrategyStatus) => (
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <div className="flex items-center space-x-2">
            <Text className="text-xs w-8">CPU</Text>
            <Progress
              percent={record.resources.cpu}
              size="small"
              showInfo={false}
              strokeColor={record.resources.cpu > 80 ? '#ff4d4f' : '#52c41a'}
              style={{ flex: 1 }}
            />
            <Text className="text-xs w-8">{record.resources.cpu}%</Text>
          </div>
          <div className="flex items-center space-x-2">
            <Text className="text-xs w-8">MEM</Text>
            <Progress
              percent={record.resources.memory}
              size="small"
              showInfo={false}
              strokeColor={record.resources.memory > 80 ? '#ff4d4f' : '#52c41a'}
              style={{ flex: 1 }}
            />
            <Text className="text-xs w-8">{record.resources.memory}%</Text>
          </div>
        </Space>
      ),
    },
    {
      title: '平均執行時間',
      dataIndex: ['performance', 'avgExecutionTime'],
      key: 'executionTime',
      render: (time: number) => (
        <Text>{time}ms</Text>
      ),
      sorter: (a, b) => a.performance.avgExecutionTime - b.performance.avgExecutionTime,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: StrategyStatus) => (
        <Space>
          <Tooltip title="查看詳情">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => onStrategyAction?.(record.id, 'view')}
            />
          </Tooltip>
          <Tooltip title="配置">
            <Button
              type="text"
              size="small"
              icon={<SettingOutlined />}
              onClick={() => onStrategyAction?.(record.id, 'config')}
            />
          </Tooltip>
          {record.status === 'running' ? (
            <Tooltip title="暫停">
              <Button
                type="text"
                size="small"
                icon={<PauseCircleOutlined />}
                onClick={() => onStrategyAction?.(record.id, 'pause')}
              />
            </Tooltip>
          ) : (
            <Tooltip title="啟動">
              <Button
                type="text"
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={() => onStrategyAction?.(record.id, 'start')}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Text strong className="text-lg">策略狀態監控</Text>
        <Button
          type="text"
          size="small"
          icon={<ReloadOutlined />}
          onClick={() => {
            // Refresh strategy list
            console.log('Refreshing strategy status...')
          }}
        >
          刷新
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={strategyList}
        rowKey="id"
        size="small"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total, range) =>
            `第 ${range[0]}-${range[1]} 條，共 ${total} 條`,
        }}
        scroll={{ x: 1000 }}
      />
    </div>
  )
}

export default StrategyStatusMonitor