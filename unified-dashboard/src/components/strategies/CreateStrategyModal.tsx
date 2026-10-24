import React, { useState, useEffect } from 'react'
import {
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Slider,
  Button,
  Space,
  Steps,
  Card,
  Row,
  Col,
  Divider,
  Alert,
  Tooltip,
  Tag,
  Upload,
  message,
} from 'antd'
import {
  InfoCircleOutlined,
  UploadOutlined,
  CopyOutlined,
  SaveOutlined,
  ArrowLeftOutlined,
  ArrowRightOutlined,
  CheckOutlined,
} from '@ant-design/icons'
import { motion, AnimatePresence } from 'framer-motion'
import { StrategyType, RiskLevel, Strategy } from '../../types'
import { useStrategies } from '../../hooks/strategies'
import ParameterConfig from './ParameterConfig'
import RiskControls from './RiskControls'

// Styles
import './CreateStrategyModal.css'

const { TextArea } = Input
const { Option } = Select
const { Step } = Steps
const { Dragger } = Upload

interface CreateStrategyModalProps {
  visible: boolean
  onClose: () => void
  onSuccess?: (strategy: Strategy) => void
  initialData?: Partial<Strategy>
  mode?: 'create' | 'edit'
}

const CreateStrategyModal: React.FC<CreateStrategyModalProps> = ({
  visible,
  onClose,
  onSuccess,
  initialData,
  mode = 'create',
}) => {
  const [form] = Form.useForm()
  const [currentStep, setCurrentStep] = useState(0)
  const [strategyType, setStrategyType] = useState<StrategyType | ''>('')
  const [riskLevel, setRiskLevel] = useState<RiskLevel>(RiskLevel.MEDIUM)
  const [useTemplate, setUseTemplate] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { createStrategy, updateStrategy, strategies } = useStrategies()

  // Reset form when modal opens/closes
  useEffect(() => {
    if (visible) {
      if (mode === 'edit' && initialData) {
        form.setFieldsValue(initialData)
        setStrategyType(initialData.type || '')
        setRiskLevel(initialData.riskLevel || RiskLevel.MEDIUM)
      } else {
        form.resetFields()
        setStrategyType('')
        setRiskLevel(RiskLevel.MEDIUM)
      }
      setCurrentStep(0)
    }
  }, [visible, mode, initialData, form])

  // Step definitions
  const steps = [
    {
      title: '基本信息',
      description: '設置策略名稱、類型等基本信息',
      icon: <InfoCircleOutlined />,
    },
    {
      title: '參數配置',
      description: '配置策略運行參數',
      icon: <CopyOutlined />,
    },
    {
      title: '風險控制',
      description: '設置風險管理規則',
      icon: <CheckOutlined />,
    },
  ]

  // Strategy type options with descriptions
  const strategyTypeOptions = [
    {
      value: StrategyType.SENTIMENT,
      label: '情感分析',
      description: '基於市場情感和情緒指標的量化策略',
      riskLevel: RiskLevel.MEDIUM,
    },
    {
      value: StrategyType.TECHNICAL,
      label: '技術分析',
      description: '基於技術指標和圖形模式的量化策略',
      riskLevel: RiskLevel.LOW,
    },
    {
      value: StrategyType.MOMENTUM,
      label: '動量策略',
      description: '捕捉市場動量和趨勢的量化策略',
      riskLevel: RiskLevel.MEDIUM,
    },
    {
      value: StrategyType.MEAN_REVERSION,
      label: '均值回歸',
      description: '基於均值回歸理論的量化策略',
      riskLevel: RiskLevel.HIGH,
    },
    {
      value: StrategyType.ARBITRAGE,
      label: '套利策略',
      description: '捕捉市場套利機會的量化策略',
      riskLevel: RiskLevel.LOW,
    },
  ]

  // Handle strategy type change
  const handleTypeChange = (type: StrategyType) => {
    setStrategyType(type)
    // Auto-set risk level based on strategy type
    const typeConfig = strategyTypeOptions.find(option => option.value === type)
    if (typeConfig) {
      setRiskLevel(typeConfig.riskLevel)
      form.setFieldsValue({ riskLevel: typeConfig.riskLevel })
    }
  }

  // Handle form submission
  const handleSubmit = async () => {
    try {
      setIsSubmitting(true)
      const values = await form.validateFields()

      // Prepare strategy data
      const strategyData = {
        ...values,
        type: strategyType,
        riskLevel,
        status: 'inactive' as const,
        performance: {
          totalReturn: 0,
          sharpeRatio: 0,
          maxDrawdown: 0,
          winRate: 0,
          profitFactor: 0,
        },
      }

      let result: Strategy

      if (mode === 'create') {
        result = await createStrategy(strategyData)
        message.success('策略創建成功')
      } else {
        result = await updateStrategy(initialData!.id!, strategyData)
        message.success('策略更新成功')
      }

      onSuccess?.(result)
      onClose()
    } catch (error) {
      console.error('Failed to save strategy:', error)
      message.error('保存策略失敗，請檢查輸入信息')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Navigation functions
  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  // Step content renderers
  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // Basic Info
        return (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="step-content"
          >
            <Row gutter={[24, 16]}>
              <Col xs={24} md={12}>
                <Form.Item
                  label="策略名稱"
                  name="name"
                  rules={[
                    { required: true, message: '請輸入策略名稱' },
                    { min: 2, max: 50, message: '策略名稱長度應在2-50個字符之間' },
                  ]}
                >
                  <Input placeholder="輸入策略名稱" />
                </Form.Item>

                <Form.Item
                  label="策略類型"
                  name="type"
                  rules={[{ required: true, message: '請選擇策略類型' }]}
                >
                  <Select
                    placeholder="選擇策略類型"
                    value={strategyType}
                    onChange={handleTypeChange}
                  >
                    {strategyTypeOptions.map(option => (
                      <Option key={option.value} value={option.value}>
                        <div>
                          <div>{option.label}</div>
                          <small className="text-gray-500">{option.description}</small>
                        </div>
                      </Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item
                  label="風險級別"
                  name="riskLevel"
                  rules={[{ required: true, message: '請選擇風險級別' }]}
                >
                  <Select
                    value={riskLevel}
                    onChange={setRiskLevel}
                    placeholder="選擇風險級別"
                  >
                    <Option value={RiskLevel.LOW}>
                      <Tag color="green">低風險</Tag>
                    </Option>
                    <Option value={RiskLevel.MEDIUM}>
                      <Tag color="orange">中風險</Tag>
                    </Option>
                    <Option value={RiskLevel.HIGH}>
                      <Tag color="red">高風險</Tag>
                    </Option>
                  </Select>
                </Form.Item>
              </Col>

              <Col xs={24} md={12}>
                <Form.Item
                  label="策略描述"
                  name="description"
                  rules={[{ max: 500, message: '描述不能超過500個字符' }]}
                >
                  <TextArea
                    rows={4}
                    placeholder="描述策略的特點、適用場景等"
                    showCount
                    maxLength={500}
                  />
                </Form.Item>

                <Form.Item
                  label={
                    <Space>
                      初始資金分配
                      <Tooltip title="策略啟動時的初始資金分配比例">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="allocation"
                >
                  <Slider
                    min={0}
                    max={100}
                    marks={{
                      0: '0%',
                      25: '25%',
                      50: '50%',
                      75: '75%',
                      100: '100%',
                    }}
                    step={5}
                  />
                </Form.Item>

                <Form.Item
                  label="是否啟用自動重啟"
                  name="autoRestart"
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>
              </Col>
            </Row>

            {/* Template Section */}
            <Divider>使用模板</Divider>
            <Row>
              <Col span={24}>
                <Form.Item name="useTemplate" valuePropName="checked">
                  <Switch
                    checkedChildren="使用模板"
                    unCheckedChildren="自定義策略"
                    onChange={setUseTemplate}
                  />
                </Form.Item>

                {useTemplate && (
                  <AnimatePresence>
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                    >
                      <Form.Item
                        label="選擇模板"
                        name="templateId"
                        rules={[{ required: true, message: '請選擇策略模板' }]}
                      >
                        <Select
                          placeholder="選擇一個策略模板作為基礎"
                          value={selectedTemplate}
                          onChange={setSelectedTemplate}
                        >
                          {/* Render strategy templates from API */}
                          {strategies?.filter(s => s.type === strategyType).map(strategy => (
                            <Option key={strategy.id} value={strategy.id}>
                              {strategy.name}
                            </Option>
                          ))}
                        </Select>
                      </Form.Item>
                    </motion.div>
                  </AnimatePresence>
                )}
              </Col>
            </Row>
          </motion.div>
        )

      case 1: // Parameters
        return (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="step-content"
          >
            <ParameterConfig
              strategyType={strategyType}
              form={form}
              useTemplate={useTemplate}
              templateId={selectedTemplate}
            />
          </motion.div>
        )

      case 2: // Risk Controls
        return (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="step-content"
          >
            <RiskControls
              strategyType={strategyType}
              riskLevel={riskLevel}
              form={form}
            />
          </motion.div>
        )

      default:
        return null
    }
  }

  return (
    <Modal
      title={
        <Space>
          {mode === 'create' ? '創建新策略' : '編輯策略'}
          <Tag color="blue">步驟 {currentStep + 1} / {steps.length}</Tag>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={900}
      footer={
        <Space>
          <Button onClick={onClose}>
            取消
          </Button>
          {currentStep > 0 && (
            <Button icon={<ArrowLeftOutlined />} onClick={prevStep}>
              上一步
            </Button>
          )}
          {currentStep < steps.length - 1 ? (
            <Button type="primary" icon={<ArrowRightOutlined />} onClick={nextStep}>
              下一步
            </Button>
          ) : (
            <Button
              type="primary"
              icon={<SaveOutlined />}
              loading={isSubmitting}
              onClick={handleSubmit}
            >
              {mode === 'create' ? '創建策略' : '保存更改'}
            </Button>
          )}
        </Space>
      }
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        requiredMark={false}
        initialValues={{
          riskLevel: RiskLevel.MEDIUM,
          allocation: 50,
          autoRestart: false,
          useTemplate: false,
        }}
      >
        {/* Steps */}
        <Steps current={currentStep} className="strategy-steps">
          {steps.map((step, index) => (
            <Step
              key={index}
              title={step.title}
              description={step.description}
              icon={step.icon}
            />
          ))}
        </Steps>

        <Divider />

        {/* Step Content */}
        <div className="steps-content">
          <AnimatePresence mode="wait">
            {renderStepContent()}
          </AnimatePresence>
        </div>

        {/* Warning for high risk strategies */}
        {riskLevel === RiskLevel.HIGH && currentStep === 2 && (
          <Alert
            message="高風險策略警告"
            description="您選擇了高風險級別，請確保已充分了解相關風險並設置了合適的風險控制措施。"
            type="warning"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </Form>
    </Modal>
  )
}

export default CreateStrategyModal
