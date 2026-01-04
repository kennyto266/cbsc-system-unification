import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select } from '@/components/ui/select'
import type { SelectOption } from '@/components/ui/select'
import {
  AlertTriangle,
  Shield,
  TrendingDown,
  Activity,
  DollarSign,
  BarChart3,
  Eye,
  Settings,
  ArrowUpRight,
  ArrowDownRight,
  Zap,
  Target,
  LineChart,
} from 'lucide-react'

// Time range options
const TIME_OPTIONS: SelectOption[] = [
  { value: '1D', label: '1天' },
  { value: '1W', label: '1周' },
  { value: '1M', label: '1月' },
  { value: '3M', label: '3月' },
]

// Mock data for risk metrics
interface RiskMetric {
  label: string
  value: string
  change: string
  trend: 'up' | 'down' | 'neutral'
  status: 'safe' | 'warning' | 'critical'
}

interface RiskAlert {
  id: string
  type: 'position' | 'leverage' | 'drawdown' | 'correlation'
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  timestamp: string
  action?: string
}

// Format currency
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

// Get status color
const getStatusColor = (status: string) => {
  switch (status) {
    case 'safe':
      return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
    case 'warning':
      return 'bg-amber-500/10 text-amber-500 border-amber-500/20'
    case 'critical':
      return 'bg-rose-500/10 text-rose-500 border-rose-500/20'
    default:
      return 'bg-neutral-500/10 text-neutral-500 border-neutral-500/20'
  }
}

// Get severity color
const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'low':
      return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
    case 'medium':
      return 'bg-amber-500/10 text-amber-500 border-amber-500/20'
    case 'high':
      return 'bg-orange-500/10 text-orange-500 border-orange-500/20'
    case 'critical':
      return 'bg-rose-500/10 text-rose-500 border-rose-500/20'
    default:
      return 'bg-neutral-500/10 text-neutral-500 border-neutral-500/20'
  }
}

