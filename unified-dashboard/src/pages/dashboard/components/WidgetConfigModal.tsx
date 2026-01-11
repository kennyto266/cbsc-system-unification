import React, { useState, useEffect } from 'react'
import {
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Button,
  Space,
  Tabs,
  Card,
  Divider,
  ColorPicker,
  Slider,
  Row,
  Col,
  Typography,
  Alert
} from 'antd'
import { SettingOutlined, SaveOutlined, ReloadOutlined } from '@ant-design/icons'
import { GridWidget } from '../../components/dashboard/ResponsiveGrid/ResponsiveGridProvider'

const { Option } = Select
const { TextArea } = Input
const { Title, Text } = Typography
const { TabPane } = Tabs

interface WidgetConfigModalProps {
  widget: GridWidget | null
  visible: boolean
  onClose: () => void
  onSave?: (widget: GridWidget) => void
}

// Widget type configurations
const WIDGET_TYPE_CONFIGS = {
  'market-overview': {
    name: '市场概览',
    configFields: [
      { name: 'symbols', label: '交易对', type: 'tags', default: ['BTC/USDT', 'ETH/USDT'] },
      { name: 'refreshInterval', label: '刷新间隔(秒)', type: 'number', default: 30, min: 5, max: 300 },
      { name: 'showVolume', label: '显示成交量', type: 'switch', default: true },
      { name: 'showChange', label: '显示涨跌幅', type: 'switch', default: true }
    ]
  },
  'technical-indicator': {
    name: '技术指标',
    configFields: [
      { name: 'indicator', label: '指标类型', type: 'select', options: [
        { value: 'RSI', label: 'RSI相对强弱指标' },
        { value: 'MACD', label: 'MACD指标' },
        { value: 'BOLL', label: '布林带' },
        { value: 'KDJ', label: 'KDJ随机指标' },
        { value: 'MA', label: '移动平均线' },
        { value: 'VOLUME', label: '成交量' }
      ]},
      { name: 'symbol', label: '交易对', type: 'select', options: [
        { value: 'BTC/USDT', label: 'BTC/USDT' },
        { value: 'ETH/USDT', label: 'ETH/USDT' },
        { value: 'BNB/USDT', label: 'BNB/USDT' }
      ]},
      { name: 'timeFrame', label: '时间框架', type: 'select', options: [
        { value: '1m', label: '1分钟' },
        { value: '5m', label: '5分钟' },
        { value: '15m', label: '15分钟' },
        { value: '30m', label: '30分钟' },
        { value: '1h', label: '1小时' },
        { value: '4h', label: '4小时' },
        { value: '1d', label: '1天' }
      ]},
      { name: 'autoUpdate', label: '自动更新', type: 'switch', default: true }
    ]
  },
  'strategy-performance': {
    name: '策略表现',
    configFields: [
      { name: 'timeRange', label: '时间范围', type: 'select', options: [
        { value: '1D', label: '1天' },
        { value: '1W', label: '1周' },
        { value: '1M', label: '1月' },
        { value: '3M', label: '3月' },
        { value: '6M', label: '6月' },
        { value: '1Y', label: '1年' }
      ]},
      { name: 'showBenchmark', label: '显示基准', type: 'switch', default: true },
      { name: 'chartType', label: '图表类型', type: 'select', options: [
        { value: 'line', label: '折线图' },
        { value: 'area', label: '面积图' },
        { value: 'candlestick', label: 'K线图' }
      ]},
      { name: 'showDetails', label: '显示详细数据', type: 'switch', default: true }
    ]
  },
  'custom-widget': {
    name: '自定义组件',
    configFields: [
      { name: 'contentType', label: '内容类型', type: 'select', options: [
        { value: 'html', label: 'HTML' },
        { value: 'markdown', label: 'Markdown' },
        { value: 'iframe', label: '嵌入页面' },
        { value: 'json', label: 'JSON数据' }
      ]},
      { name: 'content', label: '内容', type: 'textarea' },
      { name: 'autoRefresh', label: '自动刷新', type: 'switch', default: false },
      { name: 'refreshInterval', label: '刷新间隔(秒)', type: 'number', default: 60, min: 10, max: 3600 }
    ]
  }
}

