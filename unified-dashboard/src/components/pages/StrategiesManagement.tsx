import React, { useState, useEffect, useMemo } from 'react'
import {
  Row,
  Col,
  Card,
  Table,
  Tag,
  Button,
  Space,
  Input,
  Select,
  Drawer,
  Modal,
  Form,
  Switch,
  Slider,
  Typography,
  Alert,
  Tooltip,
  Dropdown,
  Badge,
  Progress,
  Divider,
  Statistic,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  DeleteOutlined,
  ExportOutlined,
  ImportOutlined,
  SettingOutlined,
  BarChartOutlined,
  FilterOutlined,
  SearchOutlined,
  ReloadOutlined,
  MoreOutlined,
  RocketOutlined,
  TrophyOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'

// Enhanced Components
import {
  StrategyPerformanceChart,
  StrategyComparisonChart
} from '../Charts'

// Hooks and Services
import { useAppSelector, useAppDispatch } from '../../hooks/redux'
import { selectStrategies, updateStrategy, createStrategy, deleteStrategy } from '../../store/slices/strategiesSlice'
import { useWebSocket } from '../../hooks/useWebSocket'

// Components
import StrategyCard from '../common/StrategyCard'
import StrategyForm from '../common/StrategyForm'
import BatchOperations from '../common/BatchOperations'
import PerformanceMetrics from '../common/PerformanceMetrics'

const { Title, Text } = Typography
const { Search } = Input
const { Option } = Select

interface StrategiesManagementProps {
  viewMode?: 'grid' | 'table'
  enableBatchOperations?: boolean
  enableRealTimeUpdates?: boolean
}

const StrategiesManagement: React.FC<StrategiesManagementProps> = ({
  viewMode = 'grid',
  enableBatchOperations = true,
  enableRealTimeUpdates = true
}) => {
  // Redux state
  const dispatch = useAppDispatch()
  const { strategies, loading } = useAppSelector(selectStrategies)

  // Local state
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([])
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<string>('name')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')

  // Modal and drawer states
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [editDrawerVisible, setEditDrawerVisible] = useState(false)
  const [selectedStrategyId, setSelectedStrategyId] = useState<string | null>(null)
  const [batchMode, setBatchMode] = useState(false)

  // WebSocket for real-time updates
  const { isConnected, lastMessage } = useWebSocket({
    enabled: enableRealTimeUpdates,
    onMessage: handleStrategyUpdate,
  })

  // Handle real-time strategy updates
  function handleStrategyUpdate(data: any) {
    if (data.type === 'strategy_update') {
      dispatch(updateStrategy(data.strategy))
    }
  }

  // Filter and sort strategies
  const filteredStrategies = useMemo(() => {
    let filtered = [...strategies]

    // Text search
    if (searchText) {
      filtered = filtered.filter(strategy =>
        strategy.name.toLowerCase().includes(searchText.toLowerCase()) ||
        strategy.description?.toLowerCase().includes(searchText.toLowerCase())
      )
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(strategy => strategy.status === statusFilter)
    }

    // Type filter
    if (typeFilter !== 'all') {
      filtered = filtered.filter(strategy => strategy.type === typeFilter)
    }

    // Sort
    filtered.sort((a, b) => {
      let aValue: any = a[sortBy as keyof typeof a]
      let bValue: any = b[sortBy as keyof typeof b]

      if (sortBy === 'performance') {
        aValue = a.performance?.totalReturn || 0
        bValue = b.performance?.totalReturn || 0
      }

      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase()
        bValue = bValue?.toLowerCase() || ''
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1
      } else {
        return aValue < bValue ? 1 : -1
      }
    })

    return filtered
  }, [strategies, searchText, statusFilter, typeFilter, sortBy, sortOrder])

  // Calculate statistics
  const statistics = useMemo(() => {
    const activeStrategies = strategies.filter(s => s.status === 'active')
    const totalReturn = strategies.reduce((sum, s) => sum + (s.performance?.totalReturn || 0), 0)
    const avgSharpeRatio = activeStrategies.length > 0
      ? activeStrategies.reduce((sum, s) => sum + (s.performance?.sharpeRatio || 0), 0) / activeStrategies.length
      : 0

    return {
      totalStrategies: strategies.length,
      activeStrategies: activeStrategies.length,
      totalReturn,
      avgSharpeRatio,
    }
  }, [strategies])

  // Table columns
  const tableColumns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: any) => (
        <Space>
          <Text strong>{text}</Text>
          {record.status === 'active' && <Badge status="success" />}
        </Space>
      ),
      sorter: true,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color="blue">{type}</Tag>
      ),
      filters: [
        { text: '情感分析', value: 'sentiment' },
        { text: '技术分析', value: 'technical' },
        { text: '动量策略', value: 'momentum' },
        { text: '均值回归', value: 'mean_reversion' },
        { text: '套利策略', value: 'arbitrage' },
      ],
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          active: { color: 'success', text: '运行中' },
          inactive: { color: 'default', text: '已停止' },
          testing: { color: 'processing', text: '测试中' },
          archived: { color: 'warning', text: '已归档' },
        }
        const config = statusConfig[status as keyof typeof statusConfig]
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '收益率',
      dataIndex: ['performance', 'totalReturn'],
      key: 'totalReturn',
      render: (value: number) => (
        <Text style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {value ? `${(value * 100).toFixed(2)}%` : '-'}
        </Text>
      ),
      sorter: true,
    },
    {
      title: '夏普比率',
      dataIndex: ['performance', 'sharpeRatio'],
      key: 'sharpeRatio',
      render: (value: number) => value?.toFixed(2) || '-',
      sorter: true,
    },
    {
      title: '最大回撤',
      dataIndex: ['performance', 'maxDrawdown'],
      key: 'maxDrawdown',
      render: (value: number) => (
        <Text style={{ color: '#ff4d4f' }}>
          {value ? `${(value * 100).toFixed(2)}%` : '-'}
        </Text>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: any) => (
        <Space>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditStrategy(record.id)}
            />
          </Tooltip>
          <Tooltip title={record.status === 'active' ? '暂停' : '启动'}>
            <Button
              type="text"
              icon={record.status === 'active' ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={() => handleToggleStrategy(record.id)}
            />
          </Tooltip>
          <Dropdown
            menu={{
              items: [
                {
                  key: 'duplicate',
                  label: '复制策略',
                  icon: <PlusOutlined />,
                },
                {
                  key: 'export',
                  label: '导出配置',
                  icon: <ExportOutlined />,
                },
                {
                  type: 'divider',
                },
                {
                  key: 'delete',
                  label: '删除策略',
                  icon: <DeleteOutlined />,
                  danger: true,
                },
              ],
            }}
          >
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ]

  // Event handlers
  const handleEditStrategy = (strategyId: string) => {
    setSelectedStrategyId(strategyId)
    setEditDrawerVisible(true)
  }

  const handleToggleStrategy = async (strategyId: string) => {
    const strategy = strategies.find(s => s.id === strategyId)
    if (strategy) {
      const newStatus = strategy.status === 'active' ? 'inactive' : 'active'
      dispatch(updateStrategy({ ...strategy, status: newStatus }))
    }
  }

  const handleCreateStrategy = (values: any) => {
    dispatch(createStrategy(values))
    setCreateModalVisible(false)
  }

  const handleBatchOperation = async (operation: string, strategyIds: string[]) => {
    // Implement batch operations
    console.log(`Batch ${operation} on strategies:`, strategyIds)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} className="!mb-2">
            策略管理
          </Title>
          <Text type="secondary">
            管理和配置您的量化交易策略
          </Text>
        </div>

        <Space>
          <Button
            icon={<PlusOutlined />}
            type="primary"
            onClick={() => setCreateModalVisible(true)}
          >
            创建策略
          </Button>
          <Button icon={<ReloadOutlined />} onClick={() => window.location.reload()}>
            刷新
          </Button>
        </Space>
      </div>

      {/* Statistics Cards */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="总策略数"
              value={statistics.totalStrategies}
              prefix={<RocketOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="运行中"
              value={statistics.activeStrategies}
              prefix={<PlayCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="平均夏普比率"
              value={statistics.avgSharpeRatio}
              precision={2}
              prefix={<TrophyOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters and Controls */}
      <Card>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Search
              placeholder="搜索策略名称或描述"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              prefix={<SearchOutlined />}
            />
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="状态筛选"
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: '100%' }}
            >
              <Option value="all">全部状态</Option>
              <Option value="active">运行中</Option>
              <Option value="inactive">已停止</Option>
              <Option value="testing">测试中</Option>
              <Option value="archived">已归档</Option>
            </Select>
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="类型筛选"
              value={typeFilter}
              onChange={setTypeFilter}
              style={{ width: '100%' }}
            >
              <Option value="all">全部类型</Option>
              <Option value="sentiment">情感分析</Option>
              <Option value="technical">技术分析</Option>
              <Option value="momentum">动量策略</Option>
              <Option value="mean_reversion">均值回归</Option>
              <Option value="arbitrage">套利策略</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="排序方式"
              value={sortBy}
              onChange={setSortBy}
              style={{ width: '70%' }}
            >
              <Option value="name">名称</Option>
              <Option value="performance">收益率</Option>
              <Option value="sharpeRatio">夏普比率</Option>
              <Option value="createdAt">创建时间</Option>
            </Select>
            <Button
              type="text"
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              style={{ width: '30%' }}
            >
              {sortOrder === 'asc' ? '↑' : '↓'}
            </Button>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Space>
              <Button
                icon={<FilterOutlined />}
                type={viewMode === 'table' ? 'primary' : 'default'}
                onClick={() => {/* Toggle view mode */}}
              >
                表格视图
              </Button>
              {enableBatchOperations && (
                <Button
                  icon={batchMode ? <ExclamationCircleOutlined /> : undefined}
                  type={batchMode ? 'primary' : 'default'}
                  onClick={() => setBatchMode(!batchMode)}
                >
                  {batchMode ? '批量操作中' : '批量操作'}
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Batch Operations (when enabled) */}
      {enableBatchOperations && batchMode && selectedStrategies.length > 0 && (
        <BatchOperations
          selectedStrategies={selectedStrategies}
          strategies={strategies}
          onOperationComplete={handleBatchOperation}
          onClearSelection={() => setSelectedStrategies([])}
        />
      )}

      {/* Strategies Display */}
      {viewMode === 'table' ? (
        <Card>
          <Table
            columns={tableColumns}
            dataSource={filteredStrategies}
            rowKey="id"
            loading={loading}
            rowSelection={
              batchMode
                ? {
                    selectedRowKeys: selectedStrategies,
                    onChange: setSelectedStrategies,
                  }
                : undefined
            }
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
            }}
          />
        </Card>
      ) : (
        <Row gutter={[16, 16]}>
          {filteredStrategies.map(strategy => (
            <Col xs={24} sm={12} lg={8} xl={6} key={strategy.id}>
              <StrategyCard
                strategy={strategy}
                onEdit={() => handleEditStrategy(strategy.id)}
                onToggle={() => handleToggleStrategy(strategy.id)}
                selectable={batchMode}
                selected={selectedStrategies.includes(strategy.id)}
                onSelect={(selected) => {
                  if (selected) {
                    setSelectedStrategies([...selectedStrategies, strategy.id])
                  } else {
                    setSelectedStrategies(selectedStrategies.filter(id => id !== strategy.id))
                  }
                }}
              />
            </Col>
          ))}
        </Row>
      )}

      {/* Empty State */}
      {filteredStrategies.length === 0 && !loading && (
        <Card>
          <div className="text-center py-12">
            <BarChartOutlined style={{ fontSize: 48, color: '#ccc' }} />
            <Title level={4} type="secondary" className="mt-4">
              没有找到匹配的策略
            </Title>
            <Text type="secondary">
              尝试调整筛选条件或创建新的策略
            </Text>
            <div className="mt-4">
              <Button type="primary" onClick={() => setCreateModalVisible(true)}>
                创建第一个策略
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Create Strategy Modal */}
      <Modal
        title="创建新策略"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        footer={null}
        width={800}
      >
        <StrategyForm onSubmit={handleCreateStrategy} />
      </Modal>

      {/* Edit Strategy Drawer */}
      <Drawer
        title="编辑策略"
        placement="right"
        open={editDrawerVisible}
        onClose={() => setEditDrawerVisible(false)}
        width={800}
      >
        {selectedStrategyId && (
          <StrategyForm
            strategy={strategies.find(s => s.id === selectedStrategyId)}
            onSubmit={(values) => {
              dispatch(updateStrategy({ ...values, id: selectedStrategyId }))
              setEditDrawerVisible(false)
            }}
          />
        )}
      </Drawer>
    </div>
  )
}

export default StrategiesManagement