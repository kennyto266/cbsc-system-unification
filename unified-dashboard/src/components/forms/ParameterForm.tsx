import React, { useState, useEffect } from 'react'
import {
  Card,
  Form,
  Input,
  InputNumber,
  Select,
  Switch,
  Slider,
  Row,
  Col,
  Space,
  Tooltip,
  Button,
  Divider,
} from 'antd'
import {
  InfoCircleOutlined,
  PlusOutlined,
  DeleteOutlined,
  SettingOutlined,
} from '@ant-design/icons'

const { Option } = Select
const { TextArea } = Input

// Parameter type definitions
type ParameterType = 'number' | 'string' | 'boolean' | 'array' | 'object' | 'select'

interface ParameterDefinition {
  name: string
  type: ParameterType
  label: string
  description?: string
  required?: boolean
  defaultValue?: any
  min?: number
  max?: number
  step?: number
  options?: { label: string; value: any }[]
  unit?: string
  validation?: {
    pattern?: string
    message?: string
  }
}

interface ParameterFormProps {
  parameters: Record<string, any>
  onChange: (parameters: Record<string, any>) => void
  parameterDefinitions?: ParameterDefinition[]
  disabled?: boolean
  showAdvanced?: boolean
}

const ParameterForm: React.FC<ParameterFormProps> = ({
  parameters,
  onChange,
  parameterDefinitions = [],
  disabled = false,
  showAdvanced = false,
}) => {
  const [form] = Form.useForm()
  const [dynamicParams, setDynamicParams] = useState<Record<string, any>>({})

  // Update form when parameters change
  useEffect(() => {
    form.setFieldsValue(parameters)
  }, [parameters, form])

  // Handle form value change
  const handleValuesChange = (changedValues: any, allValues: any) => {
    onChange(allValues)
  }

  // Render parameter field based on type
  const renderParameterField = (paramDef: ParameterDefinition) => {
    const commonProps = {
      name: paramDef.name,
      label: (
        <Space>
          {paramDef.label}
          {paramDef.required && <span className="text-red-500">*</span>}
          {paramDef.description && (
            <Tooltip title={paramDef.description}>
              <InfoCircleOutlined style={{ color: '#999' }} />
            </Tooltip>
          )}
        </Space>
      ),
      rules: paramDef.required ? [{ required: true, message: `请输入${paramDef.label}` }] : [],
    }

    switch (paramDef.type) {
      case 'number':
        return (
          <Form.Item {...commonProps}>
            <InputNumber
              style={{ width: '100%' }}
              min={paramDef.min}
              max={paramDef.max}
              step={paramDef.step || 1}
              placeholder={paramDef.defaultValue}
              addonAfter={paramDef.unit}
              disabled={disabled}
            />
          </Form.Item>
        )

      case 'string':
        return (
          <Form.Item {...commonProps}>
            <Input
              placeholder={paramDef.defaultValue}
              disabled={disabled}
            />
          </Form.Item>
        )

      case 'boolean':
        return (
          <Form.Item {...commonProps} valuePropName="checked">
            <Switch
              checkedChildren="开启"
              unCheckedChildren="关闭"
              disabled={disabled}
            />
          </Form.Item>
        )

      case 'select':
        return (
          <Form.Item {...commonProps}>
            <Select
              placeholder={`请选择${paramDef.label}`}
              disabled={disabled}
            >
              {paramDef.options?.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
        )

      case 'array':
        return (
          <Form.Item {...commonProps}>
            <Select
              mode="tags"
              placeholder={`请输入${paramDef.label}，用逗号分隔`}
              tokenSeparators={[',']}
              disabled={disabled}
            />
          </Form.Item>
        )

      case 'object':
        return (
          <Form.Item {...commonProps}>
            <TextArea
              rows={4}
              placeholder={`请输入${paramDef.label}（JSON格式）`}
              disabled={disabled}
            />
          </Form.Item>
        )

      default:
        return null
    }
  }

  // Add custom parameter
  const addCustomParameter = () => {
    const key = `custom_${Date.now()}`
    const newParams = {
      ...dynamicParams,
      [key]: { name: '', type: 'string', value: '', description: '' }
    }
    setDynamicParams(newParams)
  }

  // Remove custom parameter
  const removeCustomParameter = (key: string) => {
    const newParams = { ...dynamicParams }
    delete newParams[key]
    setDynamicParams(newParams)
  }

  // Update custom parameter
  const updateCustomParameter = (key: string, field: string, value: any) => {
    const newParams = {
      ...dynamicParams,
      [key]: {
        ...dynamicParams[key],
        [field]: value
      }
    }
    setDynamicParams(newParams)
  }

  return (
    <div className="space-y-4">
      {/* Predefined Parameters */}
      <Card title="参数配置" size="small">
        <Form
          form={form}
          layout="vertical"
          initialValues={parameters}
          onValuesChange={handleValuesChange}
        >
          <Row gutter={[16, 16]}>
            {parameterDefinitions.map(paramDef => (
              <Col key={paramDef.name} xs={24} sm={12} md={8}>
                {renderParameterField(paramDef)}
              </Col>
            ))}
          </Row>
        </Form>
      </Card>

      {/* Advanced Parameters */}
      {showAdvanced && (
        <Card title="高级参数" size="small">
          <Form
            layout="vertical"
            initialValues={parameters}
            onValuesChange={handleValuesChange}
          >
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12}>
                <Form.Item
                  label={
                    <Space>
                      信号确认
                      <Tooltip title="启用后，需要多个指标同时确认才产生信号">
                        <InfoCircleOutlined style={{ color: '#999' }} />
                      </Tooltip>
                    </Space>
                  }
                  name="signalConfirmation"
                  valuePropName="checked"
                >
                  <Switch
                    checkedChildren="开启"
                    unCheckedChildren="关闭"
                    disabled={disabled}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item
                  label="信号强度阈值"
                  name="signalStrengthThreshold"
                >
                  <Slider
                    min={0}
                    max={100}
                    marks={{
                      0: '0%',
                      50: '50%',
                      100: '100%'
                    }}
                    disabled={disabled}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item
                  label={
                    <Space>
                      动态调整
                      <Tooltip title="根据市场条件自动调整参数">
                        <InfoCircleOutlined style={{ color: '#999' }} />
                      </Tooltip>
                    </Space>
                  }
                  name="dynamicAdjustment"
                  valuePropName="checked"
                >
                  <Switch
                    checkedChildren="开启"
                    unCheckedChildren="关闭"
                    disabled={disabled}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item
                  label="更新频率"
                  name="updateFrequency"
                >
                  <Select disabled={disabled}>
                    <Option value="realtime">实时</Option>
                    <Option value="1min">每分钟</Option>
                    <Option value="5min">每5分钟</Option>
                    <Option value="15min">每15分钟</Option>
                    <Option value="1hour">每小时</Option>
                    <Option value="1day">每天</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </Form>
        </Card>
      )}

      {/* Custom Parameters */}
      {showAdvanced && (
        <Card
          title="自定义参数"
          size="small"
          extra={
            <Button
              type="dashed"
              icon={<PlusOutlined />}
              onClick={addCustomParameter}
              disabled={disabled}
            >
              添加参数
            </Button>
          }
        >
          {Object.entries(dynamicParams).map(([key, param]: [string, any]) => (
            <Card key={key} size="small" className="mb-3">
              <Row gutter={[8, 8]} align="middle">
                <Col span={6}>
                  <Input
                    placeholder="参数名"
                    value={param.name}
                    onChange={(e) => updateCustomParameter(key, 'name', e.target.value)}
                    disabled={disabled}
                  />
                </Col>
                <Col span={5}>
                  <Select
                    placeholder="类型"
                    value={param.type}
                    onChange={(value) => updateCustomParameter(key, 'type', value)}
                    disabled={disabled}
                  >
                    <Option value="string">字符串</Option>
                    <Option value="number">数字</Option>
                    <Option value="boolean">布尔值</Option>
                    <Option value="array">数组</Option>
                  </Select>
                </Col>
                <Col span={8}>
                  <Input
                    placeholder="参数值"
                    value={param.value}
                    onChange={(e) => updateCustomParameter(key, 'value', e.target.value)}
                    disabled={disabled}
                  />
                </Col>
                <Col span={3}>
                  <Button
                    type="text"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => removeCustomParameter(key)}
                    disabled={disabled}
                  />
                </Col>
              </Row>
              {param.description && (
                <div className="text-xs text-gray-500 mt-1">
                  {param.description}
                </div>
              )}
            </Card>
          ))}
        </Card>
      )}

      {/* Parameter Presets */}
      {showAdvanced && (
        <Card title="参数预设" size="small">
          <Row gutter={[8, 8]}>
            <Col span={6}>
              <Button
                block
                size="small"
                onClick={() => {
                  onChange({
                    ...parameters,
                    signalConfirmation: true,
                    signalStrengthThreshold: 70,
                    dynamicAdjustment: false,
                    updateFrequency: '5min',
                  })
                }}
                disabled={disabled}
              >
                保守型
              </Button>
            </Col>
            <Col span={6}>
              <Button
                block
                size="small"
                onClick={() => {
                  onChange({
                    ...parameters,
                    signalConfirmation: false,
                    signalStrengthThreshold: 50,
                    dynamicAdjustment: true,
                    updateFrequency: '1min',
                  })
                }}
                disabled={disabled}
              >
                平衡型
              </Button>
            </Col>
            <Col span={6}>
              <Button
                block
                size="small"
                onClick={() => {
                  onChange({
                    ...parameters,
                    signalConfirmation: false,
                    signalStrengthThreshold: 30,
                    dynamicAdjustment: true,
                    updateFrequency: 'realtime',
                  })
                }}
                disabled={disabled}
              >
                激进型
              </Button>
            </Col>
            <Col span={6}>
              <Button
                block
                size="small"
                onClick={() => {
                  onChange({
                    signalConfirmation: true,
                    signalStrengthThreshold: 60,
                    dynamicAdjustment: false,
                    updateFrequency: '15min',
                  })
                }}
                disabled={disabled}
              >
                默认设置
              </Button>
            </Col>
          </Row>
        </Card>
      )}
    </div>
  )
}

export default ParameterForm