import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Save,
  X,
  Plus,
  Trash2,
  Info,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Activity
} from 'lucide-react'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { Textarea } from '../../components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select'
import { Switch } from '../../components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { Badge } from '../../components/ui/badge'
import { Progress } from '../../components/ui/progress'
import { Separator } from '../../components/ui/separator'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '../../components/ui/accordion'
import { Grid } from '../square-ui/Grid'
import { Alert, AlertDescription, AlertTitle } from '../ui/alert'
import { cn } from '../../lib/utils'
import { Strategy } from '../../types'

interface StrategyFormModernProps {
  strategy?: Strategy
  onSubmit: (strategyData: Partial<Strategy>) => Promise<void>
  onCancel: () => void
  mode: 'create' | 'edit'
  loading?: boolean
}

const riskLevels = [
  { value: 'low', label: '低风险', description: '年化收益期望 5-15%，最大回撤 < 10%' },
  { value: 'medium', label: '中风险', description: '年化收益期望 15-30%，最大回撤 < 20%' },
  { value: 'high', label: '高风险', description: '年化收益期望 > 30%，最大回撤可能 > 30%' }
]

const timeframes = [
  { value: '1m', label: '1分钟' },
  { value: '5m', label: '5分钟' },
  { value: '15m', label: '15分钟' },
  { value: '1h', label: '1小时' },
  { value: '4h', label: '4小时' },
  { value: '1d', label: '1天' }
]

const indicators = [
  { value: 'sma', label: '简单移动平均线', category: 'trend' },
  { value: 'ema', label: '指数移动平均线', category: 'trend' },
  { value: 'bollinger', label: '布林带', category: 'volatility' },
  { value: 'rsi', label: '相对强弱指数', category: 'momentum' },
  { value: 'macd', label: 'MACD', category: 'momentum' },
  { value: 'stochastic', label: '随机指标', category: 'momentum' },
  { value: 'atr', label: '平均真实波幅', category: 'volatility' },
  { value: 'williams', label: '威廉指标', category: 'momentum' }
]

