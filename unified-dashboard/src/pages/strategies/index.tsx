import React, { useState } from 'react'
import { Layout, Card, Row, Col, Button, Space, Tabs, Badge } from 'antd'
import {
  PlusOutlined,
  SettingOutlined,
  BarChartOutlined,
  AppstoreOutlined,
} from '@ant-design/icons'
import { useStrategies } from '../../hooks/useStrategies'
import StrategyList from '../../components/strategy/StrategyList'
import StrategyForm from '../../components/strategy/StrategyForm'
import StrategyDetails from '../../components/strategy/StrategyDetails'
import { Strategy, StrategyStatus } from '../../types'

const { Content } = Layout
const { TabPane } = Tabs

const StrategiesPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('list')
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null)
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create')
  const [viewMode, setViewMode] = useState<'table' | 'card'>('table')

  const {
    strategies,
    statistics,
    isLoading,
    createStrategy,
    updateStrategy,
    deleteStrategy,
    updateStatus,
  } = useStrategies()

  // Handle strategy selection
  const handleStrategySelect = (strategy: Strategy) => {
    setSelectedStrategy(strategy)
    setActiveTab('details')
  }

  // Handle strategy edit
  const handleStrategyEdit = (strategy: Strategy) => {
    setSelectedStrategy(strategy)
    setFormMode('edit')
    setActiveTab('form')
  }

  // Handle strategy create
  const handleStrategyCreate = () => {
    setSelectedStrategy(null)
    setFormMode('create')
    setActiveTab('form')
  }

  // Handle form submission
  const handleFormSubmit = async (strategyData: Partial<Strategy>) => {
    try {
      if (formMode === 'create') {
        await createStrategy(strategyData)
      } else {
        await updateStrategy(selectedStrategy!.id, strategyData)
      }
      setActiveTab('list')
    } catch (error) {
      // Error is handled in the hook
    }
  }

  // Handle strategy status change
  const handleStatusChange = async (strategyId: string, newStatus: StrategyStatus) => {
    try {
      await updateStatus(strategyId, newStatus)
    } catch (error) {
      // Error is handled in the hook
    }
  }

  // Handle strategy delete
  const handleStrategyDelete = async (strategyId: string) => {
    try {
      await deleteStrategy(strategyId)
      if (selectedStrategy?.id === strategyId) {
        setSelectedStrategy(null)
        setActiveTab('list')
      }
    } catch (error) {
      // Error is handled in the hook
    }
  }

  // Render overview statistics
  const renderOverview = () => (
    <Row gutter={[16, 16]} className="mb-6">
      <Col xs={24} sm={12} md={6}>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">
              {statistics.total}
            </div>
            <div className="text-gray-600">总策略数</div>
          </div>
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">
              {statistics.active}
            </div>
            <div className="text-gray-600">运行中</div>
          </div>
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-orange-600">
              {statistics.testing}
            </div>
            <div className="text-gray-600">测试中</div>
          </div>
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600">
              {statistics.inactive}
            </div>
            <div className="text-gray-600">已暂停</div>
          </div>
        </Card>
      </Col>
    </Row>
  )

  return (
    <Content className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">策略管理</h1>
        <p className="text-gray-600">管理和监控您的量化交易策略</p>
      </div>

      {renderOverview()}

      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          tabBarExtraContent={
            <Space>
              <Button
                icon={<AppstoreOutlined />}
                type={viewMode === 'card' ? 'primary' : 'default'}
                onClick={() => setViewMode('card')}
              >
                卡片视图
              </Button>
              <Button
                icon={<BarChartOutlined />}
                type={viewMode === 'table' ? 'primary' : 'default'}
                onClick={() => setViewMode('table')}
              >
                表格视图
              </Button>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleStrategyCreate}
              >
                新建策略
              </Button>
            </Space>
          }
        >
          <TabPane
            tab={
              <span>
                <BarChartOutlined />
                策略列表
                <Badge count={statistics.total} className="ml-2" />
              </span>
            }
            key="list"
          >
            <StrategyList
              strategies={strategies}
              onStrategySelect={handleStrategySelect}
              onStrategyEdit={handleStrategyEdit}
              onStrategyCreate={handleStrategyCreate}
              viewMode={viewMode}
              isLoading={isLoading}
            />
          </TabPane>

          <TabPane
            tab={
              <span>
                <SettingOutlined />
                {formMode === 'create' ? '新建策略' : '编辑策略'}
              </span>
            }
            key="form"
          >
            <StrategyForm
              strategy={selectedStrategy || undefined}
              onSubmit={handleFormSubmit}
              onCancel={() => setActiveTab('list')}
              mode={formMode}
              loading={false}
            />
          </TabPane>

          {selectedStrategy && (
            <TabPane
              tab={
                <span>
                  <BarChartOutlined />
                  策略详情
                </span>
              }
              key="details"
            >
              <StrategyDetails
                strategyId={selectedStrategy.id}
                onEdit={handleStrategyEdit}
                onStatusChange={handleStatusChange}
              />
            </TabPane>
          )}
        </Tabs>
      </Card>
    </Content>
  )
}

export default StrategiesPage