const WidgetConfigModal: React.FC<WidgetConfigModalProps> = ({
  widget,
  visible,
  onClose,
  onSave
}) => {
  const [form] = Form.useForm()
  const [config, setConfig] = useState<Record<string, any>>({})
  const [activeTab, setActiveTab] = useState('basic')

  // Initialize form when widget changes
  useEffect(() => {
    if (widget) {
      form.setFieldsValue({
        name: widget.name,
        type: widget.type,
        ...widget.config
      })
      setConfig(widget.config || {})
    }
  }, [widget, form])

  // Handle form submit
  const handleSave = () => {
    form.validateFields().then(values => {
      if (!widget) return

      const updatedWidget: GridWidget = {
        ...widget,
        name: values.name,
        config: { ...config, ...values }
      }

      if (onSave) {
        onSave(updatedWidget)
      }

      onClose()
    })
  }

  // Reset to default config
  const handleReset = () => {
    if (!widget) return

    const defaultConfig = WIDGET_TYPE_CONFIGS[widget.type as keyof typeof WIDGET_TYPE_CONFIGS]
    if (defaultConfig) {
      const defaultValues: any = {}
      defaultConfig.configFields.forEach(field => {
        defaultValues[field.name] = field.default
      })

      setConfig(defaultValues)
      form.setFieldsValue(defaultValues)
    }
  }

  // Render config field based on type
  const renderConfigField = (field: any) => {
    switch (field.type) {
      case 'select':
        return (
          <Select
            value={config[field.name] || field.default}
            onChange={(value) => setConfig({ ...config, [field.name]: value })}
            placeholder={`选择${field.label}`}
          >
            {field.options?.map((option: any) => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        )

      case 'number':
        return (
          <InputNumber
            value={config[field.name] || field.default}
            onChange={(value) => setConfig({ ...config, [field.name]: value })}
            min={field.min}
            max={field.max}
            style={{ width: '100%' }}
          />
        )

      case 'switch':
        return (
          <Switch
            checked={config[field.name] ?? field.default}
            onChange={(checked) => setConfig({ ...config, [field.name]: checked })}
          />
        )

      case 'textarea':
        return (
          <TextArea
            value={config[field.name] || ''}
            onChange={(e) => setConfig({ ...config, [field.name]: e.target.value })}
            rows={4}
            placeholder={`输入${field.label}...`}
          />
        )

      case 'tags':
        return (
          <Select
            mode="tags"
            value={config[field.name] || field.default}
            onChange={(value) => setConfig({ ...config, [field.name]: value })}
            placeholder={`输入${field.label}...`}
            style={{ width: '100%' }}
          />
        )

      case 'color':
        return (
          <ColorPicker
            value={config[field.name] || field.default}
            onChange={(color) => setConfig({ ...config, [field.name]: color.toHexString() })}
            showText
          />
        )

      case 'slider':
        return (
          <Slider
            value={config[field.name] || field.default}
            onChange={(value) => setConfig({ ...config, [field.name]: value })}
            min={field.min}
            max={field.max}
            marks={field.marks}
          />
        )

      default:
        return (
          <Input
            value={config[field.name] || ''}
            onChange={(e) => setConfig({ ...config, [field.name]: e.target.value })}
            placeholder={`输入${field.label}...`}
          />
        )
    }
  }

  if (!widget) return null

  const widgetConfig = WIDGET_TYPE_CONFIGS[widget.type as keyof typeof WIDGET_TYPE_CONFIGS]

  return (
    <Modal
      title={
        <div className="flex items-center space-x-2">
          <SettingOutlined />
          <span>组件配置 - {widget.name}</span>
        </div>
      }
      open={visible}
      onCancel={onClose}
      width={800}
      footer={[
        <Button key="reset" icon={<ReloadOutlined />} onClick={handleReset}>
          重置
        </Button>,
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button key="save" type="primary" icon={<SaveOutlined />} onClick={handleSave}>
          保存配置
        </Button>
      ]}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={widget}
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* Basic Configuration */}
          <TabPane tab="基本配置" key="basic">
            <Form.Item
              name="name"
              label="组件名称"
              rules={[{ required: true, message: '请输入组件名称' }]}
            >
              <Input placeholder="输入组件名称" />
            </Form.Item>

            <Form.Item
              name="type"
              label="组件类型"
            >
              <Select disabled>
                <Option value={widget.type}>{widgetConfig?.name || widget.type}</Option>
              </Select>
            </Form.Item>

            <Divider>组件配置</Divider>

            {widgetConfig?.configFields.map((field) => (
              <Form.Item
                key={field.name}
                label={field.label}
              >
                {renderConfigField(field)}
              </Form.Item>
            ))}
          </TabPane>

          {/* Layout Configuration */}
          <TabPane tab="布局配置" key="layout">
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="宽度 (格)">
                  <InputNumber
                    value={widget.w}
                    onChange={(value) => console.log('Width:', value)}
                    min={widget.minW}
                    max={widget.maxW}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="高度 (格)">
                  <InputNumber
                    value={widget.h}
                    onChange={(value) => console.log('Height:', value)}
                    min={widget.minH}
                    max={widget.maxH}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="X 位置">
                  <InputNumber
                    value={widget.x}
                    onChange={(value) => console.log('X:', value)}
                    min={0}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Y 位置">
                  <InputNumber
                    value={widget.y}
                    onChange={(value) => console.log('Y:', value)}
                    min={0}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item label="最小尺寸">
              <Row gutter={8}>
                <Col span={12}>
                  <InputNumber
                    addonBefore="宽"
                    value={widget.minW}
                    disabled
                    style={{ width: '100%' }}
                  />
                </Col>
                <Col span={12}>
                  <InputNumber
                    addonBefore="高"
                    value={widget.minH}
                    disabled
                    style={{ width: '100%' }}
                  />
                </Col>
              </Row>
            </Form.Item>

            <Form.Item label="最大尺寸">
              <Row gutter={8}>
                <Col span={12}>
                  <InputNumber
                    addonBefore="宽"
                    value={widget.maxW}
                    disabled
                    style={{ width: '100%' }}
                  />
                </Col>
                <Col span={12}>
                  <InputNumber
                    addonBefore="高"
                    value={widget.maxH}
                    disabled
                    style={{ width: '100%' }}
                  />
                </Col>
              </Row>
            </Form.Item>
          </TabPane>

          {/* Advanced Configuration */}
          <TabPane tab="高级配置" key="advanced">
            <Alert
              message="高级配置"
              description="这些配置需要手动编辑JSON格式"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Form.Item label="配置数据 (JSON)">
              <TextArea
                value={JSON.stringify(config, null, 2)}
                onChange={(e) => {
                  try {
                    const newConfig = JSON.parse(e.target.value)
                    setConfig(newConfig)
                  } catch (error) {
                    // Invalid JSON, don't update
                  }
                }}
                rows={12}
                style={{ fontFamily: 'monospace' }}
              />
            </Form.Item>
          </TabPane>
        </Tabs>
      </Form>
    </Modal>
  )
}

export default WidgetConfigModal