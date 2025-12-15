import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import dynamic from 'next/dynamic'

// UI Components
import { Card, Button, Input, Select, Textarea, Badge, Progress } from '@/components/ui'
import {
  ArrowLeftIcon,
  ArrowRightIcon,
  DocumentTextIcon,
  CogIcon,
  CodeBracketIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'

// Hooks and API
import { useGetStrategyQuery, useCreateStrategyMutation, useUpdateStrategyMutation } from '@/store/api/apiSlice'
import { useToast } from '@/hooks/useToast'
import { useTheme } from '@/hooks/useTheme'

// Types
import type { Strategy } from '@/types/strategy'

// Dynamic import for Monaco Editor to avoid SSR issues
const MonacoEditor = dynamic(
  () => import('@monaco-editor/react').then(mod => mod.default),
  { ssr: false }
) as any

// Step definitions
const STEPS = [
  { id: 'basic', title: '基本信息', icon: DocumentTextIcon },
  { id: 'params', title: '参数配置', icon: CogIcon },
  { id: 'code', title: '策略代码', icon: CodeBracketIcon },
  { id: 'risk', title: '风险控制', icon: ShieldCheckIcon },
  { id: 'review', title: '确认提交', icon: CheckCircleIcon }
] as const

// Strategy type options
const STRATEGY_TYPES = [
  { value: 'momentum', label: '动量策略' },
  { value: 'mean_reversion', label: '均值回归' },
  { value: 'arbitrage', label: '套利策略' },
  { value: 'trend_following', label: '趋势跟踪' },
  { value: 'custom', label: '自定义' }
]

// Exchange options
const EXCHANGE_OPTIONS = [
  { value: 'binance', label: 'Binance' },
  { value: 'huobi', label: 'Huobi' },
  { value: 'okex', label: 'OKEx' },
  { value: 'coinbase', label: 'Coinbase' }
]

// Strategy form data interface
interface StrategyFormData {
  name: string
  description?: string
  type: string
  parameters: {
    symbols: string[]
    timeframe?: string
    initialCapital?: number
    maxPositionSize?: number
    stopLoss?: number
    takeProfit?: number
    exchange?: string
  }
  code?: string
  tags: string[]
}

// Default form data
const getDefaultFormData = (strategy?: Strategy): StrategyFormData => ({
  name: strategy?.name || '',
  description: strategy?.description || '',
  type: strategy?.type || 'custom',
  parameters: {
    symbols: strategy?.parameters?.symbols || [],
    timeframe: strategy?.parameters?.timeframe || '1h',
    initialCapital: strategy?.parameters?.initialCapital || 10000,
    maxPositionSize: strategy?.parameters?.maxPositionSize || 0.1,
    stopLoss: strategy?.parameters?.stopLoss || 0.02,
    takeProfit: strategy?.parameters?.takeProfit || 0.03,
    exchange: strategy?.parameters?.exchange || ''
  },
  code: strategy?.parameters?.code || '',
  tags: strategy?.tags || []
})

// Strategy Editor Component
const StrategyEditor: React.FC = () => {
  const { id } = useParams<{ id?: string }>()
  const navigate = useNavigate()
  const { theme } = useTheme()
  const { addToast } = useToast()

  const isEditing = !!id
  const [activeStep, setActiveStep] = useState(0)
  const [formData, setFormData] = useState<StrategyFormData>(getDefaultFormData())
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})
  const [isSaving, setIsSaving] = useState(false)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  // API mutations
  const [createStrategy] = useCreateStrategyMutation()
  const [updateStrategy] = useUpdateStrategyMutation()
  const { data: strategy, isLoading: isLoadingStrategy } = useGetStrategyQuery(id!, { skip: !id })

  // Load strategy data for editing
  useEffect(() => {
    if (strategy && isEditing) {
      setFormData(getDefaultFormData(strategy))
    }
  }, [strategy, isEditing])

  // Validate current step
  const validateCurrentStep = useCallback((): boolean => {
    const errors: Record<string, string> = {}

    switch (STEPS[activeStep].id) {
      case 'basic':
        if (!formData.name.trim()) {
          errors.name = '策略名称不能为空'
        } else if (formData.name.length < 2) {
          errors.name = '策略名称至少需要2个字符'
        }
        if (!formData.type) {
          errors.type = '请选择策略类型'
        }
        break

      case 'params':
        if (!formData.parameters.symbols || formData.parameters.symbols.length === 0) {
          errors.symbols = '请至少选择一个交易品种'
        }
        if (!formData.parameters.initialCapital || formData.parameters.initialCapital <= 0) {
          errors.initialCapital = '初始资金必须大于0'
        }
        if (!formData.parameters.maxPositionSize || formData.parameters.maxPositionSize <= 0) {
          errors.maxPositionSize = '最大仓位必须大于0'
        }
        if (!formData.parameters.stopLoss || formData.parameters.stopLoss <= 0) {
          errors.stopLoss = '止损比例必须大于0'
        }
        if (!formData.parameters.takeProfit || formData.parameters.takeProfit <= 0) {
          errors.takeProfit = '止盈比例必须大于0'
        }
        break

      case 'code':
        if (!formData.code || formData.code.trim().length === 0) {
          errors.code = '策略代码不能为空'
        }
        break

      case 'risk':
        // Risk control validation
        break

      case 'review':
        // Review step - summary of all data
        break
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }, [activeStep, formData])

  // Handle form data changes
  const handleFormDataChange = (field: keyof StrategyFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setHasUnsavedChanges(true)
    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors(prev => {
        const { [field]: _, ...rest } = prev
        return rest
      })
    }
  }

  // Handle parameter changes
  const handleParameterChange = (param: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      parameters: { ...prev.parameters, [param]: value }
    }))
    setHasUnsavedChanges(true)
  }

  // Navigate steps
  const handleNext = () => {
    if (validateCurrentStep() && activeStep < STEPS.length - 1) {
      setActiveStep(prev => prev + 1)
    }
  }

  const handlePrevious = () => {
    if (activeStep > 0) {
      setActiveStep(prev => prev - 1)
    }
  }

  const handleStepClick = (stepIndex: number) => {
    if (validateCurrentStep()) {
      setActiveStep(stepIndex)
    }
  }

  // Save strategy
  const handleSave = async () => {
    if (!validateCurrentStep()) return

    setIsSaving(true)
    try {
      if (isEditing && id) {
        await updateStrategy.mutateAsync({ id, data: formData })
        addToast({
          type: 'success',
          message: '策略更新成功'
        })
      } else {
        await createStrategy.mutateAsync(formData)
        addToast({
          type: 'success',
          message: '策略创建成功'
        })
      }
      setHasUnsavedChanges(false)
      navigate('/strategies')
    } catch (error) {
      addToast({
        type: 'error',
        message: `保存失败: ${error instanceof Error ? error.message : '未知错误'}`
      })
    } finally {
      setIsSaving(false)
    }
  }

  // Monaco editor setup
  const handleEditorDidMount = (editor: any, monaco: any) => {
    // Configure TypeScript
    monaco.languages.typescript.typescriptDefaults.setCompilerOptions({
      target: monaco.languages.typescript.ScriptTarget.ES2020,
      allowNonTsExtensions: true,
      moduleResolution: monaco.languages.typescript.ModuleResolutionKind.NodeJs,
      module: monaco.languages.typescript.ModuleKind.CommonJS,
      noEmit: true,
      esModuleInterop: true,
      jsx: monaco.languages.typescript.JsxEmit.React,
      reactNamespace: 'React',
      allowJs: true,
      typeRoots: ['node_modules/@types']
    })

    // Add strategy API type definitions
    monaco.languages.typescript.typescriptDefaults.addExtraLib(`
      declare module StrategyAPI {
        export interface MarketData {
          symbol: string;
          price: number;
          volume: number;
          timestamp: Date;
        }

        export function buy(symbol: string, quantity: number): Promise<TradeResult>;
        export function sell(symbol: string, quantity: number): Promise<TradeResult>;
        export function getMarketData(symbol: string): Promise<MarketData>;
        export function setRiskManagement(params: RiskParams): void;
      }

      interface TradeResult {
        success: boolean;
        orderId?: string;
        price?: number;
        quantity?: number;
      }

      interface RiskParams {
        stopLoss?: number;
        takeProfit?: number;
        maxPositionSize?: number;
      }
    `)
  }

  // Render step content
  const renderStepContent = () => {
    switch (STEPS[activeStep].id) {
      case 'basic':
        return <BasicInfoStep />
      case 'params':
        return <ParametersStep />
      case 'code':
        return <CodeStep />
      case 'risk':
        return <RiskControlStep />
      case 'review':
        return <ReviewStep />
      default:
        return null
    }
  }

  // Basic Information Step
  const BasicInfoStep = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          策略名称 *
        </label>
        <Input
          value={formData.name}
          onChange={(e) => handleFormDataChange('name', e.target.value)}
          placeholder="输入策略名称"
        />
        {validationErrors.name && (
          <p className="mt-1 text-sm text-red-600">{validationErrors.name}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          策略描述
        </label>
        <Textarea
          value={formData.description}
          onChange={(e) => handleFormDataChange('description', e.target.value)}
          placeholder="描述策略的目标和特点"
          rows={3}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            策略类型 *
          </label>
          <Select
            value={formData.type}
            onChange={(e) => handleFormDataChange('type', e.target.value)}
          >
            {STRATEGY_TYPES.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </Select>
          {validationErrors.type && (
            <p className="mt-1 text-sm text-red-600">{validationErrors.type}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            标签
          </label>
          <Input
            value={formData.tags.join(', ')}
            onChange={(e) => handleFormDataChange('tags', e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
            placeholder="输入标签，用逗号分隔"
          />
        </div>
      </div>
    </div>
  )

  // Parameters Step
  const ParametersStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">交易设置</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              交易品种
            </label>
            <Input
              value={formData.parameters.symbols?.join(', ') || ''}
              onChange={(e) => handleParameterChange('symbols', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
              placeholder="输入交易品种，用逗号分隔"
            />
            {validationErrors.symbols && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.symbols}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              时间框架
            </label>
            <Select
              value={formData.parameters.timeframe}
              onChange={(e) => handleParameterChange('timeframe', e.target.value)}
            >
              <option value="1m">1分钟</option>
              <option value="5m">5分钟</option>
              <option value="15m">15分钟</option>
              <option value="1h">1小时</option>
              <option value="4h">4小时</option>
              <option value="1d">1天</option>
            </Select>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">资金设置</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              初始资金 ($)
            </label>
            <Input
              type="number"
              value={formData.parameters.initialCapital}
              onChange={(e) => handleParameterChange('initialCapital', parseFloat(e.target.value))}
              min="0"
            />
            {validationErrors.initialCapital && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.initialCapital}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              最大仓位 (%)
            </label>
            <Input
              type="number"
              value={formData.parameters.maxPositionSize}
              onChange={(e) => handleParameterChange('maxPositionSize', parseFloat(e.target.value))}
              min="0"
              max="1"
              step="0.01"
            />
            {validationErrors.maxPositionSize && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.maxPositionSize}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              止损 (%)
            </label>
            <Input
              type="number"
              value={formData.parameters.stopLoss}
              onChange={(e) => handleParameterChange('stopLoss', parseFloat(e.target.value))}
              min="0"
              max="1"
              step="0.01"
            />
            {validationErrors.stopLoss && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.stopLoss}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              止盈 (%)
            </label>
            <Input
              type="number"
              value={formData.parameters.takeProfit}
              onChange={(e) => handleParameterChange('takeProfit', parseFloat(e.target.value))}
              min="0"
              max="1"
              step="0.01"
            />
            {validationErrors.takeProfit && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.takeProfit}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )

  // Code Step
  const CodeStep = () => {
    const editorTheme = theme.mode === 'dark' ? 'vs-dark' : 'vs-light'

    return (
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            策略代码 *
          </label>
          <div className="border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
            <MonacoEditor
              height="400px"
              language="typescript"
              theme={editorTheme}
              value={formData.code}
              onChange={(value) => handleFormDataChange('code', value || '')}
              onMount={handleEditorDidMount}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                wordWrap: 'on',
                automaticLayout: true,
                scrollBeyondLastLine: false,
                suggestOnTriggerCharacters: true,
                quickSuggestions: true
              }}
            />
          </div>
          {validationErrors.code && (
            <p className="mt-2 text-sm text-red-600">{validationErrors.code}</p>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              策略类型
            </label>
            <Select
              value={formData.type}
              onChange={(e) => handleFormDataChange('type', e.target.value)}
            >
              {STRATEGY_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              交易所
            </label>
            <Select
              value={formData.parameters.exchange || ''}
              onChange={(e) => handleParameterChange('exchange', e.target.value)}
            >
              <option value="">选择交易所</option>
              {EXCHANGE_OPTIONS.map(exchange => (
                <option key={exchange.value} value={exchange.value}>
                  {exchange.label}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </div>
    )
  }

  // Risk Control Step
  const RiskControlStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">风险管理</h3>
        <div className="space-y-4">
          <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
            <div className="flex items-start">
              <InformationCircleIcon className="h-5 w-5 text-yellow-400 mr-2 mt-0.5" />
              <div>
                <h4 className="font-medium text-yellow-800 dark:text-yellow-200">风险提示</h4>
                <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                  量化交易存在市场风险，请确保您已充分了解相关风险并使用可承受损失的资金。
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">风险控制参数</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              每日最大交易次数
            </label>
            <Input
              type="number"
              defaultValue="10"
              onChange={(e) => handleParameterChange('maxTradesPerDay', parseInt(e.target.value))}
              min="1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              最大回撤限制 (%)
            </label>
            <Input
              type="number"
              defaultValue="0.2"
              onChange={(e) => handleParameterChange('maxDrawdown', parseFloat(e.target.value))}
              min="0"
              max="1"
              step="0.01"
            />
          </div>
        </div>
      </div>
    </div>
  )

  // Review Step
  const ReviewStep = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-medium text-gray-900 dark:text-white">策略概览</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h4 className="font-medium text-gray-900 dark:text-white mb-4">基本信息</h4>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">策略名称:</span>
              <span className="text-sm font-medium">{formData.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">策略类型:</span>
              <Badge variant="blue">{STRATEGY_TYPES.find(t => t.value === formData.type)?.label}</Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">标签:</span>
              <span className="text-sm font-medium">
                {formData.tags.length > 0 ? formData.tags.join(', ') : '无'}
              </span>
            </div>
            {formData.description && (
              <div>
                <span className="text-sm text-gray-600 dark:text-gray-400">描述:</span>
                <p className="mt-1 text-sm text-gray-700 dark:text-gray-300">{formData.description}</p>
              </div>
            )}
          </div>
        </Card>

        <Card className="p-6">
          <h4 className="font-medium text-gray-900 dark:text-white mb-4">参数配置</h4>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">初始资金:</span>
              <span className="text-sm font-medium">${formData.parameters.initialCapital?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">最大仓位:</span>
              <span className="text-sm font-medium">{(formData.parameters.maxPositionSize * 100).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">止损:</span>
              <span className="text-sm font-medium">{(formData.parameters.stopLoss * 100).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">止盈:</span>
              <span className="text-sm font-medium">{(formData.parameters.takeProfit * 100).toFixed(1)}%</span>
            </div>
          </div>
        </Card>
      </div>

      <Card className="p-6">
        <h4 className="font-medium text-gray-900 dark:text-white mb-4">检查清单</h4>
        <div className="space-y-2">
          <div className="flex items-center">
            <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
            <span className="text-sm text-gray-700 dark:text-gray-300">策略名称和描述已填写</span>
          </div>
          <div className="flex items-center">
            <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
            <span className="text-sm text-gray-700 dark:text-gray-300">交易参数已配置</span>
          </div>
          <div className="flex items-center">
            <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
            <span className="text-sm text-gray-700 dark:text-gray-300">策略代码已编写</span>
          </div>
          <div className="flex items-center">
            <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
            <span className="text-sm text-gray-700 dark:text-gray-300">风险控制已设置</span>
          </div>
        </div>
      </Card>
    </div>
  )

  // Loading state
  if (isLoadingStrategy) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/4 mb-8"></div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {isEditing ? '编辑策略' : '创建策略'}
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            请按照步骤填写策略信息
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => {
            if (hasUnsavedChanges) {
              // TODO: Show confirmation dialog
              navigate('/strategies')
            } else {
              navigate('/strategies')
            }
          }}
        >
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          返回
        </Button>
      </div>

      {/* Step Indicator */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          {STEPS.map((step, index) => (
            <div key={step.id} className="flex items-center flex-1">
              <button
                onClick={() => handleStepClick(index)}
                className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                  index === activeStep
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                    : index < activeStep
                    ? 'border-green-500 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400'
                    : 'border-gray-300 dark:border-gray-600 text-gray-400'
                } transition-colors`}
              >
                <step.icon className="h-5 w-5" />
              </button>
              <div className="flex-1 mx-2">
                <div className={`h-2 ${
                  index === activeStep
                    ? 'bg-blue-500'
                    : index < activeStep
                    ? 'bg-green-500'
                    : 'bg-gray-300 dark:bg-gray-600'
                }`} />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex justify-between">
          {STEPS.map((step, index) => (
            <div key={step.id} className="text-center" style={{ marginLeft: index === 0 ? 0 : '-2rem' }}>
              <p className={`text-sm font-medium ${
                index === activeStep
                  ? 'text-blue-600 dark:text-blue-400'
                  : index < activeStep
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-gray-500 dark:text-gray-400'
              }`}>
                {step.title}
              </p>
            </div>
          ))}
        </div>
      </Card>

      {/* Form Content */}
      <Card className="p-6 mb-6">
        {renderStepContent()}
      </Card>

      {/* Action Buttons */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={activeStep === 0 ? () => navigate('/strategies') : handlePrevious}
          disabled={isSaving}
        >
          {activeStep === 0 ? '取消' : '上一步'}
        </Button>

        <div className="flex space-x-3">
          {hasUnsavedChanges && activeStep !== STEPS.length - 1 && (
            <Button variant="outline" onClick={() => /* TODO: Save draft */ {}}>
              保存草稿
            </Button>
          )}

          {activeStep < STEPS.length - 1 ? (
            <Button onClick={handleNext} disabled={isSaving}>
              下一步
              <ArrowRightIcon className="h-5 w-5 ml-2" />
            </Button>
          ) : (
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? '保存中...' : isEditing ? '更新策略' : '创建策略'}
            </Button>
          )}
        </div>
      </div>

      {/* Validation Errors */}
      {Object.keys(validationErrors).length > 0 && (
        <Card className="p-4 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
          <div className="flex items-start">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mr-2" />
            <div>
              <h4 className="font-medium text-red-800 dark:text-red-200">请修正以下错误:</h4>
              <ul className="mt-2 text-sm text-red-700 dark:text-red-300 list-disc list-inside">
                {Object.entries(validationErrors).map(([field, error]) => (
                  <li key={field}>{error}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}

export default StrategyEditor