import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play,
  Pause,
  Square,
  Edit,
  Settings,
  TrendingUp,
  TrendingDown,
  Activity,
  Calendar,
  DollarSign,
  BarChart3,
  Target,
  AlertCircle,
  Download,
  RefreshCw,
  Eye,
  ArrowUpRight,
  ArrowDownRight,
  Minus
} from 'lucide-react'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Badge } from '../../components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '../../components/ui/avatar'
import { Progress } from '../../components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table'
import { Grid } from '../square-ui/Grid'
import { MetricCard } from '../square-ui/MetricCard'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { cn } from '../../lib/utils'
import { Strategy, StrategyStatus, StrategyPerformance } from '../../types'

interface StrategyDetailsModernProps {
  strategyId: string
  onEdit: (strategy: Strategy) => void
  onStatusChange: (strategyId: string, newStatus: StrategyStatus) => Promise<void>
}

const statusConfig = {
  active: {
    label: '运行中',
    color: 'bg-green-500',
    textColor: 'text-green-700',
    bgColor: 'bg-green-50',
    icon: Play
  },
  testing: {
    label: '测试中',
    color: 'bg-orange-500',
    textColor: 'text-orange-700',
    bgColor: 'bg-orange-50',
    icon: Settings
  },
  inactive: {
    label: '已暂停',
    color: 'bg-gray-500',
    textColor: 'text-gray-700',
    bgColor: 'bg-gray-50',
    icon: Pause
  },
  stopped: {
    label: '已停止',
    color: 'bg-red-500',
    textColor: 'text-red-700',
    bgColor: 'bg-red-50',
    icon: Square
  }
}

// Mock data - in real app, this would come from API
const mockStrategy: Strategy = {
  id: 'strategy_001',
  name: 'BTC趋势跟踪策略',
  description: '基于移动平均线的比特币趋势跟踪策略，在上升趋势中做多，下降趋势中做空',
  type: 'trend_following',
  status: 'active',
  riskLevel: 'medium',
  symbols: ['BTC/USDT', 'ETH/USDT'],
  timeframe: '1h',
  allocation: 100000,
  totalReturn: 23.45,
  sharpeRatio: 1.68,
  maxDrawdown: 12.34,
  winRate: 68.5,
  dailyReturn: 0.12,
  weeklyReturn: 0.89,
  monthlyReturn: 3.21,
  createdAt: '2024-01-15',
  updatedAt: '2024-12-17',
  parameters: {
    stopLoss: 2,
    takeProfit: 5,
    positionSize: 10,
    leverage: 2,
    fastMA: 20,
    slowMA: 50,
    rsiPeriod: 14,
    rsiOverbought: 70,
    rsiOversold: 30
  },
  indicators: ['sma', 'rsi', 'macd']
}

const mockPerformanceData = [
  { date: '2024-01', return: 2.3, benchmark: 1.2 },
  { date: '2024-02', return: 3.1, benchmark: 0.8 },
  { date: '2024-03', return: -1.2, benchmark: -0.5 },
  { date: '2024-04', return: 4.5, benchmark: 2.1 },
  { date: '2024-05', return: 2.8, benchmark: 1.5 },
  { date: '2024-06', return: 5.2, benchmark: 2.8 },
  { date: '2024-07', return: 3.9, benchmark: 1.9 },
  { date: '2024-08', return: -0.8, benchmark: -1.2 },
  { date: '2024-09', return: 4.1, benchmark: 2.3 },
  { date: '2024-10', return: 6.2, benchmark: 3.1 },
  { date: '2024-11', return: 2.5, benchmark: 1.4 },
  { date: '2024-12', return: 1.8, benchmark: 0.9 }
]

const mockDrawdownData = [
  { date: '2024-01', drawdown: 0 },
  { date: '2024-02', drawdown: 0 },
  { date: '2024-03', drawdown: 8.2 },
  { date: '2024-04', drawdown: 5.1 },
  { date: '2024-05', drawdown: 3.8 },
  { date: '2024-06', drawdown: 0 },
  { date: '2024-07', drawdown: 0 },
  { date: '2024-08', drawdown: 6.9 },
  { date: '2024-09', drawdown: 4.2 },
  { date: '2024-10', drawdown: 0 },
  { date: '2024-11', drawdown: 2.1 },
  { date: '2024-12', drawdown: 1.5 }
]

