import React, { useState, useEffect } from 'react'
import { Card, Table, Tag, Button, Space, Input, Select, Row, Col, Tooltip, Popconfirm, message } from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  EyeOutlined,
  FilterOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import { Strategy, StrategyType, StrategyStatus } from '../../types'
import { useGetStrategiesQuery, useUpdateStrategyStatusMutation } from '../../store/api/strategyApi'

const { Search } = Input
const { Option } = Select

// Strategy type color mapping
const strategyTypeColors: Record<StrategyType, string> = {
  [StrategyType.SENTIMENT]: 'blue',
  [StrategyType.TECHNICAL]: 'green',
  [StrategyType.MOMENTUM]: 'purple',
  [StrategyType.MEAN_REVERSION]: 'orange',
  [StrategyType.ARBITRAGE]: 'cyan',
}

// Strategy status color mapping
const strategyStatusColors: Record<StrategyStatus, string> = {
  [StrategyStatus.ACTIVE]: 'success',
  [StrategyStatus.INACTIVE]: 'default',
  [StrategyStatus.TESTING]: 'processing',
  [StrategyStatus.ARCHIVED]: 'error',
}

// Strategy status icons
const strategyStatusIcons: Record<StrategyStatus, React.ReactNode> = {
  [StrategyStatus.ACTIVE]: <PlayCircleOutlined />,
  [StrategyStatus.INACTIVE]: <PauseCircleOutlined />,
  [StrategyStatus.TESTING]: <PlayCircleOutlined />,
  [StrategyStatus.ARCHIVED]: <PauseCircleOutlined />,
}

// Risk level color mapping
const riskLevelColors: Record<string, string> = {
  low: 'green',
  medium: 'orange',
  high: 'red',
}

interface StrategyListProps {
  onStrategySelect?: (strategy: Strategy) => void
  onStrategyEdit?: (strategy: Strategy) => void
  onStrategyCreate?: () => void
  viewMode?: 'table' | 'card'
  selectable?: boolean
  selectedStrategies?: string[]
  onSelectionChange?: (selectedIds: string[]) => void
}

