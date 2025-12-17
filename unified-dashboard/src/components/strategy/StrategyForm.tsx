import React, { useState, useEffect } from 'react'
import {
  Form,
  Input,
  Select,
  Button,
  Card,
  Row,
  Col,
  Space,
  message,
  Divider,
  Tooltip,
  InputNumber,
  Switch,
} from 'antd'
import {
  SaveOutlined,
  ClearOutlined,
  InfoCircleOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { Strategy, StrategyType, RiskLevel } from '../../types'
import IndicatorSelector from '../forms/IndicatorSelector'
import ParameterForm from '../forms/ParameterForm'
import RiskSettings from '../forms/RiskSettings'

const { TextArea } = Input
const { Option } = Select

// Form validation rules
const formRules = {
  name: [
    { required: true, message: '请输入策略名称' },
    { min: 2, max: 100, message: '策略名称长度应在2-100个字符之间' },
  ],
  description: [
    { max: 500, message: '描述不能超过500个字符' },
  ],
  type: [
    { required: true, message: '请选择策略类型' },
  ],
  riskLevel: [
    { required: true, message: '请选择风险等级' },
  ],
}

interface StrategyFormProps {
  strategy?: Strategy
  onSubmit: (strategyData: Partial<Strategy>) => Promise<void>
  onCancel: () => void
  loading?: boolean
  mode?: 'create' | 'edit'
}

const StrategyForm: React.FC<StrategyFormProps> = ({
  strategy,
  onSubmit,
  onCancel,
  loading = false,
  mode = 'create',
}) => {
  const [form] = Form.useForm()
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>(strategy?.parameters.indicators || [])
  const [riskSettings, setRiskSettings] = useState({
    maxPositionSize: strategy?.parameters.maxPositionSize || 100000,
    stopLossPercent: strategy?.parameters.stopLossPercent || 5,
    takeProfitPercent: strategy?.parameters.takeProfitPercent || 10,
    maxDrawdownPercent: strategy?.parameters.maxDrawdownPercent || 20,
    leverage: strategy?.parameters.leverage || 1,
  })

  // Initialize form with strategy data
  useEffect(() => {
    if (strategy) {
      form.setFieldsValue({
        name: strategy.name,
        description: strategy.description,
        type: strategy.type,
        riskLevel: strategy.riskLevel,
        ...strategy.parameters,
      })
      setSelectedIndicators(strategy.parameters.indicators || [])
      setRiskSettings({
        maxPositionSize: strategy.parameters.maxPositionSize || 100000,
        stopLossPercent: strategy.parameters.stopLossPercent || 5,
        takeProfitPercent: strategy.parameters.takeProfitPercent || 10,
        maxDrawdownPercent: strategy.parameters.maxDrawdownPercent || 20,
        leverage: strategy.parameters.leverage || 1,
      })
    }
  }, [strategy, form])

  // Handle form submission
  const handleSubmit = async (values: any) => {
    try {
      const strategyData: Partial<Strategy> = {
        name: values.name,
        description: values.description,
        type: values.type,
        riskLevel: values.riskLevel,
        parameters: {
          ...values,
          indicators: selectedIndicators,
          ...riskSettings,
        },
      }

      if (mode === 'edit' && strategy) {
        strategyData.id = strategy.id
      }

      await onSubmit(strategyData)
      message.success(mode === 'create' ? '策略创建成功' : '策略更新成功')
    } catch (error) {
      message.error('操作失败，请重试')
    }
  }

  // Reset form
  const handleReset = () => {
    form.resetFields()
    setSelectedIndicators([])
    setRiskSettings({
      maxPositionSize: 100000,
      stopLossPercent: 5,
      takeProfitPercent: 10,
      maxDrawdownPercent: 20,
      leverage: 1,
    })
  }

  // Dynamic parameter fields based on strategy type
  const renderDynamicParameters = () => {
    const strategyType = form.getFieldValue('type')

    switch (strategyType) {
      case StrategyType.MEAN_REVERSION:
        return (
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                label="RSI周期"
                name="rsiPeriod"
                rules={[{ required: true, message: '请输入RSI周期' }]}
              >
                <InputNumber min={2} max={100} placeholder="14" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="超卖水平"
                name="oversoldLevel"
                rules={[{ required: true, message: '请输入超卖水平' }]}
              >
                <InputNumber min={0} max={50} placeholder="30" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="超买水平"
                name="overboughtLevel"
                rules={[{ required: true, message: '请输入超买水平' }]}
              >
                <InputNumber min={50} max={100} placeholder="70" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="回望周期"
                name="lookbackPeriod"
              >
                <InputNumber min={1} max={365} placeholder="20" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        )

      case StrategyType.MOMENTUM:
        return (
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                label="快线周期"
                name="fastPeriod"
                rules={[{ required: true, message: '请输入快线周期' }]}
              >
                <InputNumber min={1} max={50} placeholder="12" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="慢线周期"
                name="slowPeriod"
                rules={[{ required: true, message: '请输入慢线周期' }]}
              >
                <InputNumber min={1} max={200} placeholder="26" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="信号线周期"
                name="signalPeriod"
                rules={[{ required: true, message: '请输入信号线周期' }]}
              >
                <InputNumber min={1} max={50} placeholder="9" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="动量阈值"
                name="momentumThreshold"
              >
                <InputNumber min={0} max={1} step={0.01} placeholder="0.02" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        )

      case StrategyType.TECHNICAL:
        return (
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                label="布林带周期"
                name="bollingerPeriod"
                rules={[{ required: true, message: '请输入布林带周期' }]}
              >
                <InputNumber min={5} max={100} placeholder="20" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="标准差倍数"
                name="bollingerStdDev"
                rules={[{ required: true, message: '请输入标准差倍数' }]}
              >
                <InputNumber min={1} max={5} step={0.1} placeholder="2" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="突破确认"
                name="breakoutConfirmation"
                valuePropName="checked"
              >
                <Switch checkedChildren="开启" unCheckedChildren="关闭" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="成交量确认"
                name="volumeConfirmation"
                valuePropName="checked"
              >
                <Switch checkedChildren="开启" unCheckedChildren="关闭" />
              </Form.Item>
            </Col>
          </Row>
        )

      case StrategyType.SENTIMENT:
        return (
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                label="情感来源"
                name="sentimentSource"
                rules={[{ required: true, message: '请选择情感来源' }]}
              >
                <Select placeholder="选择情感数据来源">
                  <Option value="twitter">Twitter</Option>
                  <Option value="reddit">Reddit</Option>
                  <Option value="news">新闻舆情</Option>
                  <Option value="social_media">社交媒体</Option>
                  <Option value="mixed">混合来源</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="情感阈值"
                name="sentimentThreshold"
                rules={[{ required: true, message: '请输入情感阈值' }]}
              >
                <InputNumber min={-1} max={1} step={0.1} placeholder="0.6" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="分析周期"
                name="sentimentPeriod"
              >
                <InputNumber min={1} max={168} placeholder="24" style={{ width: '100%' }} addonAfter="小时" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="权重调整"
                name="sentimentWeight"
              >
                <InputNumber min={0} max={1} step={0.1} placeholder="0.7" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        )

      case StrategyType.ARBITRAGE:
        return (
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                label="回望周期"
                name="lookbackPeriod"
                rules={[{ required: true, message: '请输入回望周期' }]}
              >
                <InputNumber min={5} max={365} placeholder="30" style={{ width: '100%' }} addonAfter="天" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="Z-Score阈值"
                name="zScoreThreshold"
                rules={[{ required: true, message: '请输入Z-Score阈值' }]}
              >
                <InputNumber min={0.5} max={5} step={0.1} placeholder="2" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="配对数量"
                name="pairCount"
              >
                <InputNumber min={1} max={20} placeholder="5" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="最小相关性"
                name="minCorrelation"
              >
                <InputNumber min={0.5} max={1} step={0.01} placeholder="0.8" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        )

      default:
        return null
    }
  }

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      initialValues={{
        riskLevel: RiskLevel.MEDIUM,
        leverage: 1,
      }}
    >
      {/* Basic Information */}
      <Card
        title={
          <Space>
            <InfoCircleOutlined />
            基本信息
          </Space>
        }
        className="mb-4"
      >
        <Row gutter={16}>
          <Col xs={24} md={12}>
            <Form.Item
              label="策略名称"
              name="name"
              rules={formRules.name}
            >
              <Input placeholder="请输入策略名称" />
            </Form.Item>
          </Col>
          <Col xs={24} md={12}>
            <Form.Item
              label="策略类型"
              name="type"
              rules={formRules.type}
            >
              <Select placeholder="请选择策略类型">
                <Option value={StrategyType.SENTIMENT}>情感分析策略</Option>
                <Option value={StrategyType.TECHNICAL}>技术分析策略</Option>
                <Option value={StrategyType.MOMENTUM}>动量策略</Option>
                <Option value={StrategyType.MEAN_REVERSION}>均值回归策略</Option>
                <Option value={StrategyType.ARBITRAGE}>套利策略</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col xs={24}>
            <Form.Item
              label="策略描述"
              name="description"
              rules={formRules.description}
            >
              <TextArea
                rows={4}
                placeholder="请输入策略描述..."
                showCount
                maxLength={500}
              />
            </Form.Item>
          </Col>
          <Col xs={24} md={12}>
            <Form.Item
              label={
                <Space>
                  风险等级
                  <Tooltip title="选择策略的风险等级，会影响资金分配和风控参数">
                    <InfoCircleOutlined style={{ color: '#999' }} />
                  </Tooltip>
                </Space>
              }
              name="riskLevel"
              rules={formRules.riskLevel}
            >
              <Select placeholder="请选择风险等级">
                <Option value={RiskLevel.LOW}>低风险</Option>
                <Option value={RiskLevel.MEDIUM}>中风险</Option>
                <Option value={RiskLevel.HIGH}>高风险</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>
      </Card>

      {/* Technical Indicators */}
      <Card
        title={
          <Space>
            <SettingOutlined />
            技术指标
          </Space>
        }
        className="mb-4"
      >
        <IndicatorSelector
          selectedIndicators={selectedIndicators}
          onChange={setSelectedIndicators}
        />
      </Card>

      {/* Dynamic Parameters based on Strategy Type */}
      <Card
        title="策略参数"
        className="mb-4"
      >
        {renderDynamicParameters()}
      </Card>

      {/* Risk Management Settings */}
      <Card
        title="风险管理"
        className="mb-4"
      >
        <RiskSettings
          settings={riskSettings}
          onChange={setRiskSettings}
        />
      </Card>

      {/* Form Actions */}
      <Card>
        <Row justify="end">
          <Space>
            <Button
              icon={<ClearOutlined />}
              onClick={handleReset}
            >
              重置
            </Button>
            <Button onClick={onCancel}>
              取消
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SaveOutlined />}
              loading={loading}
            >
              {mode === 'create' ? '创建策略' : '更新策略'}
            </Button>
          </Space>
        </Row>
      </Card>
    </Form>
  )
}

export default StrategyForm