const mockTradeHistory = [
  {
    id: 'trade_001',
    date: '2024-12-17 14:30:00',
    symbol: 'BTC/USDT',
    side: 'buy',
    price: 43250.00,
    quantity: 0.1,
    amount: 4325.00,
    fee: 4.33,
    pnl: 125.50,
    status: 'closed'
  },
  {
    id: 'trade_002',
    date: '2024-12-17 13:45:00',
    symbol: 'ETH/USDT',
    side: 'sell',
    price: 2250.00,
    quantity: 2,
    amount: 4500.00,
    fee: 4.50,
    pnl: -35.20,
    status: 'closed'
  },
  {
    id: 'trade_003',
    date: '2024-12-17 12:20:00',
    symbol: 'BTC/USDT',
    side: 'buy',
    price: 42800.00,
    quantity: 0.15,
    amount: 6420.00,
    fee: 6.42,
    pnl: 0,
    status: 'open'
  }
]

const mockAllocationData = [
  { name: 'BTC/USDT', value: 60, color: '#f59e0b' },
  { name: 'ETH/USDT', value: 30, color: '#8b5cf6' },
  { name: '现金', value: 10, color: '#10b981' }
]

const StrategyDetailsModern: React.FC<StrategyDetailsModernProps> = ({
  strategyId,
  onEdit,
  onStatusChange
}) => {
  const [strategy, setStrategy] = useState<Strategy>(mockStrategy)
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [realTimeData, setRealTimeData] = useState(mockPerformanceData)

  const status = statusConfig[strategy.status]
  const StatusIcon = status.icon

  useEffect(() => {
    // Simulate real-time data updates
    const interval = setInterval(() => {
      if (strategy.status === 'active') {
        // Update last data point with simulated real-time changes
        setRealTimeData(prev => {
          const newData = [...prev]
          const lastPoint = newData[newData.length - 1]
          if (lastPoint) {
            lastPoint.return = lastPoint.return + (Math.random() - 0.5) * 0.1
          }
          return newData
        })
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [strategy.status])

  const handleStatusChange = async () => {
    setIsLoading(true)
    try {
      let newStatus: StrategyStatus
      switch (strategy.status) {
        case 'active':
          newStatus = 'inactive'
          break
        case 'inactive':
        case 'stopped':
          newStatus = 'active'
          break
        default:
          newStatus = 'active'
      }

      await onStatusChange(strategyId, newStatus)
      setStrategy(prev => ({ ...prev, status: newStatus }))
    } catch (error) {
      console.error('Failed to change status:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY'
    }).format(value)
  }

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Strategy Header */}
      <Card className="shadow-lg">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-4">
              <Avatar className="h-16 w-16">
                <AvatarImage src={`/api/strategies/${strategy.id}/avatar`} />
                <AvatarFallback className="text-xl">
                  {strategy.name.slice(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <CardTitle className="text-2xl">{strategy.name}</CardTitle>
                <CardDescription className="mt-2">
                  {strategy.description}
                </CardDescription>
                <div className="mt-3 flex items-center space-x-4">
                  <Badge className={cn(status.textColor, status.bgColor)}>
                    <StatusIcon className="mr-1 h-3 w-3" />
                    {status.label}
                  </Badge>
                  <Badge variant="outline">
                    {strategy.type === 'trend_following' ? '趋势跟踪' :
                     strategy.type === 'mean_reversion' ? '均值回归' :
                     strategy.type === 'arbitrage' ? '套利' :
                     strategy.type === 'market_making' ? '做市商' :
                     strategy.type === 'momentum' ? '动量' : '自定义'}
                  </Badge>
                  <Badge variant={strategy.riskLevel === 'low' ? 'secondary' :
                                 strategy.riskLevel === 'medium' ? 'default' : 'destructive'}>
                    {strategy.riskLevel === 'low' ? '低风险' :
                     strategy.riskLevel === 'medium' ? '中风险' : '高风险'}
                  </Badge>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                onClick={() => onEdit(strategy)}
              >
                <Edit className="mr-2 h-4 w-4" />
                编辑
              </Button>
              <Button
                onClick={handleStatusChange}
                disabled={isLoading}
                className={cn(
                  strategy.status === 'active' ? 'bg-orange-500 hover:bg-orange-600' :
                  strategy.status === 'inactive' || strategy.status === 'stopped' ? 'bg-green-500 hover:bg-green-600' :
                  'bg-red-500 hover:bg-red-600',
                  'text-white'
                )}
              >
                {isLoading ? (
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  strategy.status === 'active' ? (
                    <Pause className="mr-2 h-4 w-4" />
                  ) : (
                    <Play className="mr-2 h-4 w-4" />
                  )
                )}
                {strategy.status === 'active' ? '暂停' :
                 strategy.status === 'inactive' || strategy.status === 'stopped' ? '启动' : '停止'}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Key Metrics */}
      <Grid cols={{ xs: 2, sm: 3, lg: 6 }} gap={4}>
        <MetricCard
          title="总收益率"
          value={formatPercent(strategy.totalReturn)}
          icon={strategy.totalReturn > 0 ? TrendingUp : TrendingDown}
          valueClassName={strategy.totalReturn > 0 ? 'text-green-600' : 'text-red-600'}
          trend={formatPercent(strategy.weeklyReturn)}
          trendUp={strategy.weeklyReturn > 0}
        />
        <MetricCard
          title="夏普比率"
          value={strategy.sharpeRatio.toFixed(2)}
          icon={BarChart3}
          valueClassName={strategy.sharpeRatio > 1 ? 'text-green-600' : 'text-orange-600'}
        />
        <MetricCard
          title="最大回撤"
          value={formatPercent(strategy.maxDrawdown)}
          icon={TrendingDown}
          valueClassName="text-red-600"
        />
        <MetricCard
          title="胜率"
          value={`${strategy.winRate}%`}
          icon={Target}
          valueClassName={strategy.winRate > 50 ? 'text-green-600' : 'text-red-600'}
        />
        <MetricCard
          title="初始资金"
          value={formatCurrency(strategy.allocation)}
          icon={DollarSign}
        />
        <MetricCard
          title="运行天数"
          value={Math.floor((Date.now() - new Date(strategy.createdAt).getTime()) / (1000 * 60 * 60 * 24))}
          icon={Calendar}
        />
      </Grid>

      {/* Detailed Information */}
      <Card className="shadow-lg">
        <CardContent className="p-0">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="m-0">
            <TabsList className="grid w-full grid-cols-6 bg-transparent p-0">
              <TabsTrigger value="overview">概览</TabsTrigger>
              <TabsTrigger value="performance">表现</TabsTrigger>
              <TabsTrigger value="trades">交易记录</TabsTrigger>
              <TabsTrigger value="allocation">资金分配</TabsTrigger>
              <TabsTrigger value="parameters">参数</TabsTrigger>
              <TabsTrigger value="risk">风险分析</TabsTrigger>
            </TabsList>

            <AnimatePresence mode="wait">
              {/* Overview Tab */}
              <TabsContent value="overview" className="mt-6 p-6">
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <Grid cols={{ xs: 1, lg: 2 }} gap={6}>
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">策略信息</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">策略类型</span>
                          <span>
                            {strategy.type === 'trend_following' ? '趋势跟踪' :
                             strategy.type === 'mean_reversion' ? '均值回归' :
                             strategy.type === 'arbitrage' ? '套利' :
                             strategy.type === 'market_making' ? '做市商' :
                             strategy.type === 'momentum' ? '动量策略' : '自定义'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">时间周期</span>
                          <span>{strategy.timeframe}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">交易对</span>
                          <div className="flex flex-wrap gap-1">
                            {strategy.symbols.map(symbol => (
                              <Badge key={symbol} variant="outline" className="text-xs">
                                {symbol}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">创建时间</span>
                          <span>{new Date(strategy.createdAt).toLocaleDateString('zh-CN')}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">最后更新</span>
                          <span>{new Date(strategy.updatedAt).toLocaleDateString('zh-CN')}</span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">技术指标</h3>
                      <div className="flex flex-wrap gap-2">
                        {strategy.indicators.map(indicator => (
                          <Badge key={indicator} variant="secondary">
                            {indicator === 'sma' ? 'SMA' :
                             indicator === 'ema' ? 'EMA' :
                             indicator === 'bollinger' ? '布林带' :
                             indicator === 'rsi' ? 'RSI' :
                             indicator === 'macd' ? 'MACD' :
                             indicator === 'stochastic' ? 'KDJ' :
                             indicator === 'atr' ? 'ATR' :
                             indicator === 'williams' ? 'WR' : indicator}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </Grid>
                </motion.div>
              </TabsContent>

              {/* Performance Tab */}
              <TabsContent value="performance" className="mt-6 p-6">
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="space-y-6"
                >
                  <div>
                    <h3 className="text-lg font-semibold mb-4">累计收益率</h3>
                    <div className="h-[300px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={realTimeData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis />
                          <Tooltip formatter={(value) => [`${value}%`, '收益率']} />
                          <Area
                            type="monotone"
                            dataKey="return"
                            stroke="#10b981"
                            fill="#10b981"
                            fillOpacity={0.3}
                          />
                          <Area
                            type="monotone"
                            dataKey="benchmark"
                            stroke="#6b7280"
                            fill="#6b7280"
                            fillOpacity={0.1}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold mb-4">回撤分析</h3>
                    <div className="h-[200px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={mockDrawdownData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis />
                          <Tooltip formatter={(value) => [`${value}%`, '回撤']} />
                          <Area
                            type="monotone"
                            dataKey="drawdown"
                            stroke="#ef4444"
                            fill="#ef4444"
                            fillOpacity={0.3}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </motion.div>
              </TabsContent>

              {/* Trades Tab */}
              <TabsContent value="trades" className="mt-6 p-6">
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>时间</TableHead>
                          <TableHead>交易对</TableHead>
                          <TableHead>方向</TableHead>
                          <TableHead>价格</TableHead>
                          <TableHead>数量</TableHead>
                          <TableHead>金额</TableHead>
                          <TableHead>手续费</TableHead>
                          <TableHead>盈亏</TableHead>
                          <TableHead>状态</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {mockTradeHistory.map((trade) => (
                          <TableRow key={trade.id}>
                            <TableCell className="text-sm">
                              {new Date(trade.date).toLocaleString('zh-CN')}
                            </TableCell>
                            <TableCell>{trade.symbol}</TableCell>
                            <TableCell>
                              <Badge variant={trade.side === 'buy' ? 'default' : 'destructive'}>
                                {trade.side === 'buy' ? '买入' : '卖出'}
                              </Badge>
                            </TableCell>
                            <TableCell>¥{trade.price.toLocaleString()}</TableCell>
                            <TableCell>{trade.quantity}</TableCell>
                            <TableCell>¥{trade.amount.toLocaleString()}</TableCell>
                            <TableCell>¥{trade.fee}</TableCell>
                            <TableCell className={trade.pnl > 0 ? 'text-green-600' : trade.pnl < 0 ? 'text-red-600' : ''}>
                              {trade.pnl !== 0 && formatPercent(trade.pnl / trade.amount * 100)}
                            </TableCell>
                            <TableCell>
                              <Badge variant={trade.status === 'open' ? 'secondary' : 'outline'}>
                                {trade.status === 'open' ? '开仓' : '平仓'}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </motion.div>
              </TabsContent>

              {/* Allocation Tab */}
              <TabsContent value="allocation" className="mt-6 p-6">
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="h-[400px] flex items-center justify-center">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={mockAllocationData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={120}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {mockAllocationData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => [`${value}%`, '占比']} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>

                  <div className="mt-6 space-y-3">
                    {mockAllocationData.map((item) => (
                      <div key={item.name} className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: item.color }}
                          />
                          <span>{item.name}</span>
                        </div>
                        <span className="font-medium">{item.value}%</span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              </TabsContent>

              {/* Parameters Tab */}
              <TabsContent value="parameters" className="mt-6 p-6">
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <Grid cols={{ xs: 1, md: 2 }} gap={6}>
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">交易参数</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">止损比例</span>
                          <span>{strategy.parameters.stopLoss}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">止盈比例</span>
                          <span>{strategy.parameters.takeProfit}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">仓位大小</span>
                          <span>{strategy.parameters.positionSize}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">杠杆倍数</span>
                          <span>{strategy.parameters.leverage}x</span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">技术指标参数</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">快速移动平均</span>
                          <span>{strategy.parameters.fastMA}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">慢速移动平均</span>
                          <span>{strategy.parameters.slowMA}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">RSI周期</span>
                          <span>{strategy.parameters.rsiPeriod}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">RSI超买</span>
                          <span>{strategy.parameters.rsiOverbought}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">RSI超卖</span>
                          <span>{strategy.parameters.rsiOversold}</span>
                        </div>
                      </div>
                    </div>
                  </Grid>
                </motion.div>
              </TabsContent>

              {/* Risk Analysis Tab */}
              <TabsContent value="risk" className="mt-6 p-6">
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="space-y-6"
                >
                  <Grid cols={{ xs: 1, md: 2, lg: 3 }} gap={4}>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">
                          VaR (95%)
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-red-600">-2.34%</div>
                        <div className="text-xs text-muted-foreground">
                          日风险价值
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">
                          Beta系数
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">0.85</div>
                        <div className="text-xs text-muted-foreground">
                          相对市场风险
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">
                          波动率
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">18.5%</div>
                        <div className="text-xs text-muted-foreground">
                          年化波动率
                        </div>
                      </CardContent>
                    </Card>
                  </Grid>

                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">风险评估</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span>整体风险等级</span>
                        <Badge variant={strategy.riskLevel === 'low' ? 'secondary' :
                                       strategy.riskLevel === 'medium' ? 'default' : 'destructive'}>
                          {strategy.riskLevel === 'low' ? '低风险' :
                           strategy.riskLevel === 'medium' ? '中风险' : '高风险'}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>集中度风险</span>
                        <div className="flex items-center space-x-2">
                          <Progress value={60} className="w-24" />
                          <span className="text-sm">60%</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>流动性风险</span>
                        <div className="flex items-center space-x-2">
                          <Progress value={30} className="w-24" />
                          <span className="text-sm">30%</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>杠杆风险</span>
                        <div className="flex items-center space-x-2">
                          <Progress value={40} className="w-24" />
                          <span className="text-sm">40%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              </TabsContent>
            </AnimatePresence>
          </Tabs>
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default StrategyDetailsModern