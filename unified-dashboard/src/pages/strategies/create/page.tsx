import React from 'react'
import { Layout, Button, Card, Breadcrumb } from 'antd'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeftOutlined } from '@ant-design/icons'
import StrategyForm from '../../../components/strategy/StrategyForm'
import { useStrategies } from '../../../hooks/useStrategies'
import { Strategy } from '../../../types'

const { Content } = Layout

const CreateStrategyPage: React.FC = () => {
  const navigate = useNavigate()
  const { createStrategy } = useStrategies()

  // Handle form submission
  const handleSubmit = async (strategyData: Partial<Strategy>) => {
    try {
      const newStrategy = await createStrategy(strategyData)
      navigate(`/strategies/${newStrategy.id}`)
    } catch (error) {
      // Error is handled in the hook
    }
  }

  // Handle cancel
  const handleCancel = () => {
    navigate('/strategies')
  }

  return (
    <Content className="p-6">
      <div className="mb-6">
        <Breadcrumb>
          <Breadcrumb.Item>
            <Link to="/strategies">策略管理</Link>
          </Breadcrumb.Item>
          <Breadcrumb.Item>新建策略</Breadcrumb.Item>
        </Breadcrumb>
      </div>

      <Card
        title="创建新策略"
        extra={
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={handleCancel}
          >
            返回列表
          </Button>
        }
      >
        <StrategyForm
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          mode="create"
          loading={false}
        />
      </Card>
    </Content>
  )
}

export default CreateStrategyPage