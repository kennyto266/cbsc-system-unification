import React, { useState, useEffect } from 'react'
import {
  Form,
  Input,
  InputNumber,
  Select,
  Switch,
  Slider,
  Row,
  Col,
  Card,
  Divider,
  Space,
  Button,
  Tooltip,
  Alert,
  Collapse,
  Tag,
} from 'antd'
import {
  InfoCircleOutlined,
  PlusOutlined,
  DeleteOutlined,
  SettingOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import { StrategyType } from '../../types'
import { useGetStrategyTemplatesQuery } from '../../store/api/strategiesApi'

// Styles
import './ParameterConfig.css'

const { TextArea } = Input
const { Option } = Select
const { Panel } = Collapse

interface ParameterConfigProps {
  strategyType: StrategyType | ''
  form: any
  useTemplate?: boolean
  templateId?: string | null
}

interface ParameterField {
  name: string
  label: string
  type: 'number' | 'string' | 'boolean' | 'select' | 'slider' | 'array'
  required?: boolean
  defaultValue?: any
  min?: number
  max?: number
  step?: number
  options?: Array<{ label: string; value: any }>
  description?: string
  placeholder?: string
  validation?: {
    pattern?: RegExp
    message?: string
  }
}

const ParameterConfig: React.FC<ParameterConfigProps> = ({
  strategyType,
  form,
  useTemplate = false,
  templateId,
}) => {
  const [customFields, setCustomFields] = useState<string[]>([])
  const [templateData, setTemplateData] = useState<any>(null)
  const [advancedMode, setAdvancedMode] = useState(false)

  // Fetch template data if template is selected
  const { data: template } = useGetStrategyTemplatesQuery(
    { page: 1, pageSize: 10 },
    { skip: !useTemplate || !templateId }
  )

  useEffect(() => {
    if (template && templateId) {
      const selectedTemplate = template.data?.find((t: any) => t.id === templateId)
      if (selectedTemplate) {
        setTemplateData(selectedTemplate)
        // Load template parameters into form
        form.setFieldsValue({
          parameters: selectedTemplate.parameters,
          technicalIndicators: selectedTemplate.technicalIndicators,
        })
      }
    }
  }, [template, templateId, form])

  // Strategy type parameter configurations
  const getParametersForType = (type: StrategyType): ParameterField[] => {
    const configurations = {
      [StrategyType.SENTIMENT]: [
        {
          name: 'sentiment_source',
          label: '情感數據源',
          type: 'select',
          required: true,
          options: [
            { label: 'Twitter API', value: 'twitter' },
            { label: 'Reddit API', value: 'reddit' },
            { label: '新聞API', value: 'news' },
            { label: '綜合情感', value: 'composite' },
          ],
          description: '選擇情感數據的主要來源',
        },
        {
          name: 'sentiment_threshold',
          label: '情感閾值',
          type: 'slider',
          required: true,
          min: -1,
          max: 1,
          step: 0.1,
          defaultValue: 0,
          description: '觸發買賣信號的情感分數閾值',
        },
        {
          name: 'update_frequency',
          label: '更新頻率(秒)',
          type: 'number',
          required: true,
          min: 60,
          max: 3600,
          defaultValue: 300,
          description: '情感數據更新頻率',
        },
        {
          name: 'sentiment_weight',
          label: '情感權重',
          type: 'slider',
          min: 0,
          max: 1,
          step: 0.1,
          defaultValue: 0.5,
          description: '情感分析在決策中的權重',
        },
      ],
      [StrategyType.TECHNICAL]: [
        {
          name: 'timeframe',
          label: '時間週期',
          type: 'select',
          required: true,
          options: [
            { label: '1分鐘', value: '1m' },
            { label: '5分鐘', value: '5m' },
            { label: '15分鐘', value: '15m' },
            { label: '1小時', value: '1h' },
            { label: '4小時', value: '4h' },
            { label: '1天', value: '1d' },
          ],
          description: '技術分析的時間週期',
        },
        {
          name: 'fast_ma_period',
          label: '快速移動平均線週期',
          type: 'number',
          required: true,
          min: 5,
          max: 50,
          defaultValue: 12,
          description: '快速移動平均線的計算週期',
        },
        {
          name: 'slow_ma_period',
          label: '慢速移動平均線週期',
          type: 'number',
          required: true,
          min: 20,
          max: 200,
          defaultValue: 26,
          description: '慢速移動平均線的計算週期',
        },
        {
          name: 'rsi_period',
          label: 'RSI週期',
          type: 'number',
          required: true,
          min: 5,
          max: 50,
          defaultValue: 14,
          description: '相對強弱指標的計算週期',
        },
        {
          name: 'rsi_overbought',
          label: 'RSI超買線',
          type: 'number',
          min: 50,
          max: 100,
          defaultValue: 70,
          description: 'RSI超買信號線',
        },
        {
          name: 'rsi_oversold',
          label: 'RSI超賣線',
          type: 'number',
          min: 0,
          max: 50,
          defaultValue: 30,
          description: 'RSI超賣信號線',
        },
      ],
      [StrategyType.MOMENTUM]: [
        {
          name: 'momentum_period',
          label: '動量週期',
          type: 'number',
          required: true,
          min: 1,
          max: 100,
          defaultValue: 10,
          description: '計算動量的回看週期',
        },
        {
          name: 'momentum_threshold',
          label: '動量閾值',
          type: 'slider',
          min: -1,
          max: 1,
          step: 0.1,
          defaultValue: 0,
          description: '觸發交易信號的動量閾值',
        },
        {
          name: 'volume_filter',
          label: '成交量過濾',
          type: 'boolean',
          defaultValue: true,
          description: '是否使用成交量過濾信號',
        },
        {
          name: 'volume_ma_period',
          label: '成交量移動平均週期',
          type: 'number',
          min: 5,
          max: 50,
          defaultValue: 20,
          description: '成交量移動平均的計算週期',
        },
      ],
      [StrategyType.MEAN_REVERSION]: [
        {
          name: 'lookback_period',
          label: '回看週期',
          type: 'number',
          required: true,
          min: 10,
          max: 200,
          defaultValue: 20,
          description: '計算均價的回看週期',
        },
        {
          name: 'std_dev_multiplier',
          label: '標準差倍數',
          type: 'slider',
          min: 1,
          max: 3,
          step: 0.1,
          defaultValue: 2,
          description: '布林帶標準差倍數',
        },
        {
          name: 'entry_threshold',
          label: '進場閾值',
          type: 'slider',
          min: 0.5,
          max: 2,
          step: 0.1,
          defaultValue: 1,
          description: '觸發進場的價格偏離閾值',
        },
        {
          name: 'exit_threshold',
          label: '出場閾值',
          type: 'slider',
          min: 0.1,
          max: 1,
          step: 0.1,
          defaultValue: 0.2,
          description: '觸發出場的價格回歸閾值',
        },
      ],
      [StrategyType.ARBITRAGE]: [
        {
          name: 'arbitrage_type',
          label: '套利類型',
          type: 'select',
          required: true,
          options: [
            { label: '統計套利', value: 'statistical' },
            { label: '三角套利', value: 'triangular' },
            { label: '期現套利', value: 'futures_spot' },
            { label: '跨市場套利', value: 'cross_market' },
          ],
          description: '選擇套利策略類型',
        },
        {
          name: 'min_profit_threshold',
          label: '最小盈利閾值(%)',
          type: 'number',
          required: true,
          min: 0.01,
          max: 5,
          step: 0.01,
          defaultValue: 0.1,
          description: '觸發套利的最小盈利百分比',
        },
        {
          name: 'max_holding_period',
          label: '最大持倉時間(秒)',
          type: 'number',
          min: 60,
          max: 3600,
          defaultValue: 300,
          description: '套利頭寸的最大持倉時間',
        },
        {
          name: 'correlation_threshold',
          label: '相關性閾值',
          type: 'slider',
          min: 0.5,
          max: 0.99,
          step: 0.01,
          defaultValue: 0.8,
          description: '統計套利的相關性閾值',
        },
      ],
    }

    return configurations[type] || []
  }

  // Technical indicators
  const technicalIndicators = [
    { name: 'SMA', label: '簡單移動平均線', group: 'trend' },
    { name: 'EMA', label: '指數移動平均線', group: 'trend' },
    { name: 'MACD', label: 'MACD', group: 'momentum' },
    { name: 'RSI', label: '相對強弱指標', group: 'momentum' },
    { name: 'Stochastic', label: '隨機指標', group: 'momentum' },
    { name: 'BollingerBands', label: '布林帶', group: 'volatility' },
    { name: 'ATR', label: '平均真實範圍', group: 'volatility' },
    { name: 'ADX', label: '趨勢強度指標', group: 'trend' },
    { name: 'CCI', label: '商品通道指標', group: 'momentum' },
    { name: 'WilliamsR', label: '威廉指標', group: 'momentum' },
    { name: 'VolumeProfile', label: '成交量分布', group: 'volume' },
    { name: 'VWAP', label: '成交量加權平均價', group: 'volume' },
  ]

  // Add custom parameter field
  const addCustomField = () => {
    const newField = `custom_${Date.now()}`
    setCustomFields([...customFields, newField])
  }

  // Remove custom parameter field
  const removeCustomField = (field: string) => {
    setCustomFields(customFields.filter(f => f !== field))
    form.setFieldValue(['parameters', field], undefined)
  }

  // Render parameter field
  const renderParameterField = (field: ParameterField) => {
    const commonProps = {
      placeholder: field.placeholder,
    }

    switch (field.type) {
      case 'number':
        return (
          <InputNumber
            {...commonProps}
            min={field.min}
            max={field.max}
            step={field.step}
            style={{ width: '100%' }}
          />
        )

      case 'boolean':
        return <Switch />

      case 'select':
        return (
          <Select placeholder={field.placeholder}>
            {field.options?.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        )

      case 'slider':
        return (
          <Slider
            min={field.min}
            max={field.max}
            step={field.step}
            marks={
              field.name === 'sentiment_threshold' ? {
                '-1': '-1',
                '0': '0',
                '1': '1',
              } : undefined
            }
          />
        )

      case 'array':
        return (
          <Select
            mode="multiple"
            placeholder={field.placeholder}
            style={{ width: '100%' }}
          >
            {field.options?.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        )

      default:
        return <Input {...commonProps} />
    }
  }

  const parameters = getParametersForType(strategyType)

  return (
    <div className="parameter-config">
      {/* Template Info */}
      {useTemplate && templateData && (
        <Alert
          message="基於模板配置"
          description={`正在基於模板"${templateData.name}"配置策略參數，您可以根據需要進行調整。`}
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Basic Parameters */}
      <Card
        title="基礎參數"
        extra={
          <Space>
            <Tooltip title="切換到高級模式可以查看和配置更多參數">
              <Button
                type={advancedMode ? 'primary' : 'default'}
                size="small"
                icon={<SettingOutlined />}
                onClick={() => setAdvancedMode(!advancedMode)}
              >
                {advancedMode ? '高級模式' : '基礎模式'}
              </Button>
            </Tooltip>
          </Space>
        }
        className="parameter-section"
      >
        <Row gutter={[16, 16]}>
          {parameters.map(field => (
            <Col xs={24} sm={12} md={8} key={field.name}>
              <Form.Item
                label={
                  <Space>
                    {field.label}
                    {field.required && <span style={{ color: 'red' }}>*</span>}
                    {field.description && (
                      <Tooltip title={field.description}>
                        <InfoCircleOutlined style={{ color: '#999' }} />
                      </Tooltip>
                    )}
                  </Space>
                }
                name={['parameters', field.name]}
                rules={[
                  { required: field.required, message: `請輸入${field.label}` },
                  field.validation && {
                    pattern: field.validation.pattern,
                    message: field.validation.message,
                  },
                ]}
                initialValue={field.defaultValue}
              >
                {renderParameterField(field)}
              </Form.Item>
            </Col>
          ))}
        </Row>
      </Card>

      {/* Technical Indicators */}
      <Card
        title="技術指標"
        extra={
          <Space>
            <Tag color="blue">
              <ThunderboltOutlined />
              技術指標
            </Tag>
          </Space>
        }
        className="parameter-section"
      >
        <Form.Item
          name="technicalIndicators"
          label="選擇技術指標"
        >
          <Select
            mode="multiple"
            placeholder="選擇要使用的技術指標"
            style={{ width: '100%' }}
          >
            {technicalIndicators.map(indicator => (
              <Option key={indicator.name} value={indicator.name}>
                <Space>
                  <span>{indicator.label}</span>
                  <Tag size="small">{indicator.group}</Tag>
                </Space>
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Collapse ghost>
          <Panel header="技術指標配置" key="indicator-config">
            <Alert
              message="提示"
              description="每個選中的技術指標都可以在這裡進行個別配置。詳細配置功能開發中..."
              type="info"
              showIcon
            />
          </Panel>
        </Collapse>
      </Card>

      {/* Custom Parameters */}
      {advancedMode && (
        <Card
          title="自定義參數"
          extra={
            <Button
              type="dashed"
              icon={<PlusOutlined />}
              onClick={addCustomField}
            >
              添加自定義參數
            </Button>
          }
          className="parameter-section"
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            {customFields.map(field => (
              <Row key={field} gutter={16} align="middle">
                <Col flex="auto">
                  <Form.Item
                    name={['parameters', field, 'name']}
                    placeholder="參數名稱"
                  >
                    <Input placeholder="參數名稱" />
                  </Form.Item>
                </Col>
                <Col flex="auto">
                  <Form.Item
                    name={['parameters', field, 'value']}
                    placeholder="參數值"
                  >
                    <Input placeholder="參數值" />
                  </Form.Item>
                </Col>
                <Col>
                  <Button
                    type="text"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => removeCustomField(field)}
                  />
                </Col>
              </Row>
            ))}
          </Space>
        </Card>
      )}

      {/* Execution Parameters */}
      {advancedMode && (
        <Card title="執行參數" className="parameter-section">
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <Form.Item
                label="並行執行數量"
                name={['execution', 'parallel_count']}
                initialValue={1}
              >
                <InputNumber min={1} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="執行超時(秒)"
                name={['execution', 'timeout']}
                initialValue={30}
              >
                <InputNumber min={5} max={300} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="重試次數"
                name={['execution', 'retry_count']}
                initialValue={3}
              >
                <InputNumber min={0} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="是否啟用批量執行"
                name={['execution', 'batch_enabled']}
                valuePropName="checked"
                initialValue={false}
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>
        </Card>
      )}

      {/* Custom Script */}
      {advancedMode && (
        <Card title="自定義腳本" className="parameter-section">
          <Alert
            message="高級功能"
            description="您可以在此添加自定義的Python/JavaScript代碼來實現複雜的邏輯。請確保代碼的安全性。"
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form.Item
            name="custom_script"
            label="策略腳本"
          >
            <TextArea
              rows={10}
              placeholder="在此輸入自定義策略腳本..."
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>
        </Card>
      )}
    </div>
  )
}

export default ParameterConfig