const StrategyList: React.FC<StrategyListProps> = ({
  onStrategySelect,
  onStrategyEdit,
  onStrategyCreate,
  viewMode = 'table',
  selectable = false,
  selectedStrategies = [],
  onSelectionChange,
}) => {
  // State management
  const [searchText, setSearchText] = useState('')
  const [filterType, setFilterType] = useState<StrategyType | 'all'>('all')
  const [filterStatus, setFilterStatus] = useState<StrategyStatus | 'all'>('all')
  const [filterRisk, setFilterRisk] = useState<string>('all')
  const [sortedInfo, setSortedInfo] = useState<any>({})

  // API hooks
  const { data: strategies, isLoading, error } = useGetStrategiesQuery()
  const [updateStatus, { isLoading: isUpdating }] = useUpdateStrategyStatusMutation()

  // Filter strategies
  const filteredStrategies = strategies?.filter((strategy) => {
    if (searchText && !strategy.name.toLowerCase().includes(searchText.toLowerCase())) {
      return false
    }
    if (filterType !== 'all' && strategy.type !== filterType) {
      return false
    }
    if (filterStatus !== 'all' && strategy.status !== filterStatus) {
      return false
    }
    if (filterRisk !== 'all' && strategy.riskLevel !== filterRisk) {
      return false
    }
    return true
  }) || []

  // Handle strategy status change
  const handleStatusChange = async (strategyId: string, newStatus: StrategyStatus) => {
    try {
      await updateStatus({ id: strategyId, status: newStatus }).unwrap()
      message.success(`策略状态已更新`)
    } catch (error) {
      message.error('更新策略状态失败')
    }
  }

  // Table columns configuration
  const columns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      sorter: (a: Strategy, b: Strategy) => a.name.localeCompare(b.name),
      sortOrder: sortedInfo.columnKey === 'name' ? sortedInfo.order : null,
      render: (text: string, record: Strategy) => (
        <div className="flex items-center space-x-2">
          <span className="font-medium">{text}</span>
          {record.lastActive && (
            <Tooltip title={`最后活跃: ${new Date(record.lastActive).toLocaleString()}`}>
              <span className="text-xs text-gray-500">
                {new Date(record.lastActive).toLocaleDateString()}
              </span>
            </Tooltip>
          )}
        </div>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      filters: Object.values(StrategyType).map(type => ({
        text: type,
        value: type,
      })),
      filteredValue: filterType === 'all' ? null : filterType,
      render: (type: StrategyType) => (
        <Tag color={strategyTypeColors[type]}>
          {type}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      filters: Object.values(StrategyStatus).map(status => ({
        text: status,
        value: status,
      })),
      filteredValue: filterStatus === 'all' ? null : filterStatus,
      render: (status: StrategyStatus) => (
        <Tag color={strategyStatusColors[status]} icon={strategyStatusIcons[status]}>
          {status}
        </Tag>
      ),
    },
    {
      title: '风险等级',
      dataIndex: 'riskLevel',
      key: 'riskLevel',
      filters: [
        { text: 'Low', value: 'low' },
        { text: 'Medium', value: 'medium' },
        { text: 'High', value: 'high' },
      ],
      filteredValue: filterRisk === 'all' ? null : filterRisk,
      render: (riskLevel: string) => (
        <Tag color={riskLevelColors[riskLevel]}>
          {riskLevel.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: '总收益率',
      dataIndex: 'performance.totalReturn',
      key: 'totalReturn',
      sorter: (a: Strategy, b: Strategy) => a.performance.totalReturn - b.performance.totalReturn,
      sortOrder: sortedInfo.columnKey === 'totalReturn' ? sortedInfo.order : null,
      render: (value: number) => (
        <span className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
          {value >= 0 ? '+' : ''}{(value * 100).toFixed(2)}%
        </span>
      ),
    },
    {
      title: '夏普比率',
      dataIndex: 'performance.sharpeRatio',
      key: 'sharpeRatio',
      sorter: (a: Strategy, b: Strategy) => a.performance.sharpeRatio - b.performance.sharpeRatio,
      sortOrder: sortedInfo.columnKey === 'sharpeRatio' ? sortedInfo.order : null,
      render: (value: number) => (
        <span className={value >= 1 ? 'text-green-600' : 'text-orange-600'}>
          {value.toFixed(2)}
        </span>
      ),
    },
    {
      title: '胜率',
      dataIndex: 'performance.winRate',
      key: 'winRate',
      sorter: (a: Strategy, b: Strategy) => a.performance.winRate - b.performance.winRate,
      sortOrder: sortedInfo.columnKey === 'winRate' ? sortedInfo.order : null,
      render: (value: number) => (
        <span className={value >= 0.6 ? 'text-green-600' : 'text-orange-600'}>
          {(value * 100).toFixed(1)}%
        </span>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      sorter: (a: Strategy, b: Strategy) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime(),
      sortOrder: sortedInfo.columnKey === 'createdAt' ? sortedInfo.order : null,
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right',
      width: 180,
      render: (_, record: Strategy) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => onStrategySelect?.(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => onStrategyEdit?.(record)}
            />
          </Tooltip>
          {record.status === StrategyStatus.ACTIVE ? (
            <Tooltip title="暂停">
              <Popconfirm
                title="确定要暂停此策略吗？"
                onConfirm={() => handleStatusChange(record.id, StrategyStatus.INACTIVE)}
              >
                <Button
                  type="text"
                  icon={<PauseCircleOutlined />}
                  loading={isUpdating}
                />
              </Popconfirm>
            </Tooltip>
          ) : (
            <Tooltip title="启动">
              <Popconfirm
                title="确定要启动此策略吗？"
                onConfirm={() => handleStatusChange(record.id, StrategyStatus.ACTIVE)}
              >
                <Button
                  type="text"
                  icon={<PlayCircleOutlined />}
                  loading={isUpdating}
                />
              </Popconfirm>
            </Tooltip>
          )}
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除此策略吗？此操作不可恢复！"
              onConfirm={() => {/* Handle delete */}}
            >
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ]

  // Row selection configuration
  const rowSelection = selectable ? {
    selectedRowKeys: selectedStrategies,
    onChange: (selectedRowKeys: React.Key[]) => {
      onSelectionChange?.(selectedRowKeys as string[])
    },
  } : undefined

  return (
    <div className="space-y-4">
      {/* Filters and Actions */}
      <Card className="bg-gray-50">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Search
              placeholder="搜索策略名称"
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              prefix={<SearchOutlined />}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              style={{ width: '100%' }}
              placeholder="策略类型"
              value={filterType}
              onChange={setFilterType}
              allowClear
            >
              <Option value="all">全部类型</Option>
              {Object.values(StrategyType).map(type => (
                <Option key={type} value={type}>{type}</Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              style={{ width: '100%' }}
              placeholder="状态"
              value={filterStatus}
              onChange={setFilterStatus}
              allowClear
            >
              <Option value="all">全部状态</Option>
              {Object.values(StrategyStatus).map(status => (
                <Option key={status} value={status}>{status}</Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              style={{ width: '100%' }}
              placeholder="风险等级"
              value={filterRisk}
              onChange={setFilterRisk}
              allowClear
            >
              <Option value="all">全部风险</Option>
              <Option value="low">低风险</Option>
              <Option value="medium">中风险</Option>
              <Option value="high">高风险</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Space>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={onStrategyCreate}
              >
                新建策略
              </Button>
              <Button
                icon={<FilterOutlined />}
                onClick={() => {
                  setSearchText('')
                  setFilterType('all')
                  setFilterStatus('all')
                  setFilterRisk('all')
                  setSortedInfo({})
                }}
              >
                重置筛选
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Strategy Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredStrategies}
          rowKey="id"
          loading={isLoading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条策略`,
            defaultPageSize: 10,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
          scroll={{ x: 1200 }}
          rowSelection={rowSelection}
          onChange={(pagination, filters, sorter) => {
            setSortedInfo(sorter)
          }}
        />
      </Card>
    </div>
  )
}

export default StrategyList