export default function RiskManagement() {
  const [timeRange, setTimeRange] = useState('1M')
  const [riskMetrics, setRiskMetrics] = useState<RiskMetric[]>([])
  const [alerts, setAlerts] = useState<RiskAlert[]>([])

  // Mock data - in production, fetch from API
  useEffect(() => {
    setRiskMetrics([
      {
        label: '總風險暴露',
        value: formatCurrency(2580000),
        change: '+5.2%',
        trend: 'up',
        status: 'warning',
      },
      {
        label: '最大回撤',
        value: '-12.8%',
        change: '-2.1%',
        trend: 'down',
        status: 'critical',
      },
      {
        label: 'VaR (95%)',
        value: formatCurrency(185000),
        change: '+3.5%',
        trend: 'up',
        status: 'safe',
      },
      {
        label: '夏普比率',
        value: '1.85',
        change: '+0.12',
        trend: 'up',
        status: 'safe',
      },
      {
        label: '波動率',
        value: '18.5%',
        change: '+1.8%',
        trend: 'up',
        status: 'warning',
      },
      {
        label: '貝塔係數',
        value: '0.95',
        change: '-0.03',
        trend: 'down',
        status: 'safe',
      },
    ])

    setAlerts([
      {
        id: '1',
        type: 'drawdown',
        severity: 'high',
        message: 'Technology sector exceeded maximum drawdown limit (-12%)',
        timestamp: '2 hours ago',
        action: 'Review positions',
      },
      {
        id: '2',
        type: 'leverage',
        severity: 'medium',
        message: 'Portfolio leverage at 2.1x, approaching limit of 2.5x',
        timestamp: '5 hours ago',
        action: 'Adjust leverage',
      },
      {
        id: '3',
        type: 'correlation',
        severity: 'low',
        message: 'High correlation detected between AAPL and MSFT positions',
        timestamp: '1 day ago',
      },
    ])
  }, [timeRange])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              風險管理
            </h1>
            <p className="text-slate-400">實時監控和分析投資組合風險指標</p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800">
              <Settings className="mr-2 h-4 w-4" />
              設置
            </Button>
            <Button className="bg-blue-600 hover:bg-blue-700">
              <BarChart3 className="mr-2 h-4 w-4" />
              生成報告
            </Button>
          </div>
        </div>
      </div>

      {/* Risk Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {riskMetrics.map((metric, index) => (
          <Card
            key={index}
            className="bg-slate-900/50 border-slate-800 backdrop-blur-sm overflow-hidden group hover:border-slate-700 transition-all duration-300"
            style={{
              animation: `fadeIn 0.3s ease-out ${index * 0.1}s both`,
            }}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-slate-400">
                  {metric.label}
                </CardTitle>
                <Badge className={getStatusColor(metric.status)}>
                  {metric.status === 'safe' && '安全'}
                  {metric.status === 'warning' && '警告'}
                  {metric.status === 'critical' && '危險'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-2xl font-bold text-white mb-1" style={{ fontFamily: 'JetBrains Mono, monospace' }}>
                    {metric.value}
                  </p>
                  <div className="flex items-center gap-1">
                    {metric.trend === 'up' ? (
                      <ArrowUpRight className="h-4 w-4 text-emerald-500" />
                    ) : metric.trend === 'down' ? (
                      <ArrowDownRight className="h-4 w-4 text-rose-500" />
                    ) : null}
                    <span className={`text-sm ${
                      metric.trend === 'up' ? 'text-emerald-500' :
                      metric.trend === 'down' ? 'text-rose-500' :
                      'text-slate-400'
                    }`}>
                      {metric.change}
                    </span>
                  </div>
                </div>
                <div className={`p-2 rounded-lg ${
                  metric.status === 'critical' ? 'bg-rose-500/10' :
                  metric.status === 'warning' ? 'bg-amber-500/10' :
                  'bg-emerald-500/10'
                }`}>
                  {metric.label.includes('風險') && <Shield className="h-5 w-5 text-blue-500" />}
                  {metric.label.includes('回撤') && <TrendingDown className="h-5 w-5 text-rose-500" />}
                  {metric.label.includes('VaR') && <Activity className="h-5 w-5 text-purple-500" />}
                  {metric.label.includes('夏普') && <LineChart className="h-5 w-5 text-emerald-500" />}
                  {metric.label.includes('波動') && <Zap className="h-5 w-5 text-amber-500" />}
                  {metric.label.includes('貝塔') && <Target className="h-5 w-5 text-blue-500" />}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content */}
      <Tabs defaultValue="overview" className="space-y-6">
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-1 inline-flex">
          <TabsList className="bg-transparent border-0 gap-1">
            <TabsTrigger
              value="overview"
              className="data-[state=active]:bg-slate-800 data-[state=active]:text-white text-slate-400"
            >
              概覽
            </TabsTrigger>
            <TabsTrigger
              value="positions"
              className="data-[state=active]:bg-slate-800 data-[state=active]:text-white text-slate-400"
            >
              持倉風險
            </TabsTrigger>
            <TabsTrigger
              value="correlation"
              className="data-[state=active]:bg-slate-800 data-[state=active]:text-white text-slate-400"
            >
              相關性分析
            </TabsTrigger>
            <TabsTrigger
              value="alerts"
              className="data-[state=active]:bg-slate-800 data-[state=active]:text-white text-slate-400"
            >
              警報中心
              {alerts.filter(a => a.severity === 'high' || a.severity === 'critical').length > 0 && (
                <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-rose-500 text-white">
                  {alerts.filter(a => a.severity === 'high' || a.severity === 'critical').length}
                </span>
              )}
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="overview" className="space-y-6">
          {/* Chart Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white">風險分布</CardTitle>
                  <Select
                    options={TIME_OPTIONS}
                    value={timeRange}
                    onChange={setTimeRange}
                    size="sm"
                    fullWidth={false}
                    className="w-20"
                  />
                </div>
                <CardDescription className="text-slate-400">
                  各類型風險的分布情況
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center border border-dashed border-slate-700 rounded-lg">
                  <div className="text-center">
                    <BarChart3 className="h-12 w-12 text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-500 text-sm">圖表數據加載中...</p>
                    <p className="text-slate-600 text-xs mt-1">連接至分析 API</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white">回撤分析</CardTitle>
                <CardDescription className="text-slate-400">
                  歷史回撤趨勢與預測
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center border border-dashed border-slate-700 rounded-lg">
                  <div className="text-center">
                    <LineChart className="h-12 w-12 text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-500 text-sm">圖表數據加載中...</p>
                    <p className="text-slate-600 text-xs mt-1">連接至分析 API</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="positions" className="space-y-6">
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="text-white">持倉風險明細</CardTitle>
              <CardDescription className="text-slate-400">
                單個持倉的風險貢獻分析
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12">
                <Eye className="h-12 w-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">持倉風險數據加載中...</p>
                <p className="text-slate-600 text-xs mt-1">連接至持倉 API</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="correlation" className="space-y-6">
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="text-white">相關性矩陣</CardTitle>
              <CardDescription className="text-slate-400">
                資產間的相關性分析
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12">
                <Activity className="h-12 w-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">相關性數據加載中...</p>
                <p className="text-slate-600 text-xs mt-1">連接至分析 API</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-6">
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-white">風險警報</CardTitle>
                  <CardDescription className="text-slate-400">
                    當前有 {alerts.length} 個活躍警報
                  </CardDescription>
                </div>
                <Button variant="outline" size="sm" className="border-slate-700 text-slate-300">
                  全部標記已讀
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="p-4 rounded-lg border bg-slate-800/50 hover:bg-slate-800 transition-colors cursor-pointer"
                  style={{ animation: `fadeIn 0.3s ease-out ${alert.id === '1' ? '0.1s' : alert.id === '2' ? '0.2s' : '0.3s'} both` }}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4" />
                      <span className="text-sm font-medium text-white">
                        {alert.type === 'position' && '持倉警報'}
                        {alert.type === 'leverage' && '槓桿警報'}
                        {alert.type === 'drawdown' && '回撤警報'}
                        {alert.type === 'correlation' && '相關性警報'}
                      </span>
                    </div>
                    <Badge className={getSeverityColor(alert.severity)}>
                      {alert.severity === 'low' && '低'}
                      {alert.severity === 'medium' && '中'}
                      {alert.severity === 'high' && '高'}
                      {alert.severity === 'critical' && '嚴重'}
                    </Badge>
                  </div>
                  <p className="text-sm text-slate-300 mb-3">{alert.message}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-500">{alert.timestamp}</span>
                    {alert.action && (
                      <Button variant="outline" size="sm" className="h-7 text-xs border-slate-700 text-slate-300 hover:bg-slate-700">
                        {alert.action}
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
