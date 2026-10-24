import React from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Layout, Button, Card, Breadcrumb, Spin } from 'antd'
import { Link } from 'react-router-dom'
import { ArrowLeftOutlined } from '@ant-design/icons'
import StrategyForm from '../../../../components/strategy/StrategyForm'
import { useStrategy, useStrategies } from '../../../../hooks/useStrategies'
import { Strategy } from '../../../../types'

const { Content } = Layout

const EditStrategyPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { strategy, isLoading } = useStrategy(id!)
  const { updateStrategy } = useStrategies()

  // Handle form submission
  const handleSubmit = async (strategyData: Partial<Strategy>) => {
    try {
      await updateStrategy(id!, strategyData)
      navigate(`/strategies/${id}`)
    } catch (error) {
      // Error is handled in the hook
    }
  }

  // Handle cancel
  const handleCancel = () => {
    navigate(`/strategies/${id}`)
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
          <Breadcrumb.Item>
            <Link to={`/strategies/${id}`}>{strategy.name}</Link>
          </Breadcrumb.Item>
          <Breadcrumb.Item>编辑策略</Breadcrumb.Item>
        </Breadcrumb>
      </div>

      <Card
        title={`编辑策略: ${strategy.name}`}
        extra={
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={handleCancel}
          >
            返回详情
          </Button>
        }
      >
        <StrategyForm
          strategy={strategy}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          mode="edit"
          loading={false}
        />
      </Card>
    </Content>
  )
}

export default EditStrategyPage