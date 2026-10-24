import React, { useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
  ScatterChart,
  Scatter,
  ComposedChart
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  Target,
  Activity,
  BarChart3,
  PieChart,
  Zap,
  Shield,
  DollarSign
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Badge } from '../ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs'
import { Progress } from '../ui/progress'
import { Grid } from '../square-ui/Grid'
import { MetricCard } from '../square-ui/MetricCard'
import { cn } from '../../lib/utils'
import { Strategy } from '../../types'

interface PerformanceData {
  date: string
  return: number
  benchmark: number
  drawdown?: number
  volatility?: number
  sharpe?: number
  winRate?: number
}

interface TradeData {
  date: string
  return: number
  risk: number
  size: number
  symbol: string
}

interface StrategyPerformanceChartProps {
  strategy: Strategy
  performanceData?: PerformanceData[]
  tradesData?: TradeData[]
  benchmarkData?: number[]
  className?: string
}

const chartColors = {
  primary: '#3b82f6',
  secondary: '#8b5cf6',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#06b6d4',
  grid: '#e5e7eb',
  text: '#6b7280'
}

const StrategyPerformanceChart: React.FC<StrategyPerformanceChartProps> = ({
  strategy,
  performanceData = [],
  tradesData = [],
  benchmarkData = [],
  className
}) => {
  // Calculate performance metrics
  const metrics = useMemo(() => {
    if (!performanceData.length) {
      return {
        totalReturn: strategy.totalReturn || 0,
        avgReturn: 0,
        maxDrawdown: strategy.maxDrawdown || 0,
        volatility: 0,
        sharpeRatio: strategy.sharpeRatio || 0,
        winRate: strategy.winRate || 0,
        annualReturn: 0
      }
    }

    const returns = performanceData.map(d => d.return)
    const totalReturn = performanceData[performanceData.length - 1]?.return || strategy.totalReturn || 0
    const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length
    const maxDrawdown = Math.min(...(performanceData.map(d => d.drawdown || 0)))
    const volatility = Math.sqrt(returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length) * Math.sqrt(252)
    const sharpeRatio = avgReturn / volatility * Math.sqrt(252)
    const winRate = tradesData.length > 0 ? tradesData.filter(t => t.return > 0).length / tradesData.length * 100 : strategy.winRate || 0

    return {
      totalReturn,
      avgReturn,
      maxDrawdown,
      volatility,
      sharpeRatio,
      winRate,
      annualReturn: totalReturn * (252 / performanceData.length)
    }
  }, [strategy, performanceData, tradesData])

  // Risk-return scatter data
  const riskReturnData = useMemo(() => {
    return [
      { name: '当前策略', return: metrics.totalReturn || 0, risk: metrics.volatility || 0, current: true },
      { name: '同类平均', return: 15.5, risk: 18.2, current: false },
      { name: '市场基准', return: 12.3, risk: 22.5, current: false },
      { name: '最佳策略', return: 35.2, risk: 15.8, current: false },
      { name: '最差策略', return: -8.5, risk: 28.3, current: false }
    ]
  }, [metrics])

  // Generate historical data
  const historicalData = useMemo(() => {
    if (performanceData.length > 0) {
      return performanceData
    }

    // Generate mock data if no real data
    const data = []
    const days = 90
    const baseValue = 10000
    let currentValue = baseValue
    const dailyReturn = (metrics.totalReturn || 0) / days

    for (let i = 0; i < days; i++) {
      const randomVolatility = (Math.random() - 0.5) * 0.02
      const dailyChange = dailyReturn / days + randomVolatility
      currentValue *= (1 + dailyChange)
      const returnPercent = ((currentValue - baseValue) / baseValue) * 100

      data.push({
        date: new Date(Date.now() - (days - i) * 24 * 60 * 60 * 1000).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
        return: returnPercent,
        benchmark: returnPercent * 0.7 + (Math.random() - 0.5) * 10,
        drawdown: Math.max(0, -Math.min(...data.slice(Math.max(0, i-30)).map(d => d.return || 0) + returnPercent))
      })
    }
    return data
  }, [performanceData, metrics.totalReturn])

  // Monthly performance data
  const monthlyData = useMemo(() => {
    const monthlyMap = new Map<string, { month: string; return: number; benchmark: number }>()

    historicalData.forEach(data => {
      const monthKey = data.date
      const existing = monthlyMap.get(monthKey) || { month: monthKey, return: 0, benchmark: 0 }
      monthlyMap.set(monthKey, {
        month: monthKey,
        return: Math.max(existing.return, data.return || 0),
        benchmark: Math.max(existing.benchmark, data.benchmark || 0)
      })
    })

    return Array.from(monthlyMap.values())
  }, [historicalData])

  // Custom tooltip for performance chart
  const PerformanceTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Card className="shadow-lg border-0 bg-background/95 backdrop-blur-sm">
          <CardContent className="p-3">
            <div className="text-sm font-medium mb-2">{label}</div>
            {payload.map((entry: any, index: number) => (
              <div key={index} className="flex items-center justify-between space-x-4">
                <div className="flex items-center space-x-1">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="text-sm">{entry.name}</span>
                </div>
                <span className="text-sm font-mono font-medium">
                  {entry.value.toFixed(2)}%
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      )
    }
    return null
  }

  // Custom tooltip for scatter chart
  const ScatterTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <Card className="shadow-lg border-0 bg-background/95 backdrop-blur-sm">
          <CardContent className="p-3">
            <div className="text-sm font-medium mb-2">{data.name}</div>
            <div className="flex items-center justify-between space-x-4">
              <span className="text-xs text-muted-foreground">收益率</span>
              <span className="text-sm font-mono font-medium">{data.return.toFixed(2)}%</span>
            </div>
            <div className="flex items-center justify-between space-x-4">
              <span className="text-xs text-muted-foreground">波动率</span>
              <span className="text-sm font-mono font-medium">{data.risk.toFixed(2)}%</span>
            </div>
          </CardContent>
        </Card>
      )
    }
    return null
  }

  // Radar chart data for strategy characteristics
  const radarData = [
    {
      subject: '收益性',
      score: Math.min(Math.abs((metrics.totalReturn || 0) / 50) * 100, 100),
      fullMark: 100
    },
    {
      subject: '稳定性',
      score: Math.max(100 - ((metrics.volatility || 0) / 30) * 100, 0),
      fullMark: 100
    },
    {
      subject: '风险控制',
      score: Math.max(100 - Math.abs((metrics.maxDrawdown || 0)) * 5, 0),
      fullMark: 100
    },
    {
      subject: '夏普比率',
      score: Math.min(((metrics.sharpeRatio || 0) / 3) * 100, 100),
      fullMark: 100
    },
    {
      subject: '胜率',
      score: metrics.winRate || 0,
      fullMark: 100
    },
    {
      subject: '资金效率',
      score: Math.min(Math.abs((metrics.annualReturn || 0) / 30) * 100, 100),
      fullMark: 100
    }
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn('space-y-6', className)}
    >
      {/* Key Metrics */}
      <Grid cols={{ xs: 2, sm: 3, lg: 6 }} gap={4}>
        <MetricCard
          title="总收益率"
          value={`${(metrics.totalReturn || 0).toFixed(2)}%`}
          icon={TrendingUp}
          valueClassName={(metrics.totalReturn || 0) > 0 ? 'text-green-600' : 'text-red-600'}
        />
        <MetricCard
          title="年化收益"
          value={`${(metrics.annualReturn || 0).toFixed(2)}%`}
          icon={DollarSign}
          valueClassName={(metrics.annualReturn || 0) > 0 ? 'text-green-600' : 'text-red-600'}
        />
        <MetricCard
          title="夏普比率"
          value={(metrics.sharpeRatio || 0).toFixed(2)}
          icon={Activity}
          valueClassName={(metrics.sharpeRatio || 0) > 1 ? 'text-green-600' : 'text-orange-600'}
        />
        <MetricCard
          title="最大回撤"
          value={`${Math.abs(metrics.maxDrawdown || 0).toFixed(2)}%`}
          icon={TrendingDown}
          valueClassName="text-red-600"
        />
        <MetricCard
          title="波动率"
          value={`${(metrics.volatility || 0).toFixed(2)}%`}
          icon={BarChart3}
          valueClassName="text-blue-600"
        />
        <MetricCard
          title="胜率"
          value={`${(metrics.winRate || 0).toFixed(1)}%`}
          icon={Target}
          valueClassName={(metrics.winRate || 0) > 50 ? 'text-green-600' : 'text-red-600'}
        />
      </Grid>

      {/* Performance Charts */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center">
            {strategy.name} - 策略表现分析
            <Badge className="ml-2" variant="outline">
              {strategy.type}
            </Badge>
          </CardTitle>
          <CardDescription>
            多维度展示策略的历史表现和风险收益特征
          </CardDescription>
        </CardHeader>

        <CardContent>
          <Tabs defaultValue="returns" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="returns">收益曲线</TabsTrigger>
              <TabsTrigger value="monthly">月度表现</TabsTrigger>
              <TabsTrigger value="risk">风险分析</TabsTrigger>
              <TabsTrigger value="characteristics">策略特征</TabsTrigger>
            </TabsList>

            {/* Returns Chart */}
            <TabsContent value="returns" className="mt-6">
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={historicalData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                    <XAxis
                      dataKey="date"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 10, fill: chartColors.text }}
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 10, fill: chartColors.text }}
                      domain={['dataMin - 5', 'dataMax + 5']}
                    />
                    <Tooltip content={<PerformanceTooltip />} />
                    <Legend />
                    <ReferenceLine y={0} stroke={chartColors.text} strokeDasharray="3 3" />
                    <Line
                      type="monotone"
                      dataKey="benchmark"
                      stroke={chartColors.text}
                      strokeWidth={2}
                      dot={false}
                      opacity={0.6}
                      name="基准"
                    />
                    <Line
                      type="monotone"
                      dataKey="return"
                      stroke={chartColors.primary}
                      strokeWidth={3}
                      dot={false}
                      name="策略收益"
                    />
                    <Area
                      type="monotone"
                      dataKey="drawdown"
                      fill={chartColors.danger}
                      fillOpacity={0.2}
                      stroke={chartColors.danger}
                      name="回撤"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </TabsContent>

            {/* Monthly Performance */}
            <TabsContent value="monthly" className="mt-6">
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={monthlyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                    <XAxis
                      dataKey="month"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 10, fill: chartColors.text }}
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tick={{ fontSize: 10, fill: chartColors.text }}
                    />
                    <Tooltip content={<PerformanceTooltip />} />
                    <Legend />
                    <Bar
                      dataKey="benchmark"
                      fill={chartColors.text}
                      opacity={0.6}
                      name="基准"
                    />
                    <Bar
                      dataKey="return"
                      fill={chartColors.primary}
                      name="策略收益"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </TabsContent>

            {/* Risk Analysis */}
            <TabsContent value="risk" className="mt-6 space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Risk-Return Scatter */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">风险收益分布</h3>
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <ScatterChart data={riskReturnData}>
                        <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                        <XAxis
                          dataKey="risk"
                          type="number"
                          name="风险"
                          axisLine={false}
                          tickLine={false}
                          tick={{ fontSize: 10, fill: chartColors.text }}
                          label={{ value: '风险 (%)', position: 'insideBottom', offset: -5 }}
                        />
                        <YAxis
                          dataKey="return"
                          type="number"
                          name="收益"
                          axisLine={false}
                          tickLine={false}
                          tick={{ fontSize: 10, fill: chartColors.text }}
                          label={{ value: '收益率 (%)', angle: -90, position: 'insideLeft' }}
                        />
                        <Tooltip content={<ScatterTooltip />} />
                        <Scatter name="策略" data={riskReturnData}>
                          {riskReturnData.map((entry, index) => (
                            <circle
                              key={`cell-${index}`}
                              r={entry.current ? 8 : 6}
                              fill={entry.current ? chartColors.primary : chartColors.secondary}
                              fillOpacity={entry.current ? 1 : 0.6}
                            />
                          ))}
                        </Scatter>
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Risk Metrics */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">风险指标</h3>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">VaR (95%)</span>
                        <span className="text-sm font-medium">-2.34%</span>
                      </div>
                      <Progress value={23.4} className="h-2" />
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">最大回撤</span>
                        <span className="text-sm font-medium text-red-600">
                          {Math.abs(metrics.maxDrawdown || 0).toFixed(2)}%
                        </span>
                      </div>
                      <Progress value={Math.abs(metrics.maxDrawdown || 0) * 5} className="h-2" />
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">波动率</span>
                        <span className="text-sm font-medium text-blue-600">
                          {(metrics.volatility || 0).toFixed(2)}%
                        </span>
                      </div>
                      <Progress value={(metrics.volatility || 0) * 3} className="h-2" />
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Beta系数</span>
                        <span className="text-sm font-medium">0.85</span>
                      </div>
                      <Progress value={85} className="h-2" />
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">相关性</span>
                        <span className="text-sm font-medium">0.62</span>
                      </div>
                      <Progress value={62} className="h-2" />
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* Strategy Characteristics */}
            <TabsContent value="characteristics" className="mt-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Radar Chart */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">策略雷达图</h3>
                  <div className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={radarData}>
                        <PolarGrid stroke={chartColors.grid} />
                        <PolarAngleAxis
                          dataKey="subject"
                          tick={{ fontSize: 12, fill: chartColors.text }}
                        />
                        <PolarRadiusAxis
                          angle={90}
                          domain={[0, 100]}
                          tick={{ fontSize: 10, fill: chartColors.text }}
                        />
                        <Radar
                          name="策略评分"
                          dataKey="score"
                          stroke={chartColors.primary}
                          fill={chartColors.primary}
                          fillOpacity={0.2}
                          strokeWidth={2}
                        />
                        <Tooltip />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Performance Distribution */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">表现分布</h3>
                  <div className="space-y-4">
                    {tradesData.length > 0 && (
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">平均盈亏</span>
                          <span className="text-sm font-medium text-green-600">
                            +{(tradesData.reduce((sum, t) => sum + t.return, 0) / tradesData.length).toFixed(2)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">最大盈利</span>
                          <span className="text-sm font-medium text-green-600">
                            +{Math.max(...tradesData.map(t => t.return)).toFixed(2)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">最大亏损</span>
                          <span className="text-sm font-medium text-red-600">
                            {Math.min(...tradesData.map(t => t.return)).toFixed(2)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">盈亏比</span>
                          <span className="text-sm font-medium">
                            {(Math.max(...tradesData.map(t => t.return)) / Math.abs(Math.min(...tradesData.map(t => t.return)))).toFixed(2)}
                          </span>
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-4 mt-6">
                      <Card>
                        <CardContent className="p-4 text-center">
                          <Zap className="h-8 w-8 mx-auto mb-2 text-yellow-500" />
                          <div className="text-2xl font-bold">{tradesData.length || 0}</div>
                          <div className="text-sm text-muted-foreground">总交易次数</div>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="p-4 text-center">
                          <Shield className="h-8 w-8 mx-auto mb-2 text-blue-500" />
                          <div className="text-2xl font-bold">{(metrics.winRate || 0).toFixed(0)}%</div>
                          <div className="text-sm text-muted-foreground">胜率</div>
                        </CardContent>
                      </Card>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default StrategyPerformanceChart