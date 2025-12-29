import React from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Layout, Button, Card, Breadcrumb, Spin } from 'antd'
import { Link } from 'react-router-dom'
import { ArrowLeftOutlined, EditOutlined } from '@ant-design/icons'
import StrategyDetails from '../../../components/strategy/StrategyDetails'
import { useStrategy } from '../../../hooks/useStrategies'
import { Strategy, StrategyStatus } from '../../../types'

const { Content } = Layout

const StrategyDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { strategy, isLoading } = useStrategy(id!)

  // Handle edit
  const handleEdit = (strategy: Strategy) => {
    navigate(`/strategies/${strategy.id}/edit`)
  }

  // Handle status change
  const handleStatusChange = async (strategyId: string, newStatus: StrategyStatus) => {
    // This would be handled by the StrategyDetails component
    console.log('Status change:', strategyId, newStatus)
  }

  if (isLoading) {
    return (
      <Content className="p-6">
        <div className="flex items-center justify-center h-64">
          <Spin size="large" />
        </div>
      </Content>
    )
  }

  if (!strategy) {
    return (
      <Content className="p-6">
        <Card>
          <div className="text-center py-8">
            <div className="text-gray-500 text-lg">策略不存在或已被删除</div>
            <Button type="link" onClick={() => navigate('/strategies')}>
              返回策略列表
            </Button>
          </div>
        </Card>
      </Content>
    )
  }

  return (
    <Content className="p-6">
      <div className="mb-6">
        <Breadcrumb>
          <Breadcrumb.Item>
            <Link to="/strategies">策略管理</Link>
          </Breadcrumb.Item>
          <Breadcrumb.Item>{strategy.name}</Breadcrumb.Item>
        </Breadcrumb>
      </div>

      <Card
        title={strategy.name}
        extra={
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => handleEdit(strategy)}
          >
            编辑策略
          </Button>
        }
      >
        <StrategyDetails
          strategyId={strategy.id}
          onEdit={handleEdit}
          onStatusChange={handleStatusChange}
        />
      </Card>
    </Content>
  )
}

export default StrategyDetailPage