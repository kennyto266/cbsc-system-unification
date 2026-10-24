import React, { useState } from 'react'
import {
  Form,
  InputNumber,
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
  Select,
  Input,
  Collapse,
  Tag,
} from 'antd'
import {
  InfoCircleOutlined,
  ExclamationCircleOutlined,
  SafetyCertificateOutlined,
  WarningOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import { StrategyType, RiskLevel } from '../../types'

// Styles
import './RiskControls.css'

const { Option } = Select
const { TextArea } = Input
const { Panel } = Collapse

interface RiskControlsProps {
  strategyType: StrategyType | ''
  riskLevel: RiskLevel
  form: any
}

interface RiskRule {
  name: string
  label: string
  type: 'number' | 'slider' | 'switch' | 'select'
  required?: boolean
  defaultValue?: any
  min?: number
  max?: number
  step?: number
  options?: Array<{ label: string; value: any }>
  description?: string
  placeholder?: string
  riskImpact?: 'low' | 'medium' | 'high'
}

const RiskControls: React.FC<RiskControlsProps> = ({
  strategyType,
  riskLevel,
  form,
}) => {
  const [advancedMode, setAdvancedMode] = useState(false)
  const [customRules, setCustomRules] = useState<string[]>([])

  // Risk control configurations by strategy type
  const getRiskControlsForType = (type: StrategyType, riskLevel: RiskLevel): RiskRule[] => {
    const baseControls = [
      {
        name: 'max_position_size',
        label: '最大持倉比例',
        type: 'slider' as const,
        required: true,
        min: 1,
        max: 100,
        defaultValue: riskLevel === RiskLevel.LOW ? 20 : riskLevel === RiskLevel.MEDIUM ? 50 : 100,
        description: '單個策略最大持倉資金比例',
        riskImpact: 'high' as const,
      },
      {
        name: 'max_daily_loss',
        label: '最大日損失(%)',
        type: 'number' as const,
        required: true,
        min: 0.1,
        max: 50,
        defaultValue: riskLevel === RiskLevel.LOW ? 2 : riskLevel === RiskLevel.MEDIUM ? 5 : 10,
        description: '觸發停止策略的日最大損失百分比',
        riskImpact: 'high' as const,
      },
      {
        name: 'max_drawdown',
        label: '最大回撤(%)',
        type: 'slider' as const,
        required: true,
        min: 5,
        max: 50,
        defaultValue: riskLevel === RiskLevel.LOW ? 10 : riskLevel === RiskLevel.MEDIUM ? 20 : 30,
        description: '策略整體最大回撤限制',
        riskImpact: 'high' as const,
      },
      {
        name: 'stop_loss_enabled',
        label: '啟用止損',
        type: 'switch' as const,
        defaultValue: true,
        description: '是否啟用自動止損功能',
        riskImpact: 'medium' as const,
      },
    ]

    const typeSpecificControls = {
      [StrategyType.SENTIMENT]: [
        {
          name: 'sentiment_confidence_threshold',
          label: '情感信心閾值',
          type: 'slider' as const,
          min: 0,
          max: 1,
          step: 0.1,
          defaultValue: 0.7,
          description: '執行交易所需的最低情感信心分數',
          riskImpact: 'medium' as const,
        },
        {
          name: 'contrarian_threshold',
          label: '逆向閾值',
          type: 'slider' as const,
          min: -1,
          max: 1,
          step: 0.1,
          defaultValue: 0.8,
          description: '觸發逆向操作的極端情感閾值',
          riskImpact: 'medium' as const,
        },
      ],
      [StrategyType.TECHNICAL]: [
        {
          name: 'signal_confirmation_count',
          label: '信號確認數量',
          type: 'number' as const,
          min: 1,
          max: 5,
          defaultValue: 2,
          description: '執行交易所需的最少技術指標確認數量',
          riskImpact: 'medium' as const,
        },
        {
          name: 'whipsaw_protection',
          label: '震盪保護',
          type: 'switch' as const,
          defaultValue: true,
          description: '是否啟用震盪市場保護機制',
          riskImpact: 'low' as const,
        },
      ],
      [StrategyType.MOMENTUM]: [
        {
          name: 'momentum_decay_threshold',
          label: '動量衰減閾值',
          type: 'slider' as const,
          min: 0,
          max: 1,
          step: 0.1,
          defaultValue: 0.3,
          description: '觸發平倉的動量衰減閾值',
          riskImpact: 'medium' as const,
        },
        {
          name: 'volatility_adjustment',
          label: '波動率調整',
          type: 'switch' as const,
          defaultValue: true,
          description: '是否根據市場波動率調整持倉大小',
          riskImpact: 'low' as const,
        },
      ],
      [StrategyType.MEAN_REVERSION]: [
        {
          name: 'reversion_timeout',
          label: '回歸超時(小時)',
          type: 'number' as const,
          min: 1,
          max: 168,
          defaultValue: 24,
          description: '均值回歸策略的最大等待時間',
          riskImpact: 'medium' as const,
        },
        {
          name: 'trend_filter',
          label: '趨勢過濾',
          type: 'switch' as const,
          defaultValue: false,
          description: '是否在趨勢市場中禁用回歸策略',
          riskImpact: 'low' as const,
        },
      ],
      [StrategyType.ARBITRAGE]: [
        {
          name: 'arbitrage_capital_limit',
          label: '套利資金限制(%)',
          type: 'slider' as const,
          min: 1,
          max: 50,
          defaultValue: 10,
          description: '套利策略使用的最大資金比例',
          riskImpact: 'high' as const,
        },
        {
          name: 'correlation_breakdown_threshold',
          label: '相關性失效閾值',
          type: 'slider' as const,
          min: 0,
          max: 0.5,
          step: 0.05,
          defaultValue: 0.2,
          description: '觸發平倉的相關性失效閾值',
          riskImpact: 'high' as const,
        },
      ],
    }

    return [...baseControls, ...(typeSpecificControls[type] || [])]
  }

  // Risk levels configurations
  const riskLevelConfigs = {
    [RiskLevel.LOW]: {
      color: 'green',
      description: '保守型風險控制，適合穩健投資',
      multiplier: 0.5,
    },
    [RiskLevel.MEDIUM]: {
      color: 'orange',
      description: '平衡型風險控制，適合一般投資者',
      multiplier: 1,
    },
    [RiskLevel.HIGH]: {
      color: 'red',
      description: '積極型風險控制，適合專業投資者',
      multiplier: 1.5,
    },
  }

  // Add custom risk rule
  const addCustomRule = () => {
    const newRule = `custom_${Date.now()}`
    setCustomRules([...customRules, newRule])
  }

  // Remove custom risk rule
  const removeCustomRule = (rule: string) => {
    setCustomRules(customRules.filter(r => r !== rule))
    form.setFieldValue(['risk', 'custom', rule], undefined)
  }

  // Apply risk level preset
  const applyRiskPreset = () => {
    const config = riskLevelConfigs[riskLevel]
    const controls = getRiskControlsForType(strategyType, riskLevel)

    // Update form with risk level presets
    const updates: any = {}
    controls.forEach(control => {
      if (control.defaultValue !== undefined) {
        updates[control.name] = control.defaultValue * config.multiplier
      }
    })

    form.setFieldValue('risk', updates)
  }

  const riskControls = getRiskControlsForType(strategyType, riskLevel)
  const currentRiskConfig = riskLevelConfigs[riskLevel]

  // Render risk control field
  const renderRiskField = (rule: RiskRule) => {
    const fieldProps = {
      placeholder: rule.placeholder,
    }

    switch (rule.type) {
      case 'number':
        return (
          <InputNumber
            {...fieldProps}
            min={rule.min}
            max={rule.max}
            step={rule.step}
            style={{ width: '100%' }}
          />
        )

      case 'slider':
        return (
          <Slider
            {...fieldProps}
            min={rule.min}
            max={rule.max}
            step={rule.step}
            marks={
              rule.name === 'max_drawdown' ? {
                5: '5%',
                10: '10%',
                20: '20%',
                30: '30%',
                50: '50%',
              } : rule.name === 'max_position_size' ? {
                1: '1%',
                10: '10%',
                25: '25%',
                50: '50%',
                100: '100%',
              } : undefined
            }
          />
        )

      case 'switch':
        return <Switch />

      case 'select':
        return (
          <Select placeholder={rule.placeholder}>
            {rule.options?.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        )

      default:
        return <Input {...fieldProps} />
    }
  }

  return (
    <div className="risk-controls">
      {/* Risk Level Info */}
      <Alert
        message={
          <Space>
            <SafetyCertificateOutlined />
            風險級別: <Tag color={currentRiskConfig.color}>{riskLevel}</Tag>
          </Space>
        }
        description={currentRiskConfig.description}
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {/* Risk Level Preset */}
      <Card
        title="風險預設"
        className="risk-section"
        extra={
          <Button
            type="primary"
            ghost
            onClick={applyRiskPreset}
          >
            應用風險預設
          </Button>
        }
      >
        <Row gutter={[16, 16]}>
          {Object.entries(riskLevelConfigs).map(([level, config]) => (
            <Col xs={24} sm={8} key={level}>
              <Card
                size="small"
                className={`risk-preset-card ${level === riskLevel ? 'active' : ''}`}
                hoverable
                onClick={() => form.setFieldValue('riskLevel', level)}
              >
                <div className="risk-preset-content">
                  <Tag color={config.color}>{level}</Tag>
                  <p>{config.description}</p>
                  <small>風險係數: {config.multiplier}x</small>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* Basic Risk Controls */}
      <Card
        title="基礎風險控制"
        extra={
          <Space>
            <Tooltip title="切換到高級模式可以配置更多風險控制選項">
              <Button
                type={advancedMode ? 'primary' : 'default'}
                size="small"
                onClick={() => setAdvancedMode(!advancedMode)}
              >
                {advancedMode ? '高級模式' : '基礎模式'}
              </Button>
            </Tooltip>
          </Space>
        }
        className="risk-section"
      >
        <Row gutter={[16, 16]}>
          {riskControls.map(rule => (
            <Col xs={24} sm={12} md={8} key={rule.name}>
              <Form.Item
                label={
                  <Space>
                    {rule.label}
                    {rule.required && <span style={{ color: 'red' }}>*</span>}
                    {rule.description && (
                      <Tooltip title={rule.description}>
                        <InfoCircleOutlined style={{ color: '#999' }} />
                      </Tooltip>
                    )}
                    {rule.riskImpact && (
                      <Tag
                        size="small"
                        color={
                          rule.riskImpact === 'high' ? 'red' :
                          rule.riskImpact === 'medium' ? 'orange' : 'green'
                        }
                      >
                        {rule.riskImpact === 'high' ? '高' :
                         rule.riskImpact === 'medium' ? '中' : '低'}影響
                      </Tag>
                    )}
                  </Space>
                }
                name={['risk', rule.name]}
                rules={[{ required: rule.required, message: `請設置${rule.label}` }]}
                initialValue={rule.defaultValue}
              >
                {renderRiskField(rule)}
              </Form.Item>
            </Col>
          ))}
        </Row>
      </Card>

      {/* Position Management */}
      <Card title="持倉管理" className="risk-section">
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12}>
            <Form.Item
              label="單品種最大持倉比例"
              name={['risk', 'max_single_position']}
              initialValue={10}
            >
              <Slider
                min={1}
                max={50}
                marks={{
                  1: '1%',
                  10: '10%',
                  25: '25%',
                  50: '50%',
                }}
              />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item
              label="持倉集中度限制"
              name={['risk', 'position_concentration_limit']}
              initialValue={3}
            >
              <InputNumber
                min={1}
                max={10}
                style={{ width: '100%' }}
                addonAfter="個品種"
              />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item
              label="持倉再平衡頻率"
              name={['risk', 'rebalance_frequency']}
            >
              <Select defaultValue="daily">
                <Option value="realtime">實時</Option>
                <Option value="hourly">每小時</Option>
                <Option value="daily">每日</Option>
                <Option value="weekly">每週</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item
              label="強制平倉觸發"
              name={['risk', 'force_close_trigger']}
            >
              <Select defaultValue="margin_call">
                <Option value="margin_call">保證金催告</Option>
                <Option value="stop_out">強制平倉</Option>
                <Option value="manual">手動觸發</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>
      </Card>

      {/* Advanced Risk Controls */}
      {advancedMode && (
        <Card title="高級風險控制" className="risk-section">
          {/* VaR Settings */}
          <Divider>風險價值(VaR)設置</Divider>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <Form.Item
                label="VaR置信水平"
                name={['risk', 'var_confidence']}
                initialValue={95}
              >
                <Slider
                  min={90}
                  max={99}
                  marks={{
                    90: '90%',
                    95: '95%',
                    99: '99%',
                  }}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="VaR時間跨度"
                name={['risk', 'var_horizon']}
              >
                <Select defaultValue="1d">
                  <Option value="1d">1天</Option>
                  <Option value="1w">1週</Option>
                  <Option value="1m">1月</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          {/* Stress Testing */}
          <Divider>壓力測試</Divider>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <Form.Item
                label="啟用壓力測試"
                name={['risk', 'stress_test_enabled']}
                valuePropName="checked"
                initialValue={false}
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="壓力場景"
                name={['risk', 'stress_scenarios']}
              >
                <Select mode="multiple" placeholder="選擇壓力場景">
                  <Option value="market_crash">市場崩盤</Option>
                  <Option value="volatility_spike">波動率激增</Option>
                  <Option value="liquidity_crisis">流動性危機</Option>
                  <Option value="correlation_breakdown">相關性失效</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          {/* Custom Risk Rules */}
          <Divider>自定義風險規則</Divider>
          <Space direction="vertical" style={{ width: '100%' }}>
            {customRules.map(rule => (
              <Row key={rule} gutter={16} align="middle">
                <Col flex="auto">
                  <Form.Item
                    name={['risk', 'custom', rule, 'name']}
                    placeholder="規則名稱"
                  >
                    <Input placeholder="規則名稱" />
                  </Form.Item>
                </Col>
                <Col flex="auto">
                  <Form.Item
                    name={['risk', 'custom', rule, 'condition']}
                    placeholder="條件表達式"
                  >
                    <Input placeholder="條件表達式" />
                  </Form.Item>
                </Col>
                <Col>
                  <Button
                    type="text"
                    danger
                    icon={<WarningOutlined />}
                    onClick={() => removeCustomRule(rule)}
                  />
                </Col>
              </Row>
            ))}
            <Button
              type="dashed"
              icon={<WarningOutlined />}
              onClick={addCustomRule}
            >
              添加自定義風險規則
            </Button>
          </Space>
        </Card>
      )}

      {/* Risk Alerts */}
      <Card title="風險警報" className="risk-section">
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12}>
            <Form.Item
              label="警報郵件通知"
              name={['risk', 'alert_email']}
              valuePropName="checked"
              initialValue={true}
            >
              <Switch />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item
              label="警報短信通知"
              name={['risk', 'alert_sms']}
              valuePropName="checked"
              initialValue={false}
            >
              <Switch />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item
              label="警報頻率限制"
              name={['risk', 'alert_rate_limit']}
              initialValue={300}
            >
              <InputNumber
                min={60}
                max={3600}
                style={{ width: '100%' }}
                addonAfter="秒"
              />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item
              label="緊急聯繫人"
              name={['risk', 'emergency_contact']}
            >
              <Input placeholder="緊急聯繫人郵箱或電話" />
            </Form.Item>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default RiskControls