import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Input,
  Select,
  DatePicker,
  Switch,
  Modal,
  Form,
  Row,
  Col,
  Statistic,
  Tooltip,
  Dropdown,
  Menu,
  message,
  Popconfirm,
  Badge,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  FilterOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  SettingOutlined,
  DownloadOutlined,
  EyeOutlined,
  RocketOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { Strategy, StrategyType, StrategyStatus, RiskLevel } from '@types/index'

// Hooks
import { useGetStrategiesQuery, useUpdateStrategyMutation, useDeleteStrategyMutation, useExecuteStrategyMutation } from '@store/api/strategiesApi'
import { useBatchOperationMutation } from '@store/api/strategiesApi'

// Components
import StrategyDetailModal from '@components/strategies/StrategyDetailModal'
import CreateStrategyModal from '@components/strategies/CreateStrategyModal'
import StrategyPerformanceChart from '@components/charts/StrategyPerformanceChart'

const { Search } = Input
const { Option } = Select
const { RangePicker } = DatePicker

const StrategiesPage: React.FC = () => {
  const [searchText, setSearchText] = useState('')
  const [selectedType, setSelectedType] = useState<StrategyType | null>(null)
  const [selectedStatus, setSelectedStatus] = useState<StrategyStatus | null>(null)
  const [selectedRisk, setSelectedRisk] = useState<RiskLevel | null>(null)
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // API hooks
  const { data: strategiesData, isLoading, error, refetch } = useGetStrategiesQuery({
    page: currentPage,
    pageSize,
    strategyType: selectedType,
    status: selectedStatus,
  })

  const [updateStrategy] = useUpdateStrategyMutation()
  const [deleteStrategy] = useDeleteStrategyMutation()
  const [executeStrategy] = useExecuteStrategyMutation()
  const [batchOperation] = useBatchOperationMutation()

  // Mock data for demonstration
  const mockStrategies: Strategy[] = [
    {
      id: '1',
      name: 'RSI超卖买入策略',
      description: '基于RSI指标的超卖信号买入策略',
      strategyType: StrategyType.CBSCTECHNICAL,
      parameters: { rsi_period: 14, oversold_threshold: 30 },
      status: StrategyStatus.ACTIVE,
      isActive: true,
      riskLevel: RiskLevel.MEDIUM,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-15T00:00:00Z',
      createdBy: 'user1',
      lastRunAt: '2024-01-15T10:30:00Z',
      tags: ['RSI', '技术分析'],
    },
    {
      id: '2',
      name: 'MACD金叉策略',
      description: 'MACD指标金叉买入，死叉卖出',
      strategyType: StrategyType.CBSCTECHNICAL,
      parameters: { fast_period: 12, slow_period: 26, signal_period: 9 },
      status: StrategyStatus.ACTIVE,
      isActive: true,
      riskLevel: RiskLevel.LOW,
      createdAt: '2024-01-02T00:00:00Z',
      updatedAt: '2024-01-14T00:00:00Z',
      createdBy: 'user1',
      lastRunAt: '2024-01-15T10:25:00Z',
      tags: ['MACD', '趋势跟踪'],
    },
    {
      id: '3',
      name: '布林带突破策略',
      description: '价格突破布林带上轨买入，下轨卖出',
      strategyType: StrategyType.CBSCTECHNICALADVANCED,
      parameters: { period: 20, std_dev: 2 },
      status: StrategyStatus.TESTING,
      isActive: false,
      riskLevel: RiskLevel.HIGH,
      createdAt: '2024-01-03T00:00:00Z',
      updatedAt: '2024-01-13T00:00:00Z',
      createdBy: 'user1',
      lastRunAt: '2024-01-12T15:45:00Z',
      tags: ['布林带', '突破'],
    },
    {
      id: '4',
      name: '多因子量化模型',
      description: '结合多个技术指标的综合策略',
      strategyType: StrategyType.MULTIFACTORMODEL,
      parameters: { factors: ['RSI', 'MACD', 'BB', 'VOL'] },
      status: StrategyStatus.ACTIVE,
      isActive: true,
      riskLevel: RiskLevel.MEDIUM,
      createdAt: '2024-01-04T00:00:00Z',
      updatedAt: '2024-01-15T00:00:00Z',
      createdBy: 'user1',
      lastRunAt: '2024-01-15T10:35:00Z',
      tags: ['多因子', '综合'],
    },
  ]

  const strategies = strategiesData?.strategies || mockStrategies

  // Table columns
  const columns: ColumnsType<Strategy> = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text: string, record: Strategy) => (
        <div>
          <div className="font-medium">{text}</div>
          <div className="text-sm text-gray-500">{record.description}</div>
        </div>
      ),
      filteredValue: searchText ? [searchText] : null,
      onFilter: (value, record) =>
        record.name.toLowerCase().includes(value.toLowerCase()) ||
        record.description.toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: '类型',
      dataIndex: 'strategyType',
      key: 'strategyType',
      width: 150,
      render: (type: StrategyType) => {
        const typeMap = {
          [StrategyType.CBSCTECHNICAL]: { color: 'blue', text: 'CBSC技术' },
          [StrategyType.CBSCSENTIMENT]: { color: 'green', text: 'CBSC情绪' },
          [StrategyType.CBSCTECHNICALADVANCED]: { color: 'purple', text: 'CBSC高级技术' },
          [StrategyType.MULTIFACTORMODEL]: { color: 'orange', text: '多因子模型' },
          [StrategyType.MONTHLYLOWFREQUENCY]: { color: 'cyan', text: '月度低频' },
        }
        const config = typeMap[type] || { color: 'default', text: type }
        return <Tag color={config.color}>{config.text}</Tag>
      },
      filters: Object.values(StrategyType).map(type => ({
        text: type,
        value: type,
      })),
      filteredValue: selectedType ? [selectedType] : null,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: StrategyStatus, record: Strategy) => {
        const statusConfig = {
          [StrategyStatus.ACTIVE]: { color: 'success', icon: <CheckCircleOutlined /> },
          [StrategyStatus.INACTIVE]: { color: 'default', icon: <PauseCircleOutlined /> },
          [StrategyStatus.TESTING]: { color: 'processing', icon: <ClockCircleOutlined /> },
          [StrategyStatus.ERROR]: { color: 'error', icon: <WarningOutlined /> },
        }
        const config = statusConfig[status] || { color: 'default', icon: null }
        return (
          <Tag color={config.color} icon={config.icon}>
            {status}
          </Tag>
        )
      },
      filters: Object.values(StrategyStatus).map(status => ({
        text: status,
        value: status,
      })),
      filteredValue: selectedStatus ? [selectedStatus] : null,
    },
    {
      title: '风险等级',
      dataIndex: 'riskLevel',
      key: 'riskLevel',
      width: 100,
      render: (risk: RiskLevel) => {
        const riskMap = {
          [RiskLevel.LOW]: { color: 'green', text: '低' },
          [RiskLevel.MEDIUM]: { color: 'orange', text: '中' },
          [RiskLevel.HIGH]: { color: 'red', text: '高' },
        }
        const config = riskMap[risk] || { color: 'default', text: risk }
        return <Tag color={config.color}>{config.text}</Tag>
      },
      filters: Object.values(RiskLevel).map(risk => ({
        text: risk,
        value: risk,
      })),
      filteredValue: selectedRisk ? [selectedRisk] : null,
    },
    {
      title: '收益率',
      key: 'return',
      width: 120,
      render: () => {
        const returns = [15.2, 8.7, -2.3, 12.8]
        const randomReturn = returns[Math.floor(Math.random() * returns.length)]
        const isPositive = randomReturn >= 0
        return (
          <span className={isPositive ? 'text-green-600' : 'text-red-600'}>
            {isPositive ? '+' : ''}{randomReturn.toFixed(2)}%
          </span>
        )
      },
    },
    {
      title: '夏普比率',
      key: 'sharpe',
      width: 100,
      render: () => {
        const ratios = [1.85, 1.23, 0.87, 1.56]
        return ratios[Math.floor(Math.random() * ratios.length)].toFixed(2)
      },
    },
    {
      title: '最后运行',
      dataIndex: 'lastRunAt',
      key: 'lastRunAt',
      width: 150,
      render: (date: string) => {
        if (!date) return '-'
        const parsedDate = new Date(date)
        return parsedDate.toLocaleString('zh-CN')
      },
    },
    {
      title: '激活',
      dataIndex: 'isActive',
      key: 'isActive',
      width: 80,
      render: (isActive: boolean, record: Strategy) => (
        <Switch
          checked={isActive}
          onChange={async (checked) => {
            try {
              await updateStrategy({
                strategyId: record.id,
                updates: { isActive: checked, status: checked ? StrategyStatus.ACTIVE : StrategyStatus.INACTIVE }
              })
              message.success(`策略已${checked ? '激活' : '停用'}`)
            } catch (error) {
              message.error('操作失败')
            }
          }}
          loading={false}
        />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: 'right',
      render: (_, record: Strategy) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedStrategy(record)
                setDetailModalVisible(true)
              }}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => {
                setSelectedStrategy(record)
                setCreateModalVisible(true)
              }}
            />
          </Tooltip>
          <Tooltip title="执行">
            <Button
              type="text"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={async () => {
                try {
                  await executeStrategy({ strategyId: record.id })
                  message.success('策略执行已启动')
                } catch (error) {
                  message.error('执行失败')
                }
              }}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个策略吗？"
            onConfirm={async () => {
              try {
                await deleteStrategy(record.id)
                message.success('策略已删除')
              } catch (error) {
                message.error('删除失败')
              }
            }}
          >
            <Tooltip title="删除">
              <Button
                type="text"
                size="small"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // Batch operation menu
  const batchMenu = (
    <Menu
      items={[
        {
          key: 'activate',
          label: '批量激活',
          icon: <CheckCircleOutlined />,
          onClick: async () => {
            try {
              await batchOperation({
                strategyIds: selectedRowKeys as string[],
                operation: 'activate'
              })
              message.success('批量激活成功')
              setSelectedRowKeys([])
            } catch (error) {
              message.error('批量激活失败')
            }
          }
        },
        {
          key: 'deactivate',
          label: '批量停用',
          icon: <PauseCircleOutlined />,
          onClick: async () => {
            try {
              await batchOperation({
                strategyIds: selectedRowKeys as string[],
                operation: 'deactivate'
              })
              message.success('批量停用成功')
              setSelectedRowKeys([])
            } catch (error) {
              message.error('批量停用失败')
            }
          }
        },
        {
          key: 'delete',
          label: '批量删除',
          icon: <DeleteOutlined />,
          danger: true,
          onClick: async () => {
            try {
              await batchOperation({
                strategyIds: selectedRowKeys as string[],
                operation: 'delete'
              })
              message.success('批量删除成功')
              setSelectedRowKeys([])
            } catch (error) {
              message.error('批量删除失败')
            }
          }
        },
      ]}
    />
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">策略管理</h1>
          <p className="text-gray-600">管理和监控您的量化交易策略</p>
        </div>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setSelectedStrategy(null)
              setCreateModalVisible(true)
            }}
          >
            创建策略
          </Button>
          {selectedRowKeys.length > 0 && (
            <Dropdown overlay={batchMenu} trigger={['click']}>
              <Button>
                批量操作 ({selectedRowKeys.length})
              </Button>
            </Dropdown>
          )}
        </Space>
      </div>

      {/* Statistics Cards */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="总策略数"
              value={strategies.length}
              prefix={<RocketOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="活跃策略"
              value={strategies.filter(s => s.isActive).length}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="测试中"
              value={strategies.filter(s => s.status === StrategyStatus.TESTING).length}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="异常策略"
              value={strategies.filter(s => s.status === StrategyStatus.ERROR).length}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Card size="small">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Search
              placeholder="搜索策略名称或描述"
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={6} md={4}>
            <Select
              placeholder="策略类型"
              allowClear
              value={selectedType}
              onChange={setSelectedType}
              style={{ width: '100%' }}
            >
              {Object.values(StrategyType).map(type => (
                <Option key={type} value={type}>{type}</Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={6} md={4}>
            <Select
              placeholder="状态"
              allowClear
              value={selectedStatus}
              onChange={setSelectedStatus}
              style={{ width: '100%' }}
            >
              {Object.values(StrategyStatus).map(status => (
                <Option key={status} value={status}>{status}</Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={6} md={4}>
            <Select
              placeholder="风险等级"
              allowClear
              value={selectedRisk}
              onChange={setSelectedRisk}
              style={{ width: '100%' }}
            >
              {Object.values(RiskLevel).map(risk => (
                <Option key={risk} value={risk}>{risk}</Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={6} md={4}>
            <Button icon={<FilterOutlined />}>高级过滤</Button>
          </Col>
          <Col xs={24} sm={6} md={2}>
            <Button icon={<DownloadOutlined />}>导出</Button>
          </Col>
        </Row>
      </Card>

      {/* Strategies Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={strategies}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: currentPage,
            pageSize,
            total: strategiesData?.totalCount || strategies.length,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            onChange: (page, size) => {
              setCurrentPage(page)
              setPageSize(size || 20)
            },
          }}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
            getCheckboxProps: (record) => ({
              disabled: record.status === StrategyStatus.ERROR,
            }),
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* Modals */}
      <StrategyDetailModal
        visible={detailModalVisible}
        strategy={selectedStrategy}
        onClose={() => {
          setDetailModalVisible(false)
          setSelectedStrategy(null)
        }}
      />

      <CreateStrategyModal
        visible={createModalVisible}
        strategy={selectedStrategy}
        onClose={() => {
          setCreateModalVisible(false)
          setSelectedStrategy(null)
        }}
        onSuccess={() => {
          refetch()
          setCreateModalVisible(false)
          setSelectedStrategy(null)
        }}
      />
    </div>
  )
}

export default StrategiesPage