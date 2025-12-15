import React, { useState, useEffect } from 'react'
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Clock,
  AlertTriangle,
  CheckCircle,
  Eye
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Badge } from '../ui/badge'
import { Progress } from '../ui/progress'
import { cn } from '../../lib/utils'

// 模拟实时数据
interface MarketData {
  symbol: string
  price: number
  change: number
  changePercent: number
  volume: string
  lastUpdate: Date
}

interface SystemStatus {
  status: 'healthy' | 'warning' | 'error'
  message: string
  timestamp: Date
}

const RealTimeMonitor: React.FC = () => {
  const [marketData, setMarketData] = useState<MarketData[]>([
    { symbol: 'AAPL', price: 178.45, change: 2.15, changePercent: 1.22, volume: '45.2M', lastUpdate: new Date() },
    { symbol: 'MSFT', price: 412.33, change: -1.87, changePercent: -0.45, volume: '23.8M', lastUpdate: new Date() },
    { symbol: 'GOOGL', price: 142.56, change: 0.89, changePercent: 0.63, volume: '28.4M', lastUpdate: new Date() },
    { symbol: 'AMZN', price: 155.78, change: 3.42, changePercent: 2.24, volume: '51.6M', lastUpdate: new Date() }
  ])

  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    status: 'healthy',
    message: '所有系统正常运行',
    timestamp: new Date()
  })

  const [isConnected, setIsConnected] = useState(true)

  // 模拟实时数据更新
  useEffect(() => {
    if (!isConnected) return

    const interval = setInterval(() => {
      // 更新市场数据
      setMarketData(prev =>
        prev.map(stock => ({
          ...stock,
          price: stock.price + (Math.random() - 0.5) * 2,
          change: (Math.random() - 0.5) * 5,
          changePercent: (Math.random() - 0.5) * 2,
          lastUpdate: new Date()
        }))
      )

      // 随机更新系统状态
      if (Math.random() < 0.1) {
        const statuses: SystemStatus[] = [
          { status: 'healthy', message: '所有系统正常运行', timestamp: new Date() },
          { status: 'warning', message: 'API响应时间略高', timestamp: new Date() },
          { status: 'error', message: '数据连接异常', timestamp: new Date() }
        ]
        setSystemStatus(statuses[Math.floor(Math.random() * statuses.length)])
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [isConnected])

  // 格式化时间
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('zh-CN')
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'error':
        return <Activity className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return <Badge variant="default" className="bg-green-100 text-green-800">正常</Badge>
      case 'warning':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">警告</Badge>
      case 'error':
        return <Badge variant="destructive">错误</Badge>
      default:
        return <Badge variant="outline">未知</Badge>
    }
  }

  return (
    <div className="space-y-4 h-full">
      {/* 连接状态 */}
      <div className="flex items-center justify-between p-3 bg-card border border-border rounded-lg">
        <div className="flex items-center space-x-2">
          <div className={cn(
            "w-2 h-2 rounded-full",
            isConnected ? "bg-green-500" : "bg-red-500"
          )} />
          <span className="text-sm font-medium">
            {isConnected ? '已连接' : '已断开'}
          </span>
        </div>
        <Eye className="h-4 w-4 text-muted-foreground" />
      </div>

      {/* 系统状态 */}
      <div className="p-4 bg-card border border-border rounded-lg">
        <div className="flex items-center space-x-3">
          {getStatusIcon(systemStatus.status)}
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-1">
              <span className="text-sm font-medium">系统状态</span>
              {getStatusBadge(systemStatus.status)}
            </div>
            <p className="text-xs text-muted-foreground">{systemStatus.message}</p>
            <p className="text-xs text-muted-foreground">
              {formatTime(systemStatus.timestamp)}
            </p>
          </div>
        </div>
      </div>

      {/* 实时价格 */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold px-1">实时价格</h4>
        {marketData.map((stock, index) => (
          <div
            key={stock.symbol}
            className="flex items-center justify-between p-3 bg-card border border-border rounded-lg hover:bg-accent/50 transition-colors"
          >
            <div>
              <div className="flex items-center space-x-3">
                <span className="text-sm font-mono font-medium">{stock.symbol}</span>
                <span className="text-lg font-semibold">${stock.price.toFixed(2)}</span>
              </div>
              <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                <span className={stock.change >= 0 ? 'text-green-600' : 'text-red-600'}>
                  {stock.change >= 0 ? '▲' : '▼'} {Math.abs(stock.change).toFixed(2)}
                </span>
                <span className={stock.changePercent >= 0 ? 'text-green-600' : 'text-red-600'}>
                  ({stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%)
                </span>
                <span>成交量: {stock.volume}</span>
              </div>
            </div>

            <div className="text-xs text-muted-foreground">
              {formatTime(stock.lastUpdate)}
            </div>
          </div>
        ))}
      </div>

      {/* 活动监控 */}
      <div className="p-4 bg-card border border-border rounded-lg">
        <h4 className="text-sm font-semibold mb-3">活动监控</h4>
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span>策略执行次数/分钟</span>
            <span className="font-medium">156</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span>API请求/分钟</span>
            <span className="font-medium">89</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span>数据处理延迟</span>
            <span className="font-medium text-green-600">23ms</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span>CPU使用率</span>
            <div className="flex items-center space-x-2">
              <Progress value={32} className="w-20 h-1" />
              <span className="font-medium">32%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RealTimeMonitor