const StrategyFormModern: React.FC<StrategyFormModernProps> = ({
  strategy,
  onSubmit,
  onCancel,
  mode,
  loading = false
}) => {
  const [formData, setFormData] = useState<Partial<Strategy>>({
    name: '',
    description: '',
    type: 'trend_following',
    riskLevel: 'medium',
    symbols: ['BTC/USDT', 'ETH/USDT'],
    timeframe: '1h',
    parameters: {},
    indicators: ['sma', 'rsi'],
    allocation: 100000,
    maxDrawdown: 20,
    targetReturn: 15,
    sharpeRatio: 1.5,
    ...strategy
  })

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isCalculating, setIsCalculating] = useState(false)
  const [expectedMetrics, setExpectedMetrics] = useState({
    annualReturn: 0,
    maxDrawdown: 0,
    sharpeRatio: 0,
    winRate: 0
  })

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const handleParameterChange = (param: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      parameters: { ...prev.parameters, [param]: value }
    }))
  }

  const addSymbol = (symbol: string) => {
    if (symbol && !formData.symbols?.includes(symbol)) {
      handleInputChange('symbols', [...(formData.symbols || []), symbol])
    }
  }

  const removeSymbol = (symbol: string) => {
    handleInputChange(
      'symbols',
      formData.symbols?.filter(s => s !== symbol) || []
    )
  }

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.name?.trim()) {
      newErrors.name = '策略名称不能为空'
    }

    if (!formData.symbols || formData.symbols.length === 0) {
      newErrors.symbols = '至少选择一个交易对'
    }

    if (!formData.allocation || formData.allocation <= 0) {
      newErrors.allocation = '初始资金必须大于0'
    }

    if (!formData.maxDrawdown || formData.maxDrawdown <= 0 || formData.maxDrawdown > 100) {
      newErrors.maxDrawdown = '最大回撤必须在0-100%之间'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    try {
      await onSubmit(formData)
    } catch (error) {
      console.error('Failed to save strategy:', error)
    }
  }

  const calculateExpectedMetrics = () => {
    setIsCalculating(true)
    // Simulate calculation
    setTimeout(() => {
      const riskMultiplier = formData.riskLevel === 'low' ? 0.7 :
                            formData.riskLevel === 'medium' ? 1 : 1.5
      const baseReturn = (formData.targetReturn || 15) * riskMultiplier
      const baseDrawdown = (formData.maxDrawdown || 20) * riskMultiplier

      setExpectedMetrics({
        annualReturn: baseReturn + Math.random() * 10 - 5,
        maxDrawdown: baseDrawdown + Math.random() * 10 - 5,
        sharpeRatio: (formData.sharpeRatio || 1.5) * riskMultiplier + Math.random() * 0.5 - 0.25,
        winRate: 45 + Math.random() * 20
      })
      setIsCalculating(false)
    }, 1500)
  }

  useEffect(() => {
    calculateExpectedMetrics()
  }, [formData.riskLevel, formData.allocation, formData.targetReturn, formData.maxDrawdown])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <Card className="shadow-lg">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center">
                {mode === 'create' ? '创建新策略' : '编辑策略'}
                {mode === 'edit' && strategy && (
                  <Badge className="ml-2" variant="secondary">
                    ID: {strategy.id}
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                {mode === 'create'
                  ? '配置您的量化交易策略参数'
                  : '修改现有策略的配置和参数'
                }
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={onCancel}>
              <X className="mr-2 h-4 w-4" />
              取消
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="basic">基础设置</TabsTrigger>
                <TabsTrigger value="parameters">策略参数</TabsTrigger>
                <TabsTrigger value="risk">风险管理</TabsTrigger>
                <TabsTrigger value="metrics">预期指标</TabsTrigger>
              </TabsList>

              {/* Basic Settings */}
              <TabsContent value="basic" className="space-y-4">
                <Grid cols={{ xs: 1, md: 2 }} gap={4}>
                  <div className="space-y-2">
                    <Label htmlFor="name">
                      策略名称 <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="name"
                      value={formData.name || ''}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      placeholder="例如：BTC趋势跟踪策略"
                      className={errors.name ? 'border-red-500' : ''}
                    />
                    {errors.name && (
                      <p className="text-sm text-red-500">{errors.name}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="type">策略类型</Label>
                    <Select
                      value={formData.type}
                      onValueChange={(value) => handleInputChange('type', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择策略类型" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="trend_following">趋势跟踪</SelectItem>
                        <SelectItem value="mean_reversion">均值回归</SelectItem>
                        <SelectItem value="arbitrage">套利</SelectItem>
                        <SelectItem value="market_making">做市商</SelectItem>
                        <SelectItem value="momentum">动量策略</SelectItem>
                        <SelectItem value="custom">自定义</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </Grid>

                <div className="space-y-2">
                  <Label htmlFor="description">策略描述</Label>
                  <Textarea
                    id="description"
                    value={formData.description || ''}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="描述策略的核心逻辑和投资理念..."
                    rows={3}
                  />
                </div>

                <Grid cols={{ xs: 1, md: 2 }} gap={4}>
                  <div className="space-y-2">
                    <Label>交易对 <span className="text-red-500">*</span></Label>
                    <div className="space-y-2">
                      <div className="flex space-x-2">
                        <Input
                          placeholder="输入交易对，如 BTC/USDT"
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault()
                              addSymbol((e.target as HTMLInputElement).value)
                              ;(e.target as HTMLInputElement).value = ''
                            }
                          }}
                        />
                        <Button
                          type="button"
                          variant="outline"
                          onClick={(e) => {
                            const input = e.currentTarget.previousElementSibling as HTMLInputElement
                            addSymbol(input.value)
                            input.value = ''
                          }}
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {formData.symbols?.map(symbol => (
                          <Badge
                            key={symbol}
                            variant="secondary"
                            className="flex items-center"
                          >
                            {symbol}
                            <button
                              type="button"
                              onClick={() => removeSymbol(symbol)}
                              className="ml-1 hover:text-red-500"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </Badge>
                        ))}
                      </div>
                      {errors.symbols && (
                        <p className="text-sm text-red-500">{errors.symbols}</p>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="timeframe">时间周期</Label>
                    <Select
                      value={formData.timeframe}
                      onValueChange={(value) => handleInputChange('timeframe', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择时间周期" />
                      </SelectTrigger>
                      <SelectContent>
                        {timeframes.map(tf => (
                          <SelectItem key={tf.value} value={tf.value}>
                            {tf.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </Grid>
              </TabsContent>

              {/* Strategy Parameters */}
              <TabsContent value="parameters" className="space-y-4">
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertTitle>策略参数配置</AlertTitle>
                  <AlertDescription>
                    根据您选择的策略类型，配置相应的技术指标和交易参数。
                  </AlertDescription>
                </Alert>

                <div className="space-y-4">
                  <Label>技术指标</Label>
                  <Grid cols={{ xs: 1, md: 2, lg: 3 }} gap={3}>
                    {indicators.map(indicator => (
                      <div key={indicator.value} className="flex items-center space-x-2">
                        <Switch
                          checked={formData.indicators?.includes(indicator.value)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              handleInputChange(
                                'indicators',
                                [...(formData.indicators || []), indicator.value]
                              )
                            } else {
                              handleInputChange(
                                'indicators',
                                formData.indicators?.filter(i => i !== indicator.value) || []
                              )
                            }
                          }}
                        />
                        <div className="flex-1">
                          <div className="text-sm font-medium">{indicator.label}</div>
                          <div className="text-xs text-muted-foreground">
                            {indicator.category === 'trend' ? '趋势' :
                             indicator.category === 'momentum' ? '动量' : '波动率'}
                          </div>
                        </div>
                      </div>
                    ))}
                  </Grid>
                </div>

                <Accordion type="single" collapsible className="w-full">
                  <AccordionItem value="advanced-params">
                    <AccordionTrigger>高级参数</AccordionTrigger>
                    <AccordionContent className="space-y-4">
                      <Grid cols={{ xs: 1, md: 2 }} gap={4}>
                        <div className="space-y-2">
                          <Label htmlFor="stopLoss">止损比例 (%)</Label>
                          <Input
                            id="stopLoss"
                            type="number"
                            step="0.1"
                            value={(formData.parameters?.stopLoss as number) || 2}
                            onChange={(e) => handleParameterChange('stopLoss', parseFloat(e.target.value))}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="takeProfit">止盈比例 (%)</Label>
                          <Input
                            id="takeProfit"
                            type="number"
                            step="0.1"
                            value={(formData.parameters?.takeProfit as number) || 5}
                            onChange={(e) => handleParameterChange('takeProfit', parseFloat(e.target.value))}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="positionSize">仓位大小 (%)</Label>
                          <Input
                            id="positionSize"
                            type="number"
                            step="1"
                            value={(formData.parameters?.positionSize as number) || 10}
                            onChange={(e) => handleParameterChange('positionSize', parseFloat(e.target.value))}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="leverage">杠杆倍数</Label>
                          <Input
                            id="leverage"
                            type="number"
                            step="0.1"
                            value={(formData.parameters?.leverage as number) || 1}
                            onChange={(e) => handleParameterChange('leverage', parseFloat(e.target.value))}
                          />
                        </div>
                      </Grid>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              </TabsContent>

              {/* Risk Management */}
              <TabsContent value="risk" className="space-y-4">
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>风险管理配置</AlertTitle>
                  <AlertDescription>
                    设置合理的风险参数，保护您的投资本金。
                  </AlertDescription>
                </Alert>

                <Grid cols={{ xs: 1, md: 2 }} gap={4}>
                  <div className="space-y-2">
                    <Label htmlFor="riskLevel">风险等级</Label>
                    <Select
                      value={formData.riskLevel}
                      onValueChange={(value) => handleInputChange('riskLevel', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择风险等级" />
                      </SelectTrigger>
                      <SelectContent>
                        {riskLevels.map(level => (
                          <SelectItem key={level.value} value={level.value}>
                            <div>
                              <div className="font-medium">{level.label}</div>
                              <div className="text-xs text-muted-foreground">
                                {level.description}
                              </div>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="allocation">
                      初始资金 (¥) <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="allocation"
                      type="number"
                      value={formData.allocation || 0}
                      onChange={(e) => handleInputChange('allocation', parseFloat(e.target.value))}
                      className={errors.allocation ? 'border-red-500' : ''}
                    />
                    {errors.allocation && (
                      <p className="text-sm text-red-500">{errors.allocation}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="maxDrawdown">
                      最大回撤 (%) <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="maxDrawdown"
                      type="number"
                      step="0.1"
                      value={formData.maxDrawdown || 0}
                      onChange={(e) => handleInputChange('maxDrawdown', parseFloat(e.target.value))}
                      className={errors.maxDrawdown ? 'border-red-500' : ''}
                    />
                    {errors.maxDrawdown && (
                      <p className="text-sm text-red-500">{errors.maxDrawdown}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="targetReturn">目标年化收益率 (%)</Label>
                    <Input
                      id="targetReturn"
                      type="number"
                      step="0.1"
                      value={formData.targetReturn || 0}
                      onChange={(e) => handleInputChange('targetReturn', parseFloat(e.target.value))}
                    />
                  </div>
                </Grid>

                <Separator />

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>启用动态止损</Label>
                      <p className="text-sm text-muted-foreground">
                        根据市场波动自动调整止损位
                      </p>
                    </div>
                    <Switch
                      checked={formData.parameters?.dynamicStopLoss as boolean}
                      onCheckedChange={(checked) => handleParameterChange('dynamicStopLoss', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label>启用仓位管理</Label>
                      <p className="text-sm text-muted-foreground">
                        根据信号强度自动调整仓位大小
                      </p>
                    </div>
                    <Switch
                      checked={formData.parameters?.positionManagement as boolean}
                      onCheckedChange={(checked) => handleParameterChange('positionManagement', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label>启用资金管理</Label>
                      <p className="text-sm text-muted-foreground">
                        控制单笔交易最大损失
                      </p>
                    </div>
                    <Switch
                      checked={formData.parameters?.capitalManagement as boolean}
                      onCheckedChange={(checked) => handleParameterChange('capitalManagement', checked)}
                    />
                  </div>
                </div>
              </TabsContent>

              {/* Expected Metrics */}
              <TabsContent value="metrics" className="space-y-4">
                <Alert>
                  <TrendingUp className="h-4 w-4" />
                  <AlertTitle>预期策略表现</AlertTitle>
                  <AlertDescription>
                    基于您的策略参数和历史回测数据，以下是预期的策略表现指标。
                  </AlertDescription>
                </Alert>

                {isCalculating ? (
                  <div className="flex items-center justify-center h-32">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    >
                      <Activity className="h-8 w-8 text-primary" />
                    </motion.div>
                  </div>
                ) : (
                  <Grid cols={{ xs: 1, md: 2, lg: 4 }} gap={4}>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">
                          预期年化收益
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-green-600">
                          {expectedMetrics.annualReturn.toFixed(2)}%
                        </div>
                        <div className="text-xs text-muted-foreground">
                          基于历史回测数据
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">
                          预期最大回撤
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-red-600">
                          {expectedMetrics.maxDrawdown.toFixed(2)}%
                        </div>
                        <div className="text-xs text-muted-foreground">
                          95%置信区间
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">
                          预期夏普比率
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-blue-600">
                          {expectedMetrics.sharpeRatio.toFixed(2)}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          风险调整后收益
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">
                          预期胜率
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-purple-600">
                          {expectedMetrics.winRate.toFixed(1)}%
                        </div>
                        <div className="text-xs text-muted-foreground">
                          交易成功率
                        </div>
                      </CardContent>
                    </Card>
                  </Grid>
                )}

                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertTitle>风险评估</AlertTitle>
                  <AlertDescription>
                    {formData.riskLevel === 'low' && '低风险策略，适合保守型投资者。'}
                    {formData.riskLevel === 'medium' && '中等风险策略，适合平衡型投资者。'}
                    {formData.riskLevel === 'high' && '高风险策略，仅适合有经验的投资者。'}
                    请确保您理解并接受相关风险。
                  </AlertDescription>
                </Alert>
              </TabsContent>
            </Tabs>

            <Separator />

            <div className="flex justify-end space-x-2">
              <Button type="button" variant="outline" onClick={onCancel}>
                取消
              </Button>
              <Button type="submit" disabled={loading} className="cbsc-primary">
                <Save className="mr-2 h-4 w-4" />
                {loading ? '保存中...' : (mode === 'create' ? '创建策略' : '保存修改')}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default StrategyFormModern