import React, { useState, useEffect } from 'react'
import {
  Form,
  Input,
  InputNumber,
  Switch,
  Select,
  Slider,
  ColorPicker,
  Button,
  Space,
  Card,
  Divider,
  Alert,
  Typography,
  Row,
  Col,
  Tooltip,
  Collapse,
  Tag,
  message
} from 'antd'
import {
  InfoCircleOutlined,
  SettingOutlined,
  EyeOutlined,
  ReloadOutlined,
  SaveOutlined,
  CloseOutlined
} from '@ant-design/icons'
import type { Color } from 'antd/es/color-picker'

import { TechnicalIndicator, IndicatorParameter } from '../../types/technical-indicators'

const { Title, Text, Paragraph } = Typography
const { Panel } = Collapse

interface IndicatorParameterFormProps {
  indicator?: TechnicalIndicator
  visible?: boolean
  onSubmit?: (values: any) => void
  onCancel?: () => void
  initialValues?: Record<string, any>
  mode?: 'create' | 'edit'
}

const IndicatorParameterForm: React.FC<IndicatorParameterFormProps> = ({
  indicator,
  visible = true,
  onSubmit,
  onCancel,
  initialValues,
  mode = 'create'
}) => {
  const [form] = Form.useForm()
  const [previewValues, setPreviewValues] = useState<Record<string, any>>({})
  const [activeSection, setActiveSection] = useState('parameters')

  useEffect(() => {
    if (indicator && !initialValues) {
      const defaultValues = indicator.parameters.reduce((acc, param) => {
        acc[param.name] = param.defaultValue
        return acc
      }, {} as Record<string, any>)

      // Add visual settings defaults
      defaultValues.visualSettings = {
        color: indicator.visualSettings.color,
        lineWidth: indicator.visualSettings.lineWidth,
        style: indicator.visualSettings.style,
        opacity: indicator.visualSettings.opacity
      }

      form.setFieldsValue(defaultValues)
      setPreviewValues(defaultValues)
    } else if (initialValues) {
      form.setFieldsValue(initialValues)
      setPreviewValues(initialValues)
    }
  }, [indicator, initialValues, form])

  const handleValuesChange = (changedValues: any, allValues: any) => {
    setPreviewValues(allValues)
  }

  const handleReset = () => {
    if (indicator) {
      const defaultValues = indicator.parameters.reduce((acc, param) => {
        acc[param.name] = param.defaultValue
        return acc
      }, {} as Record<string, any>)

      defaultValues.visualSettings = {
        color: indicator.visualSettings.color,
        lineWidth: indicator.visualSettings.lineWidth,
        style: indicator.visualSettings.style,
        opacity: indicator.visualSettings.opacity
      }

      form.setFieldsValue(defaultValues)
      setPreviewValues(defaultValues)
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      // Validate parameter constraints
      if (indicator) {
        for (const param of indicator.parameters) {
          const value = values[param.name]
          if (param.type === 'number') {
            if (param.min !== undefined && value < param.min) {
              message.error(`${param.name} 不能小于 ${param.min}`)
              return
            }
            if (param.max !== undefined && value > param.max) {
              message.error(`${param.name} 不能大于 ${param.max}`)
              return
            }
          }
        }
      }

      onSubmit?.(values)
      form.resetFields()
    } catch (error) {
      message.error('请检查表单填写是否正确')
    }
  }

  const renderParameterInput = (param: IndicatorParameter) => {
    const formItemProps = {
      name: param.name,
      label: (
        <Space>
          <Text strong>{param.name}</Text>
          {param.validation?.required && <Tag color="red" size="small">必填</Tag>}
          {param.description && (
            <Tooltip title={param.description}>
              <InfoCircleOutlined className="text-gray-400" />
            </Tooltip>
          )}
        </Space>
      ),
      tooltip: param.description,
      required: param.validation?.required,
      rules: [
        {
          required: param.validation?.required,
          message: `请输入 ${param.name}`
        },
        {
          pattern: param.validation?.pattern ? new RegExp(param.validation.pattern) : undefined,
          message: `${param.name} 格式不正确`
        }
      ]
    }

    switch (param.type) {
      case 'number':
        return (
          <Form.Item {...formItemProps}>
            {param.options ? (
              <Select>
                {param.options.map(option => (
                  <Select.Option key={option} value={option}>
                    {option}
                  </Select.Option>
                ))}
              </Select>
            ) : (
              <InputNumber
                min={param.min}
                max={param.max}
                step={param.step || 1}
                style={{ width: '100%' }}
                placeholder={`请输入 ${param.name}`}
              />
            )}
          </Form.Item>
        )

      case 'boolean':
        return (
          <Form.Item {...formItemProps} valuePropName="checked">
            <Switch />
          </Form.Item>
        )

      case 'string':
        return (
          <Form.Item {...formItemProps}>
            {param.options ? (
              <Select placeholder={`请选择 ${param.name}`}>
                {param.options.map(option => (
                  <Select.Option key={option} value={option}>
                    {option}
                  </Select.Option>
                ))}
              </Select>
            ) : (
              <Input
                placeholder={`请输入 ${param.name}`}
                pattern={param.validation?.pattern}
              />
            )}
          </Form.Item>
        )

      case 'array':
        return (
          <Form.Item {...formItemProps}>
            <Select
              mode="multiple"
              placeholder={`请选择 ${param.name}`}
              options={param.options?.map(option => ({
                label: option,
                value: option
              }))}
            />
          </Form.Item>
        )

      default:
        return (
          <Form.Item {...formItemProps}>
            <Input placeholder={`请输入 ${param.name}`} />
          </Form.Item>
        )
    }
  }

  const renderParametersSection = () => (
    <Card title="指标参数" size="small">
      {indicator?.parameters.map((param) => renderParameterInput(param))}

      <Divider />

      <Space>
        <Button icon={<ReloadOutlined />} onClick={handleReset}>
          重置为默认值
        </Button>
        <Button icon={<EyeOutlined />} type="primary" ghost>
          预览效果
        </Button>
      </Space>
    </Card>
  )

  const renderVisualSettingsSection = () => (
    <Card title="视觉设置" size="small">
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name={['visualSettings', 'color']}
            label="颜色"
            tooltip="指标线的颜色"
          >
            <ColorPicker
              showText
              format="hex"
              onChange={(color: Color) => {
                form.setFieldValue(['visualSettings', 'color'], color.toHexString())
              }}
            />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name={['visualSettings', 'lineWidth']}
            label="线条宽度"
            tooltip="线条的宽度，单位为像素"
          >
            <Slider
              min={1}
              max={10}
              marks={{
                1: '1px',
                5: '5px',
                10: '10px'
              }}
            />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name={['visualSettings', 'style']}
            label="线条样式"
            tooltip="指标的显示样式"
          >
            <Select>
              <Select.Option value="line">线条</Select.Option>
              <Select.Option value="histogram">柱状图</Select.Option>
              <Select.Option value="dots">点状</Select.Option>
              <Select.Option value="area">面积图</Select.Option>
            </Select>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name={['visualSettings', 'opacity']}
            label="透明度"
            tooltip="指标的透明度"
          >
            <Slider
              min={0.1}
              max={1}
              step={0.1}
              marks={{
                0.1: '10%',
                0.5: '50%',
                1: '100%'
              }}
            />
          </Form.Item>
        </Col>
      </Row>
    </Card>
  )

  const renderAdvancedSection = () => (
    <Card title="高级设置" size="small">
      <Form.Item
        name="displayName"
        label="显示名称"
        tooltip="在图表中显示的自定义名称"
      >
        <Input placeholder={indicator?.name} />
      </Form.Item>

      <Form.Item
        name="timeframe"
        label="时间框架"
        tooltip="应用该指标的时间框架"
      >
        <Select placeholder="选择时间框架">
          <Select.Option value="1m">1分钟</Select.Option>
          <Select.Option value="5m">5分钟</Select.Option>
          <Select.Option value="15m">15分钟</Select.Option>
          <Select.Option value="1h">1小时</Select.Option>
          <Select.Option value="4h">4小时</Select.Option>
          <Select.Option value="1d">日线</Select.Option>
          <Select.Option value="1w">周线</Select.Option>
          <Select.Option value="1M">月线</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item
        name="symbols"
        label="适用品种"
        tooltip="该指标适用的交易品种"
      >
        <Select mode="multiple" placeholder="选择交易品种">
          <Select.Option value="BTC">BTC/USDT</Select.Option>
          <Select.Option value="ETH">ETH/USDT</Select.Option>
          <Select.Option value="BNB">BNB/USDT</Select.Option>
          <Select.Option value="AAPL">AAPL</Select.Option>
          <Select.Option value="TSLA">TSLA</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item
        name="alertThreshold"
        label="警报阈值"
        tooltip="当指标值达到此阈值时触发警报"
      >
        <InputNumber
          style={{ width: '100%' }}
          placeholder="设置警报阈值"
        />
      </Form.Item>
    </Card>
  )

  const renderPreviewSection = () => (
    <Card title="配置预览" size="small">
      <Alert
        message="当前配置"
        description={
          <pre className="text-xs bg-gray-50 p-2 rounded">
            {JSON.stringify(previewValues, null, 2)}
          </pre>
        }
        type="info"
      />
    </Card>
  )

  const content = (
    <Form
      form={form}
      layout="vertical"
      onValuesChange={handleValuesChange}
      className="indicator-parameter-form"
    >
      {mode === 'create' && (
        <Alert
          message="创建自定义指标"
          description="配置参数以创建您的自定义技术指标"
          type="info"
          showIcon
          className="mb-4"
        />
      )}

      <Collapse
        activeKey={activeSection}
        onChange={setActiveSection}
        items={[
          {
            key: 'parameters',
            label: '参数配置',
            children: renderParametersSection()
          },
          {
            key: 'visual',
            label: '视觉设置',
            children: renderVisualSettingsSection()
          },
          {
            key: 'advanced',
            label: '高级设置',
            children: renderAdvancedSection()
          },
          {
            key: 'preview',
            label: '配置预览',
            children: renderPreviewSection()
          }
        ]}
      />

      <Divider />

      <Space className="w-full justify-end">
        <Button icon={<CloseOutlined />} onClick={onCancel}>
          取消
        </Button>
        <Button icon={<SaveOutlined />} type="primary" onClick={handleSubmit}>
          {mode === 'create' ? '创建指标' : '保存配置'}
        </Button>
      </Space>
    </Form>
  )

  if (!visible) {
    return null
  }

  return (
    <div className="indicator-parameter-form-container">
      {content}
    </div>
  )
}

export default IndicatorParameterForm